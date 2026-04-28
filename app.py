from flask import Flask, render_template, url_for, redirect, request, session, jsonify,flash

from bdd import (
    create_client_table, insert_clients_table,
    create_discussions_table, insert_disscussions_table,
    create_comments_table, insert_comments_table,
    create_likes_table, reset_all_db, insert_likes_table,
    select_all_discussions, select_comments, select_newest_discussion_id,
    select_discussion_by_id, update_like, get_discussion_likes,
    get_comment_likes, select_client_infos_from_email, check_if_exists_client,
    select_client_groupes, select_all_groupes, insert_groups_table,
    select_all_clients, select_groupe_from_name, insert_group_members,
    select_client_groupes_by_id, get_user_by_id, insert_discussion_groups,
    select_discussion_groups, select_groupe_from_id, select_all_group_discussions,
    select_member_by_id, select_clients_not_in_group, delete_member,
    update_group, delete_group, get_user_opinion, select_comments_ferme,
    select_comment_replies, update_discussion, delete_discussiongroups,
    get_score_proposition, create_groups_table, create_group_members_table,
    create_discussion_groups_table, get_email, select_comment_by_id,
    delete_discussion_from_id, update_discussion_state,delete_client,select_role_client,
    update_role
)

import time

app = Flask(__name__)
app.secret_key = "ITTorsdyP2Gfzss33gjoY34otqT5BWC5"

roles_numeros = {
    "CEO":     3,
    "Manager": 2,
    "Employe": 1,
}

with app.app_context():
    create_client_table()
    create_discussions_table()
    create_comments_table()
    create_likes_table()
    create_groups_table()
    create_group_members_table()
    create_discussion_groups_table()


# ─── Accueil ──────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))

    discussions = []
    all_groupes = []

    for row in select_all_group_discussions(session["id_client"]):
        likes, dislikes = get_discussion_likes(row[0])
        if(get_user_by_id(row[1])==None):
        
            auteur_nom ="Utilisateur supprimé"
        else:
            auteur = get_user_by_id(row[1])
            auteur_nom = auteur[1] + " " + auteur[2]
        type_disc  = "OUVERT" if row[4] == "ouvert" else "FERMÉ"

        groupes = []
        for groupe_id in select_discussion_groups(row[0]):
            groupes.append([groupe_id[0], select_groupe_from_id(groupe_id[0])[0]])

        # row : [0:id, 1:id_client, 2:title, 3:content, 4:type, 5:date, 6:time, 7:state, 8:cloner_par]
        discussions.append([
            row[2], row[3], str(row[0]), likes, dislikes,
            groupes, auteur_nom, type_disc, row[5], row[6], row[7], row[8],
        ])

    for row in select_all_groupes():
        all_groupes.append([row[0], row[1]])

    return render_template(
        "homepage.html",
        discussions=discussions,
        groupes=all_groupes,
        first_name=session['first_name'], last_name=session['last_name'],
        email=session['email'], company=session['company'],
        role=roles_numeros[session['role']], role_name=session['role'],
    )


# ─── Discussion ───────────────────────────────────────────────────────────────

