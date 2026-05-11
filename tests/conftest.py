import pytest
from flask import Flask,g
import bdd
from app import app as app_test
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
        Base de données avec membres + groupes
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
        Base de données avec + membres + groupes + appartenance des membres au groupe 
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")

        bdd.insert_groups_table("G3")
        
        # G1(M1) G2(M1,M2) G3(M1,M2,M3)
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
        Base de données avec des membres + des groupes + appartenance des membres au groupe + discussions
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")

        bdd.insert_groups_table("G3")
        
        # G1(M1) G2(M1,M2) G3(M1,M2,M3)
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

def app_with_data_v4(app):
    """
        Base de données avec des membres + des groupes + appartenance des membres au groupe + groupe pour les discussions
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")

        bdd.insert_groups_table("G3")
        
        # G1(M1) G2(M1,M2) G3(M1,M2,M3)
        bdd.insert_group_members(1,1)
        bdd.insert_group_members(2,1)
        bdd.insert_group_members(2,2)
        bdd.insert_group_members(3,1)
        bdd.insert_group_members(3,2)
        bdd.insert_group_members(3,3)

        bdd.insert_disscussions_table(1,"Title1","Content1","Ouvert",1,None)
        bdd.insert_disscussions_table(2,"Title2","Content1","Ferme",2,None)
        bdd.insert_disscussions_table(3,"Title3","Content1","Ouvert",1,None)
        
        # D1(G1,G2) D2(G2) D3(G3)
        # D1(M1,M2) D2(M1,M2) D3(M1,M2,M3)
        bdd.insert_discussion_groups(1,1)
        bdd.insert_discussion_groups(2,1)
        bdd.insert_discussion_groups(2,2)
        bdd.insert_discussion_groups(3,3)


    return app

@pytest.fixture()
def app_with_data_v5(app):
    """
        Base de données avec des membres + des groupes + appartenance des membres au groupe + groupe pour les discussions + commentaires
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")

        bdd.insert_groups_table("G3")
        
        # G1(M1) G2(M1,M2) G3(M1,M2,M3)
        bdd.insert_group_members(1,1)
        bdd.insert_group_members(2,1)
        bdd.insert_group_members(2,2)
        bdd.insert_group_members(3,1)
        bdd.insert_group_members(3,2)
        bdd.insert_group_members(3,3)

        bdd.insert_disscussions_table(1,"Title1","Content1","Ouvert",1,None)
        bdd.insert_disscussions_table(2,"Title2","Content1","Ferme",2,None)
        bdd.insert_disscussions_table(3,"Title3","Content1","Ouvert",1,None)
        
        # D1(G1,G2) D2(G2) D3(G3)
        # D1(M1,M2) D2(M1,M2) D3(M1,M2,M3)
        bdd.insert_discussion_groups(1,1)
        bdd.insert_discussion_groups(2,1)
        bdd.insert_discussion_groups(2,2)
        bdd.insert_discussion_groups(3,3)
        
        #D1(M1 propose C1 pour dans D1      )
        #  (M2 commente C2 contre dans D1   )
        #D2(M2 propose C3 contre dans D2)
        #D3(M1 propose pour <-- M2 répond pour  <-- M3 répond contre  )
        #  (                <-- M3 repond contre                      )

        bdd.insert_comments_table(1,1,"M1 propose C1 pour dans D1","proposition","pour",0)
        bdd.insert_comments_table(2,1,"M2 commente C2 contre dans D1","normal","contre",0)
        bdd.insert_comments_table(2,2,"M2 propose C3 contre dans D2","proposition","contre",0)
        bdd.insert_comments_table(1,3,"M1 propose C4 pour dans D3","proposition","pour",0)
        bdd.insert_comments_table(2,3,"M2 répond C5 à C4 neutre","normal","pour",4)
        bdd.insert_comments_table(3,3,"M3 répond C6 à C5 neutre","normal","contre",5)
        bdd.insert_comments_table(3,3,"M3 répond C7 à C4 neutre","normal","contre",4)

        

    return app

