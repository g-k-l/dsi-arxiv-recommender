
import os
import threading
import boto3
import psycopg2
from xml_parser import get_fields

def update_title(obj):
    if '.xml' not in obj.key:
        return

    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
            user='root', password='1873', database='arxivpsql') as conn:
	    cur = conn.cursor()
        query = '''UPDATE articles SET title = %s
            WHERE arxiv_id = %s;'''
	    fields = get_fields(obj.get()['Body'].read())
	    title, arxiv_id = fields[0], fields[-1]
        cur.execute(query, (title,arxiv_id))
        conn.commit()

id_key = os.environ['AWS_ACCESS_KEY_ID']
secret_key = os.environ['AWS_SECRET_ACCESS_KEY']

s3 = boto3.resource('s3')
bucket = s3.Bucket('arxivmetadata')

threads = []

for obj in bucket.objects.all():
    t = threading.Thread(target=update_title, args=(obj,))
    threads.append(t)
    t.start()
    if len(threads) % 10000 == 0:
        map(lambda t: t.join(), threads)
        print 'Batch {} completed.'.format(len(threads)/10000)
        threads = []
