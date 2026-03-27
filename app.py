from flask import Flask, render_template, url_for, redirect, request, session, jsonify

from bdd import create_client_table, insert_clients_table, create_discussions_table,  insert_disscussions_table, create_comments_table, insert_comments_table, create_likes_table, reset_all_db, insert_likes_table, select_all_discussions, select_comments, select_newest_discussion_id, select_discussion_by_id, update_like, get_discussion_likes,get_comment_likes, select_client_infos_from_email, check_if_exists_client, select_client_groupes, select_all_groupes, insert_groups_table, select_all_clients,  select_groupe_from_name, insert_group_members, select_client_groupes_by_id,get_user_by_id, insert_discussion_groups, select_discussion_groups, select_groupe_from_id, select_all_group_discussions,select_member_by_id, get_user_opinion, select_comments_ferme, select_comment_replies

import time
app = Flask(__name__)

app.secret_key = "ITTorsdyP2Gfzss33gjoY34otqT5BWC5"


roles_numeros= {
    "CEO": 3,
    "Manager": 2,
    "Employe": 1
}

with app.app_context():
    create_client_table()
    create_discussions_table()
    create_comments_table()
    create_likes_table()
    
@app.route("/")
def home():
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    result = select_all_group_discussions(session["id_client"])
    discussions=[]
    all_groupes = []

    for row in result:
        likes, dislikes = get_discussion_likes(row[0])
        res_groupes = select_discussion_groups(row[0])
        auteur = get_user_by_id(row[1])
        auteur = "" +auteur[1] +" "+ auteur[2]
        type = "FERMÉ"
        if(row[4] == "ouvert"):
            type = "OUVERT"

        groupes = []
        for groupe_id in res_groupes:
           groupes.append((groupe_id[0], select_groupe_from_id(groupe_id[0])[0]))
        discussions.append([row[2],row[3],str(row[0]),likes,dislikes, groupes, auteur, type, row[5], row[6]]) #row = [0:id, 1:id_client, 2:title, 3:content, 4:type, 5:date, 6: time]

    result = select_all_groupes()
    for row in result:
        all_groupes.append([row[0], row[1]])
    print(roles_numeros[session['role']])

    return render_template("homepage.html", discussions=discussions, first_name=session['first_name'], last_name=session['last_name'], email=session['email'], company=session['company'], role=roles_numeros[session['role']], role_name=session['role'], groupes=all_groupes)

@app.route("/main/<int:discussion_id>", methods=["GET", "POST"])
def main(discussion_id):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    id_poster, title, content, discussion_type = select_discussion_by_id(discussion_id)
    comments = []
    res=select_comments(discussion_id)
    if discussion_type == 'ferme': 
        res = select_comments_ferme(discussion_id)
        print("je susi ici main")
    for comment in res:
        id_comment=comment[0]
        id_client=comment[1]
        content_comment=comment[3]
        like_c=get_comment_likes(id_comment)[0]
        dislike_c=get_comment_likes(id_comment)[1]

        username=get_user_by_id(id_client)[2]+" "+get_user_by_id(id_client)[3]
        opinion = get_user_opinion(discussion_id, id_client)
        if opinion == None:
            opinion = "neutre"
        elif opinion[0] == 1:
            opinion = 'pour'
        else:
            opinion = 'contre'
        comments.append(dict(id_c=id_comment,content=content_comment,like=like_c,dislike=dislike_c,username=username, opinion=opinion))

    likes, dislikes = get_discussion_likes(discussion_id)
    return render_template("main.html", discussion_id=discussion_id, comments=comments, id_client=session["id_client"], title=title, content=content, likes=likes, dislikes=dislikes, first_name=session['first_name'], last_name=session['last_name'], email=session['email'], company=session['company'], role=roles_numeros[session['role']], role_name=session['role'], discussion_type=discussion_type)



@app.route("/commentaire/<int:discussion_id>/<int:reply>", methods=["POST"])
def commentaire(discussion_id, reply):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    content = request.form['commentaire']
    id_client = session['id_client'] 
    print(content)
    insert_comments_table(id_client, discussion_id, content, reply)
    return redirect(url_for("main", discussion_id= discussion_id))


@app.route("/ajouter_discussion", methods=["POST"])
def ajouter_discussion():
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    title = request.form['discussionTitle']
    content = request.form['discussionContent']
    
    groupes = request.form.getlist('groupes')
    
    id_client = session['id_client']
    type = request.form.get('discussionType')

    if title =='' or content=='' or groupes==[] or type==None:
        msg = 'tout les champs sont requises'
        return msg

    insert_disscussions_table(id_client, title, content, type)
    time.sleep(0.01)
    discussion_id = select_newest_discussion_id(id_client)[0]

    for groupe_id in groupes:
        insert_discussion_groups(groupe_id, discussion_id)

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
    origin_page = request.args.get('origin_page')
    target = "discussion"
    id_target = discussion_id
    update_like(id_client, id_target, target, action)

    if origin_page == 'homepage':
        return redirect(url_for("home"))
    elif origin_page == 'main':
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