@pytest.fixture()
def app_with_data_v6(app):
    """
        Base de données avec des membres + des groupes + appartenance des membres au groupe + groupe pour les discussions + commentaires + like (forme final)
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")

        bdd.insert_groups_table("G3")
        
        # G1(M1) G2(M1,M2) G3(M1,M2,M3)
        bdd.insert_group_members(1,1)
        bdd.insert_group_members(2,1)
        bdd.insert_group_members(2,2)
        bdd.insert_group_members(3,1)
        bdd.insert_group_members(3,2)
        bdd.insert_group_members(3,3)

        bdd.insert_disscussions_table(1,"Title1","Content1","Ouvert",1,None)
        bdd.insert_disscussions_table(2,"Title2","Content1","Ferme",2,None)
        bdd.insert_disscussions_table(3,"Title3","Content1","Ouvert",1,None)
        
        # D1(G1,G2) D2(G2) D3(G3)
        # D1(M1,M2) D2(M1,M2) D3(M1,M2,M3)
        bdd.insert_discussion_groups(1,1)
        bdd.insert_discussion_groups(2,1)
        bdd.insert_discussion_groups(2,2)
        bdd.insert_discussion_groups(3,3)
        
        #D1(M1 propose C1 pour dans D1      )
        #  (M2 commente C2 contre dans D1   )
        #D2(M2 propose C3 contre dans D2)
        #D3(M1 propose pour <-- M2 répond pour  <-- M3 répond contre  )
        #  (                <-- M3 repond contre                      )

        bdd.insert_comments_table(1,1,"M1 propose C1 pour dans D1","proposition","pour",0)
        bdd.insert_comments_table(2,1,"M2 commente C2 contre dans D1","normal","contre",0)
        bdd.insert_comments_table(2,2,"M2 propose C3 contre dans D2","proposition","contre",0)
        bdd.insert_comments_table(1,3,"M1 propose C4 pour dans D3","proposition","pour",0)
        bdd.insert_comments_table(2,3,"M2 répond C5 à C4 neutre","normal","pour",4)
        bdd.insert_comments_table(3,3,"M3 répond C6 à C5 neutre","normal","contre",5)
        bdd.insert_comments_table(3,3,"M3 répond C7 à C4 neutre","normal","contre",4)

        # D1(+M1  ) D2(- M2) D3(+ M1 M2 - M3 )
        # C1(+M1 -M2 ) C2(+ M2) C3(+ M2 ) C4(+ M1 M2 -M3) C5(-M3) C6(+M3) C7(+M3)
        
        bdd.insert_likes_table(1,"comment",1,1)
        bdd.insert_likes_table(2,"comment",1,-1)
        bdd.insert_likes_table(2,"comment",2,1)
        bdd.insert_likes_table(2,"comment",3,1)
        bdd.insert_likes_table(1,"comment",4,1)
        bdd.insert_likes_table(2,"comment",4,1)
        bdd.insert_likes_table(3,"comment",4,-1)
        bdd.insert_likes_table(3,"comment",5,-1)
        bdd.insert_likes_table(3,"comment",6,1)
        bdd.insert_likes_table(3,"comment",7,1)
        bdd.insert_likes_table(1,"discussion",1,1)
        bdd.insert_likes_table(2,"discussion",2,-1)
        bdd.insert_likes_table(1,"discussion",3,1)
        bdd.insert_likes_table(2,"discussion",3,1)
        bdd.insert_likes_table(3,"discussion",3,-1)

        

    return app


@pytest.fixture()
def app_test_algo(app):
    """
        Base de données pour tester get propose
    """
    with app.app_context():
        bdd.insert_clients_table("a@a","p_a","n_a","mdp_a","A","CEO")
        bdd.insert_clients_table("b@b","p_b","n_b","mdp_b","B","Manager")
        bdd.insert_clients_table("c@c","p_c","n_c","mdp_c","C","Employe")

        bdd.insert_groups_table("G1")
        bdd.insert_groups_table("G2")

        bdd.insert_groups_table("G3")
        
        # G1(M1) G2(M1,M2) G3(M1,M2,M3)
        bdd.insert_group_members(1,1)
        bdd.insert_group_members(2,1)
        bdd.insert_group_members(2,2)
        bdd.insert_group_members(3,1)
        bdd.insert_group_members(3,2)
        bdd.insert_group_members(3,3)

        bdd.insert_disscussions_table(1,"Title1","Content1","Ouvert",1,None)
        bdd.insert_disscussions_table(2,"Title2","Content1","Ferme",2,None)
        bdd.insert_disscussions_table(3,"Title3","Content1","Ouvert",1,None)
        
        # D1(G1,G2) D2(G2) D3(G3)
        # D1(M1,M2) D2(M1,M2) D3(M1,M2,M3)
        bdd.insert_discussion_groups(1,1)
        bdd.insert_discussion_groups(2,1)
        bdd.insert_discussion_groups(2,2)
        bdd.insert_discussion_groups(3,3)

        """
                [1] PROPOSITION
            "Ajouter un mode sombre"

            ├── [2] POUR
            │   └── "Très bonne idée"
            │       Likes : 8
            │       Dislikes : 2
            │       Net : +6
            │       Crédibilité : 7

            ├── [3] CONTRE
            │   └── "Inutile"
            │       Likes : 2
            │       Dislikes : 5
            │       Net : -3
            │       Crédibilité : 1
            │
            │       └── [5] POUR
            │           └── "Pourquoi inutile ?"
            │               Likes : 4
            │               Dislikes : 0
            │               Net : +4
            │               Crédibilité : 5
            │
            │               └── [6] CONTRE
            │                   └── "Parce que peu de gens l'utiliseront"
            │                       Likes : 3
            │                       Dislikes : 1
            │                       Net : +2
            │                       Crédibilité : 3

            └── [4] POUR
                └── "Je suis d'accord"
                    Likes : 5
                    Dislikes : 0
                    Net : +5
                    Crédibilité : 6
        """
        
        bdd.insert_comments_table(
            1,
            1,
            "Ajouter un mode sombre",
            "proposition",
            "pour",
            0
        )

        # =====================================================
        # RÉPONSES
        # =====================================================

        # id_comment = 2
        bdd.insert_comments_table(
            2,
            1,
            "Très bonne idée",
            "normal",
            "pour",
            1
        )

        # id_comment = 3
        bdd.insert_comments_table(
            3,
            1,
            "Inutile",
            "normal",
            "contre",
            1
        )

        # id_comment = 4
        bdd.insert_comments_table(
            4,
            1,
            "Je suis d'accord",
            "normal",
            "pour",
            1
        )

        # =====================================================
        # SOUS-RÉPONSES
        # =====================================================

        # réponse au commentaire 3
        # id_comment = 5
        bdd.insert_comments_table(
            5,
            1,
            "Pourquoi inutile ?",
            "normal",
            "pour",
            3
        )

        # réponse au commentaire 5
        # id_comment = 6
        bdd.insert_comments_table(
            6,
            1,
            "Parce que peu de gens l'utiliseront",
            "normal",
            "contre",
            5
        )

        # =====================================================
        # LIKES / DISLIKES
        # =====================================================

        # commentaire 2 : 8 likes / 2 dislikes
        bdd.insert_likes_table(10, 'comment', 2, 1)
        bdd.insert_likes_table(11, 'comment', 2, 1)
        bdd.insert_likes_table(12, 'comment', 2, 1)
        bdd.insert_likes_table(13, 'comment', 2, 1)
        bdd.insert_likes_table(14, 'comment', 2, 1)
        bdd.insert_likes_table(15, 'comment', 2, 1)
        bdd.insert_likes_table(16, 'comment', 2, 1)
        bdd.insert_likes_table(17, 'comment', 2, 1)

        bdd.insert_likes_table(18, 'comment', 2, -1)
        bdd.insert_likes_table(19, 'comment', 2, -1)

        # commentaire 3 : 2 likes / 5 dislikes
        bdd.insert_likes_table(20, 'comment', 3, 1)
        bdd.insert_likes_table(21, 'comment', 3, 1)

        bdd.insert_likes_table(22, 'comment', 3, -1)
        bdd.insert_likes_table(23, 'comment', 3, -1)
        bdd.insert_likes_table(24, 'comment', 3, -1)
        bdd.insert_likes_table(25, 'comment', 3, -1)
        bdd.insert_likes_table(26, 'comment', 3, -1)

        # commentaire 4 : 5 likes
        bdd.insert_likes_table(30, 'comment', 4, 1)
        bdd.insert_likes_table(31, 'comment', 4, 1)
        bdd.insert_likes_table(32, 'comment', 4, 1)
        bdd.insert_likes_table(33, 'comment', 4, 1)
        bdd.insert_likes_table(34, 'comment', 4, 1)

        # commentaire 5 : 4 likes
        bdd.insert_likes_table(40, 'comment', 5, 1)
        bdd.insert_likes_table(41, 'comment', 5, 1)
        bdd.insert_likes_table(42, 'comment', 5, 1)
        bdd.insert_likes_table(43, 'comment', 5, 1)

        # commentaire 6 : 3 likes / 1 dislike
        bdd.insert_likes_table(50, 'comment', 6, 1)
        bdd.insert_likes_table(51, 'comment', 6, 1)
        bdd.insert_likes_table(52, 'comment', 6, 1)

        bdd.insert_likes_table(53, 'comment', 6, -1)

        return app

@pytest.fixture()
def client():
    return app_test.test_client()
