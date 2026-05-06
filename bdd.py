import sqlite3
import math
from flask import g
from datetime import date
import time
db_file = "approot/app.db"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(db_file)
        g.db.row_factory = sqlite3.Row
    return g.db


#---------------------creation tables
def create_client_table():
    data = get_db()
    sql = data.cursor()
    command = """CREATE TABLE IF NOT EXISTS Client(
                id_client INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                password TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT       
                )  
            """
    sql.execute(command)
    data.commit()

def create_discussions_table():
    data = get_db()
    sql = data.cursor()
    command = """CREATE TABLE IF NOT EXISTS Discussions(
                id_discussion INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                id_c INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL,
                date_creation DATE NOT NULL,
                time_creation TIME NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('active', 'closed')) DEFAULT 'active',
                cloned_from INTEGER DEFAULT NULL,
                priority INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(id_c) REFERENCES Client(id_client)
                )
                 
            """
    sql.execute(command)
    data.commit()

def create_comments_table():
    data = get_db()
                 
    sql = data.cursor()
    command = """CREATE TABLE IF NOT EXISTS Comments(
                id_comment INTEGER PRIMARY KEY AUTOINCREMENT,
                id_c INTEGER NOT NULL,
                id_d INTEGER NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL,
                avis TEXT,
                id_reply INTEGER NOT NULL,
                state TEXT NOT NULL CHECK (state IN ('active', 'closed')) DEFAULT 'active',
                FOREIGN KEY(id_c) REFERENCES Client(id_client),
                FOREIGN KEY(id_d) REFERENCES Discussions(id_discussion)
                )
                 
            """
    sql.execute(command)
    data.commit()


def create_likes_table():
    data = get_db()
    sql = data.cursor()
    command = """CREATE TABLE IF NOT EXISTS Likes(
                id_like INTEGER PRIMARY KEY AUTOINCREMENT,
                id_c INTEGER NOT NULL,
                target TEXT NOT NULL CHECK (target IN ('discussion', 'comment')),
                id_target INTEGER NOT NULL,
                like INTEGER NOT NULL CHECK (like IN (-1, 1)),
                FOREIGN KEY(id_c) REFERENCES Client(id_client),
                UNIQUE (id_c, target, id_target)
                )
                 
            """
    sql.execute(command)
    data.commit()



def create_groups_table():
    data = get_db()
    sql = data.cursor()
    command = """CREATE TABLE IF NOT EXISTS Groups(  
                id_group INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
                )  
            """
    sql.execute(command)
    data.commit()

def create_group_members_table():
    data = get_db()
    sql = data.cursor()
    command = """CREATE TABLE IF NOT EXISTS GroupMembers(  
                id_group_member INTEGER PRIMARY KEY AUTOINCREMENT,
                id_g INTEGER NOT NULL,
                id_c INTEGER NOT NULL,

                FOREIGN KEY(id_c) REFERENCES Client(id_client),
                FOREIGN KEY(id_g) REFERENCES Groups(id_groupe),
                UNIQUE (id_g,id_c)
                )  
            """
    sql.execute(command)
    data.commit()


def create_discussion_groups_table():
    data = get_db()
    sql = data.cursor()
    command = """CREATE TABLE IF NOT EXISTS DiscussionGroups(  
                id_g INTEGER NOT NULL,
                id_d INTEGER NOT NULL,

                FOREIGN KEY(id_d) REFERENCES Discussions(id_discussion),
                FOREIGN KEY(id_g) REFERENCES Groups(id_groupe)
    

                )  
            """
    sql.execute(command)
    data.commit()



#-------------------------- insertion



