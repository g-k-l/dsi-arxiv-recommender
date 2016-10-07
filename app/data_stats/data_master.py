import csv
import os

path = os.path.dirname(os.path.abspath(__file__))

def get_data():
    ''' Tests for sample count per subject'''
    master_list = []
    with open(path+'/count_by_subject_content_not_null.txt', 'r') as f:
        data = csv.reader(f)
        col_names = data.next()
        for row in data:
            d = { col_name: value for col_name, value in zip(col_names, row)}
            master_list.append(d)
    return master_list
