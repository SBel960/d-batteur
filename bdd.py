import sqlite3
from flask import g
from datetime import date
import time
db_file = "./app.db"

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
                id_reply INTEGER NOT NULL,
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
                FOREIGN KEY(id_g) REFERENCES Groups(id_groupe)
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
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Client(email, name, last_name, password, company, role)
                VALUES (?,?,?,?,?,?)

            """
    sql.execute(command, [email, name, last_name, password, company, role])
    data.commit()


def insert_disscussions_table(id_c, title, content, type):
    data = get_db()
    sql = data.cursor()
    date_creation = date.today()
    named_tuple = time.localtime() # get struct_time
    time_creation = time.strftime("%H:%M", named_tuple)
    print(time_creation)
    command = """INSERT INTO Discussions(id_c, title, content, type, date_creation,time_creation)
                VALUES (?,?,?,?,?,?)

            """
    sql.execute(command, [id_c, title, content, type, date_creation, time_creation])
    data.commit()


def insert_comments_table(id_c, id_d, content, id_reply):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Comments(id_c, id_d, content, id_reply)
                VALUES (?,?,?,?)
            """
    sql.execute(command, [id_c, id_d, content, id_reply])
    data.commit()

def insert_likes_table(id_c, target, id_target, like):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Likes(id_c, target, id_target, like)
                VALUES (?,?,?,?)
            """
    sql.execute(command, [id_c, target, id_target, like])
    data.commit()



def insert_groups_table(name):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Groups(name)
                VALUES (?)
            """
    sql.execute(command, [name])
    data.commit()



def insert_group_members(id_group, id_client):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO GroupMembers(id_g, id_c)
                VALUES (?,?)
            """
    sql.execute(command, [id_group, id_client])
    data.commit()



def insert_discussion_groups(id_group, id_discussion):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO DiscussionGroups(id_g, id_d)
                VALUES (?,?)
            """
    sql.execute(command, [id_group, id_discussion])
    data.commit()
#------------------------------- commandes

def reset_all_db():
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
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Discussions ORDER BY date_creation DESC;
            """
    sql.execute(command)
    result = sql.fetchall()
    return result

def select_all_group_discussions(id_client):
    data = get_db()
    sql = data.cursor()
    command = """ SELECT DISTINCT Discussions.* FROM Discussions
            JOIN DiscussionGroups ON Discussions.id_discussion = DiscussionGroups.id_d 
            JOIN GroupMembers ON DiscussionGroups.id_g = GroupMembers.id_g
            WHERE GroupMembers.id_c = ? 
            ORDER BY date_creation DESC;
            """
    sql.execute(command, [id_client])
    result = sql.fetchall()
    return result


def select_comments(discussion_id):
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Comments WHERE id_d= ? AND id_reply=0;
        """
    
    sql.execute(command, [discussion_id])
    result = sql.fetchall()
    return result


def select_comments_ferme(discussion_id):
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Comments 
            FULL JOIN Likes ON Comments.id_comment = Likes.id_target AND Likes.target='comment'
            WHERE Comments.id_d= ? AND id_reply=0
            GROUP BY Comments.id_comment
            ORDER BY SUM(CASE WHEN Likes.like = 1 THEN 1 ELSE 0 END) DESC, SUM(CASE WHEN Likes.like = -1 THEN 1 ELSE 0 END);
            """
    
    sql.execute(command, [discussion_id])
    result = sql.fetchall()
    return result  

def select_comment_replies(comment_id):
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Comments WHERE id_reply=?;
            """
    
    sql.execute(command, [comment_id])
    result = sql.fetchall()
    return result
            

def select_newest_discussion_id(id_client):
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_discussion FROM Discussions WHERE id_c= ? ORDER BY id_discussion DESC;
            """
    
    sql.execute(command, [id_client])
    result = sql.fetchone()
    return result

def select_discussion_by_id(id_discussion):
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_c, title, content, type FROM Discussions WHERE id_discussion= ?;
            """
    
    sql.execute(command, [id_discussion])
    result = sql.fetchone()
    return result


