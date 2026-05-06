# prototype d'affichage de mindmap en radial et forum
# avec possibilité d'éditer les nodes (si auteur) ou d'en ajouter en dessous    
# JCY et Marc Schilter (projet Python) - 2025-2026 -v0.1
# 4 mai 2026
# main.py : affichage de la fenêtre principale, gestion de la connexion et des différentes vues (tables + mindmap)

import tkinter as tk
import tkinter.ttk as ttk
from atexit import register
from tkinter import messagebox, simpledialog, colorchooser
from login import show_login
from tree_display import display_array
from model import get_maps, get_nodes_for_map, get_users, get_nodes, create_user, update_node, delete_node, insert_node
from utils.session import Session
import math
import bcrypt

# Variable globale pour le mode DB
db_mode = None
current_map_id = None

# Vérification de connexion
def check_auth():
    return Session.is_authenticated()

# affichage des maps 
def display_maps():
    result = get_maps(db_mode)
    frm_result.tree = display_array(frm_result, result)
    frm_result.tree.bind("<Double-1>", on_map_double_click) # double clic pour afficher le mindmap dans right_frame selon le mode sélectionné (tree, radial ou forum)
#afficher les users
def display_users():
    result = get_users(db_mode)
    frm_result.tree = display_array(frm_result, result)


#afficher les nodes
def display_nodes():
    result = get_nodes(db_mode)
    # remplacer les none par 0
    for record in result:
        if record["parent_id"] is None:
            record["parent_id"] = 0
    frm_result.tree = display_array(frm_result, result)

       
# traitement de l'affichage d'un mindmap selon le mode sélectionné (tree, radial ou forum)
def on_map_double_click(event):
    selected = frm_result.tree.selection()
    if selected:
        item = frm_result.tree.item(selected[0])
        values = item['values']
        map_id = values[0]  # Supposons que id est la première colonne
        display_mindmap(map_id)

# affichage du mindmap selon le mode sélectionné
def display_mindmap(map_id):
    global current_map_id
    current_map_id = map_id
    nodes = get_nodes_for_map(map_id,db_mode)
    # Nettoyer right_frame
    for widget in right_frame.winfo_children():
        widget.destroy()
    # Afficher les nodes selon le mode
    if nodes:
        mode = display_mode.get()
        if mode == 'tree':
            display_mindmap_tree(right_frame, nodes)
        elif mode == 'forum':
            display_mindmap_forum(right_frame, nodes)
        elif mode == 'radial':
            display_mindmap_radial(right_frame, nodes)
    else:
        tk.Label(right_frame, text="Aucun node pour ce mindmap").pack()

def refresh_mindmap():
    if current_map_id is not None:
        display_mindmap(current_map_id)