@app.route("/main/<int:discussion_id>", methods=["GET"])
def main(discussion_id):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))

    id_poster, title, content, discussion_type, discussion_state, id_clone = select_discussion_by_id(discussion_id)
    cloned = id_clone is not None

    comments        = []
    cloned_comments = []

    res = select_comments(discussion_id) if discussion_type == 'ouvert' else select_comments_ferme(discussion_id)

    for comment in res:
        id_comment   = comment[0]
        id_client    = comment[1]
        type_comment = comment[4]
        like_c, dislike_c = get_comment_likes(id_comment)
        score    = (like_c - dislike_c) + get_score_proposition(id_comment) if type_comment == 'proposition' else None
        if(get_user_by_id(id_client) == None):
            username="Utilisateur supprimé"
        else:
            username = get_user_by_id(id_client)[1] + " " + get_user_by_id(id_client)[2]
        opinion  = get_user_opinion(discussion_id, id_client)
        if opinion is None:    opinion = "neutre"
        elif opinion[0] == 1: opinion = "pour"
        else:                  opinion = "contre"
        comments.append(dict(
            id_c=id_comment, content=comment[3], like=like_c, dislike=dislike_c,
            username=username, opinion=opinion, type=type_comment, avis=comment[5],
            score=score, reply_count=len(select_comment_replies(id_comment)), etat=comment[7],
        ))

    if id_clone is not None:
        for comment in select_comments_ferme(id_clone):
            id_comment   = comment[0]
            id_client    = comment[1]
            type_comment = comment[4]
            like_c, dislike_c = get_comment_likes(id_comment)
            score    = (like_c - dislike_c) + get_score_proposition(id_comment) if type_comment == 'proposition' else None
            if(get_user_by_id(id_client) == None):
                username="Utilisateur supprimé"
            else:
                username = get_user_by_id(id_client)[1] + " " + get_user_by_id(id_client)[2]
            opinion  = get_user_opinion(discussion_id, id_client)
            if opinion is None:    opinion = "neutre"
            elif opinion[0] == 1: opinion = "pour"
            else:                  opinion = "contre"
            cloned_comments.append(dict(
                id_c=id_comment, content=comment[3], like=like_c, dislike=dislike_c,
                username=username, opinion=opinion, type=type_comment, avis=comment[5],
                score=score, reply_count=len(select_comment_replies(id_comment)), etat='closed',
            ))

    if discussion_type == 'ouvert':
        sort_key = lambda c: c['score'] if c['score'] is not None else (c['like'] - c['dislike'])
        comments.sort(key=sort_key, reverse=True)
        cloned_comments.sort(key=sort_key, reverse=True)

    likes, dislikes = get_discussion_likes(discussion_id)
    return render_template(
        "main.html",
        discussion_id=discussion_id, comments=comments, cloned_comments=cloned_comments,
        id_client=session["id_client"], title=title, content=content,
        likes=likes, dislikes=dislikes,
        discussion_type=discussion_type, discussion_state=discussion_state, cloned=cloned,
        first_name=session['first_name'], last_name=session['last_name'],
        email=session['email'], company=session['company'],
        role=roles_numeros[session['role']], role_name=session['role'],
    )


@app.route("/commentaire/<int:discussion_id>/<int:reply>", methods=["POST"])
def commentaire(discussion_id, reply):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    content = request.form['commentaire']
    type_c  = request.form.get('type', 'normal')
    avis    = request.form.get('avis')
    insert_comments_table(session['id_client'], discussion_id, content, type_c, avis, reply)
    if reply != 0:
        return jsonify({'content': content, "type_c":type_c, "avis":avis})

    return redirect(url_for("main", discussion_id=discussion_id))


@app.route("/ajouter_discussion", methods=["POST"])
def ajouter_discussion():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    title   = request.form['discussionTitle']
    content = request.form['discussionContent']
    groupes = request.form.getlist('groupes')
    type_d  = request.form.get('discussionType')

    if not title or not content or not groupes or not type_d:
        return 'tout les champs sont requises'

    insert_disscussions_table(session['id_client'], title, content, type_d)
    time.sleep(0.01)
    discussion_id = select_newest_discussion_id(session['id_client'])[0]
    for groupe_id in groupes:
        insert_discussion_groups(groupe_id, discussion_id)
    return redirect(url_for("main", discussion_id=discussion_id))


@app.route("/modifier_discussion/<int:d_id>", methods=["POST"])
def modifier_discussion(d_id):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    title       = request.form['discussionTitle']
    content     = request.form['discussionContent']
    new_groupes = set(request.form.getlist('groupes'))
    update_discussion(title, content, d_id, new_groupes)
    return redirect(url_for("main", discussion_id=d_id))


@app.route("/clotre_discussion/<int:d_id>/<action>", methods=["POST"])
def clotre_discussion(d_id, action):
    update_discussion_state(d_id, action)
    return redirect(url_for('home'))


@app.route("/cloner_discussion/<int:d_id>", methods=["POST"])
def cloner_discussion(d_id):
    groups = request.form.getlist('groupes')
    id_client, title, content, type_discussion, etat, cloned_id = select_discussion_by_id(d_id)
    insert_disscussions_table(id_c=id_client, title=title, content=content,
                               type=type_discussion, cloned_from=d_id)
    discussion_id = select_newest_discussion_id(id_client)[0]
    for g_id in groups:
        insert_discussion_groups(id_group=g_id, id_discussion=discussion_id)
    return redirect(url_for('main', discussion_id=discussion_id))


@app.route("/delete_discussion/<int:d_id>", methods=["POST"])
def delete_discussion(d_id):
    delete_discussion_from_id(d_id)
    return redirect(url_for('home'))


# ─── Votes ────────────────────────────────────────────────────────────────────

@app.route("/like_discussion/<int:discussion_id>/<action>")
def like_discussion(discussion_id, action):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    id_client = session['id_client']
    if action == "like":     action_val = 1
    elif action == "unlike": action_val = -1
    else:                    return redirect(url_for("home"))

    update_like(id_client, discussion_id, "discussion", action_val)
    if request.args.get('origin_page') == 'homepage':
        return redirect(url_for("home"))
    likes, dislikes = get_discussion_likes(discussion_id)
    return jsonify({"likes": likes, "dislikes": dislikes})


