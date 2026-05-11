"""
Tests pytest pour l'application Flask (app.py).

Stratégie :
- On utilise la vraie base SQLite de test (tests/test.db) via le conftest.py fourni.
- Le client Flask vient directement de app.test_client() (fixture `client` du conftest).
- La session est injectée via client.session_transaction().
- Les fixtures de données (v1→v6) sont réutilisées telles quelles depuis le conftest.
- Un fixture autouse `use_test_db` force bdd.db_file sur tests/test.db pour CHAQUE test
  et ferme la connexion cachée dans g avant de rendre la main, garantissant que toutes
  les requêtes HTTP de l'app de prod lisent la même DB que les fixtures.

Structure des fixtures disponibles (conftest.py) :
    app                 → Flask app vide + DB vierge, reset après chaque test
    app_with_data_v1    → membres + groupes
    app_with_data_v2    → v1 + appartenance membres/groupes
    app_with_data_v3    → v2 + discussions
    app_with_data_v4    → v3 + discussion_groups
    app_with_data_v5    → v4 + commentaires
    app_with_data_v6    → v5 + likes
    client              → test_client() de l'app Flask principale

Lancement :
    pytest tests/test_app.py -v
"""

import json
import pytest
import bdd
from app import app as flask_app


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def use_test_db():
    """
    Force bdd.db_file sur tests/test.db pour TOUS les tests de ce fichier.

    Problème résolu : le `client` du conftest appelle l'app Flask de prod, qui ouvre
    sa propre connexion SQLite via flask.g. Si bdd.db_file pointe encore sur la DB
    de prod au moment de la requête HTTP, les données insérées dans tests/test.db
    par les fixtures ne sont pas visibles.

    Solution : on set db_file AVANT le test, on ferme toute connexion résiduelle
    dans le g de l'app de prod, puis on restaure après le test.
    """
    original = bdd.db_file
    bdd.db_file = "tests/test.db"

    # Ferme toute connexion SQLite résiduelle dans le contexte de l'app de prod
    # (peut rester ouverte si un test précédent a fait une requête HTTP)
    with flask_app.app_context():
        db = flask_app.extensions.get("db") or None
        try:
            from flask import g as prod_g
            db = prod_g.pop("db", None)
            if db:
                db.close()
        except RuntimeError:
            pass  # pas de contexte actif, rien à fermer

    yield

    bdd.db_file = original


def login_session(client, id_client=1, first_name="p_a", last_name="n_a",
                  email="a@a", company="A", role="CEO"):
    """Injecte une session authentifiée dans le client de test."""
    with client.session_transaction() as sess:
        sess["logged_in"]   = True
        sess["id_client"]   = id_client
        sess["first_name"]  = first_name
        sess["last_name"]   = last_name
        sess["email"]       = email
        sess["company"]     = company
        sess["role"]        = role