def select_clients_not_in_group(id_group):
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
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_client, name, last_name FROM Client;
            """
    
    sql.execute(command)
    result = sql.fetchall()
    return result

def select_all_groupes():
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Groups;
            """
    
    sql.execute(command)
    result = sql.fetchall()
    return result

def select_client_groupes(id_c):
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Groups 
        JOIN GroupMembers ON Groups.id_group = GroupMembers.id_g 
        WHERE GroupMembers.id_c=?;
            """
    
    sql.execute(command, [id_c])
    result = sql.fetchall()
    return result

def select_client_groupes_by_id(id_g, id_c):
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM GroupMembers where id_g = ? AND id_c=?;
            """
    
    sql.execute(command, [id_g,id_c])
    result = sql.fetchall()
    return result


def select_groupe_from_name(name):
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_group FROM Groups WHERE name=?;
            """
    
    sql.execute(command, [name])
    result = sql.fetchall()
    return result


def select_groupe_from_id(id_g):
    data = get_db()
    sql = data.cursor()
    command = """SELECT name FROM Groups WHERE id_group=?;
            """
    
    sql.execute(command, [id_g])
    result = sql.fetchone()
    return result

def select_discussion_groups(id_discussion):
    data = get_db()
    sql = data.cursor()
    command = """SELECT id_g FROM DiscussionGroups WHERE id_d=?;
            """
    
    sql.execute(command, [id_discussion])
    result = sql.fetchall()
    return result

def select_member_by_id(id_g):
    data = get_db()
    sql=data.cursor()
    command = """SELECT id_c from GroupMembers WHERE id_g=?
            """
    sql.execute(command,[id_g])
    res=sql.fetchall()
    return res

def delete_member(id_g,id_c):
    data =get_db()
    sql=data.cursor()
    command ="""DELETE FROM GroupMembers WHERE id_g=? AND id_c=?
        """
    sql.execute(command,[id_g,id_c])
    data.commit()
    sql.close()

def delete_group(id_g):
    data =get_db()
    sql=data.cursor()
    command ="""DELETE FROM Groups WHERE id_group=?
        """
    sql.execute(command,[id_g])
    data.commit()
    sql.close()


def update_group(name,id_g):
    data=get_db()
    sql=data.cursor()
    command="""UPDATE Groups SET name=? WHERE id_group=?
        """
    
    sql.execute(command,[name,id_g])
    data.commit()
    sql.close()

#---------------------- likes

def update_like(id_client, id_cible, cible, value):
    """ fonction a 3 cas:
    1- si il nya pas de like ou dislike deja dans la table: on insere la ligne
    2- sinon: si l'action ne correspond pas a la valeur deja dans la table, on modifie la ligne
    3- sinon: si l'action est comme la valeur deja dans la table, on supprime la ligne
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
    data = get_db()
    sql = data.cursor()
    command = """SELECT like FROM Likes WHERE id_target=? AND target =? AND id_c = ?;
            """
    sql.execute(command, [id_discussion, "discussion", id_client])
    result = sql.fetchone()
    return result


#-------------------------------authentificattion

def select_client_infos_from_email(email):
    data = get_db()
    sql= data.cursor()
    command = """SELECT password, id_client, email, name, last_name, company, role FROM Client WHERE email = ? ;
            """
    sql.execute(command, [email])
    result = sql.fetchone()
    return result


def check_if_exists_client(email, company):
    data = get_db()
    sql= data.cursor()
    command = """SELECT * FROM Client WHERE email = ? AND company = ? ;
            """
    sql.execute(command, [email, company])
    result = sql.fetchone()
    return result


def get_user_by_id(id_c):
    data = get_db()
    sql=data.cursor()
    command= """SELECT id_client, name, last_name, role FROM Client WHERE id_client= ?
            """
    sql.execute(command,[id_c])

    res=sql.fetchone()

    return res