def insert_clients_table(email, name, last_name, password, company, role):
    """
    params:
        email (str): email unique du client
        name (str): prénom
        last_name (str): nom
        password (str): mot de passe
        company (str): entreprise associée
        role (str): rôle du client (CEO, Manager, Employé)

    role:
        Insère un nouveau client dans la table Client.

    utilisation:
        - utilisé dans app.py → fonction registry()
        - utilisé dans app.py → commande CLI reset_database()
    """
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Client(email, name, last_name, password, company, role)
                VALUES (?,?,?,?,?,?)

            """
    sql.execute(command, [email, name, last_name, password, company, role])
    data.commit()

def insert_disscussions_table(id_c, title, content, type, priority, cloned_from=None):
    """
    params:
        id_c (int): id du client créateur
        title (str): titre de la discussion
        content (str): contenu
        type (str): type de discussion (ouvert / ferme)
        priority (int): priorité (1 ou 2)
        cloned_from (int | None): id de la discussion clonée (optionnel)

    role:
        Insère une nouvelle discussion avec date et heure actuelles.

    utilisation:
        - utilisé dans app.py → fonction ajouter_discussion()
        - utilisé dans app.py → fonction cloner_discussion()
        - utilisé dans app.py → route de test insert_discussions()
    """
    data = get_db()
    sql = data.cursor()
    date_creation = date.today().isoformat()
    named_tuple = time.localtime() # get struct_time
    time_creation = time.strftime("%H:%M", named_tuple)
    print(time_creation)
    command = """INSERT INTO Discussions(id_c, title, content, type, date_creation,time_creation, cloned_from, priority)
                VALUES (?,?,?,?,?,?,?,?)

            """
    sql.execute(command, [id_c, title, content, type, date_creation, time_creation, cloned_from, priority])
    data.commit()


def insert_comments_table(id_c, id_d, content, type, avis, id_reply):
    """
    params:
        id_c (int): id du client
        id_d (int): id de la discussion
        content (str): contenu du commentaire
        type (str): type (normal / proposition)
        avis (str | None): pour / contre / neutre
        id_reply (int): id du commentaire parent (0 si commentaire principal)

    role:
        Insère un commentaire ou une réponse dans la table Comments.

    utilisation:
        - utilisé dans app.py → fonction commentaire()
        - utilisé dans app.py → route de test insert_comments()
    """
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Comments(id_c, id_d, content, type, avis, id_reply)
                VALUES (?,?,?,?,?,?)
            """
    sql.execute(command, [id_c, id_d, content, type, avis, id_reply])
    data.commit()

def insert_likes_table(id_c, target, id_target, like):
    """
    params:
        id_c (int): id du client
        target (str): 'discussion' ou 'comment'
        id_target (int): id de la cible
        like (int): 1 (like) ou -1 (dislike)

    role:
        Insère un vote (like/dislike) dans la table Likes.

    utilisation:
        - utilisé dans bdd.py → fonction update_like()
        - utilisé dans app.py → route de test insert_likes()
    """
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Likes(id_c, target, id_target, like)
                VALUES (?,?,?,?)
            """
    sql.execute(command, [id_c, target, id_target, like])
    data.commit()



def insert_groups_table(name):
    """
    params:
        name (str): nom du groupe

    role:
        Crée un nouveau groupe dans la table Groups.

    utilisation:
        - utilisé dans app.py → fonction groups_page()
    """
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Groups(name)
                VALUES (?)
            """
    sql.execute(command, [name])
    data.commit()



def insert_group_members(id_group, id_client):
    """
    params:
        id_group (int): id du groupe
        id_client (int): id du client à ajouter

    role:
        Ajoute un utilisateur à un groupe.

    utilisation:
        - utilisé dans app.py → fonction change_member_group()
        - utilisé dans app.py → fonction add_member_to_group()
        - utilisé dans app.py → fonction registry() (ajout aux groupes lors de l'inscription)
    """
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO GroupMembers(id_g, id_c)
                VALUES (?,?)
            """
    sql.execute(command, [id_group, id_client])
    data.commit()



def insert_discussion_groups(id_group, id_discussion):
    """
    params:
        id_group (int): id du groupe
        id_discussion (int): id de la discussion

    role:
        Associe une discussion à un groupe.

    utilisation:
        - utilisé dans app.py → fonction ajouter_discussion()
        - utilisé dans app.py → fonction modifier_discussion() (via update_discussion)
        - utilisé dans app.py → fonction cloner_discussion()
        - utilisé dans bdd.py → fonction update_discussion()
    """

    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO DiscussionGroups(id_g, id_d)
                VALUES (?,?)
            """
    sql.execute(command, [id_group, id_discussion])
    data.commit()
