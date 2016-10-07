from flask import Flask, render_template, jsonify
from data_stats import data_master as dm

app = Flask(__name__)

@app.route("/data")
def data():
    return jsonify(dm.get_data())

@app.route("/display")
def display():
    with open('index.html') as f:
        return f.read()

if __name__ == '__main__':
    app.run()
