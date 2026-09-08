import os
import sqlite3
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# DÉPLACEMENT DE LA BASE DANS UN DOSSIER AUTORISÉ PAR WINDOWS
if getattr(sys, "frozen", False):
  # Si c'est le .exe installé, on place la base dans le dossier AppData (toujours accessible en écriture)
  dossier_app = os.path.join(os.environ["APPDATA"], "BM_PROD")
  if not os.path.exists(dossier_app):
    os.makedirs(dossier_app)
  BASE_DB = os.path.join(dossier_app, "bm_prod.db")

  # Si le fichier n'existe pas encore dans AppData, on copie celui d'origine s'il y en a un
  if not os.path.exists(BASE_DB):
    import shutil

    chemin_origine = os.path.join(os.path.dirname(sys.executable), "bm_prod.db")
    if os.path.exists(chemin_origine):
      shutil.copy(chemin_origine, BASE_DB)
else:
  # En mode développement sur le PC
  DOSSIER_COURANT = os.path.dirname(os.path.abspath(__file__))
  BASE_DB = os.path.join(DOSSIER_COURANT, "bm_prod.db")


# 1. INITIALISATION DE LA BASE DE DONNÉES
def initialiser_base():
  conn = sqlite3.connect(BASE_DB)
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL
        )
    """)
  cursor.execute(
      "INSERT OR IGNORE INTO utilisateurs (role, code) VALUES ('admin',"
      " '1234')"
  )
  cursor.execute(
      "INSERT OR IGNORE INTO utilisateurs (role, code) VALUES ('reception',"
      " '0000')"
  )

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS artistes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_artiste TEXT NOT NULL,
            date_enregistrement TEXT,
            titre_chanson TEXT,
            heure TEXT,
            telephone TEXT,
            ville TEXT,
            type_prod TEXT,
            style_musical TEXT,
            tarifs REAL DEFAULT 0,
            somme_versee REAL DEFAULT 0,
            somme_restante REAL DEFAULT 0,
            statut TEXT,
            num_facture INTEGER
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS avances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_artiste TEXT NOT NULL,
            numero TEXT,
            date_versement TEXT,
            somme_versee REAL DEFAULT 0,
            moyen_versement TEXT,
            date_prevue TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS rdv (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jour TEXT,
            nom_client TEXT NOT NULL,
            telephone TEXT,
            date_rdv TEXT,
            heure_rdv TEXT,
            statut_sms TEXT DEFAULT 'Non envoyé'
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS rdv_perso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_rdv TEXT,
            heure TEXT,
            objet TEXT,
            statut TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS conso_electricite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_conso TEXT,
            index_kwh TEXT,
            montant REAL DEFAULT 0,
            notes TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_depense TEXT,
            categorie TEXT,
            description TEXT,
            montant REAL DEFAULT 0
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes_perso (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_note TEXT,
            type_note TEXT,
            note_marquante TEXT,
            detail TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS nos_depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            achat TEXT NOT NULL,
            nombre INTEGER DEFAULT 1,
            prix_unitaire REAL DEFAULT 0,
            total REAL DEFAULT 0
        )
    """)

  conn.commit()
  conn.close()


