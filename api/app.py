from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from uuid import uuid4
from chat import ask_question
import os
import sys
import click
import datetime

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(f"{basedir}/../")
from data import index_data
from data.util import get_current_date

app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
CORS(app)


@app.route("/")
def api_index():
    return app.send_static_file("index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    request_json = request.get_json()
    question = request_json.get("question")
    if question is None:
        return jsonify({"msg": "Missing question from request JSON"}), 400

    session_id = request.args.get("session_id", str(uuid4()))
    return Response(ask_question(question, session_id), mimetype="text/event-stream")

@app.cli.command()
@click.option('--length', default=50)
@click.option('--day_before', default=1)
def update_naver_news(length, day_before):
    index_data.add_naver_news_data(length=length, day_before=day_before)

@app.cli.command()
@click.option('--start_date', default=get_current_date, help='Start date in YYYYMMDD format')
@click.option('--end_date', default=get_current_date, help='End date in YYYYMMDD format')
def update_stock(start_date, end_date):
    index_data.add_stock_data(start_date, end_date)

@app.cli.command()
@click.option('--start_date', default=get_current_date, help='Start date in YYYYMMDD format')
@click.option('--end_date', default=get_current_date, help='End date in YYYYMMDD format')
def update_dart(start_date, end_date):
    index_data.add_dart_data(start_date, end_date)

@app.cli.command()
@click.option('--start_date', default=get_current_date, help='Start date in YYYYMMDD format')
@click.option('--end_date', default=get_current_date, help='End date in YYYYMMDD format')
def update_edgar(start_date, end_date):
    index_data.add_edgar_data(start_date, end_date)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