@app.route("/like_comment/<int:discussion_id>/<int:comment_id>/<action>")
def like_comment(discussion_id, comment_id, action):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    id_client = session['id_client']
    if action == "like":     action_val = 1
    elif action == "unlike": action_val = -1
    else:                    return redirect(url_for("main", discussion_id=discussion_id))

    update_like(id_client, comment_id, "comment", action_val)
    likes, dislikes = get_comment_likes(comment_id)
    score = (likes - dislikes) + get_score_proposition(comment_id)

    # Si c'est une réponse à une proposition, renvoyer aussi le score de la proposition parente
    proposition_id    = None
    proposition_score = None
    comment_data = select_comment_by_id(comment_id)
    if comment_data:
        parent_id = comment_data[6]  # id_reply
        if parent_id != 0:
            parent_data = select_comment_by_id(parent_id)
            if parent_data and parent_data[4] == 'proposition':
                proposition_id = parent_id
                p_likes, p_dislikes = get_comment_likes(parent_id)
                proposition_score = (p_likes - p_dislikes) + get_score_proposition(parent_id)

    return jsonify({
        "likes": likes, "dislikes": dislikes, "score": score,
        "proposition_id": proposition_id, "proposition_score": proposition_score,
    })


# ─── Réponses ─────────────────────────────────────────────────────────────────

@app.route("/show_all_replies/<int:discussion_id>/<int:comment_id>")
def show_all_replies(discussion_id, comment_id):
    discussion_type       = select_discussion_by_id(discussion_id)[3]
    comment_discussion_id = select_comment_by_id(comment_id)[2]
    result = []

    for reply in select_comment_replies(comment_id):
        opinion = get_user_opinion(discussion_id, reply[1])
        if opinion is None:    opinion = "neutre"
        elif opinion[0] == 1: opinion = "pour"
        else:                  opinion = "contre"

        etat = 'closed' if discussion_id != comment_discussion_id else reply[7]
        if(get_user_by_id(reply[1])==None):
            username="Utilisateur supprimé"
        else:
            username=get_user_by_id(reply[1])[1] + " " + get_user_by_id(reply[1])[2]
        result.append({
            "id_c":            reply[0],
            "id_client":       reply[1],
            "content":         reply[3],
            "type":            reply[4],
            "avis":            reply[5],
            "username":        username,
            "like":            get_comment_likes(reply[0])[0],
            "dislike":         get_comment_likes(reply[0])[1],
            "opinion":         opinion,
            "discussion_type": discussion_type,
            "reply_count":     len(select_comment_replies(reply[0])),
            "etat":            etat,
        })

    result.sort(key=lambda r: r['like'] - r['dislike'], reverse=True)
    return jsonify(result)


# ─── Groupes ──────────────────────────────────────────────────────────────────

@app.route('/groups', methods=['GET', 'POST'])
def groups_page():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    msg = ''
    if request.method == "POST":
        group_name = request.form["groupName"]
        if not group_name:
            msg = 'tout les champs sont requises'
        elif len(select_groupe_from_name(group_name)) > 0:
            msg = "Ce group existe deja"
        else:
            insert_groups_table(group_name)

    id_client     = session['id_client']
    groups_client = [dict(id=row[0], name=row[1]) for row in select_client_groupes(id_client)]
    all_groups    = [[row[0], row[1]] for row in select_all_groupes()]
    membres       = [[row[0], row[1], row[2]] for row in select_all_clients()]

    return render_template(
        "groups.html",
        groups_client=groups_client, all_groups=all_groups, members=membres, msg=msg,
        first_name=session['first_name'], last_name=session['last_name'],
        email=session['email'], company=session['company'],
        role=roles_numeros[session['role']], role_name=session['role'],
    )


@app.route('/allgroups', methods=['POST', 'GET'])
def take_all_groupes():
    all_groups = []
    res=select_all_groupes()
    for row in res :
        all_groups.append([row[0], row[1]])
    return all_groups

@app.route('/api/group_members/<int:group_id>')
def api_group_members(group_id):
    if not session.get('logged_in'):
        return jsonify([])
    members = []
    for member in select_member_by_id(group_id):
        user = get_user_by_id(member[0])
        if user[0] != session['id_client']:
            members.append({"id": user[0], "name": user[1] + " " + user[2]})
    return jsonify(members)


