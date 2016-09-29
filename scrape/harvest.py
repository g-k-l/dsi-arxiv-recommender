
'''
Credits to sepehr125:

Harrvest metadata of ArXiv articles (including abstract)
for given subject or date range
from Open Archives Initiative (OAI).
More information: http://arxiv.org/help/oa/index
make sure you have installed oaiharvest already:
https://pypi.python.org/pypi/oaiharvest
'''
#
# import os
# from boto.s3.connection import S3Connection
# from boto.s3.key import Key
#
# id_key = os.environ['AWS_ACCESS_KEY_ID']
# secret_key = os.environ['AWS_SECRET_ACCESS_KEY']
#
# conn = S3Connection(id_key, secret_key)
# bucket = conn.create_bucket('arxiv_aws_meta_dump')
#
# k = Key(bucket)

import os
from datetime import date, timedelta

# start_date = datetime(1992,1,1)
start_date = date(2016,9,15)
end_date = date(2016,9,24)
output_dir = '../tmp'
current_date = start_date
td = timedelta(days=1)

while current_date+td != end_date:
        get_xml = "oai-harvest --from %s --until %s -d %s http://export.arxiv.org/oai2"%(str(current_date), str(current_date+td), output_dir)
        os.system(get_xml)
        push_to_s3 = ""
        current_date+=td