#------------------------------- commandes

def reset_all_db():
    """
    role:
        Supprime toutes les tables puis les recrée complètement (reset total de la base).

    utilisation:
        - utilisé dans app.py → commande CLI reset_database()
    """
    data = get_db()
    sql = data.cursor()
    tables = ["Client", "Discussions", "Comments", "Likes", "Groups", "GroupMembers", "DiscussionGroups"]
    for table in tables:
        sql.execute(f"DROP TABLE IF EXISTS {table};")
    data.commit()

    create_client_table()
    create_discussions_table()
    create_comments_table()
    create_likes_table()
    create_discussion_groups_table()
    create_groups_table()


    create_group_members_table()


#--------------------------------- selections
def select_all_discussions():
    """
    role:
        Récupère toutes les discussions triées par priorité puis date.

    utilisation:
        - non utilisé directement dans app.py
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Discussions ORDER BY priority DESC, date_creation DESC;
            """
    sql.execute(command)
    result = sql.fetchall()
    return result

def select_all_group_discussions(id_client):
    """
    params:
        id_client (int): id du client

    role:
        Récupère toutes les discussions appartenant aux groupes du client.

    utilisation:
        - utilisé dans app.py → fonction home()
        - utilisé dans app.py → fonction alldiscussions()
    """
    data = get_db()
    sql = data.cursor()
    command = """ SELECT DISTINCT Discussions.* FROM Discussions
            JOIN DiscussionGroups ON Discussions.id_discussion = DiscussionGroups.id_d 
            JOIN GroupMembers ON DiscussionGroups.id_g = GroupMembers.id_g
            WHERE GroupMembers.id_c = ? 
            ORDER BY  priority DESC, date_creation DESC, time_creation DESC;
            """
    sql.execute(command, [id_client])
    result = sql.fetchall()
    return result


def select_comments(discussion_id):
    """
    params:
        discussion_id (int): id de la discussion

    role:
        Récupère les commentaires principaux (non réponses) d’une discussion.

    utilisation:
        - utilisé dans app.py → fonction main()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Comments WHERE id_d= ? AND id_reply=0;
        """
    
    sql.execute(command, [discussion_id])
    result = sql.fetchall()
    return result


def select_comments_ferme(discussion_id):
    """
    params:
        discussion_id (int): id de la discussion

    role:
        Récupère les commentaires principaux triés par popularité (likes/dislikes).

    utilisation:
        - utilisé dans app.py → fonction main()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Comments 
            LEFT JOIN Likes ON Comments.id_comment = Likes.id_target AND Likes.target='comment'
            WHERE Comments.id_d= ? AND id_reply=0
            GROUP BY Comments.id_comment
            ORDER BY SUM(CASE WHEN Likes.like = 1 THEN 1 ELSE 0 END) DESC, SUM(CASE WHEN Likes.like = -1 THEN 1 ELSE 0 END);
            """
    
    sql.execute(command, [discussion_id])
    result = sql.fetchall()
    return result  

def select_comment_replies(comment_id):
    """
    params:
        comment_id (int): id du commentaire parent

    role:
        Récupère toutes les réponses d’un commentaire.

    utilisation:
        - utilisé dans app.py → fonction main()
        - utilisé dans app.py → fonction show_all_replies()
        - utilisé dans app.py → fonction main_comment()
        - utilisé dans bdd.py → fonction get_score_proposition()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Comments WHERE id_reply=?;
            """
    
    sql.execute(command, [comment_id])
    result = sql.fetchall()
    return result
            

