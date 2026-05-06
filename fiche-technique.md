# Fiche Technique — Les Débatteurs
**Plateforme de débat collaboratif pour entreprises**
Année 2025-2026 · Projet Web

---

## 1. Présentation générale

**Les Débatteurs** est une application web full-stack qui permet aux membres d'une entreprise de créer et participer à des discussions structurées, organisées par groupes. L'application distingue deux types de discussions (ouvertes ou fermées), propose un système de vote, de propositions de réponses, et classe les contributions grâce à un algorithme de score composite.

**Problème adressé :** Dans une entreprise, les décisions collectives se perdent souvent dans des e-mails désorganisés ou des réunions sans trace. Les Débatteurs centralise ces échanges avec un vrai système de vote et de visibilité par périmètre (groupes).

---

## 2. Stack technique

| Couche | Technologie | Version |
|--------|-------------|---------|
| Backend | Python Flask | 3.x |
| Base de données | SQLite3 | intégré Python |
| Templating | Jinja2 | intégré Flask |
| Frontend | HTML5 + CSS3 + JavaScript Vanilla | — |
| Communication async | Fetch API | natif navigateur |

**Pourquoi Flask et pas Django ?**
Flask est un micro-framework minimaliste. Il ne force pas de structure rigide, ce qui convient parfaitement à un projet académique où on veut comprendre chaque partie. Django aurait apporté trop de "magie" (ORM, admin auto, etc.) que l'on préfère gérer manuellement pour l'apprentissage.

**Pourquoi SQLite et pas PostgreSQL / MySQL ?**
SQLite ne nécessite aucune installation de serveur de base de données séparé. La BDD est un simple fichier `.db`. C'est idéal pour un projet local ou académique. En production réelle, on migrerait vers PostgreSQL.

**Pourquoi pas de framework JavaScript (React, Vue, Angular) ?**
Le projet ne nécessite pas de composants réactifs complexes. La Fetch API native + la manipulation du DOM JavaScript suffisent pour les mises à jour en temps réel (likes, scores, réponses). Éviter un framework JS réduit la complexité et le temps de développement.

**Pourquoi Jinja2 ?**
Jinja2 est intégré à Flask. Il permet le rendu côté serveur (Server-Side Rendering) : le HTML est généré par Python avant d'être envoyé au navigateur. Pas besoin d'une API REST séparée pour la plupart des pages.

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      NAVIGATEUR                          │
│   HTML / CSS / JS  ←→  Fetch API (AJAX)                 │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP (GET / POST)
┌────────────────────────────▼────────────────────────────┐
│                    SERVEUR FLASK                         │
│   app.py → Routes → Logique métier → Jinja2 templates   │
└────────────────────────────┬────────────────────────────┘
                             │ SQL (requêtes paramétrées)
