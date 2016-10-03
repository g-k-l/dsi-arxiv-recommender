import os
import string
import psycopg2
import threading

'''
Go into each subfolder, parse the unpacked source files. Put the string on PSQL server.
TODO: Separate handling for pdf files.
'''

def push():
    print 'Starting...'
    root_path = '/home/ubuntu/unpacked_src'
    walker = os.walk(root_path)

    threads = []
    for step in walker:
        try:
            t = threading.Thread(target=push_src, args=(step,))
            threads.append(t)
            t.start()
        except:
            print 'Critical Failure inside folder: ', step[0]
            print 'Exiting...'
    print 'Made all threads.'

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

    if '.pdf' in filename:
        print 'Skipping: {} is a pdf file.'.format(filename)
        return

    s = ''
    update_query = '''UPDATE articles SET content = %s WHERE arxiv_id = %s'''

    with open('/'.join([file_path, filename]), 'r') as src:
        copy = False
        for line in src:
            if 'begin{document}' in line.lower():
                copy = True
                s += 'being{document}'
            elif 'end{document}' in line.lower():
                s += 'end{document}'
                break
            elif copy:
                s =' '.join([s,line.strip().lower()])
        if copy:
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