def select_newest_discussion_id(id_client):
    """
    params:
        id_client (int): id du client

    role:
        Récupère l’id de la dernière discussion créée par un client.

    utilisation:
        - utilisé dans app.py → fonction ajouter_discussion()
        - utilisé dans app.py → fonction cloner_discussion()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_discussion FROM Discussions WHERE id_c= ? ORDER BY id_discussion DESC;
            """
    
    sql.execute(command, [id_client])
    result = sql.fetchone()
    return result

def select_discussion_by_id(id_discussion):
    """
    params:
        id_discussion (int): id de la discussion

    role:
        Récupère les informations principales d’une discussion.

    utilisation:
        - utilisé dans app.py → fonction main()
        - utilisé dans app.py → fonction main_comment()
        - utilisé dans app.py → fonction show_all_replies()
        - utilisé dans app.py → fonction cloner_discussion()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_c, title, content, type, state, cloned_from, priority FROM Discussions WHERE id_discussion= ?;
            """
    
    sql.execute(command, [id_discussion])
    result = sql.fetchone()
    return result



def select_comment_by_id(id_comment):
    """
    params:
        id_comment (int): id du commentaire

    role:
        Récupère un commentaire spécifique.

    utilisation:
        - utilisé dans app.py → fonction like_comment()
        - utilisé dans app.py → fonction main_comment()
        - utilisé dans app.py → fonction show_all_replies()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Comments WHERE id_comment= ?;
            """
    
    sql.execute(command, [id_comment])
    result = sql.fetchone()
    return result

def select_clients_not_in_group(id_group):
    """
    params:
        id_group (int): id du groupe

    role:
        Récupère les clients qui ne sont pas dans un groupe.

    utilisation:
        - utilisé dans app.py → fonction groups_page()
        - utilisé dans app.py → fonction group_info()
        - utilisé dans app.py → fonction api_group_non_members()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_client, name,last_name
                 FROM Client 
                 WHERE id_client NOT IN(
                    SELECT id_c
                    FROM GroupMembers
                    WHERE id_g = ?
                );
            """
    
    sql.execute(command, [id_group])
    result = sql.fetchall()
    return result

def select_all_clients():
    """
    role:
        Récupère tous les clients.

    utilisation:
        - utilisé dans app.py → fonction groups_page()
        - utilisé dans app.py → fonction membres()
        - utilisé dans app.py → fonction get_all_members()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_client, name, last_name,role FROM Client;
            """
    
    sql.execute(command)
    result = sql.fetchall()
    return result

def select_all_groupes():
    """
    role:
        Récupère tous les groupes.

    utilisation:
        - utilisé dans app.py → fonction home()
        - utilisé dans app.py → fonction groups_page()
        - utilisé dans app.py → fonction registry_page()
        - utilisé dans app.py → fonction take_all_groupes()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Groups;
            """
    
    sql.execute(command)
    result = sql.fetchall()
    return result

def select_client_groupes(id_c):
    """
    params:
        id_c (int): id du client

    role:
        Récupère les groupes auxquels appartient un client.

    utilisation:
        - utilisé dans app.py → fonction groups_page()
        - utilisé dans app.py → fonction profile()
        - utilisé dans app.py → fonction delete_client_from_db()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT Groups.id_group, Groups.name FROM Groups 
        JOIN GroupMembers ON Groups.id_group = GroupMembers.id_g 
        WHERE GroupMembers.id_c=?;
            """
    
    sql.execute(command, [id_c])
    result = sql.fetchall()
    return result

def select_client_groupes_by_id(id_g, id_c):
    """
    params:
        id_g (int): id du groupe
        id_c (int): id du client

    role:
        Vérifie si un client appartient à un groupe.

    utilisation:
        - utilisé dans app.py → fonction add_member_to_group()
        - utilisé dans app.py → fonction delete_member_from_group()
        - utilisé dans app.py → fonction registry()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM GroupMembers where id_g = ? AND id_c=?;
            """
    
    sql.execute(command, [id_g,id_c])
    result = sql.fetchall()
    return result