┌────────────────────────────▼────────────────────────────┐
│                     BASE DE DONNÉES                      │
│   SQLite3  ·  fichier approot/app.db  ·  7 tables        │
└─────────────────────────────────────────────────────────┘
```

**Pattern utilisé :** MVC simplifié
- **Model** : `bdd.py` — toutes les fonctions d'accès aux données
- **View** : dossier `templates/` — les fichiers HTML Jinja2
- **Controller** : `app.py` — les routes Flask

---

## 4. Modèle de données complet

### Table `Client`
| Colonne | Type | Description |
|---------|------|-------------|
| `id_client` | INTEGER PK AUTOINCREMENT | Identifiant unique |
| `email` | TEXT NOT NULL UNIQUE | Email de connexion |
| `name` | TEXT NOT NULL | Prénom |
| `last_name` | TEXT NOT NULL | Nom |
| `password` | TEXT NOT NULL | Mot de passe (non hashé — voir limites) |
| `company` | TEXT NOT NULL | Nom de l'entreprise |
| `role` | TEXT | CEO, Manager, ou Employe |

### Table `Discussions`
| Colonne | Type | Description |
|---------|------|-------------|
| `id_discussion` | INTEGER PK AUTOINCREMENT | Identifiant unique |
| `id_c` | INTEGER FK → Client | Créateur de la discussion |
| `title` | TEXT NOT NULL | Titre |
| `content` | TEXT NOT NULL | Description |
| `type` | TEXT NOT NULL | `ouvert` ou `ferme` |
| `date_creation` | DATE NOT NULL | Date de création |
| `time_creation` | TIME NOT NULL | Heure de création |
| `state` | TEXT NOT NULL | `active` ou `closed` |
| `cloned_from` | INTEGER DEFAULT NULL | ID de la discussion parente si clonée |
| `priority` | INTEGER NOT NULL DEFAULT 1 | 0 = fermée, 1 = normale, 2 = prioritaire |

### Table `Comments`
| Colonne | Type | Description |
|---------|------|-------------|
| `id_comment` | INTEGER PK AUTOINCREMENT | Identifiant unique |
| `id_c` | INTEGER FK → Client | Auteur |
| `id_d` | INTEGER FK → Discussions | Discussion associée |
| `content` | TEXT NOT NULL | Contenu du commentaire |
| `type` | TEXT NOT NULL | `proposition` ou `normal` |
| `avis` | TEXT | `pour`, `contre`, `neutre` (uniquement pour les réponses à une proposition) |
| `id_reply` | INTEGER NOT NULL | 0 si commentaire racine, sinon ID du commentaire parent |
| `state` | TEXT NOT NULL | `active` ou `closed` |

### Table `Likes`
| Colonne | Type | Description |
|---------|------|-------------|
| `id_like` | INTEGER PK AUTOINCREMENT | Identifiant unique |
| `id_c` | INTEGER FK → Client | Votant |
| `target` | TEXT NOT NULL | `discussion` ou `comment` |
| `id_target` | INTEGER NOT NULL | ID de la discussion ou du commentaire ciblé |
| `like` | INTEGER NOT NULL | +1 (like) ou -1 (dislike) |

Contrainte UNIQUE sur `(id_c, target, id_target)` → un utilisateur ne peut voter qu'une seule fois par cible. Voter deux fois de suite annule le vote (toggle).

### Table `Groups`
| Colonne | Type | Description |
|---------|------|-------------|
| `id_group` | INTEGER PK AUTOINCREMENT | Identifiant unique |
| `name` | TEXT NOT NULL | Nom du groupe |

### Table `GroupMembers`
| Colonne | Type | Description |
|---------|------|-------------|
| `id_group_member` | INTEGER PK AUTOINCREMENT | Identifiant unique |
| `id_g` | INTEGER FK → Groups | Groupe |
| `id_c` | INTEGER FK → Client | Membre |

### Table `DiscussionGroups`
| Colonne | Type | Description |
|---------|------|-------------|
| `id_g` | INTEGER FK → Groups | Groupe |
| `id_d` | INTEGER FK → Discussions | Discussion |

Une discussion peut appartenir à plusieurs groupes (relation many-to-many).

---

## 5. Routes Flask complètes

### Authentification
| Route | Méthode | Description |
|-------|---------|-------------|
| `/login_page` | GET | Affiche le formulaire de connexion |
| `/login` | POST | Vérifie les credentials, crée la session Flask |
| `/registry_page` | GET | Affiche le formulaire d'inscription |
| `/registry` | POST | Crée le compte et optionnellement ajoute aux groupes |
| `/logout` | GET/POST | Détruit la session |

### Page principale
| Route | Méthode | Description |
|-------|---------|-------------|
| `/` | GET | Page d'accueil — liste des discussions des groupes de l'utilisateur |
| `/alldiscussions` | GET | API JSON — retourne toutes les discussions visibles (pour le rendu JS) |

### Discussions
| Route | Méthode | Description |
|-------|---------|-------------|
| `/main/<id>` | GET | Page d'une discussion avec ses commentaires |
| `/main_comment/<id>/<path>` | GET | Page dédiée à un fil de réponses imbriqué |
| `/ajouter_discussion` | POST | Crée une nouvelle discussion |
| `/modifier_discussion/<id>` | POST | Modifie titre, contenu, groupes et priorité |
| `/clotre_discussion/<id>/<action>` | POST | Ouvre ou clôture une discussion |
| `/cloner_discussion/<id>` | POST | Clone une discussion vers de nouveaux groupes |
| `/delete_discussion/<id>` | POST | Supprime une discussion |

### Commentaires
| Route | Méthode | Description |
|-------|---------|-------------|
| `/commentaire/<discussion_id>/<reply>` | POST | Crée un commentaire (reply=0 pour racine, sinon ID parent) |
| `/show_all_replies/<discussion_id>/<comment_id>` | GET | API JSON — retourne les réponses d'un commentaire |

### Votes
| Route | Méthode | Description |
|-------|---------|-------------|
| `/like_discussion/<id>/<action>` | GET | Like ou unlike une discussion |
| `/like_comment/<discussion_id>/<comment_id>/<action>` | GET | Like ou unlike un commentaire, retourne le nouveau score |

### Groupes
| Route | Méthode | Description |
|-------|---------|-------------|
| `/groups` | GET/POST | Liste des groupes + création d'un nouveau groupe |
| `/group_info/<id>` | GET | Page détaillée d'un groupe avec ses membres |
| `/addgroupe/<id>` | POST | Ajoute des membres à un groupe |
| `/deletemember/<id>` | POST | Retire des membres d'un groupe |
| `/changemember/<id>` | POST | Remplace la liste des membres d'un groupe |
| `/updategroup/<id>` | POST | Renomme un groupe |
| `/deletegroup/<id>` | POST | Supprime un groupe et toutes ses liaisons |
| `/api/group_members/<id>` | GET | API JSON — membres d'un groupe |
| `/api/group_non_members/<id>` | GET | API JSON — utilisateurs hors du groupe |

### Membres & Profils
| Route | Méthode | Description |
|-------|---------|-------------|
| `/membres` | GET | Liste de tous les membres par rôle |
| `/allmembers` | GET | API JSON — tous les membres |
| `/profile/<id>` | GET | Profil d'un utilisateur |
| `/deleteclient/<id>` | POST | Supprime un utilisateur (CEO seulement) |
| `/promoteclient/<id>` | POST | Monte le rôle d'un utilisateur |
| `/demoteclient/<id>` | POST | Baisse le rôle d'un utilisateur |

---

## 6. Système de sessions Flask

Flask utilise des cookies signés côté client pour stocker la session. La `secret_key` de l'application sert à signer cryptographiquement le cookie, garantissant qu'il n'a pas été modifié.

**Données stockées en session :**
```python
session["logged_in"]   # True/False
session["id_client"]   # ID de l'utilisateur connecté
session["email"]       # Email
session["first_name"]  # Prénom
session["last_name"]   # Nom
session["company"]     # Entreprise
session["role"]        # CEO, Manager, ou Employe
```

**Sécurité :** Toutes les routes protégées vérifient `session.get('logged_in')` en premier. Si la session n'existe pas, redirection vers `/login_page`.

---

## 7. Algorithme de score des propositions

### Pourquoi un algorithme composite ?
L'algorithme linéaire initial (`votes_nets + somme_réponses_pondérées`) présentait un problème : une proposition très débattue mais équilibrée (autant pour que contre) avait un score proche de zéro, alors qu'elle est en réalité très intéressante car elle génère de l'engagement.

### Formule finale

```python
Score = votes_nets + sentiment + engagement + controverse + profondeur
```

**Composante 1 — Votes nets** (calculé dans `app.py`, pas dans la fonction)
```
votes_nets = likes_proposition - dislikes_proposition
```

**Composante 2 — Sentiment pondéré** (dans `get_score_proposition`)
```
Pour chaque réponse enfant :
  crédibilité = max(0, likes_réponse - dislikes_réponse) + 1
  if avis == 'pour'   → pour_weight  += crédibilité
  if avis == 'contre' → contre_weight += crédibilité

