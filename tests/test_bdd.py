import pytest
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
    update_role,get_db
)
import sqlite3

def test_create_table(app):
    """
        Test la création des tables

    """
    with app.app_context():
        data = get_db()
        sql = data.cursor()
        command = """SELECT name from sqlite_master WHERE type='table';
                """
        sql.execute(command)

        res=sql.fetchall()
        tables=set()
        for row in res:
            tables.add(row['name'])

        assert len(tables)==8 # 7 + 1 table crée automatiquement par sqlite

        assert "Client" in tables
        assert "Discussions" in tables
        assert "Comments" in tables
        assert "Likes" in tables
        assert "Groups" in tables
        assert "GroupMembers" in tables
        assert "DiscussionGroups" in tables

        sql.close()

def columns(nomTable):
    """
    Obtenir le nom des colonnes de la table passée en paramètre
    
    Parameters:
    nomTable(String): Nom de tables (Supposé déjà existante)

    Return:
    liste: noms de toutes les colonnes
    """
    data = get_db()
    sql = data.cursor()
    sql.execute(f"PRAGMA table_info({nomTable})")
    colonne=[]
    for row in sql.fetchall():
        colonne.append(row["name"])
    sql.close()
    return colonne


def test_table_columns(app):
    """
        Vérifie que l'on a les bonnes colonnes dans les tables 
    
    """
    with app.app_context():

        assert columns("Client")==["id_client", "email", "name", "last_name", "password", "company", "role"]
        assert columns("Discussions")==["id_discussion", "id_c", "title", "content", "type","date_creation", "time_creation", "state", "cloned_from", "priority"]
        assert columns("Comments")==["id_comment", "id_c", "id_d", "content", "type", "avis", "id_reply", "state"]
        assert columns("Likes")==["id_like", "id_c", "target", "id_target", "like"]
        assert columns("Groups")==["id_group", "name"]
        assert columns("GroupMembers")==["id_group_member", "id_g", "id_c"]
        assert columns("DiscussionGroups")==["id_g", "id_d"]


def test_insert_client_tables(app):
    """
        Vérifie que l'on insertion dans la table Client fonctionne 
    """
    
    with app.app_context():
        
        data=get_db()
        sql=data.cursor()

        sql.execute("SELECT COUNT(*) as nb FROM Client;")
        assert sql.fetchone()["nb"]==0

        insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")
    

        sql.execute("SELECT COUNT(*) as nb FROM Client;")
        assert sql.fetchone()["nb"]==3
        
        #Vérification email unique
        with pytest.raises(sqlite3.IntegrityError):
            insert_clients_table("c@c","c","c","c","C","Employe")   

        sql.close()

def test_select_all_clients(app_with_data_v1):
    """
        Test la fonction select_all_clients
        Elle doit renvoyer tous les clients (id_client,name,last_name,role) présents dans la base de données 
    """
    app=app_with_data_v1
    with app.app_context():
        all_client=select_all_clients() 
        client_list=[]

        assert len(all_client)==3

        for client in all_client:
            assert len(client)==4 #select_all_clients renvoie 4 données
            client_list.append([client['id_client'],client['name'],client['last_name'],client['role']])
        
        assert client_list[0]==[1,'p_a','n_a','CEO']
        assert client_list[1]==[2,'p_b','n_b','Manager']
        assert client_list[2]==[3,'p_c','n_c','Employe']

def test_get_user_by_id(app_with_data_v1):
    """
        Test la fonction get_user_by_id
        Elle doit renvoyer un client (id_client,name,last_name,role) à partir de l'id
    """
    app=app_with_data_v1
    with app.app_context():
        
        assert get_user_by_id(0)==None #Test de la fonction si l'id n'existe pas
        assert list(get_user_by_id(1))==[1,'p_a','n_a','CEO']
        assert list(get_user_by_id(2))==[2,'p_b','n_b','Manager']
        assert list(get_user_by_id(3))==[3,'p_c','n_c','Employe']


def test_get_email(app_with_data_v1):
    """
        Test la fonction get_email
        Elle doit renvoyer l'email du client avec son id
    """
    app=app_with_data_v1
    with app.app_context():
        
        assert get_email(0)==None #Test de la fonction si l'id n'existe pas
        assert list(get_email(1))==['a@a']
        assert list(get_email(2))==['b@b']
        assert list(get_email(3))==['c@c']
        

def test_check_if_exist_client(app_with_data_v1):
    """
        Test la fonction check_if_exist_client
        Elle doit renvoyer toutes les données du client si il existe, None sinon
    """

    app=app_with_data_v1
    with app.app_context():
        assert list(check_if_exists_client("a@a","A"))==[1,"a@a","p_a","n_a","mdp_a","A","CEO"]
        assert check_if_exists_client("oui","OUI")==None


