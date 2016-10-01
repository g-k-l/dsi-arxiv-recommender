import os

'''
Move the files into directories for better handling.
'''

with open('md_listing.txt', 'r') as f:
    count = 0
    for line in f:
        if count % 10000 == 0:
            print 'Starting iteration {}'.format(count)
        filename = line.split()[2].strip()
        os.system('s3cmd mv s3://arxivmetadata/{} s3://arxivmetadata/bin{}/{}'.format(filename,count/10000,filename)
        count+=1