sentiment = pour_weight - contre_weight
```
Chaque réponse "Pour" ou "Contre" ne compte pas seulement par sa présence, mais par sa popularité propre (les réponses très likées ont plus de poids).

**Composante 3 — Engagement logarithmique**
```
engagement = log(1 + total_votes_réponses + nb_réponses) × 2
```
Croissance logarithmique : passer de 0 à 1 réponse apporte autant que passer de 1 à ~7. Évite qu'une proposition avec 100 réponses anodines écrase tout.

**Composante 4 — Bonus de controverse**
```
controverse = √(min(pour_weight, contre_weight)) × 1.5
```
Si une proposition reçoit à la fois du "Pour" et du "Contre", elle est fortement débattue — donc intéressante. La racine carrée évite que ce bonus devienne dominant.

**Composante 5 — Profondeur**
```
child_contribution = Σ(score_enfant) × 0.6^(profondeur+1)
```
Les réponses aux réponses contribuent aussi, mais leur poids est atténué de 60% par niveau. Cela évite que des threads très profonds mais peu suivis gonflent artificiellement le score.

### Exemple concret
Une proposition avec :
- 5 likes, 2 dislikes → votes_nets = 3
- 3 réponses "Pour" (chacune avec 2 likes) → pour_weight = 9 (3×(2+1))
- 2 réponses "Contre" (chacune avec 1 like) → contre_weight = 4 (2×(1+1))
- Total votes réponses = 6, nb_réponses = 5

```
sentiment     = 9 - 4     = 5
engagement    = log(1+11) × 2 ≈ 4.9
controverse   = √(min(9,4)) × 1.5 = √4 × 1.5 = 3
score_total   = 3 + 5 + 4.9 + 3 = 15.9 → arrondi à 16
```

---

## 8. Gestion des commentaires imbriqués

Les commentaires forment un arbre :
- Colonne `id_reply = 0` → commentaire racine
- Colonne `id_reply = X` → réponse au commentaire X

**Côté serveur :** `select_comment_replies(id_comment)` retourne les enfants directs d'un commentaire.

**Côté client :** Le rendu des sous-réponses est fait en JavaScript via `toggleReplies()` qui appelle `/show_all_replies/<discussion_id>/<comment_id>`. La profondeur est trackée via `data-depth` sur les éléments HTML.

**Limite de profondeur :** Quand `data-depth >= getMaxDepth()`, au lieu d'afficher les sous-réponses en ligne, l'application redirige vers `/main_comment/<discussion_id>/<path>` qui affiche le fil depuis ce commentaire. La limite varie selon la largeur d'écran (2 sur mobile, 5 sur grand écran).

---

## 9. Fonctionnement du système de votes (AJAX)

Le vote ne recharge pas la page — il utilise la Fetch API :

1. Clic utilisateur → appel à `likeComment(event, discussion_id, comment_id, action)`
2. Fetch vers `/like_comment/<discussion_id>/<comment_id>/<action>`
3. Côté Flask : `update_like()` gère 3 cas :
   - Aucun vote existant → INSERT
   - Vote existant différent → UPDATE
   - Vote existant identique → DELETE (toggle off)
4. Retour JSON : `{likes, dislikes, score, proposition_id, proposition_score}`
5. JS met à jour les compteurs ET les classes CSS (`score-pos`, `score-neg`, `score-neutre`)

**Particularité :** Quand on like/dislike une **réponse** à une **proposition**, le score de la proposition parente est aussi recalculé et retourné dans le JSON, car les réponses influencent le score de la proposition.

---

## 10. Système de rôles

```
CEO (3)  →  Manager (2)  →  Employé (1)
```

Les rôles sont comparés numériquement dans les templates :
```python
roles_numeros = {"CEO": 3, "Manager": 2, "Employe": 1}
```

Dans les templates Jinja2 : `{% if role >= 2 %}` pour afficher les boutons disponibles aux Managers et CEO.

**Règles de permission :**
- Seul le CEO peut supprimer ou changer le rôle d'un utilisateur
- Un CEO ne peut pas se supprimer lui-même ni se rétrograder
- Seuls Manager et CEO peuvent créer des discussions
- Tout utilisateur peut voter et commenter dans ses groupes

---

## 11. Migration de base de données

**Problème rencontré :** La colonne `priority` a été ajoutée à la table `Discussions` après la création initiale de la BDD. Les installations existantes n'avaient pas cette colonne.

**Solution :** Fonction `migrate_db()` appelée au démarrage de Flask :
```python
def migrate_db():
    sql.execute("PRAGMA table_info(Discussions)")
    cols = [row[1] for row in sql.fetchall()]
    if 'priority' not in cols:
        sql.execute("ALTER TABLE Discussions ADD COLUMN priority INTEGER NOT NULL DEFAULT 1")
        data.commit()
