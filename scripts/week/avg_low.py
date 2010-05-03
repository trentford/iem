# Generate mean low temperature for the week

import sys, os
sys.path.append("../lib/")
import iemplot

import mx.DateTime
now = mx.DateTime.now()

from pyIEM import iemdb
i = iemdb.iemdb()
iem = i['iem']

# Compute normal from the climate database
sql = """
select station, 
  x(geom) as lon, y(geom) as lat, 
  avg(min_tmpf) as min_tmpf
from summary 
WHERE max_tmpf > -50 
and day >= ('TODAY'::date - '7 days'::interval)
and day < 'TODAY' 
and network ~* 'ASOS' and network != 'IQ_ASOS'
GROUP by station, lon, lat
"""

lats = []
lons = []
vals = []
rs = iem.query(sql).dictresult()
for i in range(len(rs)):
  lats.append( rs[i]['lat'] )
  lons.append( rs[i]['lon'] )
  vals.append( rs[i]['min_tmpf'] )

cfg = {
 'wkColorMap': 'BlAqGrYeOrRe',
 'nglSpreadColorStart': 2,
 'nglSpreadColorEnd'  : -1,
 '_title'             : "Iowa Past 7 Days Average Low",
 '_valid'             : "%s - %s" % ((now - mx.DateTime.RelativeDateTime(days=7)).strftime("%d %b %Y"), now.strftime("%d %b %Y") ),
 'lbTitleString'      : "[F]",
}
# Generates tmp.ps
tmpfp = iemplot.simple_contour(lons, lats, vals, cfg)

pqstr = "plot c 000000000000 summary/7day/iaavg_min_tmpf.png bogus png"
iemplot.postprocess(tmpfp, pqstr)
