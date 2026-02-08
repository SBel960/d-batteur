from flask import Flask, render_template, url_for
from bdd import create_client_table, insert_clients_table, create_discussions_table,  insert_disscussions_table, create_comments_table, insert_comments_table, create_likes_table, reset_all_db, insert_likes_table
app = Flask(__name__)

app.secret_key = "ITTorsdyP2Gfzss33gjoY34otqT5BWC5"


with app.app_context():
    create_client_table()
    create_discussions_table()
    create_comments_table()
    create_likes_table()
    
@app.route("/")
def home():
    return render_template("homepage.html")

@app.route("/main/<int:discussion_id>")
def main(discussion_id):
    return render_template("main.html", discussion_id=discussion_id)



@app.route("/create_client_table")
def create_client():
    create_client_table()
    return "created clients table succesfully!"

@app.route("/create_discussions_table")
def create_discussions():
    create_discussions_table()
    return "created discussions table succesfully!"

@app.route("/create_comments_table")
def create_comments():
    create_comments_table()
    return "created comments table succesfully!"

@app.route("/create_likes_table")
def create_likes():
    create_likes_table()
    return "created likes table succesfully!"


@app.route("/insert_client_table")
def insert_client(): #fonction a modifier quand on a la page login
    name = "Tamer"
    last_name = "Masri"
    password= "3onjour"
    company = "Debatteurs"
    role = "CEO"
    group_name = "groupe A"
    insert_clients_table(name, last_name, password, company, role, group_name)
    return "inserted clients table succesfully!"




@app.route("/insert_discussions_table")
def insert_discussions(): # fonction a modifier quand on a l'option de cree une nouvelle discussion
    id_c = 1
    title = "3onjour"
    content= "le 3 est un lettre arabe dont le son ne peut pas etre represente par l'alphabet latin donc on utilise le chiffre 3 pour le representer (on parle arabe avec le keyboard latin souvent, car le keyboard arabe a 10000 touche cest dificile)"
    insert_disscussions_table(id_c, title, content)
    return "inserted clients table succesfully!"


@app.route("/insert_comments_table")
def insert_comments(): # fonction a modifier quand on a l'option de cree une nouvelle commentaire
    id_c = 1
    id_d = 1
    content= "Tamer is the best!!!"
    insert_comments_table(id_c, id_d, content)
    return "inserted comments table succesfully!"

@app.route("/insert_likes_table")
def insert_likes(): # fonction a modifier quand on a l'option de like/dislike un commentaire/discussion
    id_c = 1
    target = "comment"
    id_target = 1
    like = 1
    insert_likes_table(id_c, target, id_target, like)
    return "inserted likes table succesfully!"


@app.cli.command("db:reset")
def reset_database():
    "resets the database tables"
    print("Dropping Database")
    reset_all_db()
    