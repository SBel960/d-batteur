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
    delete_discussion_from_id, update_discussion_state, delete_client, select_role_client,
    update_role, migrate_db
)

import time

app = Flask(__name__)
app.secret_key = "suis-je la cle secrete?"

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
    migrate_db()  # Ajoute les colonnes manquantes sur les DB existantes


# ─── Accueil ──────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    """
    Point d’entrée principal de l’application.

    Construit dynamiquement la page d’accueil pour l’utilisateur authentifié en agrégeant
    l’ensemble des discussions accessibles via ses appartenances aux groupes.

    La fonction :
    - filtre implicitement les discussions selon les groupes du client courant,
    - enrichit chaque discussion avec :
        * le score social (likes / dislikes),
        * les métadonnées temporelles et d’état,
        * les groupes associés,
        * le nom de l’auteur (ou fallback si supprimé),
    - normalise le type de discussion (OUVERT / FERMÉ) pour l’affichage.

    Retour :
        Template HTML rendu (`homepage.html`) avec toutes les données prêtes à être consommées côté frontend.

    Redirection :
        - vers la page de login si l’utilisateur n’est pas authentifié.
    """
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

        # row : [0:id, 1:id_client, 2:title, 3:content, 4:type, 5:date, 6:time, 7:state, 8:cloner_par 9: priority]
        discussions.append([
            row[2], row[3], str(row[0]), likes, dislikes,
            groupes, auteur_nom, type_disc, row[5], row[6], row[7], row[8], row[9]
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
    """
    Vue détaillée d’une discussion.

    Charge et structure l’intégralité du contenu d’une discussion :
    commentaires racines + éventuels commentaires issus d’un clonage.

    La fonction applique une logique métier non triviale :
    - sélection conditionnelle des commentaires selon le type (ouvert / fermé),
    - calcul de score pour les propositions (likes/dislikes + score métier),
    - récupération et normalisation des opinions utilisateurs (pour / contre / neutre),
    - gestion des auteurs supprimés,
    - calcul du nombre de réponses (thread depth),
    - fusion logique avec les commentaires d’une discussion clonée (lecture seule),
    - tri intelligent :
        * score si disponible,
        * sinon fallback sur (likes - dislikes).

    Paramètres :
        discussion_id (int) : identifiant unique de la discussion.

    Retour :
        Template `main.html` avec :
            - commentaires principaux,
            - commentaires clonés,
            - métadonnées complètes de la discussion.

    Redirection :
        - vers login si non authentifié.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))

    id_poster, title, content, discussion_type, discussion_state, id_clone, priority = select_discussion_by_id(discussion_id)
    cloned = id_clone is not None

    ###SECTION: verifie que l'utilisateur a droit a acceder a la discussion
    discussion_groups = [g[0] for g in select_discussion_groups(discussion_id)]
    user_groups = [g[0] for g in select_client_groupes(session['id_client'])]

    in_groupe = False
    for id_g in discussion_groups:
        if id_g in user_groups:
            in_groupe = True
            break
    if(in_groupe == False):
        flash("Tu n'appartient pas au groupes de cette discussion!")
        return redirect(url_for("home"))
    
    ###SECTION: traitement + render template

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
        print("bonjour je suis clone", id_clone, select_comments(id_clone))
        for comment in select_comments(id_clone):
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
            if opinion is None:    
                opinion = "neutre"
            elif opinion[0] == 1: 
                opinion = "pour"
            else:   
                opinion = "contre"
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

