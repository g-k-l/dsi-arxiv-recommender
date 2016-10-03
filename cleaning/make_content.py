import os
import psycopg2
import threading

conn = psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
                        user='root', password='1873', database='arxivpsql')
cur = conn.cursor()

# walker = os.walk('~/unpacked_src')
walker = os.walk('~/repo/final_project_test/content_test/'