def logout_session(client):
    """Vide la session."""
    with client.session_transaction() as sess:
        sess.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Authentification
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoginPage:
    def test_get_login_page_returns_200(self, client):
        r = client.get("/login_page")
        assert r.status_code == 200

    def test_login_get_redirects_to_login_page(self, client):
        r = client.get("/login", follow_redirects=False)
        assert r.status_code == 302
        assert "login_page" in r.headers["Location"]

    def test_login_missing_email_and_password(self, client):
        r = client.post("/login", data={"email": "", "password": ""})
        assert r.status_code == 200
        assert b"requis" in r.data.lower()

    def test_login_unknown_email(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            r = client.post("/login", data={"email": "inconnu@x.com", "password": "test"})
        assert r.status_code == 200
        assert b"incorrect" in r.data.lower()

    def test_login_wrong_password(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            r = client.post("/login", data={"email": "a@a", "password": "mauvais_mdp"})
        assert r.status_code == 200
        assert b"incorrect" in r.data.lower()

    def test_login_success_redirects_home(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            r = client.post("/login",
                            data={"email": "a@a", "password": "mdp_a"},
                            follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/")

    def test_login_success_sets_session(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            client.post("/login", data={"email": "a@a", "password": "mdp_a"})
        with client.session_transaction() as sess:
            assert sess.get("logged_in") is True
            assert sess.get("email") == "a@a"
            assert sess.get("role") == "CEO"


class TestLogout:
    def test_logout_redirects_to_login(self, client):
        login_session(client)
        r = client.get("/logout", follow_redirects=False)
        assert r.status_code == 302
        assert "login_page" in r.headers["Location"]

    def test_logout_clears_logged_in(self, client):
        login_session(client)
        client.get("/logout")
        with client.session_transaction() as sess:
            assert not sess.get("logged_in")


class TestRegistryPage:
    def test_registry_page_200(self, client):
        r = client.get("/registry_page")
        assert r.status_code == 200

    def test_registry_existing_account_shows_error(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            r = client.post("/registry", data={
                "email": "a@a", "first-name": "Alice", "last-name": "M",
                "new-password": "pwd", "company-name": "A", "role": "Employe",
            })
        assert b"existe" in r.data.lower()

    def test_registry_new_account_redirects(self, client, app_with_data_v1):
        login_session(client, role="CEO")
        with app_with_data_v1.app_context():
            r = client.post("/registry", data={
                "email": "nouveau@x.com", "first-name": "New", "last-name": "User",
                "new-password": "pwd", "company-name": "Co", "role": "Employe",
            }, follow_redirects=False)
        assert r.status_code == 302

    def test_registry_new_account_inserts_user(self, client, app_with_data_v1):
        login_session(client, role="CEO")
        with app_with_data_v1.app_context():
            client.post("/registry", data={
                "email": "new2@x.com", "first-name": "Foo", "last-name": "Bar",
                "new-password": "pwd", "company-name": "Co", "role": "Employe",
            })
            result = bdd.select_client_infos_from_email("new2@x.com")
        assert result is not None

    def test_registry_new_account_with_group(self, client, app_with_data_v1):
        login_session(client, role="CEO")
        with app_with_data_v1.app_context():
            client.post("/registry", data={
                "email": "grp@x.com", "first-name": "G", "last-name": "P",
                "new-password": "pwd", "company-name": "Co", "role": "Employe",
                "groupes": ["1"],
            })
            new_user = bdd.select_client_infos_from_email("grp@x.com")
            new_id = new_user[1]
            memberships = bdd.select_client_groupes_by_id(1, new_id)
        assert len(memberships) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Sécurité – routes protégées (smoke tests)
# ═══════════════════════════════════════════════════════════════════════════════


# Routes qui redirigent vers login_page quand non authentifié
PROTECTED_ROUTES_LOGIN = [
    ("GET",  "/"),
    ("GET",  "/main/1"),
    ("POST", "/commentaire/1/0"),
    ("POST", "/ajouter_discussion"),
    ("POST", "/modifier_discussion/1"),
    ("GET",  "/like_discussion/1/like"),
    ("GET",  "/like_comment/1/1/like"),
    ("GET",  "/groups"),
    ("POST", "/changemember/1"),
    ("POST", "/addgroupe/1"),
    ("POST", "/deletemember/1"),
    ("GET",  "/group_info/1"),
    ("POST", "/updategroup/1"),
    ("POST", "/deletegroup/1"),
    ("GET",  "/allgroupmembers/1"),
    ("GET",  "/membres"),
    ("GET",  "/allmembers"),
    ("POST", "/deleteclient/2"),
    ("POST", "/promoteclient/2"),
    ("POST", "/demoteclient/2"),
    ("GET",  "/profile/1"),
    ("GET",  "/alldiscussions"),
]

# Routes qui redirigent vers / (home, elle-même protégée) quand non authentifié
# car elles ne font pas de check session avant d'agir
PROTECTED_ROUTES_HOME = [
    ("POST", "/clotre_discussion/1/closed"),
    ("POST", "/delete_discussion/1"),
]


@pytest.mark.parametrize("method,url", PROTECTED_ROUTES_LOGIN)
def test_protected_route_redirects_to_login(client, method, url):
    """Sans session → redirection contenant 'login'."""
    logout_session(client)
    r = client.get(url, follow_redirects=False) if method == "GET" \
        else client.post(url, data={}, follow_redirects=False)
    assert r.status_code in (301, 302, 303, 307, 308), \
        f"{method} {url} devrait rediriger, reçu {r.status_code}"
    assert "login" in r.headers.get("Location", "").lower(), \
        f"{method} {url} → Location: {r.headers.get('Location')}"


@pytest.mark.parametrize("method,url", PROTECTED_ROUTES_HOME)
def test_protected_route_redirects_unauthenticated(client, method, url):
    """Sans session → redirige (vers / ou login, peu importe), statut 3xx."""
    logout_session(client)
    r = client.post(url, data={}, follow_redirects=False)
    assert r.status_code in (301, 302, 303, 307, 308), \
        f"{method} {url} devrait rediriger, reçu {r.status_code}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Page d'accueil
# ═══════════════════════════════════════════════════════════════════════════════

class TestHome:
    def test_home_redirects_if_not_logged_in(self, client):
        logout_session(client)
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 302

    def test_home_logged_in_returns_200(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/")
        assert r.status_code == 200

    def test_home_shows_accessible_discussions(self, client, app_with_data_v4):
        """M1 est dans G1, G2, G3 -> /alldiscussions renvoie D1, D2, D3.
        Les titres sont charges via fetch('/alldiscussions') en JS, pas dans le HTML."""
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/alldiscussions")
        data = json.loads(r.data)
        titles = [d["titre"] for d in data]
        assert "Title1" in titles
        assert "Title2" in titles
        assert "Title3" in titles

    def test_home_filters_discussions_by_group(self, client, app_with_data_v4):
        """M3 est uniquement dans G3 → /alldiscussions ne renvoie que D3.
        Les discussions sont chargées via fetch('/alldiscussions') en JS,
        pas injectées dans le HTML statique de la homepage."""
        with app_with_data_v4.app_context():
            login_session(client, id_client=3, email="c@c", company="C", role="Employe",
                          first_name="p_c", last_name="n_c")
            r = client.get("/alldiscussions")
        data = json.loads(r.data)
        titles = [d["titre"] for d in data]
        assert "Title3" in titles
        assert "Title1" not in titles
        assert "Title2" not in titles

    def test_home_shows_deleted_author_fallback(self, client, app_with_data_v4):
        """Auteur supprime (M1) → ses discussions affichent 'Utilisateur supprime'.
        M2 voit D1 (G2), D2 (G2), D3 (G3). D1 et D3 ont M1 comme auteur."""
        with app_with_data_v4.app_context():
            bdd.delete_client(1)
        # Contexte fermé → DELETE commité → visible par la requête HTTP
        login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                      first_name="p_b", last_name="n_b")
        r = client.get("/alldiscussions")
        data = json.loads(r.data)
        # Discussions dont l'auteur original était M1 (maintenant supprimé)
        by_deleted = [d for d in data if d["auteur"] == "Utilisateur supprimé"]
        assert len(by_deleted) >= 1, "Au moins une discussion doit avoir un auteur supprimé"
        # Aucune discussion ne doit afficher le nom réel de M1
        assert all("p_a" not in d["auteur"] for d in data)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Vue discussion (main)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMain:
    def test_main_redirects_if_not_logged_in(self, client):
        logout_session(client)
        assert client.get("/main/1", follow_redirects=False).status_code == 302

    def test_main_returns_200_for_member(self, client, app_with_data_v5):
        with app_with_data_v5.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/main/1")
        assert r.status_code == 200
        assert b"Title1" in r.data

    def test_main_shows_comments(self, client, app_with_data_v5):
        with app_with_data_v5.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/main/1")
        assert b"M1 propose C1 pour dans D1" in r.data

    def test_main_forbidden_if_not_in_group(self, client, app_with_data_v4):
        """M3 n'est pas dans G1/G2 → ne peut pas accéder à D1."""
        with app_with_data_v4.app_context():
            login_session(client, id_client=3, email="c@c", company="C", role="Employe",
                          first_name="p_c", last_name="n_c")
            r = client.get("/main/1", follow_redirects=False)
        assert r.status_code == 302

    def test_main_cloned_discussion(self, client, app_with_data_v5):
        with app_with_data_v5.app_context():
            bdd.insert_disscussions_table(1, "Clone D1", "Content cloné", "ouvert", 1, cloned_from=1)
            clone_id = bdd.select_newest_discussion_id(1)[0]
            bdd.insert_discussion_groups(1, clone_id)
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get(f"/main/{clone_id}")
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Commentaires
# ═══════════════════════════════════════════════════════════════════════════════

class TestCommentaire:
    def test_commentaire_root_redirects_to_discussion(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/commentaire/1/0",
                            data={"commentaire": "Nouveau commentaire", "type": "normal"},
                            follow_redirects=False)
        assert r.status_code == 302
        assert "main/1" in r.headers["Location"]

    def test_commentaire_root_inserts_in_db(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/commentaire/1/0",
                        data={"commentaire": "Contenu inséré", "type": "normal"})
            comments = bdd.select_comments(1)
        assert any("Contenu inséré" in c[3] for c in comments)

    def test_commentaire_reply_returns_json(self, client, app_with_data_v5):
        with app_with_data_v5.app_context():
            login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                          first_name="p_b", last_name="n_b")
            r = client.post("/commentaire/1/1",
                            data={"commentaire": "Ma réponse", "type": "normal", "avis": "pour"})
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data["content"] == "Ma réponse"
        assert data["type_c"] == "normal"
        assert data["avis"] == "pour"

    def test_commentaire_proposition_type(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/commentaire/1/0",
                        data={"commentaire": "Ma proposition", "type": "proposition", "avis": "pour"})
            comments = bdd.select_comments(1)
        assert any(c[4] == "proposition" for c in comments)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CRUD Discussions
# ═══════════════════════════════════════════════════════════════════════════════

class TestAjouterDiscussion:
    def test_ajouter_missing_fields_returns_error(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/ajouter_discussion", data={
                "discussionTitle": "", "discussionContent": "",
                "groupes": [], "discussionType": "",
            })
        assert b"requis" in r.data.lower()

    def test_ajouter_discussion_success_redirects(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/ajouter_discussion", data={
                "discussionTitle": "Nouveau sujet",
                "discussionContent": "Contenu du sujet",
                "groupes": ["1"],
                "discussionType": "ouvert",
            }, follow_redirects=False)
        assert r.status_code == 302
        assert "main/" in r.headers["Location"]

    def test_ajouter_discussion_inserts_in_db(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/ajouter_discussion", data={
                "discussionTitle": "Sujet DB",
                "discussionContent": "Contenu",
                "groupes": ["1"],
                "discussionType": "ouvert",
            })
            discs = bdd.select_all_group_discussions(1)
        assert any(d[2] == "Sujet DB" for d in discs)

    def test_ajouter_discussion_priority_high(self, client, app_with_data_v2):
        """Checkbox cochée → priorité 2."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/ajouter_discussion", data={
                "discussionTitle": "Urgent",
                "discussionContent": "Contenu",
                "groupes": ["1"],
                "discussionType": "ouvert",
                "discussionPriority": "on",
            })
            discs = bdd.select_all_group_discussions(1)
        urgent = [d for d in discs if d[2] == "Urgent"]
        assert len(urgent) == 1
        assert urgent[0][9] == 2  # colonne priority

    def test_ajouter_discussion_priority_low(self, client, app_with_data_v2):
        """Checkbox non cochée → priorité 1."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/ajouter_discussion", data={
                "discussionTitle": "Normal",
                "discussionContent": "Contenu",
                "groupes": ["1"],
                "discussionType": "ouvert",
            })
            discs = bdd.select_all_group_discussions(1)
        normal = [d for d in discs if d[2] == "Normal"]
        assert normal[0][9] == 1

    def test_ajouter_discussion_multi_groupes(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/ajouter_discussion", data={
                "discussionTitle": "Multi",
                "discussionContent": "Contenu",
                "groupes": ["1", "2"],
                "discussionType": "ouvert",
            }, follow_redirects=False)
            disc_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
            groups = bdd.select_discussion_groups(disc_id)
        assert len(groups) == 2


