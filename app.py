from flask import Flask, render_template, url_for

app = Flask(__name__)

app.secret_key = "ITTorsdyP2Gfzss33gjoY34otqT5BWC5"

@app.route("/")
def home():
    return render_template("homepage.html")

@app.route("/main/<int:discussion_id>")
def main(discussion_id):
    return render_template("main.html", discussion_id=discussion_id)
