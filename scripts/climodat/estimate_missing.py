"""Crude estimator of IEM Climate Stations

This is only run for the exceptions, when data is marked as missing for some
reason.  The main data estimator is found at `daily_estimator.py`.

This script utilizes the IEMRE web service to provide data.
"""
from __future__ import print_function
import sys
import requests
from pyiem.network import Table as NetworkTable
from pyiem.util import get_dbconn

# Database Connection
COOP = get_dbconn('coop')

state = sys.argv[1]
nt = NetworkTable("%sCLIMATE" % (state.upper(),))

URI = ("http://iem.local/iemre/daily/"
       "%(date)s/%(lat)s/%(lon)s/json")


def do_var(varname):
    """Run our estimator for a given variable"""
    ccursor = COOP.cursor()
    ccursor2 = COOP.cursor()
    sql = """
        select day, station from alldata_%s WHERE %s is null
        and day >= '1893-01-01' ORDER by day ASC
        """ % (state.lower(), varname)
    ccursor.execute(sql)
    dataformat = '%.0f' if varname in ['high', 'low'] else '%.2f'

    for i, row in enumerate(ccursor):
        day = row[0]
        station = row[1]
        if (station not in nt.sts or station[2] == 'C' or
                station.endswith('0000')):
            continue
        temp24hour = nt.sts[station]['temp24_hour']
        prefix = "12z_" if temp24hour != 0 else 'daily_'
        units = '_in' if varname == 'precip' else '_f'

        # pre 1900 dates strftime fails for
        wsuri = URI % {'date': "%s-%02i-%02i" % (day.year, day.month, day.day),
                       'lon': nt.sts[station]['lon'],
                       'lat': nt.sts[station]['lat']}
        req = requests.get(wsuri)
        try:
            estimated = req.json()['data'][0]
        except Exception as exp:
            print(("\n%s Failure:%s\n%s\nExp: %s"
                   ) % (station, req.content, wsuri, exp))
            continue
        newvalue = estimated["%s%s%s" % (prefix, varname, units)]
        # Prefer PRISM, if available
        if prefix == '12z_' and varname == 'precip':
            prism = estimated["prism_precip_in"]
            if prism is not None:
                newvalue = prism
        if newvalue is None:
            print("IEMRE Failure for day: %s" % (day,))
            continue

        print(('Set station: %s day: %s varname: %s value: %s'
               ) % (station, day, varname, dataformat % (newvalue,)))
        sql = """
            UPDATE alldata_%s SET estimated = true, %s = %s WHERE
            station = '%s' and day = '%s'
            """ % (state.lower(), varname,
                   dataformat % (newvalue,), station, day)
        sql = sql.replace(' nan ', ' null ')
        ccursor2.execute(sql)
        if i > 1000 and i % 1000 == 0:
            ccursor2.close()
            COOP.commit()
            ccursor2 = COOP.cursor()

    ccursor2.close()
    COOP.commit()


def main():
    """Go Main Go"""
    for varname in ['high', 'low', 'precip']:
        do_var(varname)


if __name__ == '__main__':
    main()