def select_groupe_from_name(name):
    """
    params:
        name (str): nom du groupe

    role:
        Récupère l’id d’un groupe à partir de son nom.

    utilisation:
        - utilisé dans app.py → fonction groups_page()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_group FROM Groups WHERE name=?;
            """
    
    sql.execute(command, [name])
    result = sql.fetchall()
    return result


def select_groupe_from_id(id_g):
    """
    params:
        id_g (int): id du groupe

    role:
        Récupère le nom d’un groupe.

    utilisation:
        - utilisé dans app.py → fonction home()
        - utilisé dans app.py → fonction alldiscussions()
        - utilisé dans app.py → fonction group_info()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT name FROM Groups WHERE id_group=?;
            """
    
    sql.execute(command, [id_g])
    result = sql.fetchone()
    return result

def select_discussion_groups(id_discussion):
    """
    params:
        id_discussion (int): id de la discussion

    role:
        Récupère les groupes liés à une discussion.

    utilisation:
        - utilisé dans app.py → fonction home()
        - utilisé dans app.py → fonction alldiscussions()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_g FROM DiscussionGroups WHERE id_d=?;
            """
    
    sql.execute(command, [id_discussion])
    result = sql.fetchall()
    return result

def select_member_by_id(id_g):
    """
    params:
        id_g (int): id du groupe

    role:
        Récupère les membres d’un groupe.

    utilisation:
        - utilisé dans app.py → fonction api_group_members()
        - utilisé dans app.py → fonction group_info()
        - utilisé dans app.py → fonction change_member_group()
        - utilisé dans app.py → fonction delete_group_from_db()
    """
    data = get_db()
    sql=data.cursor()
    command = """SELECT id_c from GroupMembers WHERE id_g=?
            """
    sql.execute(command,[id_g])
    res=sql.fetchall()
    return res

def select_role_client(id_c):
    """
    params:
        id_c (int): id du client

    role:
        Récupère le rôle d’un client.

    utilisation:
        - utilisé dans app.py → fonction promote_client()
        - utilisé dans app.py → fonction demote_client()
    """
    data = get_db()
    sql=data.cursor()
    command = """SELECT role from Client WHERE id_client=?
            """
    sql.execute(command,[id_c])
    res=sql.fetchone()
    return res
# DELETE FUNCTION

def delete_member(id_g,id_c):
    """
    params:
        id_g (int): id du groupe
        id_c (int): id du client

    role:
        Supprime un membre d’un groupe.

    utilisation:
        - utilisé dans app.py → fonction change_member_group()
        - utilisé dans app.py → fonction delete_member_from_group()
        - utilisé dans app.py → fonction delete_group_from_db()
        - utilisé dans app.py → fonction delete_client_from_db()
    """
    data =get_db()
    sql=data.cursor()
    command ="""DELETE FROM GroupMembers WHERE id_g=? AND id_c=?
        """
    sql.execute(command,[id_g,id_c])
    data.commit()
    sql.close()

def delete_group(id_g):
    """
    params:
        id_g (int): id du groupe

    role:
        Supprime un groupe.

    utilisation:
        - utilisé dans app.py → fonction delete_group_from_db()
    """
    data =get_db()
    sql=data.cursor()
    command ="""DELETE FROM Groups WHERE id_group=?
        """
    sql.execute(command,[id_g])
    data.commit()
    sql.close()

def delete_discussiongroups(id_g):
    """
    params:
        id_g (int): id du groupe

    role:
        Supprime les liens entre un groupe et les discussions.

    utilisation:
        - utilisé dans app.py → fonction delete_group_from_db()
    """
    data =get_db()
    sql=data.cursor()
    command ="""DELETE FROM DiscussionGroups WHERE id_g=?
        """
    sql.execute(command,[id_g])
    data.commit()
    sql.close()

def delete_client(id_c):
    """
    params:
        id_c (int): id du client

    role:
        Supprime un client.

    utilisation:
        - utilisé dans app.py → fonction delete_client_from_db()
    """
    data =get_db()
    sql=data.cursor()
    command ="""DELETE FROM Client WHERE id_client=?
        """
    sql.execute(command,[id_c])
    data.commit()
    sql.close()