@app.route("/main_comment/<int:discussion_id>/<path:comment_ids>", methods=["GET"])
def main_comment(discussion_id, comment_ids):
    """
    Vue spécialisée pour la navigation dans un thread profond de commentaires.

    Permet d’isoler et d’afficher un commentaire précis dans une hiérarchie imbriquée,
    en reconstruisant dynamiquement le chemin de navigation (breadcrumb/back).

    Logique principale :
    - parsing du chemin `comment_ids` (format hiérarchique),
    - identification du commentaire courant (feuille du chemin),
    - reconstruction conditionnelle d’une URL de retour vers le parent,
    - enrichissement du commentaire avec :
        * score (si proposition),
        * likes / dislikes,
        * opinion utilisateur,
        * nombre de réponses,
        * état,
        * auteur (avec fallback si supprimé).

    Paramètres :
        discussion_id (int) : discussion parente.
        comment_ids (str)   : chemin hiérarchique (ex: "12/45/78").

    Retour :
        Template partiel `partials/main_comment.html`.

    Redirection :
        - vers login si non authentifié.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))

    id_poster, title, content, discussion_type, discussion_state, id_clone, priority = select_discussion_by_id(discussion_id)
    
    #####section comment parent
    path = [int(x) for x in comment_ids.strip('/').split('/')]
    back_url=None
    if len(path) > 1:
        back_url = url_for('main_comment', discussion_id=discussion_id, comment_ids='/'.join(str(x) for x in path[:-1]))
                           
    comment_id = path[-1]
    comment_parent       = select_comment_by_id(comment_id)
    
    id_comment   = comment_parent[0]
    id_client    = comment_parent[1]
    type_comment = comment_parent[4]
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
    comment_parent = dict(
        id_c=id_comment, content=comment_parent[3], like=like_c, dislike=dislike_c,
        username=username, opinion=opinion, type=type_comment, avis=comment_parent[5],
        score=score, reply_count=len(select_comment_replies(id_comment)), etat=comment_parent[7],
    )



    likes, dislikes = get_discussion_likes(discussion_id)
    return render_template(
        "partials/main_comment.html",
        discussion_id=discussion_id, comment_parent=comment_parent,
        id_client=session["id_client"], title=title, content=content,
        likes=likes, dislikes=dislikes,
        discussion_type=discussion_type, discussion_state=discussion_state, 
        first_name=session['first_name'], last_name=session['last_name'],
        email=session['email'], company=session['company'],
        role=roles_numeros[session['role']], role_name=session['role'],
        back_url=back_url
    )



@app.route("/commentaire/<int:discussion_id>/<int:reply>", methods=["POST"])
def commentaire(discussion_id, reply):
    """
    Endpoint d’insertion de commentaire.

    Gère à la fois :
    - la création d’un commentaire racine,
    - la réponse à un commentaire existant (threading).

    Comportement :
    - extrait les données du formulaire (contenu, type, avis),
    - insère en base avec liaison parent/enfant via `reply`,
    - retourne une réponse JSON en cas de reply (AJAX),
      sinon redirection classique vers la discussion.

    Paramètres :
        discussion_id (int) : discussion cible.
        reply (int)         : id du commentaire parent (0 = racine).

    Retour :
        - JSON (si réponse imbriquée),
        - redirection sinon.

    Redirection :
        - vers login si non authentifié.
    """
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
    """
    Création d’une nouvelle discussion.

    Pipeline complet :
    1. Validation des champs obligatoires (titre, contenu, groupes, type),
    2. Normalisation de la priorité (bool → niveau métier),
    3. Insertion en base,
    4. Récupération de l’ID nouvellement créé (via workaround temporel),
    5. Association aux groupes sélectionnés (relation N-N).

    Particularité :
        Utilise un `sleep` court pour contourner un problème de synchronisation
        lors de la récupération de l’ID (approche non idéale mais pragmatique).

    Retour :
        Redirection vers la page de la discussion créée.

    Redirection :
        - vers login si non authentifié.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    title   = request.form['discussionTitle']
    content = request.form['discussionContent']
    groupes = request.form.getlist('groupes')
    type_d  = request.form.get('discussionType')
    priorite = request.form.get('discussionPriority')

    if not title or not content or not groupes or not type_d:
        return 'tout les champs sont requises'
    if(priorite):
        priorite=2
    else:
        priorite=1
    

    insert_disscussions_table(session['id_client'], title, content, type_d, priorite)
    time.sleep(0.01)
    discussion_id = select_newest_discussion_id(session['id_client'])[0]
    for groupe_id in groupes:
        insert_discussion_groups(groupe_id, discussion_id)
    return redirect(url_for("main", discussion_id=discussion_id))


