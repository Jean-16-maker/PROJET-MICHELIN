# -*- coding: utf-8 -*-
"""DONNÉES FICTIVES. Fabrique 100 réponses simulées au questionnaire de la vague 2 (avec contrôle de manipulation).

Même principe que fabriquer_fictif.py : des réglages visibles, et chaque ligne marquée comme fictive
(identifiant « FICTIF-V2- », colonne source = fictif). Trois profils de répondants : étudiants, actifs, retraités.

Ce que la simulation suppose (hypothèses, pas des mesures) :
  - un effet de la durée de vie : annoncer 50 000 km fait choisir Michelin plus souvent ;
  - la version B est perçue comme plus durable (question de contrôle manip_km, de 1 à 7) ;
  - la fidélité à Michelin fait choisir Michelin, la conscience du prix pousse vers le Hankook ;
  - les retraités sont plus fidèles à Michelin, les étudiants plus attentifs au prix et roulent moins.

Lancer :  python fabriquer_vague2_fictive.py
Produit : donnees/reponses-FICTIVES-vague2.csv (pour l'analyse)
          ../site/serveur/fictif/reponses-FICTIVES-vague2.jsonl (onglet « Vague 2 fictive » de export.php)
"""
import json
import os

import numpy as np
import pandas as pd

GRAINE = 2211                 # même graine = mêmes données à chaque lancement
N = 100                       # 50 répondants par version
EFFET_DUREE = 0.95            # effet de la version B (50 000 km) sur le logit du choix de Michelin
CONSTANTE = -0.15             # niveau de base du choix de Michelin (version A, profil moyen)
EFFET_FIDELITE = 0.80         # effet d'un écart-type de fidélité sur le logit
EFFET_PRIX = -0.45            # effet d'un écart-type de conscience du prix sur le logit
MANIP_A, MANIP_B = 3.5, 5.4   # « Le Michelin m'a semblé durer plus longtemps que le Hankook », moyennes sur 7

# profil : part de l'échantillon, âge (moyenne, écart-type, bornes), km par an, décalage de fidélité et de prix
PROFILS = {
    "etudiant": dict(part=0.30, age=(22, 2.5, 18, 27), km=(9000, 4000), fid=-0.30, prix=0.40),
    "actif":    dict(part=0.50, age=(42, 10, 25, 64), km=(16000, 6000), fid=0.00, prix=0.00),
    "retraite": dict(part=0.20, age=(70, 5, 62, 85), km=(9000, 4000), fid=0.45, prix=-0.10),
}

rng = np.random.default_rng(GRAINE)
version = rng.permutation(np.repeat(["A", "B"], N // 2))
B = (version == "B").astype(int)
profil = rng.choice(list(PROFILS), size=N, p=[p["part"] for p in PROFILS.values()])
cfg = [PROFILS[p] for p in profil]

F = rng.normal(0, 1, N) + np.array([c["fid"] for c in cfg])
Q = 0.35 * F + rng.normal(0, 0.94, N)
P = -0.20 * F + rng.normal(0, 0.98, N) + np.array([c["prix"] for c in cfg])


def likert(latent, centre, pente=0.95, bruit=0.65):
    return np.clip(np.rint(centre + pente * latent + rng.normal(0, bruit, N)), 1, 5).astype(int)


lo1, lo2, lo3 = likert(F, 2.9), likert(F, 3.1), likert(F, 2.7)
ql2, ql3 = likert(Q, 3.9), likert(Q, 4.0)
pr1, pr2, pr3 = likert(P, 3.6), likert(P, 2.9), likert(P, 3.8)

age = np.array([int(np.clip(np.rint(rng.normal(c["age"][0], c["age"][1])), c["age"][2], c["age"][3])) for c in cfg])
km = np.array([int(np.clip(np.rint(rng.normal(*c["km"]) / 1000) * 1000, 1000, 50000)) for c in cfg])
duree = np.clip(np.rint(rng.lognormal(np.log(75), 0.4, N)), 30, 400).astype(int)

logit = CONSTANTE + EFFET_DUREE * B + EFFET_FIDELITE * F + EFFET_PRIX * P
choix = np.where(rng.random(N) < 1 / (1 + np.exp(-logit)), "michelin", "hankook")
manip = np.clip(np.rint(np.where(B == 1, MANIP_B, MANIP_A) + rng.normal(0, 1.2, N)), 1, 7).astype(int)


def oui_non(p):
    return np.where(rng.random(N) < p, "oui", "non")


d = pd.DataFrame({
    "horodatage": pd.Timestamp("2026-11-02 12:00:00").strftime("%Y-%m-%d %H:%M:%S"),  # date de fabrication
    "id": [f"FICTIF-V2-{i:03d}" for i in range(1, N + 1)],
    "test": 0, "version": version, "duree_s": duree, "consentement": "oui", "age": age, "voiture": "oui", "cible": 1,
    "km_an": km, "choix_pneu": choix,
    "likert_lo1": lo1, "likert_lo2": lo2, "likert_lo3": lo3, "likert_ql2": ql2, "likert_ql3": ql3,
    "likert_pr1": pr1, "likert_pr2": pr2, "likert_pr3": pr3,
    "achat_garage": oui_non(0.5), "achat_specialiste": oui_non(0.4), "achat_centre_auto": oui_non(0.5),
    "achat_internet": oui_non(0.3), "achat_reparateur_rapide": oui_non(0.25),
    "manip_km": manip, "vague": 2, "source": "fictif", "profil": profil,
})

ici = os.path.dirname(os.path.abspath(__file__))
d.to_csv(os.path.join(ici, "donnees", "reponses-FICTIVES-vague2.csv"), sep=";", index=False)
dossier_site = os.path.join(ici, "..", "site", "serveur", "fictif")
os.makedirs(dossier_site, exist_ok=True)
with open(os.path.join(dossier_site, "reponses-FICTIVES-vague2.jsonl"), "w", encoding="utf-8") as f:
    for r in d.to_dict("records"):
        f.write(json.dumps({k: (v.item() if hasattr(v, "item") else v) for k, v in r.items()}, ensure_ascii=False) + "\n")

print(f"{N} réponses FICTIVES (vague 2) écrites")
print(d.groupby("version").agg(n=("id", "size"), michelin=("choix_pneu", lambda s: f"{(s == 'michelin').mean():.0%}"), manip=("manip_km", "mean")).to_string())
print(d.profil.value_counts().to_string())