def test_select_client_infos_from_email(app_with_data_v1):
    """
        Test la fonction select_client_infos_from_email
        Elle doit renvoyer un client (password,id_client,email,name,last_name,company,role) à partir de l'email
    """
    app=app_with_data_v1
    with app.app_context():
        assert list(select_client_infos_from_email('b@b'))==["mdp_b",2,"b@b","p_b","n_b","B","Manager"]
        assert select_client_infos_from_email("no@no")==None


def test_select_role_client(app_with_data_v1):
    """
        Test la fonction select_role_client
        Elle renvoie le role du client avec son id
    """
    app=app_with_data_v1
    with app.app_context():
        assert list(select_role_client(3))==["Employe"]
        assert select_client_infos_from_email(0)==None

def test_delete_client(app_with_data_v1):
    """
        Test la fonction delete_client 
        Elle supprime un client de la base de données à partir de son id
    """
    with app_with_data_v1.app_context():

        assert len(select_all_clients())==3
        assert get_user_by_id(1) != None
        delete_client(1)
        assert get_user_by_id(1) == None
        assert len(select_all_clients())==2


def test_update_role(app_with_data_v1):
    """
        Test la fonction update_role 
        Elle teste la promotion et rétrogradation d'un client avec son id

    """
    app=app_with_data_v1
    with app.app_context():

        update_role("NON",3) #Test si le role n'est pas dans les choix possible
        assert list(select_role_client(3))==["Employe"]
        update_role("Manager",3)
        assert list(select_role_client(3))==["Manager"]
        update_role("CEO",3)
        assert list(select_role_client(3))==["CEO"]
        update_role("Manager",3)
        assert list(select_role_client(3))==["Manager"]
        update_role("Employe",3)
        assert list(select_role_client(3))==["Employe"]



def test_insert_groupe_tables(app):
    """
        Vérifie que l'insertion dans la table Groups fonctionne 
    """
    
    with app.app_context():
        
        data=get_db()
        sql=data.cursor()

        sql.execute("SELECT COUNT(*) as nb FROM Groups;")
        assert sql.fetchone()["nb"]==0

        insert_groups_table("G1")
        insert_groups_table("G2")

        sql.execute("SELECT COUNT(*) as nb FROM Groups;")
        assert sql.fetchone()["nb"]==2

        insert_groups_table("G3")

        sql.execute("SELECT COUNT(*) as nb FROM Groups;")
        assert sql.fetchone()["nb"]==3
         

        sql.close()


def test_select_all_groupes(app_with_data_v1):
    """
        Test la fonction select_all_groupes 
        Elle doit renvoyer tous les groupes (id_group,name)
    """
    app=app_with_data_v1

    with app.app_context():
        all_groups=select_all_groupes()

        groups=[]
        assert len(all_groups)==3

        for g in all_groups:
            assert len(g)==2

            groups.append(list(g))
        
        assert groups[0]==[1,"G1"]
        assert groups[1]==[2,"G2"]
        assert groups[2]==[3,"G3"]



def test_select_groupe_from_id(app_with_data_v1):
    """
        Test la fonction select_groupe_from_id
        Elle doit renvoyer le nom du groupe à partir de son id
    """
    app=app_with_data_v1
    with app.app_context():
        assert select_groupe_from_id(0)==None
        assert list(select_groupe_from_id(2))==["G2"]


def test_select_groupe_from_name(app_with_data_v1):
    """
        Test la fonction select_groupe_from_name
        Elle doit renvoyer le id du groupe à partir de son nom
    """
    app=app_with_data_v1
    with app.app_context():
        assert select_groupe_from_name("G0")==[]

        insert_groups_table("G2")
        assert len(select_groupe_from_name("G2"))==2
        assert list(select_groupe_from_name("G2")[0])==[2]
        assert list(select_groupe_from_name("G2")[1])==[4]


def test_update_group(app_with_data_v1):
    """
        Test la fonction update_group
        Elle doit changer le nom du groupe à partir de son id
    """
    app=app_with_data_v1

    with app.app_context():
        assert list(select_groupe_from_id(3))==["G3"]
        assert list(select_groupe_from_id(2))==["G2"]
        update_group("NewG2",3)
        assert list(select_groupe_from_id(3))==["NewG2"]
        assert list(select_groupe_from_id(2))==["G2"]

def test_delete_group(app_with_data_v1):
    """
        Test la fonction update_group
        Elle doit changer le nom du groupe à partir de son id
    """
    app=app_with_data_v1

    with app.app_context():
        assert len(select_all_groupes())==3
        assert list(select_groupe_from_id(2))==["G2"]
        delete_group(2)
        assert len(select_all_groupes())==2
        assert select_groupe_from_id(2)==None

