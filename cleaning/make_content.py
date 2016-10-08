import os
import string
from multiprocessing import Pool, cpu_count
from threading import Thread
import psycopg2
from pdf_to_text import convert_pdf_to_txt as conv_pdf

'''
Go into each subfolder, parse the unpacked source files. Put the string on PSQL server.
Push() calls push_src(), which multiprocesses push_one_src(), which multithreads upload_one()
'''

def push():
    print 'Starting...'
    root_path = '/home/ubuntu/unpacked_src'
    walker = os.walk(root_path)
    for step in walker:
        push_src(step)
    print 'Made all processes.'

def push_src(step):
    pool = Pool()
    for filename in step[2]:
        pool.apply_async(push_one_src, (step[2],step[0]))
    pool.close()
    pool.join()
    print 'Completed One Step in Walk: ' step[0]

def push_one_src(filename, file_path):
    s = ''
    path = '/'.join([file_path, filename])
    if '.pdf' in filename:
        try:
            s = conv_pdf(path)
        except:
            print 'Critical Failure converting pdf at file: ', filename
            return
    else:
        try:
            with open(filename, 'r') as src:
                for line in enumerate(src):
                    s ='\n'.join([s,line.strip().lower()])
            detex_path = path + '__detexed'
            detex_filename = filename + '__detexed'
            os.system('sudo detex {} > {}'.format(filename, detex_filename))
            os.system('sudo rm {}'.format(detex_path))
        except:
            print 'Critical Failure processing: ', filename
            return
        t = Thread(target=upload_one, args= (s, filename, update_query))
        t.start()

    print filename, ' Completed'

def upload_one(s, filename, update_query):
    update_query = '''UPDATE articles SET content = %s WHERE arxiv_id = %s'''
    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
        user='root', password='1873', database='arxivpsql') as conn:
        cur = conn.cursor()
        cur.execute(update_query, (s, get_arxiv_id(filename)))
        conn.commit()
    print 'Finished uploading: ', filename

def get_arxiv_id(filename):
    root_url = 'http://arxiv.org/abs/'
    paper_id = filename
    break_idx = max(filename.rfind(l) for l in string.ascii_letters)
    if break_idx != -1:
        paper_id = '{}/{}'.format(filename[0:break_idx+1], filename[break_idx+1:])
    return root_url + paper_id


if __name__ == '__main__':
    push()
