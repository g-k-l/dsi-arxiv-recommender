
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
from boto.s3.connection import S3Connection
from boto.s3.key import Key

id_key = os.environ['AWS_ACCESS_KEY_ID']
secret_key = os.environ['AWS_SECRET_ACCESS_KEY']

conn = S3Connection(id_key, secret_key)
bucket = conn.create_bucket('arxiv_aws_meta_dump')

k = Key(bucket)




start_date = '1992-01-01'
end_date = '2016-09-24'
output_dir = '../meta_data'
# run the following at the terminal, (altering the dates to suit your needs)
cmd = "oai-harvest --from %s --until %s -d %s http://export.arxiv.org/oai2"%(start_date, end_date, output_dir)
os.system(cmd)
