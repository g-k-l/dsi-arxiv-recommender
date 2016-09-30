import xml_parser as xp
import psycopg2

# Get the database connection
psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
                        user='root', password='1873', database='arxivpsql')
cur = conn.cursor()

'''Columns: index, title, authors, subject, abstract, last_submitted, arxiv_id'''

sql_create = """CREATE TABLE IF NOT EXISTS articles (
            index serial PRIMARY KEY, title text, authors text,
            subject text, abstract text, last_submitted date, arxiv_id text UNIQUE )"""

cur.execute(sql_create)
conn.commit()
