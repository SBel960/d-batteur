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
                id_reference INTEGER NOT NULL,
                bool_discussion INTEGER NOT NULL,
                likes INTEGER NOT NULL DEFAULT 0,
                dislike INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(id_c) REFERENCES Client(id_client)
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