@app.route("/modifier_discussion/<int:d_id>", methods=["POST"])
def modifier_discussion(d_id):
    """
    Mise à jour d’une discussion existante.

    Permet de modifier :
    - le titre,
    - le contenu,
    - les groupes associés (via reconstruction d’ensemble),
    - la priorité métier.

    Logique :
    - conversion des groupes en `set` pour faciliter le diff côté DB,
    - normalisation de la priorité (bool → int),
    - délégation de la logique de mise à jour à la couche BDD.

    Paramètres :
        d_id (int) : identifiant de la discussion.

    Retour :
        Redirection vers la vue détaillée mise à jour.

    Redirection :
        - vers login si non authentifié.
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    title       = request.form['discussionTitle']
    content     = request.form['discussionContent']
    new_groupes = set(request.form.getlist('groupes'))
    priorite = request.form.get('discussionPriority')
    if(priorite):
        priorite=2
    else:
        priorite=1
    update_discussion(title, content, d_id, new_groupes, priorite)
    return redirect(url_for("main", discussion_id=d_id))


@app.route("/clotre_discussion/<int:d_id>/<action>", methods=["POST"])
def clotre_discussion(d_id, action):
    """
    Transition d’état d’une discussion.

    Permet de modifier dynamiquement le statut d’une discussion
    (ex : active → closed), impactant implicitement le comportement
    des commentaires associés.

    Paramètres :
        d_id (int)    : identifiant de la discussion.
        action (str)  : nouvel état cible.

    Effet :
        - mise à jour persistée en base.

    Retour :
        Redirection vers la page d’accueil.

    Remarque :
        Aucune validation stricte de `action` n’est faite ici
        (dépendance implicite à la couche BDD).
    """
    update_discussion_state(d_id, action)
    return redirect(url_for('home'))


@app.route("/cloner_discussion/<int:d_id>", methods=["POST"])
def cloner_discussion(d_id):
    """
    Duplication logique d’une discussion.

    Crée une nouvelle discussion basée sur une existante,
    en copiant uniquement :
    - le contenu,
    - les métadonnées principales.

    Les commentaires :
        Ne sont PAS dupliqués en base.
        Ils sont récupérés dynamiquement via `main()` (liaison logique).

    Processus :
    - récupération de la discussion source,
    - insertion avec référence `cloned_from`,
    - association aux nouveaux groupes sélectionnés.

    Paramètres :
        d_id (int) : discussion source.

    Retour :
        Redirection vers la nouvelle discussion clonée.
    """
    groups = request.form.getlist('groupes')
    id_client, title, content, type_discussion, etat, cloned_id, priorite = select_discussion_by_id(d_id)
    insert_disscussions_table(id_c=id_client, title=title, content=content,
                               type=type_discussion, priority=priorite, cloned_from=d_id)
    discussion_id = select_newest_discussion_id(id_client)[0]
    for g_id in groups:
        insert_discussion_groups(id_group=g_id, id_discussion=discussion_id)
    return redirect(url_for('main', discussion_id=discussion_id))


@app.route("/delete_discussion/<int:d_id>", methods=["POST"])
def delete_discussion(d_id):
    """
    Suppression d’une discussion.

    Supprime définitivement une discussion identifiée,
    sans logique intermédiaire (hard delete).

    Paramètres :
        d_id (int) : identifiant de la discussion.

    Effet :
        - suppression en base via couche BDD.

    Retour :
        Redirection vers la page d’accueil.
    """
    delete_discussion_from_id(d_id)
    return redirect(url_for('home'))


# ─── Votes ────────────────────────────────────────────────────────────────────

@app.route("/like_discussion/<int:discussion_id>/<action>")
def like_discussion(discussion_id, action):
    """
    Gestion des interactions sociales sur une discussion.

    Permet à un utilisateur d’exprimer ou retirer une opinion :
    - like (+1),
    - unlike (-1).

    Logique :
    - traduction de l’action en valeur numérique,
    - mise à jour idempotente via la couche BDD,
    - gestion de deux contextes de retour :
        * redirection (si homepage),
        * JSON (mise à jour dynamique UI).

    Paramètres :
        discussion_id (int) : discussion cible.
        action (str)        : "like" ou "unlike".

    Retour :
        - JSON contenant les nouveaux scores,
        - ou redirection selon le contexte.

    Redirection :
        - vers login si non authentifié.
    """
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
    """
    Params:
        discussion_id (int): Contexte discussion.
        comment_id (int): Commentaire ciblé.
        action (str): 'like' ou 'unlike'.

    Role:
        Gère les votes sur un commentaire et met à jour les scores.

        Fonctionnement:
            - update_like sur le commentaire
            - recalcul:
                - likes/dislikes (get_comment_likes)
                - score proposition (get_score_proposition)

        Spécificité:
            - Si réponse à une proposition:
                → recalcule aussi le score de la proposition parente

        Retour:
            JSON avec scores mis à jour

        Utilisé dans:
            Route "/like_comment/<discussion_id>/<comment_id>/<action>"
    """
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
    """
    Params:
        discussion_id (int): Identifiant de la discussion courante.
        comment_id (int): Identifiant du commentaire parent.

    Role:
        Récupère et retourne toutes les réponses directes d’un commentaire
        sous forme JSON, enrichies avec des métadonnées calculées.

        Traitements:
            - Récupération des réponses (select_comment_replies)
            - Calcul des likes/dislikes (get_comment_likes)
            - Détermination de l’opinion utilisateur (get_user_opinion)
            - Résolution du username (get_user_by_id)
            - Calcul du nombre de sous-réponses
            - Gestion de l’état (fermé si discussion différente)

        Spécificité:
            - Tri final par score simple (likes - dislikes)

        Utilisé dans:
            Route "/show_all_replies/<discussion_id>/<comment_id>"
            → endpoint AJAX pour chargement dynamique des réponses
    """
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
    """
    Role:
        Page principale de gestion des groupes.

        Fonctionnalités:
            - Création de groupe (POST)
                → validation nom
                → vérification unicité (select_groupe_from_name)
                → insertion (insert_groups_table)
            - Affichage:
                → groupes du client (select_client_groupes)
                → tous les groupes (select_all_groupes)
                → tous les membres (select_all_clients)

        Gestion:
            - Messages d’erreur utilisateur (msg)

        Utilisé dans:
            Route "/groups"
    """

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
    """
    Role:
        Retourne la liste brute de tous les groupes.

        Fonctionnement:
            - select_all_groupes
            - format minimal [id, nom]

        ⚠️ Retour non JSON (liste Python brute)

        Utilisé dans:
            Route "/allgroups"
    """
    all_groups = []
    res=select_all_groupes()
    for row in res :
        all_groups.append([row[0], row[1]])
    return all_groups

@app.route('/api/group_members/<int:group_id>')
def api_group_members(group_id):
    """
    Params:
        group_id (int): Identifiant du groupe.

    Role:
        Retourne les membres d’un groupe (hors utilisateur courant) en JSON.

        Fonctionnement:
            - select_member_by_id
            - récupération infos utilisateur (get_user_by_id)
            - exclusion du user courant

        Utilisé dans:
            Route "/api/group_members/<group_id>"
            → endpoint AJAX
    """
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
    """
    Params:
        group_id (int): Identifiant du groupe.

    Role:
        Retourne les utilisateurs qui ne sont pas membres du groupe.

        Fonctionnement:
            - select_clients_not_in_group
            - transformation en JSON

        Utilisé dans:
            Route "/api/group_non_members/<group_id>"
    """
    if not session.get('logged_in'):
        return jsonify([])
    return jsonify([
        {"id": m[0], "name": m[1] + " " + m[2]}
        for m in select_clients_not_in_group(group_id)
    ])


@app.route('/changemember/<int:group_id>', methods=['POST'])
def change_member_group(group_id):
    """
    Params:
        group_id (int): Identifiant du groupe.

    Role:
        Synchronise complètement les membres d’un groupe
        avec la liste envoyée par le formulaire.

        Fonctionnement:
            - Récupère nouveaux membres (POST)
            - Compare avec anciens (select_member_by_id)
            - Calcule:
                → suppressions (delete_member)
                → ajouts (insert_group_members)

        Utilisé dans:
            Route "/changemember/<group_id>"
    """
    if not(session.get('logged_in')):
        return redirect(url_for('login_page'))
    new_members= set(request.form.getlist('memberList'))
    new_members.add(str(session['id_client']))
    if new_members == None:
        new_members = set()

    old_members=set()
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
    """
    Params:
        group_id (int): Identifiant du groupe.

    Role:
        Ajoute des membres à un groupe sans supprimer les existants.

        Fonctionnement:
            - Vérifie non-existence (select_client_groupes_by_id)
            - Insert uniquement si absent

        Redirection:
            - dépend de "origin" (groups / groupinfo)

        Utilisé dans:
            Route "/addgroupe/<group_id>"
    """
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
    """
    Params:
        group_id (int): Identifiant du groupe.

    Role:
        Supprime des membres d’un groupe.

        Fonctionnement:
            - Vérifie existence (sécurité)
            - Supprime via delete_member

        Redirection:
            - dépend de "origin"

        Utilisé dans:
            Route "/deletemember/<group_id>"
    """
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
    """
    Params:
        g_id (int): Identifiant du groupe.

    Role:
        Affiche la page détaillée d’un groupe.

        Contenu:
            - membres actuels (select_member_by_id + get_user_by_id)
            - infos groupe (select_groupe_from_id)
            - utilisateurs non membres (select_clients_not_in_group)

        Utilisé dans:
            Route "/group_info/<g_id>"
    """
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
    """
    Params:
        group_id (int): Identifiant du groupe.

    Role:
        Met à jour le nom d’un groupe.

        Fonctionnement:
            - update_group
            - redirection conditionnelle (origin)

        Utilisé dans:
            Route "/updategroup/<group_id>"
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    origin = request.form.get('origin', 'groupinfo')
    update_group(request.form["groupName"], group_id)
    if origin == 'groups':
        return redirect(url_for("groups_page"))
    return redirect(url_for("group_info", g_id=group_id))