```
`PRAGMA table_info` retourne les métadonnées des colonnes d'une table SQLite. Si `priority` n'est pas dans la liste, on l'ajoute avec `ALTER TABLE`. L'opération est idempotente (sans effet si la colonne existe déjà).

---

## 12. Sécurité SQL — Requêtes paramétrées

Toutes les requêtes SQL utilisent des paramètres liés (`?`) pour éviter les injections SQL :
```python
# ✅ Correct — valeur passée séparément
sql.execute("SELECT * FROM Client WHERE email = ?", [email])

# ❌ Dangereux — concaténation directe (jamais fait dans le projet)
sql.execute(f"SELECT * FROM Client WHERE email = '{email}'")
```
La bibliothèque `sqlite3` de Python échappe automatiquement les valeurs passées comme paramètres.

---

## 13. Design & Interface

**Palette de couleurs :**
- Fond : `#090D18` (navy très sombre)
- Accent principal : `#6366F1` (indigo)
- Accent secondaire : `#22D3EE` (cyan)
- Texte : `rgba(255,255,255,0.92)`

**CSS Architecture :**
- `base.css` : styles partagés (topbar, boutons, cards, formulaires)
- `<page>.css` : styles spécifiques à chaque page

**Mise à jour dynamique sans rechargement :**
La page d'accueil charge les discussions via Fetch (`/alldiscussions`) et les rend en JavaScript. Cela permet le filtrage côté client sans requête serveur.

