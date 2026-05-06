# les-debatteurs
Membre du groupe : Numéro d'étudiant

- François ALICANTE : 21414341
- Justin KANG : 21431641
- Soufiane BEL HADJ : 21303076
- Tamer AL MASRI : 21412678

# Description du projet
L'objectif principal de ce projet est de fournir une plateforme de délibération pour les entreprises.

Elle a été conçue dans le but d'aider les chefs d'entreprises et les managers à formuler, discuter, choisir des solutions à leurs problèmes avec leurs employés.

# Conditions & premières étapes

Les librairies utilisées dans ce projet sont les suivants :

```diff
- sqlite3
* flask
- datetime
- time
```

Les librairies marquées en rouge sont des librairies standards python, il n'est donc pas nécessaire d'exécuter la commande `pip install [nom de la librairie]` si vous avez déjà installé python sur votre machine.

Afin de lancer un serveur local, il faut donc installer le module flask via la commande ci-dessous : 

```
pip install Flask
```

Après avoir installé ce module, il suffit d'exécuter la commande suivante dans un terminal :

```
python -m flask db:reset
python -m flask --debug run
```

Il faut noter que la première ligne de commande n'est qu'optionnelle et a pour but de supprimer le contenu crée lors de sessions de test précédentes.

## Tester les fonctionnalités du projet

Afin de vous pourvoir la pleine expérience avec la plateforme, nous avons mis à disposition un "compte test" vous permettant de tester l'ensemble des fonctionnalités du site :

<div style="
    height: 80px;
    margin-bottom: 20px;
    ">
    <div style="
        width: 350px;
        height: 50%;
        margin: auto auto;
        display: flex;
    ">
        <div style="
            width: 100%;
            text-align: center;
            vertical-align: middle;
            line-height: 40px;
            border: 1px solid white;
            background: grey;
        ">
            E-mail
        </div>
        <div style="
            width: 100%;
            text-align: center;
            vertical-align: middle;
            line-height: 40px;
            border: 1px solid white;
            background: grey;
        ">
            Mot de passe
        </div>
    </div>
    <div style="
        width: 350px;
        height: 50%;
        margin: auto auto;
        display: flex;
    ">
        <div style="
            width: 100%;
            text-align: center;
            vertical-align: middle;
            line-height: 40px;
            border: 1px solid white;
            background: grey;
        ">
            test@test
        </div>
        <div style="
            width: 100%;
            text-align: center;
            vertical-align: middle;
            line-height: 40px;
            border: 1px solid white;
            background: grey;
        ">
            test
        </div>
    </div>
</div>

Ce compte possède tous les droits et vous permet de :

* Créer, clôner, éditer, clôturer des discussions
* Créer, gérer des groupes
* Ajouter, supprimer des membres à votre entreprise
* Promouvoir, rétrograder des membres
* Pourvoir du feedback : commenter, voter, proposer des solutions


