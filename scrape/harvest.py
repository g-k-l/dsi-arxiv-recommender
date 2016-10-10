
'''
Credits to sepehr125:

Harrvest metadata of ArXiv articles (including abstract)
for given subject or date range
from Open Archives Initiative (OAI).
More information: http://arxiv.org/help/oa/index
make sure you have installed oaiharvest already:
https://pypi.python.org/pypi/oaiharvest
'''

import os
from concurrent import futures
from datetime import date, timedelta

start_date = date(1992,1,1)
end_date = date(2016,9,24)
output_dir = '../tmp'
current_date = start_date
td = timedelta(days=180)

while current_date+td != end_date:
    try:
        get_xml = "oai-harvest --from %s --until %s -d %s http://export.arxiv.org/oai2"%(str(current_date), str(current_date+td), output_dir)
        os.system(get_xml)
        move_to_s3 = "aws s3 mv ../tmp s3://arxivmetadata --recursive"
        os.system(move_to_s3)
        current_date+=td
    except:
        print 'An error occured. Last iteration current_date: {}'.format(current_date)