# 2. APPLICATION PRINCIPALE
class ApplicationBMProd:

  def __init__(self, root):
    self.root = root
    self.root.title("BIG S MEDIA PRODUCTION - LOGICIEL DE GESTION")
    self.root.geometry("1180x720")
    self.root.configure(bg="#12181f")

    self.c_bg = "#12181f"
    self.c_card = "#1e2732"
    self.c_accent = "#f1c40f"
    self.c_btn = "#2980b9"
    self.c_btn_hover = "#3498db"
    self.c_text = "#ffffff"

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Treeview",
        background="#ffffff",
        foreground="#000000",
        fieldbackground="#ffffff",
        rowheight=25,
    )
    style.configure(
        "Treeview.Heading",
        background="#2c3e50",
        foreground="#ffffff",
        font=("Helvetica", 9, "bold"),
    )

    self.grille_tarifs = {
        "SOYAYA": "15 000,00 XOF",
        "SIYASA": "25 000,00 XOF",
        "KASIDA": "10 000,00 XOF",
        "SEMI LIVE": "45 000,00 XOF",
        "LIVE": "60 000,00 XOF",
        "PROGRAMATION": "35 000,00 XOF",
        "FACE A": "60 000,00 XOF",
        "PRISE DE VOIX": "25 000,00 XOF",
        "REGAE": "35 000,00 XOF",
        "AURE/HIGYAI": "25 000,00 XOF",
        "SARAUTA": "25 000,00 XOF",
        "ANIVERSAIRE": "25 000,00 XOF",
        "PRISE DE VOIX VIP": "40 000,00 XOF",
        "VOIX OFF": "15 000,00 XOF",
        "INSTALATION STUDIO SIMPLE": "18 000,00 XOF",
        "INSTALATION STUDIO SIMPLE COMPLETE": "25 000,00 XOF",
        "CONVERSION CASSETTE VIDEO BANDE": "10 000,00 XOF",
        "CONVERSION CASSETTE RADIO BANDE": "5 000,00 XOF",
        "MIXDOWN": "10 000,00 XOF",
        "KIDA SOYAYA": "7 500,00 XOF",
        "KIDA KASIDA": "5 000,00 XOF",
        "KIDA JINJINA": "8 500,00 XOF",
        "JINJINA": "25 000,00 XOF",
    }

    self.creer_menu_principal()

  def verifier_acces(self, niveau_requis):
    if niveau_requis == "libre":
      return True

    code_saisi = simpledialog.askstring(
        "Accès Protégé",
        f"Entrez le code d'accès ({niveau_requis.upper()}) :",
        show="*",
    )
    if not code_saisi:
      return False

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()

    if niveau_requis == "admin":
      cursor.execute(
          "SELECT code FROM utilisateurs WHERE role='admin' AND code=?",
          (code_saisi,),
      )
    elif niveau_requis == "reception":
      cursor.execute(
          "SELECT code FROM utilisateurs WHERE role IN ('admin', 'reception')"
          " AND code=?",
          (code_saisi,),
      )

    valide = cursor.fetchone() is not None
    conn.close()

    if not valide:
      messagebox.showerror(
          "Accès Refusé",
          f"Code d'accès incorrect ! Niveau requis : {niveau_requis.upper()}",
      )
      return False

    return True

  def modifier_mots_de_passe(self):
    if not self.verifier_acces("admin"):
      return

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT role, code FROM utilisateurs")
    codes_actuels = dict(cursor.fetchall())
    conn.close()

    fen_pass = tk.Toplevel(self.root)
    fen_pass.title("Gestion des Codes d'Accès")
    fen_pass.geometry("420x360")
    fen_pass.configure(bg=self.c_card)
    fen_pass.grab_set()

    tk.Label(
        fen_pass,
        text="MODIFIER LES CODES D'ACCÈS",
        font=("Helvetica", 11, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    ).pack(pady=15)

    frame_champs = tk.Frame(fen_pass, bg=self.c_card)
    frame_champs.pack(pady=5)

    tk.Label(
        frame_champs,
        text="Code ADMIN :",
        fg=self.c_text,
        bg=self.c_card,
        font=("Helvetica", 10),
    ).grid(row=0, column=0, padx=10, pady=8, sticky="e")
    e_admin = tk.Entry(frame_champs, font=("Helvetica", 10), show="*")
    e_admin.insert(0, codes_actuels.get("admin", "1234"))
    e_admin.grid(row=0, column=1, padx=10, pady=8)

    tk.Label(
        frame_champs,
        text="Code RÉCEPTION :",
        fg=self.c_text,
        bg=self.c_card,
        font=("Helvetica", 10),
    ).grid(row=1, column=0, padx=10, pady=8, sticky="e")
    e_recep = tk.Entry(frame_champs, font=("Helvetica", 10), show="*")
    e_recep.insert(0, codes_actuels.get("reception", "0000"))
    e_recep.grid(row=1, column=1, padx=10, pady=8)

    var_afficher = tk.BooleanVar(value=False)

    def basculer_visibilite():
      caractere = "" if var_afficher.get() else "*"
      e_admin.config(show=caractere)
      e_recep.config(show=caractere)

    chk_afficher = tk.Checkbutton(
        fen_pass,
        text=" Afficher les mots de passe",
        variable=var_afficher,
        command=basculer_visibilite,
        bg=self.c_card,
        fg=self.c_accent,
        selectcolor=self.c_bg,
        activebackground=self.c_card,
        font=("Helvetica", 9, "bold"),
    )
    chk_afficher.pack(pady=8)

    def enregistrer_codes():
      code_a = e_admin.get().strip()
      code_r = e_recep.get().strip()

      if not code_a or not code_r:
        messagebox.showwarning(
            "Attention", "Les deux champs doivent être remplis !"
        )
        return

      conn = sqlite3.connect(BASE_DB)
      cursor = conn.cursor()
      cursor.execute(
          "UPDATE utilisateurs SET code = ? WHERE role = 'admin'", (code_a,)
      )
      cursor.execute(
          "UPDATE utilisateurs SET code = ? WHERE role = 'reception'",
          (code_r,),
      )
      conn.commit()
      conn.close()

      messagebox.showinfo(
          "Succès", "Les codes d'accès ont été mis à jour avec succès !"
      )
      fen_pass.destroy()

    def reinitialiser_defaut():
      if messagebox.askyesno(
          "Réinitialisation",
          "Remettre les codes par défaut (Admin: 1234 / Réception: 0000) ?",
      ):
        conn = sqlite3.connect(BASE_DB)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE utilisateurs SET code = '1234' WHERE role = 'admin'"
        )
        cursor.execute(
            "UPDATE utilisateurs SET code = '0000' WHERE role = 'reception'"
        )
        conn.commit()
        conn.close()
        messagebox.showinfo(
            "Succès", "Codes réinitialisés : Admin = 1234 | Réception = 0000"
        )
        fen_pass.destroy()

    btn_frame = tk.Frame(fen_pass, bg=self.c_card)
    btn_frame.pack(pady=15)

    btn_valider = tk.Button(
        btn_frame,
        text="Enregistrer",
        command=enregistrer_codes,
        bg="#2ecc71",
        fg="#ffffff",
        font=("Helvetica", 9, "bold"),
        padx=12,
        pady=4,
        relief="flat",
        cursor="hand2",
    )
    btn_valider.pack(side="left", padx=5)

    btn_reset = tk.Button(
        btn_frame,
        text="Réinitialiser (1234 / 0000)",
        command=reinitialiser_defaut,
        bg="#e74c3c",
        fg="#ffffff",
        font=("Helvetica", 9, "bold"),
        padx=12,
        pady=4,
        relief="flat",
        cursor="hand2",
    )
    btn_reset.pack(side="left", padx=5)

  def verifier_avance_client(self, event=None):
    num = self.e_recherche_tel.get().strip()
    if not num:
      self.lbl_info_avance.config(
          text="Entrez un numéro de téléphone", fg="#7f8c8d"
      )
      self.lbl_montant_avance.config(text="0 XOF")
      return

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nom_artiste, somme_versee FROM avances WHERE numero LIKE ?",
        (f"%{num}%",),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
      nom, montant = row[0], row[1]
      self.lbl_info_avance.config(
          text=f"Avance trouvée pour : {nom}", fg="#2ecc71"
      )
      self.lbl_montant_avance.config(text=f"{montant:,.0f} XOF")
    else:
      self.lbl_info_avance.config(
          text="Aucune avance trouvée pour ce numéro", fg="#e74c3c"
      )
      self.lbl_montant_avance.config(text="0 XOF")

  def verifier_reliquat_telephone(self, event=None):
    widget_tel = self.champs.get("Téléphone :")
    if not widget_tel:
      return
    numero = widget_tel.get().strip()
    if not numero:
      self.lbl_alerte_impaye.config(text="")
      return

    try:
      conn = sqlite3.connect(BASE_DB)
      cursor = conn.cursor()
      # On cherche la somme des impayés (somme_restante) dans la table artistes pour ce numéro
      cursor.execute(
          "SELECT SUM(somme_restante) FROM artistes WHERE telephone = ? AND"
          " statut != 'PAYER'",
          (numero,),
      )
      resultat = cursor.fetchone()
      conn.close()

      total_impaye = resultat[0] if resultat and resultat[0] else 0

      if total_impaye > 0:
        self.lbl_alerte_impaye.config(
            text=f"ATTENTION - Reliquat impayé : {total_impaye:,.0f} XOF",
            fg="#e74c3c",
        )
      else:
        self.lbl_alerte_impaye.config(
            text="Aucun impayé pour ce numéro.", fg="#2ecc71"
        )
    except Exception as e:
      print(f"Erreur vérification reliquat : {e}")

  def ouvrir_section(self, nom_section, niveau_requis):
    if self.verifier_acces(niveau_requis):
      if nom_section == "Formulaire BM Prod":
        self.creer_ecran_formulaire()
      elif nom_section == "Tableau de bord":
        self.creer_ecran_tableau_de_bord()
      elif nom_section == "LES AVANCES AVANT JOB":
        self.creer_ecran_avances()
      elif nom_section in ["VIDER RDV", "AJOUTER RDV"]:
        self.creer_ecran_vider_rdv()
      elif nom_section == "BASE DONNEES ARTISTES":
        self.creer_ecran_base_artistes()
      elif nom_section == "NOS TARIFS":
        self.creer_ecran_nos_tarifs()
      elif nom_section == "Interface Quotidien":
        self.creer_ecran_interface_quotidien()
      elif nom_section == "Données Quotidien":
        self.creer_ecran_donnees_quotidien()
      elif nom_section == "NOS DEPENSES":
        self.creer_ecran_nos_depenses()
      elif nom_section == "RECHERCHE":
        self.creer_ecran_recherche()
      elif nom_section == "FACTURE":
        self.creer_ecran_facture()

  def obtenir_dernier_numero(self):
    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(num_facture) FROM artistes")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] is not None else 0

  def creer_entete_nav(self, titre):
    for widget in self.root.winfo_children():
      widget.destroy()

    top = tk.Frame(self.root, bg=self.c_card)
    top.pack(fill="x", padx=10, pady=10)

    btn_accueil = tk.Button(
        top,
        text=" ACCUEIL ",
        command=self.creer_menu_principal,
        bg=self.c_accent,
        fg="#000000",
        font=("Helvetica", 10, "bold"),
        padx=15,
        pady=4,
        relief="flat",
        cursor="hand2",
    )
    btn_accueil.pack(side="right", padx=10)

    tk.Label(
        top,
        text=titre,
        font=("Helvetica", 14, "bold"),
        fg=self.c_text,
        bg=self.c_card,
    ).pack(side="left", padx=10, pady=5)

  def creer_menu_principal(self):
    for widget in self.root.winfo_children():
      widget.destroy()

    dernier_num = self.obtenir_dernier_numero()

    cadre_top = tk.Frame(self.root, bg=self.c_card, height=45)
    cadre_top.pack(fill="x", padx=15, pady=10)

    tk.Label(
        cadre_top,
        text="  NUMÉRO EN COURS : 0  ",
        font=("Helvetica", 10, "bold"),
        bg="#2c3e50",
        fg=self.c_text,
        pady=5,
    ).pack(side="left", padx=10, pady=5)
    tk.Label(
        cadre_top,
        text=f"  DERNIER NUMÉRO ENREGISTRÉ : {dernier_num}  ",
        font=("Helvetica", 10, "bold"),
        bg=self.c_accent,
        fg="#000000",
        pady=5,
    ).pack(side="right", padx=10, pady=5)

    cadre_titre = tk.Frame(self.root, bg=self.c_bg)
    cadre_titre.pack(fill="x", padx=20, pady=5)
    tk.Label(
        cadre_titre,
        text="TABLEAU DE BORD PRINCIPAL",
        font=("Helvetica", 18, "bold"),
        bg=self.c_bg,
        fg=self.c_text,
    ).pack()

    zone_centrale = tk.Frame(self.root, bg=self.c_bg)
    zone_centrale.pack(expand=True, fill="both", padx=20, pady=10)

    col_gauche = tk.Frame(
        zone_centrale,
        bg=self.c_card,
        bd=1,
        relief="solid",
        highlightbackground="#2c3e50",
    )
    col_gauche.pack(side="left", fill="both", expand=True, padx=15, pady=10)

    col_centre = tk.Frame(
        zone_centrale,
        bg=self.c_card,
        highlightbackground=self.c_accent,
        highlightthickness=2,
        width=280,
    )
    col_centre.pack(side="left", fill="both", padx=10, pady=10, ipadx=10)

    tk.Label(
        col_centre,
        text="BIG S MEDIA\nPRODUCTION",
        font=("Helvetica", 16, "bold"),
        bg=self.c_card,
        fg=self.c_accent,
        justify="center",
    ).pack(pady=15)

    cadre_verif = tk.LabelFrame(
        col_centre,
        text=" TÉLÉPHONE CLIENT (AVANCE) ",
        font=("Helvetica", 8, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    cadre_verif.pack(padx=10, pady=10, fill="x")

    self.e_recherche_tel = tk.Entry(
        cadre_verif, font=("Helvetica", 10, "bold"), justify="center"
    )
    self.e_recherche_tel.pack(padx=5, pady=5, fill="x")
    self.e_recherche_tel.bind("<KeyRelease>", self.verifier_avance_client)

    self.lbl_info_avance = tk.Label(
        cadre_verif,
        text="Entrez un numéro de téléphone",
        font=("Helvetica", 7, "italic"),
        fg="#7f8c8d",
        bg=self.c_card,
    )
    self.lbl_info_avance.pack(pady=2)

    self.lbl_montant_avance = tk.Label(
        cadre_verif,
        text="0 XOF",
        font=("Helvetica", 12, "bold"),
        bg="#27ae60",
        fg="#ffffff",
        pady=4,
    )
    self.lbl_montant_avance.pack(padx=5, pady=5, fill="x")

    btn_codes = tk.Button(
        col_centre,
        text=" CODES D'ACCÈS ",
        command=self.modifier_mots_de_passe,
        bg="#e67e22",
        fg="#ffffff",
        font=("Helvetica", 8, "bold"),
        pady=5,
        relief="flat",
        cursor="hand2",
    )
    btn_codes.pack(pady=15)

    col_droite = tk.Frame(
        zone_centrale,
        bg=self.c_card,
        bd=1,
        relief="solid",
        highlightbackground="#2c3e50",
    )
    col_droite.pack(side="left", fill="both", expand=True, padx=15, pady=10)

    self.creer_petit_bouton(
        col_gauche,
        "Formulaire BM Prod",
        lambda: self.ouvrir_section("Formulaire BM Prod", "libre"),
    )
    self.creer_petit_bouton(
        col_gauche,
        "Tableau de bord",
        lambda: self.ouvrir_section("Tableau de bord", "admin"),
    )
    self.creer_petit_bouton(
        col_gauche,
        "LES AVANCES AVANT JOB",
        lambda: self.ouvrir_section("LES AVANCES AVANT JOB", "admin"),
    )
    self.creer_petit_bouton(
        col_gauche,
        "VIDER RDV",
        lambda: self.ouvrir_section("VIDER RDV", "admin"),
    )
    self.creer_petit_bouton(
        col_gauche,
        "BASE DONNEES ARTISTES",
        lambda: self.ouvrir_section("BASE DONNEES ARTISTES", "admin"),
    )

    self.creer_petit_bouton(
        col_droite,
        "NOS TARIFS",
        lambda: self.ouvrir_section("NOS TARIFS", "reception"),
    )
    self.creer_petit_bouton(
        col_droite,
        "Interface Quotidien",
        lambda: self.ouvrir_section("Interface Quotidien", "reception"),
    )
    self.creer_petit_bouton(
        col_droite,
        "AJOUTER RDV",
        lambda: self.ouvrir_section("AJOUTER RDV", "reception"),
    )
    self.creer_petit_bouton(
        col_droite,
        "Données Quotidien",
        lambda: self.ouvrir_section("Données Quotidien", "admin"),
    )
    self.creer_petit_bouton(
        col_droite,
        "NOS DEPENSES",
        lambda: self.ouvrir_section("NOS DEPENSES", "admin"),
    )
    self.creer_petit_bouton(
        col_droite,
        "RECHERCHE",
        lambda: self.ouvrir_section("RECHERCHE", "admin"),
    )
    self.creer_petit_bouton(
        col_droite,
        "FACTURE",
        lambda: self.ouvrir_section("FACTURE", "reception"),
    )

  def creer_petit_bouton(self, parent, texte, commande):
    btn = tk.Button(
        parent,
        text=texte,
        command=commande,
        bg=self.c_btn,
        fg=self.c_text,
        font=("Helvetica", 9, "bold"),
        width=26,
        pady=6,
        relief="raised",
        bd=2,
        activebackground=self.c_btn_hover,
        activeforeground=self.c_text,
        cursor="hand2",
    )
    btn.pack(pady=7, anchor="center")

  def creer_ecran_formulaire(self):
    self.creer_entete_nav("FORMULAIRE BM PROD")
    cadre_form = tk.LabelFrame(
        self.root,
        text=" Saisie d'un Nouvel Enregistrement ",
        font=("Helvetica", 11, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    cadre_form.pack(padx=20, pady=20, fill="both", expand=True)

    options_type_prod = [
        "DANDALI",
        "KASIDA",
        "TALLAH",
        "ORCHESTRE",
        "LECTURE CORANIC",
        "VOIX OFF",
        "HIPHOP",
        "TRADI",
    ]
    options_style_musical = list(self.grille_tarifs.keys())

    self.champs = {}
    champs_liste = [
        ("Nom d'Artiste :", 0, 0, "entry"),
        ("Date d'enregistrement (JJ/MM/AAAA) :", 0, 2, "entry"),
        ("Titre de chanson :", 1, 0, "entry"),
        ("Heure :", 1, 2, "entry"),
        ("Téléphone :", 2, 0, "entry"),
        ("Ville :", 2, 2, "entry"),
        ("Type de prod :", 3, 0, "combo_type"),
        ("Style Musical :", 3, 2, "combo_style"),
        ("Tarifs (XOF) :", 4, 0, "entry"),
        ("Somme versée (XOF) :", 4, 2, "entry"),
    ]

    for label_text, row, col, type_widget in champs_liste:
      lbl = tk.Label(
          cadre_form,
          text=label_text,
          fg=self.c_text,
          bg=self.c_card,
          font=("Helvetica", 10),
      )
      lbl.grid(row=row, column=col, padx=15, pady=10, sticky="e")

      if type_widget == "entry":
        widget = tk.Entry(cadre_form, font=("Helvetica", 10), width=30)
      elif type_widget == "combo_type":
        widget = ttk.Combobox(
            cadre_form,
            values=options_type_prod,
            font=("Helvetica", 10),
            width=28,
            state="readonly",
        )
      elif type_widget == "combo_style":
        widget = ttk.Combobox(
            cadre_form,
            values=options_style_musical,
            font=("Helvetica", 10),
            width=28,
            state="readonly",
        )

      widget.grid(row=row, column=col + 1, padx=15, pady=10, sticky="w")
      self.champs[label_text] = widget

    # Intégration propre de l'alerte de reliquat à côté du champ Téléphone
    # Alerte placée tout en haut, bien au-dessus du formulaire pour ne rien cacher
    self.lbl_alerte_impaye = tk.Label(
        cadre_form, text="", font=("Helvetica", 10, "bold"), bg=self.c_card
    )
    self.lbl_alerte_impaye.grid(
        row=0, column=0, columnspan=4, pady=(0, 10), sticky="n"
    )

    widget_tel = self.champs.get("Téléphone :")
    if widget_tel:
      widget_tel.bind("<KeyRelease>", self.verifier_reliquat_telephone)

    btn_envoyer = tk.Button(
        cadre_form,
        text=" Valider et Envoyer à la Base de Données",
        command=self.enregistrer_dans_base,
        bg="#2ecc71",
        fg="#ffffff",
        font=("Helvetica", 11, "bold"),
        padx=20,
        pady=8,
        relief="flat",
        cursor="hand2",
    )
    btn_envoyer.grid(row=5, column=0, columnspan=4, pady=25)

  def enregistrer_dans_base(self):
    nom = self.champs["Nom d'Artiste :"].get()
    tarif = self.champs["Tarifs (XOF) :"].get() or 0
    verse = self.champs["Somme versée (XOF) :"].get() or 0

    if not nom:
      messagebox.showwarning(
          "Attention", "Le Nom d'Artiste est obligatoire !"
      )
      return

    try:
      tarif_f = float(tarif)
      verse_f = float(verse)
      restant_f = tarif_f - verse_f
      statut = "PAYER" if restant_f <= 0 else "NON PAYER"
    except ValueError:
      messagebox.showerror(
          "Erreur", "Les montants doivent être des chiffres valides."
      )
      return

    num_facture = self.obtenir_dernier_numero() + 1

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO artistes (
                nom_artiste, date_enregistrement, titre_chanson, heure, telephone, 
                ville, type_prod, style_musical, tarifs, somme_versee, somme_restante, statut, num_facture
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nom,
            self.champs["Date d'enregistrement (JJ/MM/AAAA) :"].get(),
            self.champs["Titre de chanson :"].get(),
            self.champs["Heure :"].get(),
            self.champs["Téléphone :"].get(),
            self.champs["Ville :"].get(),
            self.champs["Type de prod :"].get(),
            self.champs["Style Musical :"].get(),
            tarif_f,
            verse_f,
            restant_f,
            statut,
            num_facture,
        ),
    )
    conn.commit()
    conn.close()

    messagebox.showinfo(
        "Succès", f"Saisie envoyée à la Base de Données ! (N° {num_facture})"
    )
    self.creer_ecran_formulaire()

  def creer_ecran_tableau_de_bord(self):
    self.creer_entete_nav("TABLEAU DE BORD DYNAMIQUE")

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT date_enregistrement, somme_versee FROM artistes")
    lignes = cursor.fetchall()
    conn.close()

    recette_totale = sum(r[1] for r in lignes if r[1])
    epargne_totale = recette_totale * 0.10
    recettes_mois = {m: 0.0 for m in range(1, 13)}

    for dt, vers in lignes:
      if dt and vers:
        try:
          parties = dt.split("/")
          if len(parties) == 3:
            num_m = int(parties[1])
            if 1 <= num_m <= 12:
              recettes_mois[num_m] += float(vers)
        except ValueError:
          pass

    cadre_haut = tk.Frame(self.root, bg=self.c_card, padx=15, pady=15)
    cadre_haut.pack(fill="x", padx=15, pady=15)

    bloc_gauche = tk.Frame(
        cadre_haut,
        bg=self.c_accent,
        highlightbackground="#000000",
        highlightthickness=1,
    )
    bloc_gauche.pack(side="left", padx=10, pady=5)

    tk.Label(
        bloc_gauche,
        text="RECETTE TOTAL",
        font=("Helvetica", 9, "bold"),
        bg=self.c_card,
        fg=self.c_text,
        padx=10,
        pady=3,
    ).pack(fill="x")
    tk.Label(
        bloc_gauche,
        text=f"{recette_totale:,.0f} XOF",
        font=("Helvetica", 11, "bold"),
        bg=self.c_accent,
        fg="#000000",
        padx=15,
        pady=5,
    ).pack()

    tk.Label(
        bloc_gauche,
        text="Objectif Épargne (10%)",
        font=("Helvetica", 9, "bold"),
        bg="#ffff00",
        fg="#000000",
        padx=10,
        pady=3,
    ).pack(fill="x")
    tk.Label(
        bloc_gauche,
        text=f"{epargne_totale:,.0f} XOF",
        font=("Helvetica", 11, "bold"),
        bg="#000080",
        fg="#ffffff",
        padx=15,
        pady=5,
    ).pack()

    cadre_mois = tk.Frame(cadre_haut, bg=self.c_card)
    cadre_mois.pack(side="left", fill="x", expand=True, padx=10)

    config_mois = [
        (2, "FEVRIER", "#e67e22"),
        (3, "MARS", "#2980b9"),
        (4, "AVRIL", "#d35400"),
        (5, "MAI", "#f39c12"),
        (6, "JUIN", "#27ae60"),
        (7, "JUILLET", "#c0392b"),
        (8, "AOUT", "#1abc9c"),
        (9, "SEPTEMBRE", "#34495e"),
        (10, "OCTOBRE", "#16a085"),
        (11, "NOVEMBRE", "#2980b9"),
        (12, "DECEMBRE", "#27ae60"),
    ]

    for col_idx, (num_m, nom_m, col_bg) in enumerate(config_mois):
      valeur_m = recettes_mois[num_m]
      epargne_m = valeur_m * 0.10

      col_frame = tk.Frame(
          cadre_mois,
          bg=self.c_bg,
          highlightbackground="#000000",
          highlightthickness=1,
      )
      col_frame.grid(row=0, column=col_idx, padx=2, sticky="nsew")

      tk.Label(
          col_frame,
          text=nom_m,
          font=("Helvetica", 7, "bold"),
          bg=col_bg,
          fg="#ffffff",
          width=12,
      ).pack(fill="x")
      tk.Label(
          col_frame,
          text=f"{valeur_m:,.0f} F",
          font=("Helvetica", 8, "bold"),
          bg=self.c_card,
          fg=self.c_text,
      ).pack(pady=2)
      tk.Label(
          col_frame,
          text="Épargne",
          font=("Helvetica", 7),
          bg="#34495e",
          fg="#ffffff",
      ).pack(fill="x")
      tk.Label(
          col_frame,
          text=f"{epargne_m:,.0f} F",
          font=("Helvetica", 8, "bold"),
          bg=col_bg,
          fg="#ffffff",
      ).pack(pady=2)

  def creer_ecran_avances(self):
    self.creer_entete_nav("LES AVANCES AVANT JOB")

    cadre_form = tk.LabelFrame(
        self.root,
        text=" Saisie d'une Avance ",
        font=("Helvetica", 11, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    cadre_form.pack(fill="x", padx=15, pady=10)

    self.champs_avance = {}
    champs_list = [
        ("Nom de l'Artiste :", 0, 0),
        ("Numéro de Téléphone :", 0, 2),
        ("Date de versement :", 1, 0),
        ("Somme Versée (XOF) :", 1, 2),
        ("Moyen de versement :", 2, 0),
        ("Date prévue session :", 2, 2),
    ]

    for label_text, row, col in champs_list:
      lbl = tk.Label(
          cadre_form,
          text=label_text,
          fg=self.c_text,
          bg=self.c_card,
          font=("Helvetica", 10),
      )
      lbl.grid(row=row, column=col, padx=10, pady=5, sticky="e")

      entry = tk.Entry(cadre_form, font=("Helvetica", 10), width=25)
      entry.grid(row=row, column=col + 1, padx=10, pady=5, sticky="w")
      self.champs_avance[label_text] = entry

    btn_enregistrer = tk.Button(
        cadre_form,
        text=" Enregistrer l'Avance",
        command=self.sauvegarder_avance,
        bg="#2ecc71",
        fg="#ffffff",
        font=("Helvetica", 10, "bold"),
        padx=15,
        pady=5,
        relief="flat",
    )
    btn_enregistrer.grid(row=3, column=0, columnspan=2, pady=10)

    btn_suppr = tk.Button(
        cadre_form,
        text=" Supprimer Sélection ",
        command=self.supprimer_avance,
        bg="#e74c3c",
        fg="#ffffff",
        font=("Helvetica", 10, "bold"),
        padx=15,
        pady=5,
        relief="flat",
    )
    btn_suppr.grid(row=3, column=2, columnspan=2, pady=10)

    cadre_table = tk.Frame(self.root, bg=self.c_card, padx=10, pady=10)
    cadre_table.pack(fill="both", expand=True, padx=15, pady=10)

    colonnes = (
        "ID",
        "Artiste",
        "Téléphone",
        "Date Versement",
        "Somme Versée",
        "Moyen Versement",
        "Date Prévue",
    )
    self.table_avances = ttk.Treeview(
        cadre_table, columns=colonnes, show="headings"
    )

    for col in colonnes:
      self.table_avances.heading(col, text=col)
      self.table_avances.column(
          col, width=60 if col == "ID" else 120, anchor="center"
      )

    self.table_avances.pack(fill="both", expand=True)
    self.rafraichir_avances()

  def sauvegarder_avance(self):
    nom = self.champs_avance["Nom de l'Artiste :"].get()
    somme = self.champs_avance["Somme Versée (XOF) :"].get() or 0

    if not nom:
      messagebox.showwarning(
          "Attention", "Le Nom de l'Artiste est obligatoire !"
      )
      return

    try:
      somme_f = float(somme)
    except ValueError:
      messagebox.showerror(
          "Erreur", "La somme versée doit être un chiffre valide."
      )
      return

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO avances (nom_artiste, numero, date_versement, somme_versee, moyen_versement, date_prevue)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            nom,
            self.champs_avance["Numéro de Téléphone :"].get(),
            self.champs_avance["Date de versement :"].get(),
            somme_f,
            self.champs_avance["Moyen de versement :"].get(),
            self.champs_avance["Date prévue session :"].get(),
        ),
    )
    conn.commit()
    conn.close()

    messagebox.showinfo("Succès", "Avance enregistrée !")
    self.creer_ecran_avances()

  def supprimer_avance(self):
    selected_item = self.table_avances.selection()
    if not selected_item:
      messagebox.showwarning(
          "Attention", "Veuillez sélectionner une ligne à supprimer !"
      )
      return

    item_values = self.table_avances.item(selected_item[0], "values")
    id_ligne = item_values[0]

    if messagebox.askyesno("Confirmation", f"Supprimer l'avance ID {id_ligne} ?"):
      conn = sqlite3.connect(BASE_DB)
      cursor = conn.cursor()
      cursor.execute("DELETE FROM avances WHERE id = ?", (id_ligne,))
      conn.commit()
      conn.close()

      messagebox.showinfo("Succès", "Ligne supprimée !")
      self.rafraichir_avances()

  def rafraichir_avances(self):
    for item in self.table_avances.get_children():
      self.table_avances.delete(item)

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nom_artiste, numero, date_versement, somme_versee,"
        " moyen_versement, date_prevue FROM avances ORDER BY id DESC"
    )
    for row in cursor.fetchall():
      self.table_avances.insert("", "end", values=row)
    conn.close()

  def creer_ecran_vider_rdv(self):
    self.creer_entete_nav("BASE DE DONNÉES RDV")

    cadre_saisie = tk.LabelFrame(
        self.root,
        text=" Saisie Manuelle de Rendez-Vous ",
        font=("Helvetica", 10, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    cadre_saisie.pack(fill="x", padx=15, pady=10)

    jours_semaine = [
        "Lundi",
        "Mardi",
        "Mercredi",
        "Jeudi",
        "Vendredi",
        "Samedi",
        "Dimanche",
    ]
    self.champs_rdv = {}
    f_list = [
        ("Jour :", 0, 0, "combo_jour"),
        ("Nom du Client :", 0, 2, "entry"),
        ("Téléphone :", 1, 0, "entry"),
        ("Date du RDV :", 1, 2, "entry"),
        ("Heure du RDV :", 2, 0, "entry"),
        ("Statut SMS :", 2, 2, "entry"),
    ]

    for lbl_text, row, col, w_type in f_list:
      tk.Label(
          cadre_saisie,
          text=lbl_text,
          fg=self.c_text,
          bg=self.c_card,
          font=("Helvetica", 9),
      ).grid(row=row, column=col, padx=8, pady=4, sticky="e")
      if w_type == "entry":
        e = tk.Entry(cadre_saisie, font=("Helvetica", 9), width=22)
      else:
        e = ttk.Combobox(
            cadre_saisie,
            values=jours_semaine,
            font=("Helvetica", 9),
            width=20,
            state="readonly",
        )
      e.grid(row=row, column=col + 1, padx=8, pady=4, sticky="w")
      self.champs_rdv[lbl_text] = e

    btn_ajouter = tk.Button(
        cadre_saisie,
        text=" Ajouter RDV ",
        command=self.ajouter_rdv_manuel,
        bg="#2ecc71",
        fg="#ffffff",
        font=("Helvetica", 9, "bold"),
        relief="flat",
    )
    btn_ajouter.grid(row=3, column=0, columnspan=2, pady=6)

    btn_suppr = tk.Button(
        cadre_saisie,
        text=" Supprimer Ligne ",
        command=self.supprimer_rdv_selectionne,
        bg="#e67e22",
        fg="#ffffff",
        font=("Helvetica", 9, "bold"),
        relief="flat",
    )
    btn_suppr.grid(row=3, column=2, columnspan=2, pady=6)

    btn_vider = tk.Button(
        cadre_saisie,
        text=" Vider Tous les RDV ",
        command=self.vider_tous_les_rdv,
        bg="#e74c3c",
        fg="#ffffff",
        font=("Helvetica", 9, "bold"),
        relief="flat",
    )
    btn_vider.grid(row=3, column=4, columnspan=2, pady=6)

    cadre_table = tk.Frame(self.root, bg=self.c_card, padx=10, pady=10)
    cadre_table.pack(fill="both", expand=True, padx=15, pady=10)

    colonnes = (
        "ID_RDV",
        "Jour",
        "Nom du client",
        "Téléphone",
        "Date du RDV",
        "Heure du RDV",
        "Statut sms",
    )
    self.table_rdv = ttk.Treeview(
        cadre_table, columns=colonnes, show="headings"
    )

    for col in colonnes:
      self.table_rdv.heading(col, text=col)
      self.table_rdv.column(col, width=120, anchor="center")

    self.table_rdv.pack(fill="both", expand=True)
    self.rafraichir_rdv()

  def ajouter_rdv_manuel(self):
    nom = self.champs_rdv["Nom du Client :"].get()
    if not nom:
      messagebox.showwarning("Attention", "Le Nom du client est requis !")
      return

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO rdv (jour, nom_client, telephone, date_rdv, heure_rdv, statut_sms)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            self.champs_rdv["Jour :"].get(),
            nom,
            self.champs_rdv["Téléphone :"].get(),
            self.champs_rdv["Date du RDV :"].get(),
            self.champs_rdv["Heure du RDV :"].get(),
            self.champs_rdv["Statut SMS :"].get() or "Non envoyé",
        ),
    )
    conn.commit()
    conn.close()

    messagebox.showinfo("Succès", "RDV ajouté !")
    self.creer_ecran_vider_rdv()

  def supprimer_rdv_selectionne(self):
    selected_item = self.table_rdv.selection()
    if not selected_item:
      messagebox.showwarning(
          "Attention", "Veuillez sélectionner un RDV à supprimer !"
      )
      return

    item_values = self.table_rdv.item(selected_item[0], "values")
    id_rdv = item_values[0]

    if messagebox.askyesno("Confirmation", f"Supprimer le RDV ID {id_rdv} ?"):
      conn = sqlite3.connect(BASE_DB)
      cursor = conn.cursor()
      cursor.execute("DELETE FROM rdv WHERE id = ?", (id_rdv,))
      conn.commit()
      conn.close()

      messagebox.showinfo("Succès", "Rendez-vous supprimé !")
      self.rafraichir_rdv()

  def vider_tous_les_rdv(self):
    if messagebox.askyesno("Confirmation", "Effacer TOUS les rendez-vous ?"):
      conn = sqlite3.connect(BASE_DB)
      cursor = conn.cursor()
      cursor.execute("DELETE FROM rdv")
      conn.commit()
      conn.close()
      messagebox.showinfo("Succès", "Liste vidée !")
      self.creer_ecran_vider_rdv()

  def rafraichir_rdv(self):
    for item in self.table_rdv.get_children():
      self.table_rdv.delete(item)

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rdv ORDER BY id ASC")
    for row in cursor.fetchall():
      self.table_rdv.insert("", "end", values=row)
    conn.close()

  def creer_ecran_base_artistes(self):
    self.creer_entete_nav("BASE DE DONNÉES ARTISTES")

    cadre_conteneur = tk.Frame(self.root, bg=self.c_card, padx=15, pady=15)
    cadre_conteneur.pack(fill="both", expand=True, padx=15, pady=15)

    colonnes = (
        "Artiste",
        "Date",
        "Titre",
        "Heure",
        "Téléphone",
        "Ville",
        "Type Prod",
        "Style",
        "Tarifs",
        "Versé",
        "Restant",
        "STATUT",
        "N° Facture",
    )
    self.table_artistes = ttk.Treeview(
        cadre_conteneur, columns=colonnes, show="headings"
    )

    for col in colonnes:
      self.table_artistes.heading(col, text=col)
      self.table_artistes.column(col, width=80, anchor="center")

    self.table_artistes.pack(fill="both", expand=True)

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nom_artiste, date_enregistrement, titre_chanson, heure,"
        " telephone, ville, type_prod, style_musical, tarifs, somme_versee,"
        " somme_restante, statut, num_facture FROM artistes ORDER BY id DESC"
    )
    for row in cursor.fetchall():
      self.table_artistes.insert("", "end", values=row)
    conn.close()

  def creer_ecran_nos_tarifs(self):
    self.creer_entete_nav("NOS TARIFS - BM PROD")

    zone_centre = tk.Frame(self.root, bg=self.c_card, padx=20, pady=20)
    zone_centre.pack(pady=30)

    f_genre = tk.Frame(zone_centre, bg=self.c_card)
    f_genre.pack(side="left", padx=15)
    tk.Label(
        f_genre,
        text="Genre Musical :",
        font=("Helvetica", 10, "bold"),
        bg=self.c_card,
        fg=self.c_text,
    ).pack(pady=2)

    self.combo_tarif = ttk.Combobox(
        f_genre,
        values=list(self.grille_tarifs.keys()),
        font=("Helvetica", 11, "bold"),
        width=25,
        state="readonly",
    )
    self.combo_tarif.pack()
    self.combo_tarif.bind(
        "<<ComboboxSelected>>", self.afficher_tarif_selectionne
    )

    f_tarif = tk.Frame(zone_centre, bg=self.c_card)
    f_tarif.pack(side="left", padx=15)
    tk.Label(
        f_tarif,
        text="Tarif correspondant :",
        font=("Helvetica", 10, "bold"),
        bg=self.c_card,
        fg=self.c_text,
    ).pack(pady=2)

    self.lbl_tarif_valeur = tk.Label(
        f_tarif,
        text="0 XOF",
        font=("Helvetica", 12, "bold"),
        bg=self.c_accent,
        fg="#000000",
        width=20,
        pady=3,
        relief="flat",
    )
    self.lbl_tarif_valeur.pack()

  def afficher_tarif_selectionne(self, event):
    genre = self.combo_tarif.get()
    tarif = self.grille_tarifs.get(genre, "0 XOF")
    self.lbl_tarif_valeur.config(text=tarif)

  def creer_ecran_interface_quotidien(self):
    self.creer_entete_nav("INTERFACE DE GESTION QUOTIDIENNE")

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(montant) FROM depenses")
    tot_dep = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(montant) FROM conso_electricite")
    tot_elec = cursor.fetchone()[0] or 0.0
    conn.close()

    main_frame = tk.Frame(self.root, bg=self.c_bg)
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)

    col_gauche = tk.Frame(main_frame, bg=self.c_card, padx=15, pady=15)
    col_gauche.pack(side="left", fill="y", padx=10)

    tk.Label(
        col_gauche,
        text="RÉSUMÉ DES DÉPENSES",
        font=("Helvetica", 10, "bold"),
        bg=self.c_card,
        fg=self.c_accent,
    ).pack(anchor="w", pady=5)
    tk.Label(
        col_gauche,
        text=f"Dépenses : {tot_dep:,.0f} FCFA",
        font=("Helvetica", 9, "bold"),
        fg=self.c_text,
        bg=self.c_card,
    ).pack(anchor="w", pady=3)
    tk.Label(
        col_gauche,
        text=f"Électricité : {tot_elec:,.0f} FCFA",
        font=("Helvetica", 9, "bold"),
        fg=self.c_text,
        bg=self.c_card,
    ).pack(anchor="w", pady=3)

    col_droite = tk.Frame(main_frame, bg=self.c_bg)
    col_droite.pack(side="left", fill="both", expand=True, padx=10)

    f_rdv = tk.LabelFrame(
        col_droite,
        text=" RDV PERSO ",
        font=("Helvetica", 9, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    f_rdv.pack(fill="x", pady=5)
    self.e_rdv_dt = tk.Entry(f_rdv, width=12)
    self.e_rdv_hr = tk.Entry(f_rdv, width=10)
    self.e_rdv_obj = tk.Entry(f_rdv, width=25)
    self.e_rdv_st = tk.Entry(f_rdv, width=15)

    tk.Label(
        f_rdv, text="Date:", bg=self.c_card, fg=self.c_text, font=("Helvetica", 8)
    ).grid(row=0, column=0)
    self.e_rdv_dt.grid(row=0, column=1, padx=2)
    tk.Label(
        f_rdv,
        text="Heure:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=2)
    self.e_rdv_hr.grid(row=0, column=3, padx=2)
    tk.Label(
        f_rdv,
        text="Objet:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=4)
    self.e_rdv_obj.grid(row=0, column=5, padx=2)
    tk.Label(
        f_rdv,
        text="Statut:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=6)
    self.e_rdv_st.grid(row=0, column=7, padx=2)

    btn_add_rdv = tk.Button(
        f_rdv,
        text="Ajouter",
        command=self.ajouter_rdv_perso,
        bg=self.c_btn,
        fg="#ffffff",
        font=("Helvetica", 8, "bold"),
        relief="flat",
    )
    btn_add_rdv.grid(row=0, column=8, padx=5, pady=3)

    f_elec = tk.LabelFrame(
        col_droite,
        text=" ÉLECTRICITÉ ",
        font=("Helvetica", 9, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    f_elec.pack(fill="x", pady=5)
    self.e_el_dt = tk.Entry(f_elec, width=12)
    self.e_el_idx = tk.Entry(f_elec, width=12)
    self.e_el_mnt = tk.Entry(f_elec, width=15)
    self.e_el_nts = tk.Entry(f_elec, width=25)

    tk.Label(
        f_elec,
        text="Date:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=0)
    self.e_el_dt.grid(row=0, column=1, padx=2)
    tk.Label(
        f_elec,
        text="Index:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=2)
    self.e_el_idx.grid(row=0, column=3, padx=2)
    tk.Label(
        f_elec,
        text="Montant:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=4)
    self.e_el_mnt.grid(row=0, column=5, padx=2)

    btn_add_el = tk.Button(
        f_elec,
        text="Ajouter",
        command=self.ajouter_conso_elec,
        bg=self.c_btn,
        fg="#ffffff",
        font=("Helvetica", 8, "bold"),
        relief="flat",
    )
    btn_add_el.grid(row=0, column=8, padx=5, pady=3)

    f_dep = tk.LabelFrame(
        col_droite,
        text=" DÉPENSES ",
        font=("Helvetica", 9, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    f_dep.pack(fill="x", pady=5)
    self.e_dp_dt = tk.Entry(f_dep, width=12)
    self.e_dp_cat = tk.Entry(f_dep, width=15)
    self.e_dp_dsc = tk.Entry(f_dep, width=25)
    self.e_dp_mnt = tk.Entry(f_dep, width=15)

    tk.Label(
        f_dep, text="Date:", bg=self.c_card, fg=self.c_text, font=("Helvetica", 8)
    ).grid(row=0, column=0)
    self.e_dp_dt.grid(row=0, column=1, padx=2)
    tk.Label(
        f_dep,
        text="Catégorie:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=2)
    self.e_dp_cat.grid(row=0, column=3, padx=2)
    tk.Label(
        f_dep,
        text="Description:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=4)
    self.e_dp_dsc.grid(row=0, column=5, padx=2)
    tk.Label(
        f_dep,
        text="Montant:",
        bg=self.c_card,
        fg=self.c_text,
        font=("Helvetica", 8),
    ).grid(row=0, column=6)
    self.e_dp_mnt.grid(row=0, column=7, padx=2)

    btn_add_dp = tk.Button(
        f_dep,
        text="Ajouter",
        command=self.ajouter_depense,
        bg=self.c_btn,
        fg="#ffffff",
        font=("Helvetica", 8, "bold"),
        relief="flat",
    )
    btn_add_dp.grid(row=0, column=8, padx=5, pady=3)

  def ajouter_rdv_perso(self):
    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO rdv_perso (date_rdv, heure, objet, statut) VALUES (?, ?,"
        " ?, ?)",
        (
            self.e_rdv_dt.get(),
            self.e_rdv_hr.get(),
            self.e_rdv_obj.get(),
            self.e_rdv_st.get(),
        ),
    )
    conn.commit()
    conn.close()
    messagebox.showinfo("Succès", "RDV Perso enregistré !")
    self.creer_ecran_interface_quotidien()

  def ajouter_conso_elec(self):
    try:
      mnt = float(self.e_el_mnt.get() or 0)
    except ValueError:
      mnt = 0.0
    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conso_electricite (date_conso, index_kwh, montant, notes)"
        " VALUES (?, ?, ?, ?)",
        (
            self.e_el_dt.get(),
            self.e_el_idx.get(),
            mnt,
            self.e_el_nts.get(),
        ),
    )
    conn.commit()
    conn.close()
    messagebox.showinfo("Succès", "Électricité enregistrée !")
    self.creer_ecran_interface_quotidien()

  def ajouter_depense(self):
    try:
      mnt = float(self.e_dp_mnt.get() or 0)
    except ValueError:
      mnt = 0.0
    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO depenses (date_depense, categorie, description, montant)"
        " VALUES (?, ?, ?, ?)",
        (
            self.e_dp_dt.get(),
            self.e_dp_cat.get(),
            self.e_dp_dsc.get(),
            mnt,
        ),
    )
    conn.commit()
    conn.close()
    messagebox.showinfo("Succès", "Dépense enregistrée !")
    self.creer_ecran_interface_quotidien()

  def creer_ecran_donnees_quotidien(self):
    self.creer_entete_nav("DONNÉES QUOTIDIEN (HISTORIQUE GLOBAL)")

    notebook = ttk.Notebook(self.root)
    notebook.pack(fill="both", expand=True, padx=15, pady=15)

    f1 = tk.Frame(notebook, bg=self.c_card, padx=10, pady=10)
    notebook.add(f1, text=" Électricité ")
    t1 = ttk.Treeview(
        f1,
        columns=("Date", "Index (kWh)", "Montant (FCFA)", "Notes"),
        show="headings",
    )
    for c in ("Date", "Index (kWh)", "Montant (FCFA)", "Notes"):
      t1.heading(c, text=c)
      t1.column(c, anchor="center")
    t1.pack(fill="both", expand=True)

    f2 = tk.Frame(notebook, bg=self.c_card, padx=10, pady=10)
    notebook.add(f2, text=" Dépenses ")
    t2 = ttk.Treeview(
        f2,
        columns=("Date", "Catégorie", "Description", "Montant (FCFA)"),
        show="headings",
    )
    for c in ("Date", "Catégorie", "Description", "Montant (FCFA)"):
      t2.heading(c, text=c)
      t2.column(c, anchor="center")
    t2.pack(fill="both", expand=True)

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT date_conso, index_kwh, montant, notes FROM conso_electricite"
        " ORDER BY id DESC"
    )
    for r in cursor.fetchall():
      t1.insert("", "end", values=r)

    cursor.execute(
        "SELECT date_depense, categorie, description, montant FROM depenses"
        " ORDER BY id DESC"
    )
    for r in cursor.fetchall():
      t2.insert("", "end", values=r)

    conn.close()

  def creer_ecran_nos_depenses(self):
    self.creer_entete_nav("NOS DÉPENSES - ACHATS MATÉRIEL")

    cadre_saisie = tk.LabelFrame(
        self.root,
        text=" Saisie Rapide d'un Achat ",
        font=("Helvetica", 10, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    cadre_saisie.pack(fill="x", padx=15, pady=10)

    tk.Label(
        cadre_saisie,
        text="Achat (Désignation) :",
        fg=self.c_text,
        bg=self.c_card,
        font=("Helvetica", 9),
    ).grid(row=0, column=0, padx=5, pady=5, sticky="e")
    self.e_achat = tk.Entry(cadre_saisie, font=("Helvetica", 9), width=22)
    self.e_achat.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(
        cadre_saisie,
        text="Nombre :",
        fg=self.c_text,
        bg=self.c_card,
        font=("Helvetica", 9),
    ).grid(row=0, column=2, padx=5, pady=5, sticky="e")
    self.e_nbr = tk.Entry(cadre_saisie, font=("Helvetica", 9), width=8)
    self.e_nbr.insert(0, "1")
    self.e_nbr.grid(row=0, column=3, padx=5, pady=5)

    tk.Label(
        cadre_saisie,
        text="Prix Unitaire (XOF) :",
        fg=self.c_text,
        bg=self.c_card,
        font=("Helvetica", 9),
    ).grid(row=0, column=4, padx=5, pady=5, sticky="e")
    self.e_pu = tk.Entry(cadre_saisie, font=("Helvetica", 9), width=12)
    self.e_pu.grid(row=0, column=5, padx=5, pady=5)

    btn_ajouter = tk.Button(
        cadre_saisie,
        text=" Ajouter Achat ",
        command=self.ajouter_achat_materiel,
        bg="#2ecc71",
        fg="#ffffff",
        font=("Helvetica", 9, "bold"),
        padx=10,
        relief="flat",
    )
    btn_ajouter.grid(row=0, column=6, padx=5, pady=5)

    btn_supprimer = tk.Button(
        cadre_saisie,
        text=" Supprimer Ligne ",
        command=self.supprimer_achat_materiel,
        bg="#e74c3c",
        fg="#ffffff",
        font=("Helvetica", 9, "bold"),
        padx=10,
        relief="flat",
    )
    btn_supprimer.grid(row=0, column=7, padx=5, pady=5)

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total) FROM nos_depenses")
    somme_globale = cursor.fetchone()[0] or 0.0
    conn.close()

    cadre_total = tk.Frame(self.root, bg=self.c_card, padx=10, pady=5)
    cadre_total.pack(fill="x", padx=15, pady=5)

    tk.Label(
        cadre_total,
        text="SOMME TOTALES :",
        font=("Helvetica", 11, "bold"),
        bg="#d35400",
        fg="#ffffff",
        padx=10,
        pady=3,
    ).pack(side="left")
    tk.Label(
        cadre_total,
        text=f"{somme_globale:,.0f} XOF",
        font=("Helvetica", 11, "bold"),
        bg="#27ae60",
        fg="#ffffff",
        padx=15,
        pady=3,
    ).pack(side="left", padx=5)

    cadre_table = tk.Frame(self.root, bg=self.c_card, padx=10, pady=10)
    cadre_table.pack(fill="both", expand=True, padx=15, pady=10)

    colonnes = ("ID", "ACHAT", "NOMBRE", "PRIX UNITAIRE", "TOTALE")
    self.table_nos_depenses = ttk.Treeview(
        cadre_table, columns=colonnes, show="headings"
    )

    for col in colonnes:
      self.table_nos_depenses.heading(col, text=col)
      self.table_nos_depenses.column(
          col, width=50 if col == "ID" else 150, anchor="center"
      )

    self.table_nos_depenses.pack(fill="both", expand=True)
    self.rafraichir_nos_depenses()

  def ajouter_achat_materiel(self):
    achat = self.e_achat.get()
    nbr_str = self.e_nbr.get() or "1"
    pu_str = self.e_pu.get() or "0"

    if not achat:
      messagebox.showwarning("Attention", "La désignation d'achat est requise !")
      return

    try:
      nbr = int(nbr_str)
      pu = float(pu_str)
      tot = nbr * pu
    except ValueError:
      messagebox.showerror(
          "Erreur", "Le Nombre et le Prix Unitaire doivent être numériques."
      )
      return

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        """
            INSERT INTO nos_depenses (achat, nombre, prix_unitaire, total)
            VALUES (?, ?, ?, ?)
        """,
        (achat, nbr, pu, tot),
    )
    conn.commit()
    conn.close()

    messagebox.showinfo("Succès", "Achat enregistré !")
    self.creer_ecran_nos_depenses()

  def supprimer_achat_materiel(self):
    selected_item = self.table_nos_depenses.selection()
    if not selected_item:
      messagebox.showwarning(
          "Attention", "Veuillez sélectionner une ligne dans le tableau !"
      )
      return

    item_values = self.table_nos_depenses.item(selected_item[0], "values")
    id_ligne = item_values[0]

    if messagebox.askyesno("Confirmation", f"Supprimer la ligne ID {id_ligne} ?"):
      conn = sqlite3.connect(BASE_DB)
      cursor = conn.cursor()
      cursor.execute("DELETE FROM nos_depenses WHERE id = ?", (id_ligne,))
      conn.commit()
      conn.close()

      messagebox.showinfo("Succès", "Ligne supprimée !")
      self.rafraichir_nos_depenses()

  def rafraichir_nos_depenses(self):
    for item in self.table_nos_depenses.get_children():
      self.table_nos_depenses.delete(item)

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, achat, nombre, prix_unitaire, total FROM nos_depenses ORDER"
        " BY id DESC"
    )
    for r in cursor.fetchall():
      f_row = (r[0], r[1], r[2], f"{r[3]:,.0f} XOF", f"{r[4]:,.0f} XOF")
      self.table_nos_depenses.insert("", "end", values=f_row)
    conn.close()

  def creer_ecran_recherche(self):
    self.creer_entete_nav("RECHERCHE DYNAMIQUE DANS LA BASE ARTISTES")

    cadre_filtres = tk.LabelFrame(
        self.root,
        text=" Critères de Recherche (Filtre Automatique) ",
        font=("Helvetica", 10, "bold"),
        fg=self.c_accent,
        bg=self.c_card,
    )
    cadre_filtres.pack(fill="x", padx=15, pady=10)

    tk.Label(
        cadre_filtres,
        text="Artiste / Tél / N° Facture :",
        fg=self.c_text,
        bg=self.c_card,
        font=("Helvetica", 9),
    ).grid(row=0, column=0, padx=5, pady=5, sticky="e")
    self.e_search_text = tk.Entry(
        cadre_filtres, font=("Helvetica", 9), width=20
    )
    self.e_search_text.grid(row=0, column=1, padx=5, pady=5)
    self.e_search_text.bind("<KeyRelease>", self.filtrer_base_artistes)

    tk.Label(
        cadre_filtres,
        text="Date (JJ/MM/AAAA) :",
        fg=self.c_text,
        bg=self.c_card,
        font=("Helvetica", 9),
    ).grid(row=0, column=2, padx=5, pady=5, sticky="e")
    self.e_search_date = tk.Entry(
        cadre_filtres, font=("Helvetica", 9), width=15
    )
    self.e_search_date.grid(row=0, column=3, padx=5, pady=5)
    self.e_search_date.bind("<KeyRelease>", self.filtrer_base_artistes)

    tk.Label(
        cadre_filtres,
        text="Style Musical :",
        fg=self.c_text,
        bg=self.c_card,
        font=("Helvetica", 9),
    ).grid(row=0, column=4, padx=5, pady=5, sticky="e")
    styles_list = [""] + list(self.grille_tarifs.keys())
    self.combo_search_style = ttk.Combobox(
        cadre_filtres,
        values=styles_list,
        font=("Helvetica", 9),
        width=18,
        state="readonly",
    )
    self.combo_search_style.grid(row=0, column=5, padx=5, pady=5)
    self.combo_search_style.bind(
        "<<ComboboxSelected>>", self.filtrer_base_artistes
    )

    btn_reset = tk.Button(
        cadre_filtres,
        text=" Réinitialiser ",
        command=self.reinitialiser_recherche,
        bg="#e67e22",
        fg="#ffffff",
        font=("Helvetica", 9, "bold"),
        relief="flat",
    )
    btn_reset.grid(row=0, column=6, padx=10, pady=5)

    cadre_table = tk.Frame(self.root, bg=self.c_card, padx=10, pady=10)
    cadre_table.pack(fill="both", expand=True, padx=15, pady=10)

    colonnes = (
        "Artiste",
        "Date",
        "Titre",
        "Heure",
        "Téléphone",
        "Ville",
        "Type Prod",
        "Style",
        "Tarifs",
        "Versé",
        "Restant",
        "STATUT",
        "N° Facture",
    )
    self.table_search = ttk.Treeview(
        cadre_table, columns=colonnes, show="headings"
    )

    for col in colonnes:
      self.table_search.heading(col, text=col)
      self.table_search.column(col, width=80, anchor="center")

    self.table_search.pack(fill="both", expand=True)
    self.filtrer_base_artistes()

  def filtrer_base_artistes(self, event=None):
    txt = self.e_search_text.get().strip()
    dt = self.e_search_date.get().strip()
    st = self.combo_search_style.get().strip()

    for item in self.table_search.get_children():
      self.table_search.delete(item)

    query = (
        "SELECT nom_artiste, date_enregistrement, titre_chanson, heure,"
        " telephone, ville, type_prod, style_musical, tarifs, somme_versee,"
        " somme_restante, statut, num_facture FROM artistes WHERE 1=1"
    )
    params = []

    if txt:
      query += (
          " AND (nom_artiste LIKE ? OR telephone LIKE ? OR CAST(num_facture AS"
          " TEXT) LIKE ?)"
      )
      params.extend([f"%{txt}%", f"%{txt}%", f"%{txt}%"])

    if dt:
      query += " AND date_enregistrement LIKE ?"
      params.append(f"%{dt}%")

    if st:
      query += " AND style_musical = ?"
      params.append(st)

    query += " ORDER BY id DESC"

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(query, params)

    for row in cursor.fetchall():
      self.table_search.insert("", "end", values=row)

    conn.close()

  def reinitialiser_recherche(self):
    self.e_search_text.delete(0, tk.END)
    self.e_search_date.delete(0, tk.END)
    self.combo_search_style.set("")
    self.filtrer_base_artistes()

  def creer_ecran_facture(self):
    self.creer_entete_nav("GÉNÉRATEUR DE FACTURE / REÇU DE PAIEMENT (A4)")

    cadre_top_saisie = tk.Frame(self.root, bg=self.c_card, padx=10, pady=5)
    cadre_top_saisie.pack(fill="x", padx=15, pady=5)

    tk.Label(
        cadre_top_saisie,
        text="NUMÉRO DE FACTURE :",
        font=("Helvetica", 10, "bold"),
        fg=self.c_text,
        bg=self.c_card,
    ).pack(side="left", padx=5)
    self.e_facture_num = tk.Entry(
        cadre_top_saisie, font=("Helvetica", 10, "bold"), width=10
    )
    self.e_facture_num.pack(side="left", padx=5)
    self.e_facture_num.bind("<KeyRelease>", self.charger_donnees_facture)

    btn_imprimer = tk.Button(
        cadre_top_saisie,
        text=" IMPRIMER (PAGE A4 UNIQUE) ",
        command=self.imprimer_facture,
        bg="#27ae60",
        fg="#ffffff",
        font=("Helvetica", 10, "bold"),
        padx=12,
        relief="flat",
        cursor="hand2",
    )
    btn_imprimer.pack(side="right", padx=10)

    self.scrollable_frame = tk.Frame(self.root, bg="#ffffff")
    self.scrollable_frame.pack(fill="both", expand=True, padx=15, pady=5)

    self.afficher_modele_vide()

  def charger_donnees_facture(self, event=None):
    num_str = self.e_facture_num.get().strip()

    for w in self.scrollable_frame.winfo_children():
      w.destroy()

    if not num_str:
      self.afficher_modele_vide()
      return

    conn = sqlite3.connect(BASE_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nom_artiste, date_enregistrement, titre_chanson, heure,"
        " telephone, ville, type_prod, style_musical, tarifs, somme_versee,"
        " somme_restante, statut, num_facture FROM artistes WHERE"
        " CAST(num_facture AS TEXT) = ?",
        (num_str,),
    )
    row = cursor.fetchone()
    conn.close()

    if row:
      self.construire_fiche_double(row)
    else:
      tk.Label(
          self.scrollable_frame,
          text=f"Aucune facture trouvée pour le N° {num_str}",
          font=("Helvetica", 11, "italic"),
          fg="red",
          bg="#ffffff",
      ).pack(pady=20)

  def afficher_modele_vide(self):
    empty_row = (
        "---",
        "---",
        "---",
        "---",
        "---",
        "---",
        "---",
        "---",
        0,
        0,
        0,
        "---",
        "---",
    )
    self.construire_fiche_double(empty_row)

  def construire_fiche_double(self, data):
    self.creer_bloc_recu(data, "EXEMPLAIRE CLIENT")

    f_sep = tk.Frame(self.scrollable_frame, bg="#ffffff")
    f_sep.pack(fill="x", pady=4)
    tk.Label(
        f_sep,
        text=(
            "- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -"
            " - - - - - - LIGNE DE COUPE - - - - - - - - - - - - - - - - - - - - - -"
            " - - - - - - - - - - - - -"
        ),
        font=("Helvetica", 7, "italic"),
        fg="#7f8c8d",
        bg="#ffffff",
    ).pack()

    self.creer_bloc_recu(data, "EXEMPLAIRE STUDIO")

  def creer_bloc_recu(self, d, tampon_titre):
    f_recu = tk.Frame(
        self.scrollable_frame,
        bg="#ffffff",
        highlightbackground="#000000",
        highlightthickness=1,
        padx=8,
        pady=3,
    )
    f_recu.pack(fill="x", padx=5, pady=2)

    f_top = tk.Frame(f_recu, bg="#ffffff")
    f_top.pack(fill="x")

    tk.Label(
        f_top,
        text=f"BM PROD - REÇU DE PAIEMENT ({tampon_titre})",
        font=("Helvetica", 9, "bold"),
        fg="#c0392b",
        bg="#ffffff",
    ).pack(side="left")
    tk.Label(
        f_top,
        text=f"N° FACTURE : {d[12]}",
        font=("Helvetica", 9, "bold"),
        bg="#f1c40f",
        fg="#000000",
        padx=6,
    ).pack(side="right")

    f_mid = tk.Frame(f_recu, bg="#ffffff")
    f_mid.pack(fill="x", pady=2)

    f_g = tk.Frame(f_mid, bg="#ffffff")
    f_g.pack(side="left", fill="both", expand=True)

    details_g = [
        ("Téléphone :", d[4]),
        ("Nom d'Artiste :", d[0]),
        ("Date session :", d[1]),
        ("Titre chanson :", d[2]),
        ("Heure d'entrée :", d[3]),
        ("Ville :", d[5]),
    ]
    for lbl, val in details_g:
      f_row = tk.Frame(f_g, bg="#ffffff")
      f_row.pack(fill="x", pady=0)
      tk.Label(
          f_row,
          text=lbl,
          font=("Helvetica", 7, "bold"),
          width=15,
          anchor="w",
          bg="#ffffff",
      ).pack(side="left")
      tk.Label(
          f_row,
          text=val,
          font=("Helvetica", 7),
          relief="solid",
          bd=1,
          width=22,
          anchor="w",
          bg="#f9f9f9",
      ).pack(side="left")

    f_d = tk.Frame(f_mid, bg="#ffffff")
    f_d.pack(side="left", fill="both", expand=True, padx=5)

    try:
      t_val = f"{float(d[8]):,.0f} XOF"
      v_val = f"{float(d[9]):,.0f} XOF"
      r_val = f"{float(d[10]):,.0f} FCFA"
    except (ValueError, TypeError):
      t_val, v_val, r_val = "0 XOF", "0 XOF", "0 FCFA"

    details_d = [
        ("Tarif Total :", t_val),
        ("Somme Versée :", v_val),
        ("Statut :", d[11]),
        ("Restant à payer :", r_val),
        ("Style musical :", d[7]),
        ("Genre musical :", d[6]),
    ]
    for lbl, val in details_d:
      f_row = tk.Frame(f_d, bg="#ffffff")
      f_row.pack(fill="x", pady=0)
      tk.Label(
          f_row,
          text=lbl,
          font=("Helvetica", 7, "bold"),
          width=15,
          anchor="w",
          bg="#ffffff",
      ).pack(side="left")
      tk.Label(
          f_row,
          text=val,
          font=("Helvetica", 7),
          relief="solid",
          bd=1,
          width=18,
          anchor="w",
          bg="#f9f9f9",
      ).pack(side="left")

    f_leg = tk.Frame(f_recu, bg="#ffffff")
    f_leg.pack(fill="x", pady=2)
    tk.Label(
        f_leg,
        text=(
            "BIG S MEDIA PRODUCTION | NIF: 1495556/P | RCCM:"
            " NE-01-2025-A-03906//22/09/2025 | LICENCE: Entrepreneur Culturel/C"
            " 0207"
        ),
        font=("Helvetica", 6, "bold"),
        bg="#ffffff",
    ).pack()
    tk.Label(
        f_leg,
        text="Tél: +227 96 55 81 93 | Email: sanistomoussa@gmail.com",
        font=("Helvetica", 6),
        bg="#ffffff",
    ).pack()

  def imprimer_facture(self):
    num_str = self.e_facture_num.get().strip()
    if not num_str:
      messagebox.showwarning(
          "Attention", "Veuillez entrer un numéro de facture valide !"
      )
      return
    messagebox.showinfo(
        "Impression Directe A4",
        f"Envoi du reçu N° {num_str} vers votre imprimante...",
    )
if __name__ == "__main__":
  initialiser_base()

  try:
    import importer_tous_les_csv

    importer_tous_les_csv.importer_tout()
  except ImportError:
    # Si le fichier d'importation n'existe pas, on l'ignore silencieusement pour ne pas bloquer le logiciel
    pass
  except Exception:
    pass

  root = tk.Tk()
  app = ApplicationBMProd(root)
  root.mainloop()