@app.route('/deletegroup/<int:group_id>', methods=['POST'])
def delete_group_from_db(group_id):
    """
    Params:
        group_id (int): Identifiant du groupe.

    Role:
        Supprime complètement un groupe.

        Étapes:
            - suppression des membres (delete_member)
            - suppression des liens discussions (delete_discussiongroups)
            - suppression du groupe (delete_group)

        ⚠️ Pas de gestion de contraintes SQL en cascade → manuel

        Utilisé dans:
            Route "/deletegroup/<group_id>"
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    for member in select_member_by_id(group_id):
        delete_member(group_id, member[0])
    delete_discussiongroups(group_id)
    delete_group(group_id)
    return redirect(url_for("groups_page"))

@app.route('/allgroupmembers/<int:group_id>', methods=['GET'])
def get_all_members_groups(group_id):
    """
    Params:
        group_id (int): Identifiant du groupe.

    Role:
        Retourne tous les membres d’un groupe avec leurs rôles.

        Fonctionnement:
            - select_member_by_id
            - enrichissement via get_user_by_id
            - retour JSON

        Utilisé dans:
            Route "/allgroupmembers/<group_id>"
    """
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
    """
    Role:
        Affiche la page de gestion des membres.

        Contenu:
            - liste complète des utilisateurs (select_all_clients)
            - informations session

        Utilisé dans:
            Route "/membres"
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    
    return render_template(
        "membres.html",
        first_name=session['first_name'], last_name=session['last_name'],
        email=session['email'], company=session['company'],
        role=roles_numeros[session['role']], role_name=session['role'],
        id=session['id_client'],all_member=select_all_clients()
    )