def test_insert_group_members(app_with_data_v1):
    """
        Test la fonction insert_group_members
        Cree le lien entre un client et un groupe
    """
    app=app_with_data_v1

    with app.app_context():
        data=get_db()
        sql=data.cursor()

        sql.execute("SELECT COUNT(*) AS nb FROM GroupMembers")
        assert sql.fetchone()['nb']==0

        insert_group_members(1,1)
        insert_group_members(1,2)

        sql.execute("SELECT COUNT(*) AS nb FROM GroupMembers")
        assert sql.fetchone()['nb']==2
        
        with pytest.raises(sqlite3.IntegrityError):
            insert_group_members(1,1)


def test_select_member_by_id(app_with_data_v2):
    """
        Test la fonction select_member_by_id
        Elle renvoie tous les clients (id_client) qui appartiennent au groupe  
    """
    app=app_with_data_v2

    with app.app_context():
        assert len(select_member_by_id(1))==1
        assert len(select_member_by_id(2))==2
        assert len(select_member_by_id(3))==3

        assert list(select_member_by_id(1)[0])==[1]

        assert list(select_member_by_id(2)[0])==[1]
        assert list(select_member_by_id(2)[1])==[2]

        assert list(select_member_by_id(3)[0])==[1]
        assert list(select_member_by_id(3)[1])==[2]
        assert list(select_member_by_id(3)[2])==[3]


def test_select_clients_not_in_group(app_with_data_v2):
    """
        Test la fonction select_clients_not_group
        Elle renvoie tous les clients (id_client,name,last_name) qui n'appartiennent pas au groupe  
    """
    app=app_with_data_v2

    with app.app_context():
        assert len(select_clients_not_in_group(1))==2
        assert len(select_clients_not_in_group(2))==1
        assert select_clients_not_in_group(3)==[] #fetchall donc []

        assert list(select_clients_not_in_group(2)[0])==[3,'p_c','n_c']

        assert list(select_clients_not_in_group(1)[0])==[2,'p_b','n_b']
        assert list(select_clients_not_in_group(1)[1])==[3,'p_c','n_c']


def test_select_client_groupes(app_with_data_v2):
    """
        Test la fonction select_client_groupes
        Elle renvoie tous les groupes (id_g,name) où le client appartient dans l'ordre croissant en id_g 
    """
    app=app_with_data_v2

    with app.app_context():
        insert_clients_table("d@d","p_d","n_d","mdp_d","D","Employe")
        assert len(select_client_groupes(2))==2
        assert list(select_client_groupes(2)[0])==[2,"G2"]
        assert list(select_client_groupes(2)[1])==[3,"G3"]
        assert select_client_groupes(4)==[] 

def test_select_client_groupes_by_id(app_with_data_v2):
    """
        Test la fonction select_client_groupes_by_id
        Elle renvoie tous les couple groupe,client (id,id_g,id_c) 
    """
    app=app_with_data_v2

    with app.app_context():
        assert select_client_groupes_by_id(1,3)==[]
        assert list(select_client_groupes_by_id(1,1)[0])==[1,1,1]


def test_delete_member(app_with_data_v2):
    """
        Test la fonction delete_member
        Supprime un membre du groupe  
    """
    app=app_with_data_v2

    with app.app_context():
        assert len(select_member_by_id(3))==3
        assert list(select_member_by_id(3)[0])==[1]
        assert list(select_member_by_id(3)[1])==[2]
        assert list(select_member_by_id(3)[2])==[3]



def test_insert_disscussions_table(app_with_data_v2):
    """
        Test la fonction insert_disscussions_table
        Crée une discussion dans la table Discussions
    """
    app=app_with_data_v2

    with app.app_context():
        data=get_db()
        sql=data.cursor()

        sql.execute("SELECT COUNT(*) AS nb FROM Discussions;")
        assert sql.fetchone()['nb']==0

        insert_disscussions_table(1,"Title1","Content1","Ouvert",1,None)
        insert_disscussions_table(2,"Title2","Content1","Ferme",1,None)
        insert_disscussions_table(2,"Title3","Content1","Ouvert",1,None)

        sql.execute("SELECT COUNT(*) AS nb FROM Discussions;")
        assert sql.fetchone()['nb']==3

def test_select_all_discussions(app_with_data_v3):
    """
        Test la fonction select_all_discussions
        Récupère toutes les discussions(id_c,title,content,type,date_creation,time_creation,cloned_from,priority) dans l'ordre priorité decroissant puis date
    """
    app=app_with_data_v3

    with app.app_context():
        assert len(select_all_discussions())==3