# Affichage du mindmap en TreeView (version simple)
def display_mindmap_tree(frame, nodes):

    # Créer le Treeview
    tree = ttk.Treeview(frame, columns=(), show='tree')  # Pas de colonnes supplémentaires
    tree.heading('#0', text='Text')

    # Police plus petite et interligne ajusté pour beaucoup d'enregistrements
    style = ttk.Style()
    style.configure("Right.Treeview", font=("TkDefaultFont", 20), rowheight=35)
    tree.configure(style="Right.Treeview")

    # Donne le focus au canvas pour permettre le scroll avec la molette, lorsque la souris le survole.
    tree.bind("<Enter>", lambda e: tree.focus_set())

    # Scroll vertical
    tree.bind("<MouseWheel>", lambda e: tree.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Scroll horizontal avec SHIFT
    tree.bind("<Shift-MouseWheel>", lambda e: tree.xview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Fonction récursive pour insérer les nodes
    def insert_nodes(parent, parent_id=None):
        for node in nodes:
            if node['parent_id'] == parent_id:
                item = tree.insert(parent, 'end', text=node['text'])  # Seulement le text
                insert_nodes(item, node['id'])

    insert_nodes('')

    # Scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.pack(side='left', fill='both', expand=True)
    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')

# Affichage du mindmap en forum (version plus compacte et adaptée à l'affichage de nombreux nodes, avec possibilité d'éditer les nodes ou d'en ajouter en dessous)
def display_mindmap_forum(frame, nodes):
    container = tk.Frame(frame)
    container.pack(fill='both', expand=True)

    canvas = tk.Canvas(container, bg='white')
    vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    hsb = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

    canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)
    # Donne le focus au canvas pour permettre le scroll avec la molette, lorsque la souris le survole.
    canvas.bind("<Enter>", lambda e: canvas.focus_set())

    # Scroll vertical
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Scroll horizontal avec SHIFT
    canvas.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Mise à jour de la zone scrollable
    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", update_scroll_region)

    # Trouver le root
    root_node = next((n for n in nodes if n['parent_id'] is None or n['parent_id'] == 0), None)
    if not root_node:
        return

    canvas_width = 800
    canvas_height = 600
    node_height = 25  # Réduit à 30 pour moins de place verticale

    # Crée un rectangle arrondi (pour les nodes du forum)
    def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=10, **kwargs):

        # sécurité : éviter un rayon trop grand
        radius = min(radius, abs(x2 - x1)//2, abs(y2 - y1)//2)

        points = [ x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius, x1, y1,
            x1 + radius, y1 ]

        return canvas.create_polygon(points, smooth=True, **kwargs)
    # Place les nodes en mode forum de manière récursive
    def place_forum(node, x, y, width_percent, level=0):
        width = int(canvas_width * width_percent / 100)
        item = create_rounded_rectangle(canvas, x, y, x + width, y + node_height, radius=8, fill='lightblue' if level == 0 else node["color"], outline='black')
        canvas.create_text(x + width/2, y + node_height/2, text=node['text'][:40], anchor='center', font=("Arial", 12))  # Police augmentée
        # Binder le clic droit sur le node pour éditer
        canvas.tag_bind(item, "<Button-3>", lambda e, n=node: edit_node(e, n)) # n contient les infos du node pour l'édition    
        children = [n for n in nodes if n['parent_id'] == node['id']]
        total_height = node_height + 10  # hauteur du node + marge
        if children:
            child_x = x + int(canvas_width * 20 / 100)  # décalage de 20%
            child_width_percent = max(width_percent - 5, 10)  # diminuer de 5% par niveau, min 10%
            current_y = y + node_height + 10
            for child in children:
                child_height = place_forum(child, child_x, current_y, child_width_percent, level+1)
                current_y += child_height
                total_height += child_height
        return total_height

    place_forum(root_node, 20, 20, 50) # le root prend 50% de la largeur, les enfants 45%, etc. 
    update_scroll_region()

# Affichage du mindmap en radial avec canvas
def display_mindmap_radial(frame, nodes):
    container = tk.Frame(frame)
    container.pack(fill='both', expand=True)

    canvas = tk.Canvas(container, bg='white')
    vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    hsb = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

    canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    # Donne le focus au canvas pour permettre le scroll avec la molette, lorsque la souris le survole.
    canvas.bind("<Enter>", lambda e: canvas.focus_set())

    # Scroll vertical
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    # Scroll horizontal avec SHIFT
    canvas.bind("<Shift-MouseWheel>", lambda e: canvas.xview_scroll(int(-1 * (e.delta / 120)), "units"))


    def zoom(event):
        scale_factor = 1.0  # niveau de zoom actuel

        # facteur de zoom
        if event.delta > 0:
            factor = 1.1  # zoom in
        else:
            factor = 0.9  # zoom out

        scale_factor *= factor

        # position de la souris dans le canvas
        x = canvas.canvasx(event.x)
        y = canvas.canvasy(event.y)

        # applique le zoom à tous les éléments
        canvas.scale("all", x, y, factor, factor)

        # ajuste la zone scrollable
        canvas.configure(scrollregion=canvas.bbox("all"))

    # binder le zoom à la molette de la souris + ctrl
    canvas.bind("<Control-MouseWheel>", zoom)


    # Mise à jour de la zone scrollable
    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", update_scroll_region)

    width = 1200
    height = 900

    # Centre du mindmap
    center_x = width // 2
    center_y = height // 2

    # Taille des ovales
    oval_width = 120
    oval_height = 60

    # Distance entre les niveaux
    level_spacing = 180

    # Détermine la racine du radial
    root = next((n for n in nodes if n['parent_id'] in (None, 0)), None)
    if not root:
        return

    # Crée un dictionnaire des enfants
    children_map = {}
    for node in nodes:
        children_map.setdefault(node['parent_id'], []).append(node)

    # fonction de dessin d'un node
    def draw_node(x, y, node, color="lightblue"):
        #centre l’ovale autour du point (x, y)
        oval = canvas.create_oval(x - oval_width // 2,y - oval_height // 2,x + oval_width // 2,y + oval_height // 2,fill=color,outline="black")
        # Ajoute le texte au centre de l'ovale
        canvas.create_text(x,y,text=node['text'][:20],width=oval_width - 10)
        # Associe un clic droit à cet ovale pour éditer le node
        canvas.tag_bind(oval, "<Button-3>", lambda e, n=node: edit_node(e, n))

    # Fonction simple pour aller jusqu'au bord de l'ovale
    def get_edge_point(cx, cy, angle):
        return (cx + (oval_width // 2) * math.cos(angle), cy + (oval_height // 2) * math.sin(angle))

    # Fonction récursive pour le dessin des enfants
    def draw_children(parent_node, x, y, level=1, angle_start=0, angle_end=360):

        # Récupère la liste des enfants du node courant
        children = children_map.get(parent_node['id'], [])

        # Si le node n'a pas d'enfants, on arrête ici
        if not children:
            return

        # Distance (linéaire + ajustée selon nb enfants)
        radius = level_spacing + (level - 1) * 80 + len(children) * 8

        # Angle (avec petite marge fixe pour éviter l'étalement total)
        margin = 30
        # Angle réellement utilisé pour placer les enfants
        angle_total = (angle_end - angle_start) - margin
        # espace angulaire entre chaque enfant pour la répartition
        angle_step = angle_total / len(children)
        # impose un minimum de 18° pour éviter que les nodes soient trop serrés
        angle_step = max(angle_step, 18)
        # décale le point de départ pour centrer les enfants dans la zone disponible
        start_angle = angle_start + margin / 2

        for i, child in enumerate(children):
            # Calcule l'angle du child en degrés (répartition autour du parent)
            angle_deg = start_angle + i * angle_step

            # Convertit l'angle en radians (obligatoire pour cos/sin)
            angle_rad = math.radians(angle_deg)

            # Position du child (coordonnées polaires → cartésiennes)
            child_x = x + radius * math.cos(angle_rad)  # position horizontale
            child_y = y + radius * math.sin(angle_rad)  # position verticale

            # Calcule le point de départ sur le bord de l’ovale parent
            start_x, start_y = get_edge_point(x, y, angle_rad)

            # Calcule le point d’arrivée sur le bord de l’ovale enfant
            # (angle + π = direction opposée)
            end_x, end_y = get_edge_point(child_x, child_y, angle_rad + math.pi)

            # Dessine une ligne entre les deux ovales (bord à bord)
            canvas.create_line(start_x, start_y, end_x, end_y)

            # Dessiner le node enfant
            draw_node(child_x, child_y, child, child.get("color", "lightgreen"))

            # Récursion (angle FIXE autour du parent → évite explosion)
            spread = max(90, min(160, len(children) * 20))
            draw_children(child,child_x,child_y,level + 1,angle_deg - spread/2,angle_deg + spread/2)

    # Dessin final
    draw_node(center_x, center_y, root,root.get("color", "lightblue"))
    draw_children(root, center_x, center_y)

#Cette fonction propose 3 actions sur un node : éditer le texte, supprimer le node ou insérer un nouveau node en dessous
def edit_node(event, node):
    #if not check_auth():
    #    messagebox.showerror("Erreur", "Vous devez être connecté en tant qu'utilisateur pour effectuer cette action.")
    #    return
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Éditer", command=lambda: edit_text(node))
    menu.add_command(label="Supprimer", command=lambda: delete_node_action(node))
    menu.add_command(label="Insérer en dessous", command=lambda: insert_below(node))
    menu.post(event.x_root, event.y_root)

# propose d'éditer le texte d'un node (seulement si l'utilisateur est l'auteur du node)
def edit_text(node):
    # Compare l'author id du node au id de l'utilisateur connecté
    if node["author_id"] != Session.id:
        messagebox.showerror("Erreur", "Vous n'êtes pas l'auteur de ce node.")
        return
    # Si les deux id correspondent, propose une fenêtre de saisie pour éditer le texte du node
    new_text = simpledialog.askstring("Éditer le node", "Nouveau texte :", initialvalue=node["text"])
    # vérifie que le texte a bien changé avant de faire la requête de mise à jour.
    if new_text and new_text != node["text"]:
        try:
            update_node(node["id"], new_text, db_mode=db_mode)
            refresh_mindmap()  # rafraîchir l'affichage du mindmap pour voir le changement
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de mettre à jour le node : {str(e)}")

# propose de supprimer un node (seulement si l'utilisateur est l'auteur du node)
def delete_node_action(node):
    # Compare l'author id du node au id de l'utilisateur connecté
    if node["author_id"] != Session.id:
        messagebox.showerror("Erreur", "Vous n'êtes pas l'auteur de ce node.")
        return
    # Si les deux id correspondent, propose une confirmation avant de supprimer le node
    if messagebox.askyesno("Confirmer la suppression", "Êtes-vous sûr de vouloir supprimer ce node ?"):
        try:
            delete_node(node["id"], db_mode)
            refresh_mindmap()  # rafraîchir l'affichage du mindmap pour voir le changement
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de supprimer le node : {str(e)}")

# propose d'insérer un nouveau node en dessous du node sélectionné (le nouveau node aura comme parent le node sélectionné)
def insert_below(node):
    if not check_auth():
        messagebox.showerror("Erreur", "Vous devez être connecté en tant qu'utilisateur pour effectuer cette action.")
        return
    new_text = simpledialog.askstring("Insérer un node", "Texte du nouveau node :")
    # vérifie que le texte n'est pas vide avant de faire la requête d'insertion.
    if new_text and new_text.strip() != "":
        try:
            insert_node(current_map_id, node["id"], Session.id, new_text, node["level"] + 1, db_mode)
            refresh_mindmap()  # rafraîchir l'affichage du mindmap pour voir le nouveau node
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'insérer le node : {str(e)}")
    else:
        messagebox.showerror("Erreur", "Le texte du node ne peut pas être vide.")


# Permet de changer le mode de la base de données (local ou remote) et met à jour la variable globale db_mode
def set_db_mode(mode):
    global db_mode
    if (mode != db_mode): # éviter de faire un logout inutile qui ferait perdre la connexion à l'utilisateur
        db_mode = mode
        #Session.logout()  # forcer le logout pour éviter les incohérences
        lbl_user.config(text="Non connecté")
        lbl_db_mode.config(text=f"Mode DB: {db_mode}", bg="red" if db_mode == "remote" else "green", fg="white")
        display_maps()  # rafraîchir l'affichage des maps pour éviter les incohérences

# connexion (appelle une fenêtre de login)
def login():
    show_login(root)
    if Session.is_authenticated():
        lbl_user.config(text=f"Connecté en tant que {Session.pseudo}")
# deconnexion
def logout():
    #déconnecte la session authentifiée
    Session.logout()
    lbl_user.config(text="Non connecté")

# inscription
def register_user():

    win = tk.Toplevel(root)
    win.title("Inscription")
    win.geometry("500x300")

    win.transient(root)  # lie la fenêtre à la fenêtre principale
    win.grab_set()  # bloque les interactions avec le reste de l'app
    win.focus_set()  # donne le focus à la fenêtre

    tk.Label(win, text="Pseudo").pack(pady=5)
    entry_pseudo = tk.Entry(win)
    entry_pseudo.pack()

    tk.Label(win, text="Mot de passe").pack(pady=5)
    entry_password = tk.Entry(win, show="*")
    entry_password.pack()

    tk.Label(win, text="Confirmation").pack(pady=5)
    entry_confirm = tk.Entry(win, show="*")
    entry_confirm.pack()

    # Affiche un label indiquant à l'utilisateur qu'il doit choisir une couleur
    tk.Label(win, text="Choisir une couleur").pack(pady=5)

    # Variable Tkinter qui stocke la couleur sélectionnée (format hex)
    selected_color = tk.StringVar(value="#4F46E5")

    # Label qui sert d’aperçu visuel de la couleur choisie. Le fond (bg) est initialisé avec la couleur par défaut
    preview = tk.Label(win, text="Aperçu", bg=selected_color.get(), width=20)
    preview.pack(pady=5)

    # Fonction appelée quand l'utilisateur clique sur le bouton
    def choose_color():
        # Ouvre la fenêtre native de sélection de couleur, askcolor() retourne (RGB, HEX), on prend la valeur HEX [1]
        color = colorchooser.askcolor()[1]

        if color:
            # Met à jour la variable avec la nouvelle couleur
            selected_color.set(color)
            # Met à jour l’aperçu visuel
            preview.config(bg=color)

    # Bouton qui permet d’ouvrir le color picker
    tk.Button(win, text="Choisir une couleur", command=choose_color).pack(pady=5)


    def submit():
        pseudo = entry_pseudo.get()
        password = entry_password.get()
        confirm = entry_confirm.get()
        color = selected_color.get()

        # Vérifie que les champs ne sont pas vides
        if not pseudo or not password:
            messagebox.showerror("Erreur", "Champs vides")
            return
        # Vérifie que le mot de passe et la confirmation sont identiques
        if password != confirm:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            return
        # Hashe le mot de passe avec bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        try:
            create_user(pseudo, hashed.decode('utf-8'), db_mode, color)

            messagebox.showinfo("Succès", "Utilisateur créé")
            win.destroy()

        except Exception as e:
            # Message d'erreur si le pseudo est déjà pris
            if "Duplicate entry" in str(e) or "UNIQUE" in str(e):
                messagebox.showerror("Erreur", "Ce pseudo existe déjà")
            else:
                messagebox.showerror("Erreur", str(e))

    # Frame pour aligner les boutons horizontalement en bas de la fenêtre d'inscription.
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Créer", command=submit).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Annuler", command=win.destroy).pack(side="left", padx=5)




# Fenêtre principale
root = tk.Tk()
# Ajusté pour accommoder les deux frames
root.minsize(1200, 800)
root.title("Mindmaps - Version de base v0.1")

# Création du menu
menubar = tk.Menu(root)

# Menu Afficher
display_menu = tk.Menu(menubar, tearoff=0)
display_menu.add_command(label="Maps", command=display_maps)
display_menu.add_command(label="Users", command=display_users)
display_menu.add_command(label="Nodes", command=display_nodes)
menubar.add_cascade(label="Afficher", menu=display_menu)
# Menu Login/Register
login_menu = tk.Menu(menubar, tearoff=0)
login_menu.add_command(label="Login", command=login)
login_menu.add_command(label="Logout", command=logout)
login_menu.add_command(label="Register", command=register_user)
menubar.add_cascade(label="Login/Register", menu=login_menu)

# Menu local/remote
db_menu = tk.Menu(menubar, tearoff=0)
db_menu.add_command(label="Local", command=lambda: set_db_mode('local'))
db_menu.add_command(label="Remote", command=lambda: set_db_mode('remote'))
menubar.add_cascade(label="Mode DB", menu=db_menu)

root.config(menu=menubar)

# Configuration du grid pour root
root.columnconfigure(0, minsize=500)  # Frame gauche de largeur fixe 500
root.columnconfigure(1, weight=1)     # Frame droite prend le reste
root.rowconfigure(0, weight=1)

# Frame gauche pour contrôles et affichage des tables
left_frame = tk.Frame(root, bg="lightgray", width=500)
left_frame.grid(column=0, row=0, sticky="ns")  # "ns" pour étirement vertical seulement

# Frame droite pour l'affichage du mindmap
right_frame = tk.Frame(root, bg="white")
right_frame.grid(column=1, row=0, sticky="nsew")

# Variable pour le mode d'affichage
display_mode = tk.StringVar(value='tree')

# Configuration du grid pour left_frame
left_frame.rowconfigure(3, weight=1)  # frm_result prend l'espace restant
left_frame.columnconfigure(0, weight=1)
left_frame.columnconfigure(1, weight=1)

# Information sur la connexion dans left_frame
lbl_user = tk.Label(left_frame, text="Non connecté")
lbl_user.grid(column=0, row=0, padx=10, pady=10)
# Information sur la base de données utilisée 
lbl_db_mode = tk.Label(left_frame, text="db_mode: local")
lbl_db_mode.grid(column=1, row=0, padx=10, pady=10)

# frame pour les boutons dans left_frame
frm_buttons = tk.Frame(left_frame, bg="lightblue")
frm_buttons.grid(column=0, row=1, pady=10)

# frame pour les options d'affichage
frm_options = tk.Frame(left_frame, bg="lightyellow")
frm_options.grid(column=0, row=2, pady=10)

tk.Label(frm_options, text="Mode d'affichage Mindmap:").pack(anchor='w')
tk.Radiobutton(frm_options, text="Treeview", variable=display_mode, value='tree', command=refresh_mindmap).pack(anchor='w')
tk.Radiobutton(frm_options, text="Forum", variable=display_mode, value='forum', command=refresh_mindmap).pack(anchor='w')
tk.Radiobutton(frm_options, text="Radial",variable=display_mode, value='radial', command=refresh_mindmap).pack(anchor='w')

# frame pour l'affichage des résultats dans left_frame
frm_result = tk.Frame(left_frame, bg="lightgreen")
frm_result.grid(column=0, row=3, columnspan=2, sticky="nsew", padx=10, pady=10)

# Placeholder pour le mindmap dans right_frame
tk.Label(right_frame, text="Zone Mindmap", font=("Arial", 16)).pack(expand=True)

# remplissage de frm_result
tk.Label(frm_result,text="RESULTS").pack()

# Affiche les maps au démarrage
set_db_mode("local")
display_maps()
root.mainloop()