from flask import Flask, render_template, send_from_directory, jsonify
from data_stats import data_master as dm

# app = Flask(__name__, static_url_path='')
app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')
#
# @app.route("/data")
# def data():
#     return str(dm.get_data())
#
# @app.route("/display")
# def display():
#     return send_from_directory('','index.html')

if __name__ == '__main__':
    app.run()
    # url_for('static','index.html')
    # url_for('static','bubble.html')
