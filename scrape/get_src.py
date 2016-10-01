import os

'''
This module obtains the arXiv source files
Requires s3cmd 1.6.x
'''

os.system('s3cmd get s3://arXiv/src/\* --recursive') #this takes a long time
os.system('')

from boto.s3.connection import S3Connection

id_key = os.environ['AWS_ACCESS_KEY_ID']
secret_key = os.environ['AWS_SECRET_ACCESS_KEY']

conn = S3Connection(id_key, secret_key)
bucket = conn.create_bucket('arxivmetadata')