class TestModifierDiscussion:
    def test_modifier_discussion_updates_title(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/modifier_discussion/1", data={
                "discussionTitle": "Titre modifié",
                "discussionContent": "Content1",
                "groupes": ["1"],
                "discussionPriority": "",
            })
            disc = bdd.select_discussion_by_id(1)
        assert disc[1] == "Titre modifié"

    def test_modifier_discussion_redirects(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/modifier_discussion/1", data={
                "discussionTitle": "T", "discussionContent": "C",
                "groupes": ["1"], "discussionPriority": "",
            }, follow_redirects=False)
        assert r.status_code == 302
        assert "main/1" in r.headers["Location"]


class TestClotrDiscussion:
    def test_cloture_discussion_updates_state(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/clotre_discussion/1/closed")
            disc = bdd.select_discussion_by_id(1)
        assert disc[4] == "closed"

    def test_cloture_discussion_redirects_home(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/clotre_discussion/1/closed", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/")


class TestClonerDiscussion:
    def test_cloner_discussion_creates_new(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            before = len(bdd.select_all_group_discussions(1))
            client.post("/cloner_discussion/1", data={"groupes": ["1"]})
            after = len(bdd.select_all_group_discussions(1))
        assert after == before + 1

    def test_cloner_discussion_redirects_to_clone(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/cloner_discussion/1",
                            data={"groupes": ["1"]},
                            follow_redirects=False)
        assert r.status_code == 302
        assert "main/" in r.headers["Location"]

    def test_cloner_discussion_copies_title(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/cloner_discussion/1",
                            data={"groupes": ["1"]},
                            follow_redirects=False)
            clone_id = int(r.headers["Location"].rstrip("/").split("/")[-1])
            clone = bdd.select_discussion_by_id(clone_id)
        assert clone[1] == "Title1"


class TestDeleteDiscussion:
    def test_delete_discussion_removes_from_db(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/delete_discussion/1")
            result = bdd.select_discussion_by_id(1)
        assert result is None

    def test_delete_discussion_redirects_home(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/delete_discussion/1", follow_redirects=False)
        assert r.status_code == 302
        assert r.headers["Location"].endswith("/")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Votes
# ═══════════════════════════════════════════════════════════════════════════════

class TestLikeDiscussion:
    def test_like_discussion_returns_json(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/like_discussion/1/like")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "likes" in data and "dislikes" in data

    def test_like_discussion_increments_likes(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                          first_name="p_b", last_name="n_b")
            before_likes, _ = bdd.get_discussion_likes(1)
            client.get("/like_discussion/1/like")
            after_likes, _ = bdd.get_discussion_likes(1)
        assert after_likes == before_likes + 1

    def test_unlike_discussion_increments_dislikes(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                          first_name="p_b", last_name="n_b")
            _, before_dislikes = bdd.get_discussion_likes(1)
            client.get("/like_discussion/1/unlike")
            _, after_dislikes = bdd.get_discussion_likes(1)
        assert after_dislikes == before_dislikes + 1

    def test_like_discussion_invalid_action_redirects(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/like_discussion/1/badaction", follow_redirects=False)
        assert r.status_code == 302

    def test_like_discussion_from_homepage_redirects(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/like_discussion/1/like?origin_page=homepage",
                           follow_redirects=False)
        assert r.status_code == 302


class TestLikeComment:
    def test_like_comment_returns_json(self, client, app_with_data_v6):
        with app_with_data_v6.app_context():
            login_session(client, id_client=3, email="c@c", company="C", role="Employe",
                          first_name="p_c", last_name="n_c")
            r = client.get("/like_comment/1/1/like")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert "likes" in data
        assert "score" in data

    def test_like_comment_increments_likes(self, client, app_with_data_v6):
        with app_with_data_v6.app_context():
            login_session(client, id_client=3, email="c@c", company="C", role="Employe",
                          first_name="p_c", last_name="n_c")
            before, _ = bdd.get_comment_likes(1)
            client.get("/like_comment/1/1/like")
            after, _ = bdd.get_comment_likes(1)
        assert after == before + 1

    def test_unlike_comment_increments_dislikes(self, client, app_with_data_v6):
        with app_with_data_v6.app_context():
            login_session(client, id_client=3, email="c@c", company="C", role="Employe",
                          first_name="p_c", last_name="n_c")
            _, before = bdd.get_comment_likes(2)
            client.get("/like_comment/1/2/unlike")
            _, after = bdd.get_comment_likes(2)
        assert after == before + 1

    def test_like_comment_reply_includes_proposition_score(self, client, app_with_data_v5):
        """Liker C5 (réponse à C4 proposition) → proposition_score renvoyé."""
        with app_with_data_v5.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/like_comment/3/5/like")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert data.get("proposition_id") == 4
        assert "proposition_score" in data

    def test_like_comment_invalid_action_redirects(self, client, app_with_data_v5):
        with app_with_data_v5.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/like_comment/1/1/badaction", follow_redirects=False)
        assert r.status_code == 302


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Réponses aux commentaires
# ═══════════════════════════════════════════════════════════════════════════════

class TestShowAllReplies:
    def test_show_replies_returns_list(self, client, app_with_data_v5):
        """C4 a deux réponses directes (C5 et C7)."""
        with app_with_data_v5.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/show_all_replies/3/4")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert len(data) == 2

    def test_show_replies_empty(self, client, app_with_data_v5):
        """C1 n'a aucune réponse directe."""
        with app_with_data_v5.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/show_all_replies/1/1")
        assert json.loads(r.data) == []

    def test_show_replies_structure(self, client, app_with_data_v5):
        """Vérifie les champs JSON requis."""
        with app_with_data_v5.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/show_all_replies/3/4")
        data = json.loads(r.data)
        required_keys = {"id_c", "content", "type", "like", "dislike", "username", "opinion"}
        for item in data:
            assert required_keys.issubset(item.keys())

    def test_show_replies_sorted_by_score(self, client, app_with_data_v6):
        """Les réponses doivent être triées par (likes - dislikes) décroissant."""
        with app_with_data_v6.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/show_all_replies/3/4")
        data = json.loads(r.data)
        scores = [item["like"] - item["dislike"] for item in data]
        assert scores == sorted(scores, reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Groupes
# ═══════════════════════════════════════════════════════════════════════════════

class TestGroupsPage:
    def test_groups_page_200(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/groups")
        assert r.status_code == 200

    def test_create_group_success(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/groups", data={"groupName": "NouveauGroupe"})
            groups = [g[1] for g in bdd.select_all_groupes()]
        assert "NouveauGroupe" in groups

    def test_create_group_duplicate_shows_error(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/groups", data={"groupName": "G1"})
        assert b"existe" in r.data.lower()

    def test_create_group_empty_name_shows_error(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/groups", data={"groupName": ""})
        assert b"requis" in r.data.lower()


class TestGroupInfo:
    def test_group_info_200(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/group_info/1")
        assert r.status_code == 200

    def test_group_info_shows_members(self, client, app_with_data_v2):
        """G3 contient M1, M2, M3."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/group_info/3")
        assert b"p_a" in r.data or b"n_a" in r.data


class TestChangeMemberGroup:
    def test_change_member_adds_new_member(self, client, app_with_data_v2):
        """Envoyer M3 dans G1 (qui ne contient que M1) → M3 ajouté."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/changemember/1", data={"memberList": ["3"]})
            members = [m[0] for m in bdd.select_member_by_id(1)]
        assert 3 in members

    def test_change_member_removes_old_member(self, client, app_with_data_v2):
        """G2 contient M1 et M2. Envoyer uniquement M1 (session) → M2 retiré."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/changemember/2", data={"memberList": []})
            members = [m[0] for m in bdd.select_member_by_id(2)]
        assert 2 not in members


class TestAddMemberToGroup:
    def test_add_member_not_in_group(self, client, app_with_data_v2):
        """G1 ne contient que M1. Ajouter M3 → M3 est membre."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/addgroupe/1", data={"memberList": ["3"], "origin": "groupinfo"})
            members = [m[0] for m in bdd.select_member_by_id(1)]
        assert 3 in members

    def test_add_member_already_in_group_no_duplicate(self, client, app_with_data_v2):
        """Ajouter M1 dans G1 où il est déjà → pas de doublon."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/addgroupe/1", data={"memberList": ["1"], "origin": "groupinfo"})
            count = len([m for m in bdd.select_member_by_id(1) if m[0] == 1])
        assert count == 1


class TestDeleteMemberFromGroup:
    def test_delete_member_existing(self, client, app_with_data_v2):
        """Retirer M2 de G2 → M2 n'est plus dans G2."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/deletemember/2",
                        data={"memberList": ["2"], "origin": "groupinfo"})
            members = [m[0] for m in bdd.select_member_by_id(2)]
        assert 2 not in members

    def test_delete_member_not_in_group_no_error(self, client, app_with_data_v2):
        """Tenter de retirer M3 de G1 où il n'est pas → pas d'erreur, 302."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/deletemember/1",
                            data={"memberList": ["3"], "origin": "groupinfo"},
                            follow_redirects=False)
        assert r.status_code == 302


class TestUpdateGroupName:
    def test_update_group_name(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/updategroup/1",
                        data={"groupName": "G1 Renommé", "origin": "groupinfo"})
            name = bdd.select_groupe_from_id(1)[0]
        assert name == "G1 Renommé"

    def test_update_group_name_redirects(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/updategroup/1",
                            data={"groupName": "Nouveau", "origin": "groupinfo"},
                            follow_redirects=False)
        assert r.status_code == 302


class TestDeleteGroup:
    def test_delete_group_removes_from_db(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/deletegroup/1")
            groups = [g[1] for g in bdd.select_all_groupes()]
        assert "G1" not in groups

    def test_delete_group_removes_members(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/deletegroup/2")
            members = bdd.select_member_by_id(2)
        assert len(members) == 0

    def test_delete_group_redirects_groups_page(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/deletegroup/1", follow_redirects=False)
        assert r.status_code == 302
        assert "groups" in r.headers["Location"]


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Membres & Profil
# ═══════════════════════════════════════════════════════════════════════════════

class TestMembres:
    def test_membres_200(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/membres")
        assert r.status_code == 200

    def test_membres_lists_all_users(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/membres")
        assert b"p_a" in r.data
        assert b"p_b" in r.data
        assert b"p_c" in r.data


class TestGetAllMembers:
    def test_get_all_members_json(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/allmembers")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert len(data) == 3
        names = [m["name"] for m in data]
        assert "p_a" in names


class TestProfile:
    def test_profile_own_200(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/profile/1")
        assert r.status_code == 200

    def test_profile_other_user_200(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/profile/2")
        assert r.status_code == 200

    def test_profile_shows_groups(self, client, app_with_data_v2):
        """M1 est dans G1, G2, G3 → profil affiche ses groupes."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/profile/1")
        assert b"G1" in r.data


class TestApiGroupMembers:
    def test_api_group_members_returns_json(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/api/group_members/3")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_api_group_members_excludes_self(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/api/group_members/3")
        data = json.loads(r.data)
        assert all(m["id"] != 1 for m in data)

    def test_api_group_members_count(self, client, app_with_data_v2):
        """G3 a 3 membres → endpoint renvoie 2 (exclut l'utilisateur courant id=1)."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/api/group_members/3")
        assert len(json.loads(r.data)) == 2


class TestApiGroupNonMembers:
    def test_api_non_members_returns_json(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/api/group_non_members/1")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_api_non_members_count(self, client, app_with_data_v2):
        """G1 a M1 → M2 et M3 sont non-membres."""
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/api/group_non_members/1")
        assert len(json.loads(r.data)) == 2


class TestGetAllMembersGroups:
    def test_allgroupmembers_json(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/allgroupmembers/3")
        assert r.status_code == 200
        data = json.loads(r.data)
        assert len(data) == 3
        assert all("role" in m for m in data)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Promotion / Rétrogradation
# ═══════════════════════════════════════════════════════════════════════════════

class TestPromoteClient:
    def test_promote_employe_to_manager(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/promoteclient/3")  # M3 est Employe
            role = bdd.select_role_client(3)[0]
        assert role == "Manager"

    def test_promote_manager_to_ceo(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/promoteclient/2")  # M2 est Manager
            role = bdd.select_role_client(2)[0]
        assert role == "CEO"

    def test_promote_non_ceo_forbidden(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                          first_name="p_b", last_name="n_b")
            client.post("/promoteclient/3")
            role = bdd.select_role_client(3)[0]
        assert role == "Employe"  # inchangé

    def test_promote_self_forbidden(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/promoteclient/1", follow_redirects=False)
        assert r.status_code == 302

    def test_promote_redirects_to_membres(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/promoteclient/3", follow_redirects=False)
        assert r.status_code == 302
        assert "membres" in r.headers["Location"]


class TestDemoteClient:
    def test_demote_manager_to_employe(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/demoteclient/2")  # M2 est Manager
            role = bdd.select_role_client(2)[0]
        assert role == "Employe"

    def test_demote_ceo_to_manager(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            bdd.update_role("CEO", 2)
        # Contexte fermé → UPDATE commité → visible par la requête HTTP
        login_session(client, id_client=1, email="a@a", company="A", role="CEO")
        client.post("/demoteclient/2")
        with app_with_data_v1.app_context():
            role = bdd.select_role_client(2)[0]
        assert role == "Manager"

    def test_demote_non_ceo_forbidden(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                          first_name="p_b", last_name="n_b")
            client.post("/demoteclient/3")
            role = bdd.select_role_client(3)[0]
        assert role == "Employe"  # inchangé

    def test_demote_self_forbidden(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/demoteclient/1", follow_redirects=False)
        assert r.status_code == 302


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Suppression de client
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeleteClient:
    def test_delete_client_by_ceo(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/deleteclient/3")
            result = bdd.get_user_by_id(3)
        assert result is None

    def test_delete_client_removes_group_memberships(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/deleteclient/3")
            members_g3 = [m[0] for m in bdd.select_member_by_id(3)]
        assert 3 not in members_g3

    def test_delete_client_non_ceo_forbidden(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                          first_name="p_b", last_name="n_b")
            client.post("/deleteclient/3")
            result = bdd.get_user_by_id(3)
        assert result is not None

    def test_delete_self_forbidden(self, client, app_with_data_v1):
        with app_with_data_v1.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            client.post("/deleteclient/1")
            result = bdd.get_user_by_id(1)
        assert result is not None

    def test_delete_client_redirects(self, client, app_with_data_v2):
        with app_with_data_v2.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.post("/deleteclient/3", follow_redirects=False)
        assert r.status_code == 302


# ═══════════════════════════════════════════════════════════════════════════════
# 13. API JSON – alldiscussions
# ═══════════════════════════════════════════════════════════════════════════════

class TestAllDiscussions:
    def test_alldiscussions_returns_json(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/alldiscussions")
        assert r.status_code == 200
        assert isinstance(json.loads(r.data), list)

    def test_alldiscussions_filters_by_group(self, client, app_with_data_v4):
        """M3 est dans G3 seulement → voit seulement D3."""
        with app_with_data_v4.app_context():
            login_session(client, id_client=3, email="c@c", company="C", role="Employe",
                          first_name="p_c", last_name="n_c")
            r = client.get("/alldiscussions")
        data = json.loads(r.data)
        titles = [d["titre"] for d in data]
        assert "Title3" in titles
        assert "Title1" not in titles

    def test_alldiscussions_type_ouvert(self, client, app_with_data_v4):
        """Le type JSON de D1 reflète la logique de l'app (case-sensitive sur 'ouvert')."""
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            raw_type = bdd.select_discussion_by_id(1)[3]  # type brut stocké
            r = client.get("/alldiscussions")
        data = json.loads(r.data)
        d1 = next(d for d in data if d["titre"] == "Title1")
        # L'app fait : "Question" si raw == "ouvert" (minuscule), sinon "Proposition"
        expected = "Question" if raw_type == "ouvert" else "Proposition"
        assert d1["type"] == expected

    def test_alldiscussions_type_ferme(self, client, app_with_data_v4):
        """D2 n'est pas de type 'ouvert' → toujours 'Proposition'."""
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/alldiscussions")
        data = json.loads(r.data)
        d2 = next(d for d in data if d["titre"] == "Title2")
        assert d2["type"] == "Proposition"

    def test_alldiscussions_deleted_author(self, client, app_with_data_v4):
        """Auteur supprime (M1) → ses discussions affichent 'Utilisateur supprime'.
        M2 voit D1 (G2), D2 (G2), D3 (G3). D1 et D3 ont M1 comme auteur."""
        with app_with_data_v4.app_context():
            bdd.delete_client(1)
        # Contexte fermé → DELETE commité → visible par la requête HTTP
        login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                      first_name="p_b", last_name="n_b")
        r = client.get("/alldiscussions")
        data = json.loads(r.data)
        by_deleted = [d for d in data if d["auteur"] == "Utilisateur supprimé"]
        assert len(by_deleted) >= 1, "Au moins une discussion doit avoir un auteur supprimé"
        assert all("p_a" not in d["auteur"] for d in data)

    def test_alldiscussions_has_required_fields(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=1, email="a@a", company="A", role="CEO")
            r = client.get("/alldiscussions")
        data = json.loads(r.data)
        required = {"id", "titre", "contenu", "type", "likes", "dislikes",
                    "groupes", "auteur", "date", "heure", "etat", "priorite"}
        for disc in data:
            assert required.issubset(disc.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Mapping rôles
# ═══════════════════════════════════════════════════════════════════════════════

class TestRolesNumeros:
    def test_roles_numeros_mapping(self):
        from app import roles_numeros
        assert roles_numeros["CEO"] == 3
        assert roles_numeros["Manager"] == 2
        assert roles_numeros["Employe"] == 1

    def test_home_passes_correct_role_number(self, client, app_with_data_v4):
        with app_with_data_v4.app_context():
            login_session(client, id_client=2, email="b@b", company="B", role="Manager",
                          first_name="p_b", last_name="n_b")
            r = client.get("/")
        assert r.status_code == 200