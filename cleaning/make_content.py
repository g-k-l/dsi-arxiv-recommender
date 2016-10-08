import os
import string
from multiprocessing import Pool, cpu_count
from threading import Thread
import psycopg2
from pdf_to_text import convert_pdf_to_txt as conv_pdf

'''
Go into each subfolder of source files, parse the unpacked source files.
Put the string on PSQL server. Push() calls push_src(), which multiprocesses push_one_src(),
which multithreads upload_one()
'''

def push():
    print 'Starting...'
    root_path = '/home/ubuntu/unpacked_src'
    walker = os.walk(root_path)
    pool = Pool()
    for step in walker:
        pool.apply_async(push_src, (step,))
    print 'All Processes Running.'
    pool.close()
    pool.join()
    print 'Completed Job.'

def push_src(step):
    for i, filename in enumerate(step[2]):
        t = Thread(target=push_one_src,args=(filename,step[0],))
        t.start()
    t.join()
    print 'Completed {}-th Step in Walk: '.format(i), step[0]

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
	    detex_path = path + '__detexed'
        detex_filename = filename + '__detexed'
        os.system('sudo detex {} > {}'.format(path, detex_path))
        with open(detex_path, 'r') as detexed:
            for line in detexed:
                if len(line.split())>5:
                    s ='\n'.join([s,line.strip().lower()])
        os.system('sudo rm {}'.format(detex_path))
    t = Thread(target=upload_one, args= (s, filename,))
    t.start()

    print get_arxiv_id(filename), ' Completed'

def upload_one(s, filename):
    update_query = '''UPDATE articles SET content = %s WHERE arxiv_id = %s'''
    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
        user='root', password='1873', database='arxivpsql') as conn:
        cur = conn.cursor()
        cur.execute(update_query, (s, get_arxiv_id(filename)))
        conn.commit()
    print 'Finished uploading: ', filename

def get_arxiv_id(filename):
    '''
    Parses the filename and attach it to the root url to get the arxiv_id
    '''
    root_url = 'http://arxiv.org/abs/'
    paper_id = filename
    break_idx = max(filename.rfind(l) for l in string.ascii_letters)
    if break_idx != -1:
        paper_id = '{}/{}'.format(filename[0:break_idx+1], filename[break_idx+1:])
    return root_url + paper_id


if __name__ == '__main__':
    push()