@app.route('/allmembers', methods=['GET'])
def get_all_members():
    """
    Role:
        Retourne tous les membres sous forme JSON.

        Fonctionnement:
            - select_all_clients
            - transformation en structure API

        Utilisé dans:
            Route "/allmembers"
    """
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
    """
    Params:
        id_c (int): Identifiant du client.

    Role:
        Supprime un utilisateur (réservé au CEO).

        Sécurité:
            - vérifie rôle CEO
            - empêche auto-suppression

        Étapes:
            - suppression des appartenances groupe
            - suppression du client (delete_client)

        Utilisé dans:
            Route "/deleteclient/<id_c>"
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    if session["role"] != "CEO":
        flash("Tu n'es pas un CEO! petit malin")  
        return redirect(url_for('membres'))
    if id_c == session["id_client"]:
        flash("tu ne peux pas te virer! tu ne veux plus etre le ceo??")  
        return redirect(url_for('membres'))

    for id_g in select_client_groupes(id_c):
        delete_member(id_g[0],id_c)
    
    delete_client(id_c)
    return redirect(url_for('membres'))

    

@app.route('/promoteclient/<int:id_c>', methods=['POST'])
def promote_client(id_c):
    """
    Params:
        id_c (int): Identifiant du client.

    Role:
        Promeut un utilisateur (Employe → Manager → CEO).

        Contraintes:
            - réservé au CEO
            - interdit sur soi-même

        Fonctionnement:
            - récupération rôle (select_role_client)
            - update_role
            - feedback utilisateur (flash)

        Utilisé dans:
            Route "/promoteclient/<id_c>"
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    if session["role"] != "CEO":
        flash("Tu n'es pas un CEO! petit malin")  
        return redirect(url_for('membres'))
    if id_c == session["id_client"]:
        flash("tu ne peux pas te retrograder! tu ne veux plus etre le ceo??")  
        return redirect(url_for('membres'))
    role=select_role_client(id_c)[0]
    username=get_user_by_id(id_c)[1]+" "+get_user_by_id(id_c)[2]
    if(role == "Manager"):
        update_role("CEO",id_c)
        flash(username+" a été promu en tant que CEO")
    if(role == "Employe"):
        update_role("Manager",id_c)
        flash(username+" a été promu en tant que Manager")     
    return redirect(url_for('membres'))