---

## 14. Points faibles connus (limites actuelles)

| Limite | Impact | Amélioration possible |
|--------|--------|----------------------|
| Mots de passe stockés en clair | Sécurité critique | Utiliser `bcrypt` ou `werkzeug.security` |
| SQLite non adapté à la production multi-utilisateurs | Performance | Migrer vers PostgreSQL |
| Pas de tests unitaires | Fiabilité | Ajouter `pytest` + `pytest-flask` |
| Sessions côté client (cookie) | Sécurité | Ajouter expiration + refresh |
| Pas de rate limiting | Sécurité | Limiter les requêtes par IP |
| Performances : N+1 queries | Perf | Utiliser des JOIN au lieu de boucles Python |

---

## 15. Questions fréquentes (Q&A)

**Q : Qu'est-ce que Flask ?**
Flask est un micro-framework web Python. Il gère le routage HTTP (quelle fonction appeler pour quelle URL), les sessions, et s'intègre avec Jinja2 pour le templating. Il ne force pas d'ORM ni de structure particulière.

**Q : Qu'est-ce que Jinja2 ?**
Jinja2 est un moteur de templates pour Python. Il permet d'écrire du HTML avec des variables (`{{ variable }}`), des boucles (`{% for %}`), des conditions (`{% if %}`). Flask l'utilise pour générer le HTML côté serveur avant de l'envoyer au navigateur.

