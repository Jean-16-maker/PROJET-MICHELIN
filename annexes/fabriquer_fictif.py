# -*- coding: utf-8 -*-
"""DONNÉES FICTIVES. Fabrique une base simulée : ce qu'aurait donné un test réussi.

Le professeur a proposé, puisque notre vrai test n'a pas montré d'effet, de présenter aussi le résultat
qu'on aurait souhaité, à partir de données fictives. Ce script les fabrique, avec des réglages visibles
ci-dessous : rien n'est caché, et chaque ligne porte un identifiant « FICTIF- ».

Ce que la simulation suppose (ce sont des hypothèses, pas des mesures) :
  - un test mieux conçu : 240 répondants (120 par version), comme le calcul de puissance le demande
    pour un effet de 15 à 20 points, et une question de contrôle de manipulation (manip_km) ;
  - un échantillon plus proche des acheteurs de pneus : âge médian autour de 40 ans ;
  - un vrai effet de la durée de vie : annoncer 50 000 km au lieu de 40 000 km fait passer la part
    qui choisit Michelin d'environ 47 % à environ 67 % ;
  - les mêmes mécanismes que dans nos vraies données : la fidélité à Michelin fait choisir Michelin,
    la conscience du prix pousse vers le Hankook.

Mêmes colonnes que l'export réel, plus manip_km. Lancer :  python fabriquer_fictif.py
Produit : donnees/reponses-FICTIVES.csv
"""
import os

import numpy as np
import pandas as pd

GRAINE = 2026                 # même graine = mêmes données à chaque lancement
N = 240                       # 120 répondants par version
EFFET_DUREE = 0.85            # effet de la version B (50 000 km) sur le logit du choix de Michelin
CONSTANTE = -0.10             # niveau de base du choix de Michelin (version A, profil moyen)
EFFET_FIDELITE = 0.80         # effet d'un écart-type de fidélité sur le logit
EFFET_PRIX = -0.45            # effet d'un écart-type de conscience du prix sur le logit
MANIP_A, MANIP_B = 3.5, 5.4   # « Le Michelin m'a semblé durer plus longtemps que le Hankook », moyennes sur 7

rng = np.random.default_rng(GRAINE)
version = rng.permutation(np.repeat(["A", "B"], N // 2))
B = (version == "B").astype(int)

# trois traits latents : fidélité, qualité perçue (liée à la fidélité), conscience du prix
F = rng.normal(0, 1, N)
Q = 0.35 * F + rng.normal(0, 0.94, N)
P = -0.20 * F + rng.normal(0, 0.98, N)


def likert(latent, centre, pente=0.95, bruit=0.65):
    return np.clip(np.rint(centre + pente * latent + rng.normal(0, bruit, N)), 1, 5).astype(int)


lo1, lo2, lo3 = likert(F, 2.9), likert(F, 3.1), likert(F, 2.7)
ql2, ql3 = likert(Q, 3.9, 0.95), likert(Q, 4.0, 0.95)
pr1, pr2, pr3 = likert(P, 3.6), likert(P, 2.9), likert(P, 3.8)

age = np.clip(np.rint(rng.lognormal(np.log(40), 0.35, N)), 18, 80).astype(int)
km = np.clip(np.rint(rng.normal(14000, 6000, N) / 1000) * 1000, 1000, 50000).astype(int)
duree = np.clip(np.rint(rng.lognormal(np.log(85), 0.45, N)), 30, 600).astype(int)

logit = CONSTANTE + EFFET_DUREE * B + EFFET_FIDELITE * F + EFFET_PRIX * P
choix = np.where(rng.random(N) < 1 / (1 + np.exp(-logit)), "michelin", "hankook")
manip = np.clip(np.rint(np.where(B == 1, MANIP_B, MANIP_A) + rng.normal(0, 1.2, N)), 1, 7).astype(int)


def oui_non(p):
    return np.where(rng.random(N) < p, "oui", "non")


debut = pd.Timestamp("2026-10-12 09:00:00")
d = pd.DataFrame({
    "horodatage": [(debut + pd.Timedelta(minutes=int(m))).strftime("%Y-%m-%d %H:%M:%S") for m in np.sort(rng.integers(0, 9 * 24 * 60, N))],
    "id": [f"FICTIF-{i:03d}" for i in range(1, N + 1)],
    "test": 0, "version": version, "duree_s": duree, "consentement": "oui", "age": age, "voiture": "oui", "cible": 1,
    "km_an": km, "choix_pneu": choix,
    "likert_lo1": lo1, "likert_lo2": lo2, "likert_lo3": lo3, "likert_ql2": ql2, "likert_ql3": ql3,
    "likert_pr1": pr1, "likert_pr2": pr2, "likert_pr3": pr3,
    "achat_garage": oui_non(0.5), "achat_specialiste": oui_non(0.4), "achat_centre_auto": oui_non(0.5),
    "achat_internet": oui_non(0.3), "achat_reparateur_rapide": oui_non(0.25),
    "manip_km": manip,
})
chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "donnees", "reponses-FICTIVES.csv")
d.to_csv(chemin, sep=";", index=False)
print(f"{N} réponses FICTIVES écrites dans donnees/reponses-FICTIVES.csv")
print(d.groupby("version").choix_pneu.apply(lambda s: f"{(s == 'michelin').mean():.0%} choisissent Michelin").to_string())