def select_comments_from_clientid(id_c):
    """
    params:
        id_c (int): id du client

    role:
        Récupère les ids des commentaires d’un client.

    utilisation:
        - non utilisé dans app.py
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_comment FROM Comments WHERE id_c=?;
            """
    
    sql.execute(command, [id_c])
    result = sql.fetchall()
    return result


# UPDATE FUNCTION


def update_group(name,id_g):
    """
    params:
        name (str): nouveau nom
        id_g (int): id du groupe

    role:
        Modifie le nom d’un groupe.

    utilisation:
        - utilisé dans app.py → fonction change_group_name()
    """
    data=get_db()
    sql=data.cursor()
    command="""UPDATE Groups SET name=? WHERE id_group=?
        """
    
    sql.execute(command,[name,id_g])
    data.commit()
    sql.close()

def update_discussion(title,content, d_id, new_groupes, priority):
    """
    params:
        title (str)
        content (str)
        d_id (int)
        new_groupes (iterable)
        priority (int)

    role:
        Met à jour une discussion et remplace ses groupes associés.

    utilisation:
        - utilisé dans app.py → fonction modifier_discussion()
    """
    data=get_db()
    sql=data.cursor()
    #premierement, supprime tout les anciens groupes de la discussion 
    command = """DELETE FROM DiscussionGroups WHERE id_d=?
     """
    sql.execute(command,[d_id])
    data.commit()

    #deuxiemenent, mis a jour de la discussion avec le nouveau titre, contenu, type
    command="""UPDATE Discussions SET title=?, content=?, priority=? WHERE id_discussion=?
        """
    
    sql.execute(command,[title,content,priority, d_id])
    data.commit()

    #troisiement, inserer les nouveaux groupes de discussion
    for g_id in new_groupes:
        insert_discussion_groups(g_id, d_id)
    sql.close()


def update_discussion_state(id_discussion, action):
    """
    params:
        id_discussion (int)
        action (str): active / closed

    role:
        Change l’état d’une discussion et de tous ses commentaires.

    utilisation:
        - utilisé dans app.py → fonction clotre_discussion()
    """
    data=get_db()
    sql=data.cursor()
    command="""UPDATE Discussions SET state=?, priority=0 WHERE id_discussion=?
        """
    sql.execute(command,[action, id_discussion])
    data.commit()
    
    command="""UPDATE Comments SET state=? WHERE id_d=?
        """
    sql.execute(command,[action, id_discussion])
    data.commit()
    sql.close()
    return

def update_role(role,id_c):
    """
    params:
        role (str)
        id_c (int)

    role:
        Modifie le rôle d’un utilisateur.

    utilisation:
        - utilisé dans app.py → fonction promote_client()
        - utilisé dans app.py → fonction demote_client()
    """
    if role=="CEO" or role=="Manager" or role=="Employe":
        data=get_db()
        sql=data.cursor()
        command="""UPDATE Client SET role=? WHERE id_client=?
            """
        sql.execute(command,[role, id_c])
        data.commit()
        sql.close()

#---------------------- likes

def update_like(id_client, id_cible, cible, value):
    """ 
    params:
        id_client (int)
        id_cible (int)
        cible (str)
        value (int)

    fonction a 3 cas:
        1- si il nya pas de like ou dislike deja dans la table: on insere la ligne
        2- sinon: si l'action ne correspond pas a la valeur deja dans la table, on modifie la ligne
        3- sinon: si l'action est comme la valeur deja dans la table, on supprime la ligne

    utilisation:
        - utilisé dans app.py → fonction like_discussion()
        - utilisé dans app.py → fonction like_comment()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT like FROM Likes WHERE id_c= ? AND id_target=? AND target=?;
            """
    
    sql.execute(command, [id_client, id_cible, cible])
    result = sql.fetchone()
    if not result:
        insert_likes_table(id_client, cible, id_cible, value)
        return 
    else:
        if result[0] != value:
            command = """UPDATE Likes SET like=? WHERE id_c= ? AND id_target=? AND target=?;
                """      
            sql.execute(command, [value, id_client, id_cible, cible])
            data.commit()
        else:
            command = """DELETE FROM Likes WHERE id_c= ? AND id_target=? AND target=?;
                """      
            sql.execute(command, [id_client, id_cible, cible])
            data.commit()