#--------------------------- section group
@app.route('/groups', methods=['GET', 'POST'])
def groups_page():
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    msg = ''
    if request.method == "POST":
        group_name = request.form["groupName"]
        if group_name == "":
            msg = 'tout les champs sont requises'
        elif len(select_groupe_from_name(group_name)) > 0:
            msg="Ce group existe deja"
        else:
            insert_groups_table(group_name)
    id_client = session['id_client']
    groups_client = []
    res= select_client_groupes(id_client)
    for row in res:
        groups_client.append(dict(id=row[0],name=row[1]))

    all_groups = []
    res = select_all_groupes()
    for row in res:
        all_groups.append([row[0], row[1]])

    membres = []
    res =select_all_clients()
    for row in res:
        membres.append([row[0], row[1], row[2]])
    return render_template("groups.html", groups_client=groups_client, all_groups=all_groups, members=membres, msg=msg, first_name=session['first_name'], last_name=session['last_name'], email=session['email'], company=session['company'], role=roles_numeros[session['role']], role_name=session['role'])

@app.route('/allgroups', methods=['POST', 'GET'])
def take_all_groupes():
    all_groups = []
    res=select_all_groupes()
    for row in res :
        all_groups.append([row[0], row[1]])
    return all_groups


@app.route('/addgroupe/<int:group_id>', methods=['POST'])
def add_member_to_group(group_id):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    id_c_inserter= request.form['membres']
    id_groupe = group_id
    if len(select_client_groupes_by_id(id_groupe, id_c_inserter)) == 0:
        insert_group_members(id_groupe, id_c_inserter)
    return redirect(url_for("groups_page"))

@app.route('/group_info/<int:g_id>',methods=['POST','GET'])
def group_info(g_id):
    members=[]
    for member in select_member_by_id(g_id):
        nom_c=get_user_by_id(member[0])[1]
        last_name_c=get_user_by_id(member[0])[2]
        members.append(nom_c+" "+last_name_c)
    group_client=dict(name=select_groupe_from_id(g_id)[0],id=g_id,members=members)
        
    return render_template("groupinfo.html",group_client=group_client)


@app.route('/membres', methods=["GET"])
def membres():
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    return "bonjour"

@app.route('/profile/<int:id_c>')
def profile(id_c):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    my_profile = id_c == session["id_client"] #si la profile cible est le profile du user
    id_c, name, last_name, role = get_user_by_id(id_c)
    res = select_client_groupes_by_id(id_c)
    groupes = []
    for row in res:
        groupes.append(row[0])
    
    return render_template("profile.html", my_profile=my_profile, name=name, last_name=last_name, role=role, groupes=groupes)
    


########################## authentificatiojn
@app.route('/login_page', methods=['GET'])
def login_page():
    return render_template("login.html")

@app.route('/registry_page', methods=['GET'])
def registry_page():
    return render_template("registry.html")



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
    session['id_client'], session['email'], session['first_name'], session['last_name'], session['company'], session['role'] = client_infos[1::]
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
    
    result = check_if_exists_client(email, company)
    if result != None:
        msg = 'Ce compte existe deja'
        return render_template('registry.html', message=msg)
    
    insert_clients_table(email, first_name, last_name, password, company, role)

    
    return redirect(url_for('login_page')) #a changer quand on a hierarchy


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for("login_page"))


#--------------------------- 
@app.route("/show_all_replies/<int:discussion_id>/<int:comment_id>")
def show_all_replies(discussion_id, comment_id):
    res = select_comment_replies(comment_id)
    result = []
    for reply in res:
        opinion = get_user_opinion(discussion_id, reply[1])
        if opinion == None:
            opinion = "neutre"
        elif opinion[0] == 1:
            opinion = 'pour'
        else:
            opinion = 'contre'
        result.append({
            "id_c": reply[0],
            "id_client": reply[1],
            "content": reply[3],
            "like": get_comment_likes(reply[0])[0],
            "dislike": get_comment_likes(reply[0])[1],
            "username": get_user_by_id(reply[1])[2] + " " + get_user_by_id(reply[1])[3],
            "opinion": opinion  # adapt depending on your schema
        })

    return jsonify(result)

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



#################examples utiliations
@app.route("/insert_client_table")
def insert_client(): #fonction a modifier quand on a la page login
    insert_clients_table("test@test", 'test', 'test', 'test', 'test', 'test')
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
    insert_clients_table("test@test", 'test', 'test', 'test', 'test', 'CEO')
    print("reset successful")