@app.route('/demoteclient/<int:id_c>', methods=['POST'])

def demote_client(id_c):
    """
    Params:
        id_c (int): Identifiant du client.

    Role:
        Rétrograde un utilisateur (CEO → Manager → Employe).

        Contraintes:
            - réservé au CEO
            - interdit sur soi-même

        Spécificité:
            - met à jour la session si auto-modification

        Utilisé dans:
            Route "/demoteclient/<id_c>"
    """
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))
    if session["role"] != "CEO":
        flash("Tu n'es pas un CEO! petit malin")  
        return redirect(url_for('membres'))
    if id_c == session["id_client"]:
        flash("tu ne peux pas te retrograder! tu ne veux plus etre le ceo??")  
        return redirect(url_for('membres'))
    
    role=select_role_client(id_c)[0]
    username=get_user_by_id(id_c)[1]+" "+get_user_by_id(id_c)[2]
    if(role == "CEO"):
        newrole="Manager"
        update_role(newrole,id_c)
        flash(username+" a été rétrogradé en tant que Manager")
    if(role == "Manager"):
        newrole="Employe"
        update_role(newrole,id_c)
        flash(username+" a été rétrogradé en tant que Employe")

    if(session['id_client']==id_c):
        session['role']=newrole
    
    return redirect(url_for('membres'))


