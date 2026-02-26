from flask import Flask, render_template, url_for, redirect, request, session
from bdd import create_client_table, insert_clients_table, create_discussions_table,  insert_disscussions_table, create_comments_table, insert_comments_table, create_likes_table, reset_all_db, insert_likes_table, select_all_discussions, select_comments, select_newest_discussion_id, select_discussion_by_id, update_like, get_discussion_likes,get_comment_likes, select_client_infos_from_email, check_if_exists_client
import time
app = Flask(__name__)

app.secret_key = "ITTorsdyP2Gfzss33gjoY34otqT5BWC5"


with app.app_context():
    create_client_table()
    create_discussions_table()
    create_comments_table()
    create_likes_table()
    
@app.route("/")
def home():
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    result = select_all_discussions()

    discussions=[]

    for row in result:
        discussions.append([row[2],row[3],str(row[0])])
    print(discussions)
    return render_template("homepage.html", discussions=discussions, first_name=session['first_name'], last_name=session['last_name'], email=session['email'], company=session['company'], role=session['role'], group_name=session['group_name'])

@app.route("/main/<int:discussion_id>", methods=["GET", "POST"])
def main(discussion_id):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    id_poster, title, content = select_discussion_by_id(discussion_id)
    comments = []
    for comment in select_comments(discussion_id):
        comments.append(dict(id_c=comment[0],content=comment[3],like=get_comment_likes(comment[0])[0],dislike=get_comment_likes(comment[0])[1]))

    likes, dislikes = get_discussion_likes(discussion_id)
    return render_template("main.html", discussion_id=discussion_id, comments=comments, id_client=session["id_client"], title=title, content=content, likes=likes, dislikes=dislikes, first_name=session['first_name'], last_name=session['last_name'], email=session['email'], company=session['company'], role=session['role'], group_name=session['group_name'])



@app.route("/commentaire/<int:discussion_id>", methods=["POST"])
def commentaire(discussion_id):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    content = request.form['commentaire']
    id_client = session['id_client'] 
    
    insert_comments_table(id_client, discussion_id, content)
    return redirect(url_for("main", discussion_id= discussion_id))


@app.route("/ajouter_discussion", methods=["POST"])
def ajouter_discussion():
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    title = request.form['discussionTitle']
    content = request.form['discussionContent']
    
    id_client = session['id_client']
    
    insert_disscussions_table(id_client, title, content)
    time.sleep(0.01)
    discussion_id = select_newest_discussion_id(id_client)[0]

    return redirect(url_for("main", discussion_id= discussion_id))



@app.route("/like_discussion/<int:discussion_id>/<action>")
def like_discussion(discussion_id, action):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    id_client = session['id_client'] 
    if(action == "like"):
        action = 1
    elif(action == "unlike"):
        action = -1
    else:
        return 
    
# a changer
    target = "discussion"
    id_target = discussion_id
    update_like(id_client, id_target, target, action)
    return redirect(url_for("main", discussion_id=discussion_id))

@app.route("/like_comment/<int:discussion_id>/<int:comment_id>/<action>")
def like_comment(discussion_id,comment_id, action):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    
    id_client = session['id_client'] 
    if(action == "like"):
        action = 1
    elif(action == "unlike"):
        action = -1
    else:
        return 
    
# a changer
    target = "comment"
    id_target = comment_id
    update_like(id_client, id_target, target, action)
    return redirect(url_for("main", discussion_id=discussion_id))



@app.route('/login_page', methods=['GET'])
def login_page():
    return render_template("login.html")

@app.route('/registry_page', methods=['GET'])
def registry_page():
    return render_template("registry.html")


# login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return redirect(url_for('login_page'))
    
    message = ''

    email = request.form["email"]
    password = request.form["password"]
    if not email or not password:
        message = "tout les champs sont requis"
        return render_template('login.html', message= message)
    
    client_infos = select_client_infos_from_email(email)
    if not(client_infos):
        message = "Email or password is incorrect. Please try again"
        return render_template('login.html', message= message)
    if password != client_infos[0]:
        message = "Email or password is incorrect. Please try again"
        return render_template('login.html', message= message)
    
    session["logged_in"] = True
    session['id_client'], session['email'], session['first_name'], session['last_name'], session['company'], session['role'], session['group_name'] = client_infos[1::]
    return redirect(url_for("home"))



@app.route('/registry', methods=['GET', 'POST'])
def registry():
    if request.method == "GET":
        return redirect(url_for('registry_page'))
    ##si method est post
    email = request.form["email"]
    first_name = request.form["first-name"]
    last_name = request.form["last-name"]
    password = request.form["new-password"]
    company = request.form["company-name"]
    role = request.form["role"]
    group_name = 'groupe A' ##a changer
    result = check_if_exists_client(email, company)
    if result != None:
        msg = 'Ce compte existe deja'
        return render_template('registry.html', message=msg)
    
    insert_clients_table(email, first_name, last_name, password, company, role, group_name)

    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    return redirect(url_for("home"))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for("login_page"))


#--------------------------- 

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
    email = "tamer@gmail.com"
    name = "Tamer"
    last_name = "Masri"
    password= "3onjour"
    company = "Debatteurs"
    role = "CEO"
    group_name = "groupe A"
    insert_clients_table(email, name, last_name, password, company, role, group_name)
    return "inserted clients table succesfully!"




@app.route("/insert_discussions_table")
def insert_discussions(): # fonction a modifier quand on a l'option de cree une nouvelle discussion
    id_c = 1
    title = "Jason"
    content= "Jason son nom est jason"
    insert_disscussions_table(id_c, title, content)
    return "inserted clients table succesfully!"


@app.route("/insert_comments_table")
def insert_comments(): # fonction a modifier quand on a l'option de cree une nouvelle commentaire
    id_c = 1
    id_d = 1
    content= "Tamer is the vire!!!"
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



#-------------------------------------------------


###COMMANDS
@app.cli.command("db:reset") #usage    flask db:reset
def reset_database():
    "resets the database tables"
    print("Dropping Database")
    reset_all_db()
    print("reset successful")