def get_discussion_likes(id_discussion):
    """
    params:
        id_discussion (int)

    role:
        Compte les likes et dislikes d’une discussion.

    utilisation:
        - utilisé dans app.py → fonction home()
        - utilisé dans app.py → fonction main()
        - utilisé dans app.py → fonction like_discussion()
        - utilisé dans app.py → fonction alldiscussions()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT like FROM Likes WHERE id_target=? AND target =?;
            """
    sql.execute(command, [id_discussion, "discussion"])
    result = sql.fetchall()
    likes = 0
    dislikes = 0
    for res in result:
        if res[0] == 1:
            likes += 1
        else:
            dislikes += 1

    return (likes, dislikes)

def get_comment_likes(id_comment):
    """
    params:
        id_comment (int)

    role:
        Compte les likes et dislikes d’un commentaire.

    utilisation:
        - utilisé dans app.py → fonction main()
        - utilisé dans app.py → fonction like_comment()
        - utilisé dans app.py → fonction show_all_replies()
        - utilisé dans bdd.py → fonction get_score_proposition()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT like FROM Likes WHERE id_target=? AND target =?;
            """
    sql.execute(command, [id_comment, "comment"])
    result = sql.fetchall()
    likes = 0
    dislikes = 0
    for res in result:
        if res[0] == 1:
            likes += 1
        else:
            dislikes += 1

    return (likes, dislikes)

def get_user_opinion(id_discussion, id_client):
    """
    params:
        id_discussion (int)
        id_client (int)

    role:
        Récupère l’opinion (like/dislike) d’un utilisateur sur une discussion.

    utilisation:
        - utilisé dans app.py → fonction main()
        - utilisé dans app.py → fonction main_comment()
        - utilisé dans app.py → fonction show_all_replies()
    """
    data = get_db()
    sql = data.cursor()
    command = """SELECT like FROM Likes WHERE id_target=? AND target =? AND id_c = ?;
            """
    sql.execute(command, [id_discussion, "discussion", id_client])
    result = sql.fetchone()
    return result


#-------------------------------authentificattion

def select_client_infos_from_email(email):
    """
    params:
        email (str)

    role:
        Récupère toutes les infos d’un client à partir de son email.

    utilisation:
        - utilisé dans app.py → fonction login()
        - utilisé dans app.py → fonction registry()
    """
    data = get_db()
    sql= data.cursor()
    command = """SELECT password, id_client, email, name, last_name, company, role FROM Client WHERE email = ? ;
            """
    sql.execute(command, [email])
    result = sql.fetchone()
    return result


def check_if_exists_client(email, company):
    """
    params:
        email (str)
        company (str)

    role:
        Vérifie si un client existe déjà.

    utilisation:
        - utilisé dans app.py → fonction registry()
    """
    data = get_db()
    sql= data.cursor()
    command = """SELECT * FROM Client WHERE email = ? AND company = ? ;
            """
    sql.execute(command, [email, company])
    result = sql.fetchone()
    return result


def get_user_by_id(id_c):
    """
    params:
        id_c (int)

    role:
        Récupère les infos d’un utilisateur.

    utilisation:
        - utilisé dans app.py → fonction home()
        - utilisé dans app.py → fonction main()
        - utilisé dans app.py → fonction main_comment()
        - utilisé dans app.py → fonction show_all_replies()
        - utilisé dans app.py → fonction group_info()
        - utilisé dans app.py → fonction api_group_members()
        - utilisé dans app.py → fonction promote_client()
        - utilisé dans app.py → fonction demote_client()
        - utilisé dans app.py → fonction profile()
    """
    data = get_db()
    sql=data.cursor()
    command= """SELECT id_client, name, last_name, role FROM Client WHERE id_client= ?
            """
    sql.execute(command,[id_c])

    res=sql.fetchone()

    return res