@app.route('/api/group_non_members/<int:group_id>')
def api_group_non_members(group_id):
    if not session.get('logged_in'):
        return jsonify([])
    return jsonify([
        {"id": m[0], "name": m[1] + " " + m[2]}
        for m in select_clients_not_in_group(group_id)
    ])


@app.route('/changemember/<int:group_id>', methods=['POST'])
def change_member_group(group_id):
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    new_members= set(request.form.getlist('memberList'))

    old_members=set()
    print(select_member_by_id(group_id)[0])
    for m in select_member_by_id(group_id):
        old_members.add(m[0])

    del_members=list(old_members-new_members)
    add_members=list(new_members-old_members)

    for d in del_members:
        delete_member(group_id,d)
    
    for a in add_members:
        insert_group_members(group_id,a)
   
    return redirect(url_for("group_info",g_id=group_id))

@app.route('/addgroupe/<int:group_id>', methods=['POST'])
def add_member_to_group(group_id):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    origin = request.form.get('origin', 'groupinfo')
    for membre in request.form.getlist('memberList'):
        if len(select_client_groupes_by_id(group_id, membre)) == 0:
            insert_group_members(group_id, membre)
    if origin == 'groups':
        return redirect(url_for("groups_page"))
    return redirect(url_for("group_info", g_id=group_id))


@app.route('/deletemember/<int:group_id>', methods=['POST'])
def delete_member_from_group(group_id):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    origin = request.form.get('origin', 'groupinfo')
    for membre in request.form.getlist("memberList"):
        if len(select_client_groupes_by_id(group_id, membre)) == 1:
            delete_member(group_id, membre)
    if origin == 'groups':
        return redirect(url_for("groups_page"))
    return redirect(url_for("group_info", g_id=group_id))


@app.route('/group_info/<int:g_id>', methods=['POST', 'GET'])
def group_info(g_id):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    members = []
    for member in select_member_by_id(g_id):
        id_c, nom_c, last_name, role = get_user_by_id(member[0])
        members.append(dict(id=id_c, name=nom_c, last_name=last_name, role=role))

    group_client = dict(name=select_groupe_from_id(g_id)[0], id=g_id)
    other = [dict(id=m[0], name=m[1], last_name=m[2]) for m in select_clients_not_in_group(g_id)]

    return render_template(
        "groupinfo.html",
        group_client=group_client, other=other, members=members,
        id_client=session['id_client'],
        first_name=session['first_name'], last_name=session['last_name'],
        email=session['email'], company=session['company'],
        role=roles_numeros[session['role']], role_name=session['role'],
    )


@app.route('/updategroup/<int:group_id>', methods=['POST'])
def change_group_name(group_id):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    origin = request.form.get('origin', 'groupinfo')
    update_group(request.form["groupName"], group_id)
    if origin == 'groups':
        return redirect(url_for("groups_page"))
    return redirect(url_for("group_info", g_id=group_id))


@app.route('/deletegroup/<int:group_id>', methods=['POST'])
def delete_group_from_db(group_id):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    for member in select_member_by_id(group_id):
        delete_member(group_id, member[0])
    delete_discussiongroups(group_id)
    delete_group(group_id)
    return redirect(url_for("groups_page"))

@app.route('/allgroupmembers/<int:group_id>', methods=['GET'])
def get_all_members_groups(group_id):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    result = select_member_by_id(group_id)
    members = []
    for row in result:
        id_c, name, last_name, role = get_user_by_id(row[0])
        members.append({
            "id": id_c,
            "name": name,
            "last_name": last_name,
            "role": role
        })
    return jsonify(members)

# ─── Membres & Profil ─────────────────────────────────────────────────────────


@app.route('/membres', methods=["GET"])
def membres():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    return render_template(
        "membres.html",
        first_name=session['first_name'], last_name=session['last_name'],
        email=session['email'], company=session['company'],
        role=roles_numeros[session['role']], role_name=session['role'],
    )


@app.route('/allmembers', methods=['GET'])
def get_all_members():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    result = select_all_clients()
    members = []
    for row in result:
        members.append({
            "id": row[0],
            "name": row[1],
            "last_name": row[2],
            "role": row[3]
        })
    return jsonify(members)

@app.route('/deleteclient/<int:id_c>', methods=['POST'])
def delete_client_from_db(id_c):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))

    for id_g in select_client_groupes(id_c):
        delete_member(id_g[0],id_c)
    
    delete_client(id_c)
    return redirect(url_for('membres'))

    

@app.route('/promoteclient/<int:id_c>')

