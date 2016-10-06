import xml_parser as xp
import psycopg2

'''
Create the table to house the parsed information
'''
conn = psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
                        user='root', password='1873', database='arxivpsql')
cur = conn.cursor()

'''Columns: index, title, authors, subject, abstract, last_submitted, arxiv_id'''

sql_create = """CREATE TABLE IF NOT EXISTS articles (
            index serial PRIMARY KEY, title text, authors text ARRAY,
            subject text, abstract text, last_submitted date, arxiv_id text UNIQUE )"""

cur.execute(sql_create)
conn.commit()

'''
Parse XML file and store in Postgres
Comment: psycopg2 connection is thread safe, but not multiprocess safe ?
'''

import os
import boto3
import threading
from xml_parser import get_fields

id_key = os.environ['AWS_ACCESS_KEY_ID']
secret_key = os.environ['AWS_SECRET_ACCESS_KEY']

s3 = boto3.resource('s3')
bucket = s3.Bucket('arxivmetadata')

query_template = """INSERT INTO articles
                    (title, authors, subject, abstract, last_submitted, arxiv_id) VALUES (%s, %s, %s, %s, %s, %s)"""

def to_psql(obj):
    key = obj.key
    if '.xml' not in key:
        print '{} not a XML file'.format(key)
        return
    body = obj.get()['Body'].read()
    values = get_fields(body)

    try:
        cur.execute(query_template,values)
    except psycopg2.IntegrityError:
        print 'IntegrityError: Duplicates'
	conn.rollback()

threads=[]
i=0
for obj in bucket.objects.all():
    if i % 10000 == 0:
        conn.commit()
        print 'iteration', i
    to_psql(obj)
#    t = threading.Thread(target=to_psql, args=(obj,))
#    threads.append(t)
#    t.start()
#    if len(threads) % 10000==0:
    i+=1
#        threads[-1].join()
#        conn.commit()
#	print 'batch {} complete'.format(i)
#        threads = []
