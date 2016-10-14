import cPickle as pickle
from itertools import combinations
import pandas as pd
from flask import Flask
from flask import render_template, request, redirect
from data_stats import data_master as dm

#Load the model and other infrastructure here
subjects_info= pd.read_csv('./data_stats/count_by_subject.txt')
subjects_info.columns = ['subject','subject_id','count']
subjects_info.sort(columns='subject',inplace=True)

results_dict = {}
comb = combinations(range(1,147), 2)

# for subject_id_1, subject_id_2 in comb:
#     file_path = '../model/assets/precompute/{}_{}_scores_list.pkl'.format(subject_id_1, subject_id_2)
#     with open(file_path, 'rb') as f:
#         results_dict[(subject_id_1, subject_id_2)] = pickle.load(f)


app = Flask(__name__)
@app.route("/")
@app.route("/index.html")
def index():
    #Run the model here to get some result.
    #Pass the result to Jinja template in render_template
    return render_template('index.html',subjects=subjects_info['subject'].tolist())

@app.route("/result.html", methods=['POST'])
def result():
    value_list = request.form.getlist('select[]')
    not_two = len(value_list) != 2
    if not_two:
        return redirect("/index.html")

    subject_id_1 = int(subjects_info[subjects_info['subject']==value_list[0]]['subject_id'])
    subject_id_2 = int(subjects_info[subjects_info['subject']==value_list[1]]['subject_id'])

    # result_list = results_dict[(min(subject_id_1, subject_id_2), max(subject_id_1,subject_id_2))]
    result_list = [('http://www.google.com', 0.212123121), ('more url', 0.126318894)]
    return render_template('result.html', results=result_list)

@app.route("/about.html")
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