def promote_client(id_c):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    
    role=select_role_client(id_c)[0]
    username=get_user_by_id(id_c)[1]+" "+get_user_by_id(id_c)[2]
    if(role == "Manager"):
        update_role("CEO",id_c)
        flash(username+" a été promu en tant que CEO")
    if(role == "Employe"):
        update_role("Manager",id_c)
        flash(username+" a été promu en tant que Manager")
        
    return redirect(url_for('membres'))

@app.route('/demoteclient/<int:id_c>')

def demote_client(id_c):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    
    role=select_role_client(id_c)[0]
    username=get_user_by_id(id_c)[1]+" "+get_user_by_id(id_c)[2]
    if(role == "CEO"):
        update_role("Manager",id_c)
        flash(username+" a été rétrogradé en tant que Manager")
    if(role == "Manager"):
        update_role("Employe",id_c)
        flash(username+" a été rétrogradé en tant que Employe")
    
    return redirect(url_for('membres'))


@app.route('/profile/<int:id_c>')
def profile(id_c):
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    my_profile = (id_c == session["id_client"])
    id_c, name, last_name, role = get_user_by_id(id_c)
    groupes = [dict(id=row[0], name=row[1]) for row in select_client_groupes(id_c)]
    return render_template(
        "profile.html",
        my_profile=my_profile, name_p=name, last_name_p=last_name,
        role_p=role, email_p=get_email(id_c)[0], groupes=groupes,
        first_name=session['first_name'], last_name=session['last_name'],
        email=session['email'], company=session['company'],
        role=roles_numeros[session['role']], role_name=session['role'],
    )


@app.route('/alldiscussions', methods=["GET"])
def alldiscussions():
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    discussions = []
    for row in select_all_group_discussions(session["id_client"]):
        likes, dislikes = get_discussion_likes(row[0])
        groupes = [
            {"id": g[0], "nom": select_groupe_from_id(g[0])[0]}
            for g in select_discussion_groups(row[0])
        ]
        if(get_user_by_id(row[1])==None):
            auteur="Utilisateur supprimé"
        else:
            auteur=get_user_by_id(row[1])[1]+" "+get_user_by_id(row[1])[2]
        discussions.append({
            "id": row[0], "titre": row[2], "contenu": row[3],
            "type": "Question" if row[4] == "ouvert" else "Proposition",
            "likes": likes, "dislikes": dislikes,
            "groupes": groupes,"auteur":auteur,
            "date": row[5], "heure": row[6], "etat": row[7], "cloner_par": row[8],
        })

        

    return jsonify(discussions)


# ─── Authentification ─────────────────────────────────────────────────────────

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
    email    = request.form["email"]
    password = request.form["password"]
    if not email or not password:
        return render_template('login.html', message="tout les champs sont requis")
    client_infos = select_client_infos_from_email(email)
    if not client_infos or password != client_infos[0]:
        return render_template('login.html', message="Email or password is incorrect. Please try again")
    session["logged_in"] = True
    session['id_client'], session['email'], session['first_name'], \
    session['last_name'], session['company'], session['role'] = client_infos[1:]
    return redirect(url_for("home"))


@app.route('/registry', methods=['GET', 'POST'])
def registry():
    if request.method == "GET":
        return redirect(url_for('registry_page'))
    email      = request.form["email"]
    first_name = request.form["first-name"]
    last_name  = request.form["last-name"]
    password   = request.form["new-password"]
    company    = request.form["company-name"]
    role       = request.form["role"]
    if check_if_exists_client(email, company) is not None:
        return render_template('registry.html', message='Ce compte existe deja')
    insert_clients_table(email, first_name, last_name, password, company, role)
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    
    return redirect(url_for('membres'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['logged_in'] = False
    return redirect(url_for("login_page"))


# ─── Utilitaires DB (dev) ─────────────────────────────────────────────────────

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
def insert_client():
    insert_clients_table("test@test", 'test', 'test', 'test', 'test', 'test')
    return "inserted clients table succesfully!"


@app.route("/insert_discussions_table")
def insert_discussions():
    insert_disscussions_table(1, "Jason", "Jason son nom est jason")
    return "inserted clients table succesfully!"


@app.route("/insert_comments_table")
def insert_comments():
    insert_comments_table(1, 1, "Tamer is the vire!!!")
    return "inserted comments table succesfully!"


@app.route("/insert_likes_table")
def insert_likes():
    insert_likes_table(1, "comment", 1, 1)
    return "inserted likes table succesfully!"


# ─── CLI ──────────────────────────────────────────────────────────────────────

@app.cli.command("db:reset")  # usage : flask db:reset
def reset_database():
    "resets the database tables"
    print("Dropping Database")
    reset_all_db()
    insert_clients_table("test@test", 'test', 'test', 'test', 'test', 'CEO')
    print("reset successful")