def get_email(id_c):
    """
    params:
        id_c (int)

    role:
        Récupère l’email d’un utilisateur.

    utilisation:
        - utilisé dans app.py → fonction profile()
    """
    data = get_db()
    sql=data.cursor()
    command= """SELECT email FROM Client WHERE id_client= ?
            """
    sql.execute(command,[id_c])

    res=sql.fetchone()

    return res

def get_score_proposition(id_commentaire, _depth=0):
    """
    Score composite mesurant l'intérêt réel des utilisateurs pour une proposition.
    (Ne compte PAS les votes directs sur la proposition — déjà gérés dans app.py)

    Composantes :
    ┌─ Sentiment      : Σ(crédibilité_réponse × direction)
    │    Chaque réponse "pour"/"contre" compte selon ses propres likes (qualité > quantité)
    ├─ Engagement     : log(1 + votes_réponses + nb_réponses) × 2
    │    Croissance logarithmique — 100 réponses ne vaut pas 100× 1 réponse
    ├─ Controverse    : √(min(poids_pour, poids_contre)) × 1.5
    │    Bonus si les deux camps sont représentés — le débat = intérêt
    └─ Profondeur     : contributions imbriquées atténuées par 0.6^profondeur
         Les échanges profonds comptent, mais avec moins de poids
    """
    enfants = select_comment_replies(id_commentaire)
    if not enfants:
        return 0

    pour_weight = 0
    contre_weight = 0
    total_reply_votes = 0

    for enfant in enfants:
        r_likes, r_dislikes = get_comment_likes(enfant['id_comment'])
        r_net = r_likes - r_dislikes
        total_reply_votes += r_likes + r_dislikes
        # Crédibilité = popularité nette + 1 (chaque réponse compte au moins 1)
        r_credibility = max(0, r_net) + 1

        if enfant['avis'] == 'pour':
            pour_weight += r_credibility
        elif enfant['avis'] == 'contre':
            contre_weight += r_credibility

    # 1. Sentiment net pondéré par la crédibilité des réponses
    sentiment = pour_weight - contre_weight

    # 2. Engagement logarithmique (volume d'activité sans effet viral linéaire)
    engagement = math.log1p(total_reply_votes + len(enfants)) * 2

    # 3. Bonus de controverse : intérêt si les deux camps s'expriment
    controversy = math.sqrt(min(pour_weight, contre_weight)) * 1.5

    # 4. Contribution des sous-réponses, atténuée selon la profondeur
    depth_factor = 0.6 ** (_depth + 1)
    child_contribution = sum(
        get_score_proposition(e['id_comment'], _depth + 1)
        for e in enfants
    ) * depth_factor

    return round(sentiment + engagement + controversy + child_contribution)



def migrate_db():
    """Ajoute les colonnes manquantes si la DB existe déjà sans elles."""
    data = get_db()
    sql = data.cursor()
    # Vérifier si la colonne 'priority' existe dans Discussions
    sql.execute("PRAGMA table_info(Discussions)")
    cols = [row[1] for row in sql.fetchall()]
    if 'priority' not in cols:
        sql.execute("ALTER TABLE Discussions ADD COLUMN priority INTEGER NOT NULL DEFAULT 1")
        data.commit()


####deletes
def delete_discussion_from_id(id_discussion):
    """
    params:
        id_discussion (int)

    role:
        Supprime une discussion.

    utilisation:
        - utilisé dans app.py → fonction delete_discussion()
    """
    data = get_db()
    sql=data.cursor()
    command= """DELETE FROM Discussions WHERE id_discussion=?
            """
    sql.execute(command,[id_discussion])

    data.commit()
    return

    
