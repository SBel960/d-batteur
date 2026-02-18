import sqlite3
from flask import g

db_file = "approot/app.db"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(db_file)
        g.db.row_factory = sqlite3.Row
    return g.db



def create_client_table():
    data = get_db()
    sql = data.cursor()
    command = """CREATE TABLE IF NOT EXISTS Client(
                id_client INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                password TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT,
                group_name TEXT
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
                FOREIGN KEY(id_c) REFERENCES Client(id_client),
                FOREIGN KEY(id_d) REFERENCES Client(id_discussion)
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


def insert_clients_table(name, last_name, password, company, role, group_name):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Client(name, last_name, password, company, role, group_name)
                VALUES (?,?,?,?,?,?)

            """
    sql.execute(command, [name, last_name, password, company, role, group_name])
    data.commit()


def insert_disscussions_table(id_c, title, content):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Discussions(id_c, title, content)
                VALUES (?,?,?)

            """
    sql.execute(command, [id_c, title, content])
    data.commit()


def insert_comments_table(id_c, id_d, content):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Comments(id_c, id_d, content)
                VALUES (?,?,?)
            """
    sql.execute(command, [id_c, id_d, content])
    data.commit()

def insert_likes_table(id_c, target, id_target, like):
    data = get_db()
    sql = data.cursor()
    command = """INSERT INTO Likes(id_c, target, id_target, like)
                VALUES (?,?,?,?)
            """
    sql.execute(command, [id_c, target, id_target, like])
    data.commit()



def reset_all_db():
    data = get_db()
    sql = data.cursor()
    tables = ["Client", "Discussions", "Comments", "Likes"]
    for table in tables:
        sql.execute(f"DROP TABLE IF EXISTS {table};")
    data.commit()

    create_client_table()
    create_discussions_table()
    create_comments_table()
    create_likes_table()


def select_all_discussions():
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Discussions;
            """
    sql.execute(command)
    result = sql.fetchall()
    return result


def select_comments(discussion_id):
    data = get_db()
    sql = data.cursor()
    command = """SELECT * FROM Comments WHERE id_d= ?;
            """
    
    sql.execute(command, [discussion_id])
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
    command = """SELECT id_c, title, content FROM Discussions WHERE id_discussion= ?;
            """
    
    sql.execute(command, [id_discussion])
    result = sql.fetchone()
    return result