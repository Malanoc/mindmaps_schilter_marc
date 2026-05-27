# README – Application Mindmaps Python

## Présentation

Cette application permet de créer, modifier et visualiser des mindmaps collaboratifs en Python avec une interface graphique Tkinter.

Le projet a été réalisé dans le cadre du cours de Python 2025-2026.

L’application propose plusieurs modes d’affichage des mindmaps :
- TreeView
- Forum
- Radial

Elle permet également :
- La gestion des utilisateurs
- La connexion/déconnexion
- Les permissions selon le niveau utilisateur
- L’export PDF
- L’impression
- La gestion de bases de données locales et distantes

---

# Fonctionnalités principales

## Gestion des utilisateurs

- Inscription d’un utilisateur
- Connexion / Déconnexion
- Mot de passe hashé avec bcrypt
- Sélection d’une couleur utilisateur
- Gestion des permissions selon le niveau utilisateur

### Permissions

#### Niveau 1
- Peut modifier uniquement ses propres nodes/mindmaps

#### Niveau 2
- Administrateur
- Peut modifier/supprimer tous les éléments

---

# Gestion des mindmaps

## Création de mindmaps

- Création d’un nouveau mindmap
- Création automatique du node racine
- Association du mindmap à son auteur

## Modification

- Modification du titre
- Mise à jour automatique du node racine

## Suppression

- Suppression sécurisée avec confirmation
- Vérification des permissions utilisateur

---

# Gestion des nodes

## Actions disponibles

- Ajouter un node enfant
- Modifier un node
- Supprimer un node

## Menu contextuel

Clic droit sur un node :
- Éditer
- Supprimer
- Ajouter un node en dessous

---

# Modes d’affichage

## 1. TreeView

Affichage hiérarchique classique avec `ttk.Treeview`.

---

## 2. Forum

Affichage compact en style forum :
- Rectangles arrondis
- Indentation des réponses
- Adapté aux grands mindmaps

---

## 3. Radial

Affichage graphique radial :
- Organisation circulaire
- Zoom avec CTRL + molette
- Scroll horizontal et vertical

---

# Navigation

- Scroll vertical avec la molette
- Scroll horizontal avec SHIFT + molette
- Zoom dans le mode radial avec CTRL + molette

---

# Base de données

## Modes disponibles

- Local
- Remote

L’utilisateur peut changer dynamiquement le mode de connexion à la base de données.

---

# Technologies utilisées

## Interface graphique

- Tkinter
- canvas
- ttk.Treeview

## Base de données

- MySQL

## Sécurité

- bcrypt

## Export PDF

- reportlab

## Variables d’environnement

- python-dotenv

---

# Librairies externes à installer

Installer les dépendances avec :

```bash
pip install bcrypt
pip install mysql-connector-python
pip install python-dotenv
pip install reportlab
```

# Structure du projet

```text
main.py
model.py
config.py
login.py
tree_display.py
utils/
    session.py
.env
```
# Fonctionnement général

## main.py

Contient :
- l’interface principale
- l’affichage des mindmaps
- les menus
- la gestion utilisateur
- l’export PDF

---

## model.py

Contient :
- les requêtes SQL
- les insert/update/delete
- les accès à la base de données

---

## config.py

Charge les variables d’environnement :
- base locale
- base distante

---

## session.py

Gère :
- l’utilisateur connecté
- le niveau utilisateur
- les permissions

---

# Fonctionnalités techniques intéressantes

## Export PDF et impression

Le PDF est généré directement depuis les éléments du canvas :
- Lignes
- Ovales
- Polygones
- Textes

L’utilisateur peut également :
- Imprimer directement le mindmap depuis l’application.

---

## Gestion des permissions

Fonction centralisée :

```python
def can_edit(author_id):
```
Ce que fait cette fonction :
- autorise les admins,
- vérifie les auteurs.

## Affichage radial récursif

Le mode radial utilise :

- des calculs trigonométriques
- une fonction récursive pour positionner les nodes

# Auteurs

Projet réalisé par :
- JCY (structure de base)
- Marc Schilter (réalisation du projet pour le module Projet Python)

CPNV 2025-2026