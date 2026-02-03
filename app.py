from flask import Flask, render_template, url_for
from .bdd import create_client_table, create_discussions_table, create_comments_table, create_likes_table, insert_clients_table, insert_disscussions_table, insert_comments_table  

app = Flask(__name__)

app.secret_key = "ITTorsdyP2Gfzss33gjoY34otqT5BWC5"

@app.route("/")
def home():
    return render_template("homepage.html")

@app.route("/main/<int:discussion_id>")
def main(discussion_id):
    return render_template("main.html", discussion_id=discussion_id)

@app.route("/main/<int:discussion_id>")
def main(discussion_id):
    return render_template("main.html", discussion_id=discussion_id)


@app.route("/create_client_table")
def create_client():
    return create_client_table()



