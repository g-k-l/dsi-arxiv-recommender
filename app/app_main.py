import pandas as pd
from flask import Flask
from flask import render_template, request
from data_stats import data_master as dm

#Load the model and other infrastructure here
subjects_info= pd.read_csv('./data_stats/count_by_subject.txt')
subjects_info.columns = ['subject','subject_id','count']
subjects_info.sort(columns='subject',inplace=True)

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
    too_many = len(value_list)>2
    result_list=[]
    return render_template('result.html', result=result_list)

@app.route("/about.html")
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