**Q : Pourquoi SQLite et pas une vraie BDD ?**
SQLite est une vraie base de données relationnelle complète — elle supporte SQL, les jointures, les clés étrangères. La différence avec PostgreSQL est qu'elle fonctionne en mode "embedded" (stockée dans un fichier) sans serveur séparé. Pour un projet académique ou un prototypage, c'est parfait.

**Q : C'est quoi une injection SQL ?**
Si on construit une requête SQL en concaténant directement l'input utilisateur, quelqu'un peut injecter du SQL malveillant. Par exemple, l'email `' OR 1=1 --` pourrait déverrouiller n'importe quel compte. Les requêtes paramétrées passent les valeurs séparément du SQL → le moteur les échappe automatiquement.

**Q : Comment fonctionne la session Flask ?**
Flask stocke un cookie signé dans le navigateur. Quand l'utilisateur se connecte, on stocke ses infos dans `session["key"] = value`. Flask signe ce cookie avec la `secret_key` pour empêcher la falsification. À chaque requête, Flask lit le cookie et reconstruit le dictionnaire `session`.

**Q : Pourquoi l'algorithme de score est-il logarithmique pour l'engagement ?**
Si on utilisait une croissance linéaire, une proposition avec 100 réponses aurait 100× l'engagement d'une proposition avec 1 réponse. Avec le logarithme, 100 réponses valent seulement ~2× plus que 10 réponses. Cela évite que les "posts viraux" écrasent tout, et favorise la qualité plutôt que la quantité.

**Q : Qu'est-ce qu'une clé étrangère ?**
Une clé étrangère (FOREIGN KEY) est une contrainte qui garantit qu'une valeur dans une colonne correspond bien à une valeur existante dans une autre table. Par exemple, `Comments.id_c` est une FK vers `Client.id_client` : on ne peut pas créer un commentaire avec un `id_c` qui ne correspond à aucun client réel.

**Q : Comment gérez-vous les commentaires imbriqués ?**
Chaque commentaire a une colonne `id_reply`. Si `id_reply = 0`, c'est un commentaire racine. Sinon, c'est une réponse au commentaire dont l'ID est `id_reply`. Pour afficher les sous-réponses, on appelle récursivement la fonction `select_comment_replies()`. Côté client, on limite à 5 niveaux et on redirige ensuite vers une page dédiée pour éviter un DOM trop profond.

**Q : Qu'est-ce que la Fetch API ?**
La Fetch API est une interface JavaScript native permettant de faire des requêtes HTTP depuis le navigateur sans recharger la page (anciennement fait avec XMLHttpRequest). Dans Les Débatteurs, elle sert pour les votes (likes), l'affichage des réponses, et le chargement des listes de membres et discussions.

**Q : Pourquoi le score peut-il être négatif ?**
Oui, c'est voulu. Une proposition avec beaucoup de réponses "Contre" bien likées aura un `sentiment` négatif qui peut dépasser les bonus d'engagement et controverse. Un score négatif signale un rejet actif de la proposition par la communauté.

**Q : Comment avez-vous géré la migration de la base de données ?**
Lors d'un ajout de colonne (`priority`) après la création initiale, les BDD existantes ne l'avaient pas. Plutôt que de forcer un reset, on a créé `migrate_db()` qui utilise `PRAGMA table_info` (une commande SQLite qui liste les colonnes d'une table) pour vérifier si la colonne existe. Si non, elle l'ajoute avec `ALTER TABLE`. Cette fonction est appelée à chaque démarrage Flask.

**Q : L'application est-elle responsive ?**
Partiellement. Des `@media` queries sont définies dans les CSS pour adapter la topbar et les grilles de membres sur écran < 980px. La limite de profondeur des réponses s'adapte aussi à la taille d'écran (2 niveaux sur mobile vs 5 sur desktop).

---

*Fiche rédigée pour accompagner la soutenance — Les Débatteurs, 2025-2026*
