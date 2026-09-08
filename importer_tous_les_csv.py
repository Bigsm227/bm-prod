import csv
import os
import sqlite3

BASE_DB = "bm_prod.db"


def net_m(val):
  if not val:
    return 0.0
  v = (
      val.replace("FCFA", "")
      .replace("XOF", "")
      .replace("F", "")
      .replace('"', "")
      .replace(" ", "")
      .replace("\xa0", "")
      .replace(",", ".")
      .strip()
  )
  try:
    return float(v)
  except:
    return 0.0


def importer_tout():
  conn = sqlite3.connect(BASE_DB)
  cursor = conn.cursor()

  # 1. IMPORTation ARTISTES (artistes.csv)
  if os.path.exists("artistes.csv"):
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
    cursor.execute("DELETE FROM artistes")

    with open(
        "artistes.csv", mode="r", encoding="utf-8-sig", errors="ignore"
    ) as f:
      reader = csv.reader(f, delimiter=",")
      next(reader, None)
      next(reader, None)

      compteur = 0
      for r in reader:
        if not r or len(r) < 3:
          continue
        nom = r[0].strip() if len(r) > 0 else ""
        dt = r[1].strip() if len(r) > 1 else ""
        titre = r[2].strip() if len(r) > 2 else ""
        hr = r[3].strip() if len(r) > 3 else ""
        offset = 1 if (len(r) > 4 and r[4].strip() == "") else 0

        tel = r[4 + offset].strip() if len(r) > (4 + offset) else ""
        ville = r[5 + offset].strip() if len(r) > (5 + offset) else ""
        t_prod = r[6 + offset].strip() if len(r) > (6 + offset) else ""
        st_mus = r[7 + offset].strip() if len(r) > (7 + offset) else ""

        tar = net_m(r[8 + offset]) if len(r) > (8 + offset) else 0.0
        vers = net_m(r[9 + offset]) if len(r) > (9 + offset) else 0.0
        rest = tar - vers
        statut = "PAYER" if rest <= 0 else "NON PAYER"

        num_f = None
        if len(r) > 0:
          derniere_col = r[-1].strip()
          if derniere_col.isdigit():
            num_f = int(derniere_col)
        if not num_f:
          num_f = compteur + 1

        cursor.execute(
            """
                    INSERT INTO artistes (nom_artiste, date_enregistrement, titre_chanson, heure, telephone, ville, type_prod, style_musical, tarifs, somme_versee, somme_restante, statut, num_facture)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                nom,
                dt,
                titre,
                hr,
                tel,
                ville,
                t_prod,
                st_mus,
                tar,
                vers,
                rest,
                statut,
                num_f,
            ),
        )
        compteur += 1

  # 2. IMPORTATION AVANCES (avances.csv - Gestion du décalage de 3 virgules)
  if os.path.exists("avances.csv"):
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
    cursor.execute("DELETE FROM avances")

    with open(
        "avances.csv", mode="r", encoding="utf-8-sig", errors="ignore"
    ) as f:
      reader = csv.reader(f, delimiter=",")
      for r in reader:
        # Nettoyer les éléments vides au début de la ligne
        vrais_elements = [item.strip() for item in r if item.strip() != ""]
        if not vrais_elements or "Noms D'Artiste" in vrais_elements[0]:
          continue

        nom = vrais_elements[0] if len(vrais_elements) > 0 else ""
        num = vrais_elements[1] if len(vrais_elements) > 1 else ""
        dt_v = vrais_elements[2] if len(vrais_elements) > 2 else ""
        som = net_m(vrais_elements[3]) if len(vrais_elements) > 3 else 0.0
        moy = vrais_elements[4] if len(vrais_elements) > 4 else ""
        dt_p = vrais_elements[5] if len(vrais_elements) > 5 else ""

        cursor.execute(
            """
                    INSERT INTO avances (nom_artiste, numero, date_versement, somme_versee, moyen_versement, date_prevue)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
            (nom, num, dt_v, som, moy, dt_p),
        )

  # 3. IMPORTATION ACHATS MATÉRIEL (Depenses.csv)
  if os.path.exists("Depenses.csv"):
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS nos_depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                achat TEXT NOT NULL,
                nombre INTEGER DEFAULT 1,
                prix_unitaire REAL DEFAULT 0,
                total REAL DEFAULT 0
            )
        """)
    cursor.execute("DELETE FROM nos_depenses")

    with open(
        "Depenses.csv", mode="r", encoding="utf-8-sig", errors="ignore"
    ) as f:
      reader = csv.reader(f, delimiter=",")
      next(reader, None)  # Ignorer en-tête

      for r in reader:
        if not r or len(r) < 2:
          continue
        achat = r[0].strip() if len(r) > 0 else ""
        if not achat or "ACHAT" in achat:
          continue
        try:
          nbr = int(r[1].strip()) if len(r) > 1 else 1
        except:
          nbr = 1
        pu = net_m(r[2]) if len(r) > 2 else 0.0
        tot = nbr * pu

        cursor.execute(
            """
                    INSERT INTO nos_depenses (achat, nombre, prix_unitaire, total)
                    VALUES (?, ?, ?, ?)
                """,
            (achat, nbr, pu, tot),
        )

  # 4. IMPORTATION DÉPENSES QUOTIDIENNES (quotidiens.csv - Gestion du décalage massif de virgules)
  if os.path.exists("quotidiens.csv"):
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS depenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date_depense TEXT,
                categorie TEXT,
                description TEXT,
                montant REAL DEFAULT 0
            )
        """)
    cursor.execute("DELETE FROM depenses")

    with open(
        "quotidiens.csv", mode="r", encoding="utf-8-sig", errors="ignore"
    ) as f:
      reader = csv.reader(f, delimiter=",")
      for r in reader:
        vrais_elements = [item.strip() for item in r if item.strip() != ""]
        if not vrais_elements or "Date" in vrais_elements[0]:
          continue

        dt_dp = vrais_elements[0] if len(vrais_elements) > 0 else ""
        desc = vrais_elements[1] if len(vrais_elements) > 1 else ""
        mnt = net_m(vrais_elements[2]) if len(vrais_elements) > 2 else 0.0
        cat = vrais_elements[3] if len(vrais_elements) > 3 else "Autre"

        cursor.execute(
            """
                    INSERT INTO depenses (date_depense, categorie, description, montant)
                    VALUES (?, ?, ?, ?)
                """,
            (dt_dp, cat, desc, mnt),
        )

  conn.commit()
  conn.close()


def lire_et_importer_artistes():
  importer_tout()


if __name__ == "__main__":
  importer_tout()