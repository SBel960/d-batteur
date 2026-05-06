import pytest
from flask import Flask,g
import bdd

@pytest.fixture(scope="function")
def app():
    
    app = Flask(__name__)
    app.secret_key = "ITTorsdyP2Gfzss33gjoY34otqT5BWC5"
    bdd.db_file = "tests/test.db"

    def close_db(e=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    app.teardown_appcontext(close_db)

    yield app

    with app.app_context():
        bdd.reset_all_db()

@pytest.fixture()
def app_with_data_v1(app):
    """
        Base de données avec seulement des membres et des groupes
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")
        bdd.insert_groups_table("G3")
    return app

@pytest.fixture()
def app_with_data_v2(app):
    """
        Base de données avec des membres des groupes et appartenance des membres au groupe 
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")

        bdd.insert_groups_table("G3")
        
        # G1(1) G2(1,2) G3(1,2,3)
        bdd.insert_group_members(1,1)
        bdd.insert_group_members(2,1)
        bdd.insert_group_members(2,2)
        bdd.insert_group_members(3,1)
        bdd.insert_group_members(3,2)
        bdd.insert_group_members(3,3)

    return app

@pytest.fixture()
def app_with_data_v3(app):
    """
        Base de données avec des membres des groupes et appartenance des membres au groupe 
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")

        bdd.insert_groups_table("G3")
        
        # G1(1) G2(1,2) G3(1,2,3)
        bdd.insert_group_members(1,1)
        bdd.insert_group_members(2,1)
        bdd.insert_group_members(2,2)
        bdd.insert_group_members(3,1)
        bdd.insert_group_members(3,2)
        bdd.insert_group_members(3,3)

        bdd.insert_disscussions_table(1,"Title1","Content1","Ouvert",1,None)
        bdd.insert_disscussions_table(2,"Title2","Content1","Ferme",2,None)
        bdd.insert_disscussions_table(3,"Title3","Content1","Ouvert",1,None)


    return app


@pytest.fixture()
def client(app):
    return app.test_client()