@app.route('/profile/<int:id_c>')
def profile(id_c):
    """
    Params:
        id_c (int): Identifiant du profil.

    Role:
        Affiche le profil d’un utilisateur.

        Contenu:
            - informations utilisateur (get_user_by_id)
            - email (get_email)
            - groupes (select_client_groupes)

        Spécificité:
            - distingue profil personnel vs autre utilisateur

        Utilisé dans:
            Route "/profile/<id_c>"
    """
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
    """
    Role:
        Retourne toutes les discussions accessibles à l’utilisateur en JSON.

        Fonctionnement:
            - select_all_group_discussions
            - enrichissement:
                → likes/dislikes
                → groupes
                → auteur
                → métadonnées complètes

        Utilisé dans:
            Route "/alldiscussions"
    """
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
            "date": row[5], "heure": row[6], "etat": row[7], "cloner_par": row[8], "priorite":row[9]
        })

        

    return jsonify(discussions)


# ─── Authentification ─────────────────────────────────────────────────────────

@app.route('/login_page', methods=['GET'])
def login_page():
    """
    Role:
        Affiche la page de connexion.

        Utilisé dans:
            Route "/login_page"
    """
    return render_template("login.html")


@app.route('/registry_page', methods=['GET'])
def registry_page():
    """
    Role:
        Affiche la page d’inscription.

        Contenu:
            - liste des groupes disponibles (select_all_groupes)

        Utilisé dans:
            Route "/registry_page"
    """
    all_groups = [[row[0], row[1]] for row in select_all_groupes()]
    return render_template("registry.html", all_groups=all_groups)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Role:
        Authentifie un utilisateur.

        Fonctionnement:
            - validation champs
            - récupération user (select_client_infos_from_email)
            - vérification mot de passe
            - initialisation session

        ⚠️ Mot de passe en clair → sécurité faible

        Utilisé dans:
            Route "/login"
    """
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
    """
    Role:
        Crée un nouvel utilisateur.

        Fonctionnement:
            - vérifie existence (check_if_exists_client)
            - insertion (insert_clients_table)
            - ajout aux groupes sélectionnés

        Spécificité:
            - récupération id via select_client_infos_from_email

        Utilisé dans:
            Route "/registry"
    """
    if request.method == "GET":
        return redirect(url_for('registry_page'))
    email      = request.form["email"]
    first_name = request.form["first-name"]
    last_name  = request.form["last-name"]
    password   = request.form["new-password"]
    company    = request.form["company-name"]
    role       = request.form["role"]
    if check_if_exists_client(email, company) is not None:
        all_groups = [[row[0], row[1]] for row in select_all_groupes()]
        return render_template('registry.html', message='Ce compte existe deja', all_groups=all_groups)
    insert_clients_table(email, first_name, last_name, password, company, role)
    # Ajouter l'utilisateur aux groupes sélectionnés
    groupes = request.form.getlist('groupes')
    if groupes:
        new_user = select_client_infos_from_email(email)
        if new_user:
            new_user_id = new_user[1]  # index 1 = id_client
            for groupe_id in groupes:
                if len(select_client_groupes_by_id(groupe_id, new_user_id)) == 0:
                    insert_group_members(groupe_id, new_user_id)
    if not session.get('logged_in'):
        return redirect(url_for('login_page'))

    return redirect(url_for('membres'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """
    Role:
        Déconnecte l’utilisateur.

        Fonctionnement:
            - reset session

        Utilisé dans:
            Route "/logout"
    """
    session['logged_in'] = False
    return redirect(url_for("login_page"))



# ─── CLI ──────────────────────────────────────────────────────────────────────

@app.cli.command("db:reset")  # usage : flask db:reset
def reset_database():
    """
    Role:
        Commande CLI pour réinitialiser entièrement la base de données.

        Fonctionnement:
            - drop + recreate tables (reset_all_db)
            - insertion utilisateur test (CEO)

        Utilisation:
            flask db:reset
    """
    print("Dropping Database")
    reset_all_db()
    insert_clients_table("test@test", 'test', 'test', 'test', 'test', 'CEO')
    print("reset successful")
