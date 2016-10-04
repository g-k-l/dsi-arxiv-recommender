import os
import string
import psycopg2
import threading
from pdf_to_text import convert_pdf_to_txt as conv_pdf
from multiprocessing import Process, cpu_count

'''
Go into each subfolder, parse the unpacked source files. Put the string on PSQL server.
TODO: Separate handling for pdf files.
'''

def push():
    print 'Starting...'
    root_path = '/home/ubuntu/unpacked_src'
    walker = os.walk(root_path)

    processes = []
    for step in walker:
        if len(processes) == cpu_count():
            map(lambda p: p.join(), processes)
            processes = []
        try:
            p = Process(target=push_src, args=(step,))
            processes.append(p)
            p.start()
        except:
            print 'Critical Failure inside folder: ', step[0]
            print 'Exiting...'
    print 'Made all processes.'

def push_src(step):
    threads = []
    for filename in step[2]:
        try:
            t = threading.Thread(target=push_one_src, args=(filename,step[0]))
            threads.append(t)
            t.start()
        except:
            print 'Critical Failure at file: ', filename


def push_one_src(filename, file_path):

    s = ''
    path = '/'.join([file_path, filename])
    update_query = '''UPDATE articles SET content = %s WHERE arxiv_id = %s'''

    if '.pdf' in filename:
        s = conv_pdf(path)
    else:
        detex_path = path + '__detexed'
        detex_filename = filename + '__detexed'
        os.system('sudo detex {} > {}'.format(filename, detex_filename))
        with open(detex_path, 'r') as src:
            for line in src:
                s =' '.join([s,line.strip().lower()])
        os.system('sudo rm {}'.format(detex_path))

    s = filter(lambda x: x in string.printable, s)

    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
        user='root', password='1873', database='arxivpsql') as conn:
        cur = conn.cursor()
        cur.execute(update_query, (s, get_arxiv_id(filename)))
        conn.commit()
    print filename, ' Completed'

def get_arxiv_id(filename):
    root_url = 'http://arxiv.org/abs/'
    paper_id = filename
    break_idx = max(filename.rfind(l) for l in string.ascii_letters)
    if break_idx != -1:
        paper_id = '{}/{}'.format(filename[0:break_idx+1], filename[break_idx+1:])
    return root_url + paper_id


if __name__ == '__main__':
    push()
