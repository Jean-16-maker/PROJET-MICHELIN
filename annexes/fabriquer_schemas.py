# -*- coding: utf-8 -*-
"""Fabrique les schémas du site (SVG) à partir des réponses du questionnaire, et les place dans les pages.

Principe : chaque schéma est un dessin SVG écrit par une fonction Python. Les chiffres ne sont jamais tapés à la main :
ils sont recalculés ici à partir des sorties de l'analyse (squelette analyse-projet-prix du cours d'Analyse de données).
Dans les pages HTML, chaque schéma occupe la place entre deux balises :
    <!-- schema:choix -->  ...  <!-- /schema:choix -->
Le script remplace ce qu'il y a entre les deux ; le texte autour, écrit par le groupe, ne bouge pas.

Lancer (depuis le dossier site/, avec l'environnement Python de l'analyse) :
    ../analyse-projet-prix/.venv/bin/python annexes/fabriquer_schemas.py

Les réponses individuelles restent sur l'ordinateur du groupe : seules des moyennes et des parts arrivent dans les pages.
"""
import json
import re
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_confint

SITE = Path(__file__).resolve().parents[1]
ANALYSE = SITE.parent / "analyse-projet-prix" / "sorties" / "vague2"

# ---- les couleurs : celles du site ; A et B validées (contraste, daltonisme) ---------------------------------
A_, B_ = "#A86B00", "#27509B"            # version A (ocre), version B (bleu Michelin)
ENCRE, GRIS, TRAIT, CIEL = "#10203F", "#566179", "#D5DDEC", "#EAF0FA"
OK, ALERTE, NEUTRE = "#1B7F4B", "#C2410C", "#8A94A8"
BLEU_FONCE, JAUNE = "#0F2A5C", "#FCE500"
# échelle d'accord de 1 à 7 : divergente, violet (pas d'accord) / gris (neutre) / sarcelle (d'accord)
ACCORD = ["#5E3C99", "#8C6BB1", "#BFAEDB", "#C9CED8", "#9FD3C7", "#3FA392", "#157A6E"]


# ---- les nombres à la française ------------------------------------------------------------------------------
def fr(x, d=2):
    return f"{x:,.{d}f}".replace(",", " ").replace(".", ",").replace("-", "−")


def pc(x, d=0):
    return f"{fr(100 * x, d)} %"


def pval(p):
    return "p < 0,001" if p < 0.001 else f"p = {fr(p, 3)}"


# =================================================================================================================
# 1. Les calculs
# =================================================================================================================
d = pd.read_csv(ANALYSE / "donnees_propres.csv")
comp = json.loads((ANALYSE / "complements.json").read_text(encoding="utf-8"))
d["m"] = (d.choix_pneu == "michelin").astype(int)
d["B"] = (d.version == "B").astype(int)
d["fid"] = d[["likert_lo1", "likert_lo2", "likert_lo3"]].mean(axis=1)
d["qual"] = d[["likert_ql2", "likert_ql3"]].mean(axis=1)
d["prix"] = d[["likert_pr1", "likert_pr3"]].mean(axis=1)
d["age10"] = d.age / 10
d["garage"] = (d.achat_garage == "oui").astype(int)
d["gros"] = (d.km_an > 15000).astype(int)
AGES = ["18-24", "25-34", "35-49", "50 et +"]
KMS = ["moins de 10 000", "10 000-20 000", "plus de 20 000"]
d["tage"] = pd.cut(d.age, [0, 24, 34, 49, 200], labels=AGES)
d["tkm"] = pd.cut(d.km_an, [-1, 9999, 20000, 1e9], labels=KMS)
A, B = d[d.B == 0], d[d.B == 1]
nA, nB, N = len(A), len(B), len(d)
kA, kB = int(A.m.sum()), int(B.m.sum())
pA, pB = kA / nA, kB / nB
icA, icB = proportion_confint(kA, nA, method="wilson"), proportion_confint(kB, nB, method="wilson")
tab = pd.crosstab(d.version, d.m)
chi2, p_chi2, _, attendus = stats.chi2_contingency(tab, correction=False)
V = float(np.sqrt(chi2 / N))
ecart = pB - pA
se = np.sqrt(pA * (1 - pA) / nA + pB * (1 - pB) / nB)
ic_ecart = (ecart - 1.96 * se, ecart + 1.96 * se)
h = 2 * np.arcsin(np.sqrt(pB)) - 2 * np.arcsin(np.sqrt(pA))
POW = NormalIndPower()
puissance = POW.power(h, nobs1=nA, alpha=0.05, ratio=nB / nA)
n80 = int(np.ceil(POW.solve_power(effect_size=h, alpha=0.05, power=0.8)))
man = comp["manipulation"]


def logit(f, donnees=d):
    return smf.logit(f, donnees).fit(disp=False)


reponses = ["version", "age", "km_an", "choix_pneu", "manip_km"] + [c for c in d.columns if c.startswith(("likert_", "achat_"))]
repetee = d.sort_values("horodatage").duplicated(subset=reponses, keep="first").reindex(d.index)


def p_chi(donnees):
    return stats.chi2_contingency(pd.crosstab(donnees.version, donnees.m), correction=False)[1]


complet = logit("m ~ B + fid + qual + prix + age10")
ROBUSTESSE = [
    ("Chi² de Pearson (le test de référence)", p_chi2),
    ("Chi² avec la correction de Yates", stats.chi2_contingency(tab, correction=True)[1]),
    ("Test exact de Fisher", stats.fisher_exact(tab.values)[1]),
    ("Régression logistique, la version seule", logit("m ~ B").pvalues["B"]),
    ("Régression logistique, avec le profil", complet.pvalues["B"]),
    ("Idem, avec les km et l'achat chez un garagiste", logit("m ~ B + fid + qual + prix + age10 + km_an + garage").pvalues["B"]),
    ("Sans les 4 réponses en double", p_chi(d[~repetee])),
]
ci = complet.conf_int()
FOREST = [(lib, float(np.exp(complet.params[k])), float(np.exp(ci.loc[k, 0])), float(np.exp(ci.loc[k, 1])), float(complet.pvalues[k]))
          for k, lib in [("B", "Version B (50 000 km)"), ("fid", "Fidélité (par point)"), ("qual", "Qualité perçue (par point)"),
                         ("prix", "Conscience du prix (par point)"), ("age10", "Âge (par tranche de 10 ans)")]]
ols_a = smf.ols("manip_km ~ B", d).fit()
med = logit("m ~ B + manip_km")
MED = {"a": ols_a.params["B"], "pa": ols_a.pvalues["B"], "b": med.params["manip_km"], "pb": med.pvalues["manip_km"],
       "c": med.params["B"], "pc": med.pvalues["B"], "ab": comp["mediation"]["ab"], "bas": comp["mediation"]["bas"], "haut": comp["mediation"]["haut"]}
p_inter_age = logit("m ~ B * age").pvalues["B:age"]
p_inter_gros = logit("m ~ B * gros").pvalues["B:gros"]
POIDS = comp["mesure_complete"]["poids"]
SEUIL_EFFET = 123614 / 200000 * ecart * 100          # effet (en points) au point mort de la campagne


def gain(effet_points):
    return 200000 * effet_points / (ecart * 100) * 20.22 - 2_500_000


# =================================================================================================================
# 2. Les briques du dessin
# =================================================================================================================
def T(x, y, s, taille=12, couleur=ENCRE, ancre="start", gras=False, classe=""):
    g = ' font-weight="700"' if gras else ""
    c = f' class="{classe}"' if classe else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{taille}" fill="{couleur}" text-anchor="{ancre}"{g}{c}>{escape(s)}</text>'


def L(x1, y1, x2, y2, couleur=TRAIT, ep=1, tirets=False):
    t = ' stroke-dasharray="5 4"' if tirets else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{couleur}" stroke-width="{ep}"{t}/>'


def barre_v(x, y_base, hauteur, largeur, couleur, info):
    """Une colonne posée sur la ligne de base, bout arrondi de 4 px en haut, carré en bas."""
    r = min(4, hauteur / 2, largeur / 2)
    y = y_base - hauteur
    chemin = (f"M{x:.1f},{y_base:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} H{x + largeur - r:.1f} "
              f"Q{x + largeur:.1f},{y:.1f} {x + largeur:.1f},{y + r:.1f} V{y_base:.1f} Z")
    return f'<path d="{chemin}" fill="{couleur}" tabindex="0"><title>{escape(info)}</title></path>'


def barre_h(x0, y, longueur, epaisseur, couleur, info):
    """Une barre horizontale partant de x0, bout arrondi de 4 px à droite."""
    r = min(4, abs(longueur) / 2, epaisseur / 2)
    x1 = x0 + longueur
    chemin = (f"M{x0:.1f},{y:.1f} H{x1 - r:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f} V{y + epaisseur - r:.1f} "
              f"Q{x1:.1f},{y + epaisseur:.1f} {x1 - r:.1f},{y + epaisseur:.1f} H{x0:.1f} Z")
    return f'<path d="{chemin}" fill="{couleur}" tabindex="0"><title>{escape(info)}</title></path>'


def point(x, y, couleur, info, r=5):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{couleur}" stroke="#fff" stroke-width="2" tabindex="0">'
            f'<title>{escape(info)}</title></circle>')


def boite(x, y, l, h_, lignes, fond="#fff", bord=BLEU_FONCE, texte=ENCRE, taille=12.5, gras_premiere=True):
    out = [f'<rect x="{x}" y="{y}" width="{l}" height="{h_}" rx="10" fill="{fond}" stroke="{bord}" stroke-width="1.5"/>']
    y0 = y + h_ / 2 - (len(lignes) - 1) * (taille + 3) / 2 + taille * 0.35
    for i, s in enumerate(lignes):
        out.append(T(x + l / 2, y0 + i * (taille + 3), s, taille, texte, "middle", gras=(i == 0 and gras_premiere)))
    return "".join(out)


def fleche(x1, y1, x2, y2, couleur=BLEU_FONCE, ep=2, tirets=False, id_="f"):
    t = ' stroke-dasharray="6 5"' if tirets else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{couleur}" stroke-width="{ep}"{t} '
            f'marker-end="url(#{id_})"/>')


def defs_fleches(nom, couleurs):
    return "<defs>" + "".join(
        f'<marker id="{nom}-{i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for i, c in enumerate(couleurs)) + "</defs>"


def svg(nom, largeur, hauteur, titre, description, corps):
    return (f'<svg viewBox="0 0 {largeur} {hauteur}" role="img" aria-labelledby="{nom}-t {nom}-d">'
            f'<title id="{nom}-t">{escape(titre)}</title><desc id="{nom}-d">{escape(description)}</desc>{corps}</svg>')


def legende(entrees):
    return '<div class="leg">' + "".join(f'<span style="--c:{c}">{escape(l)}</span>' for l, c in entrees) + "</div>"


def tableau(entetes, lignes):
    th = "".join(f"<th>{escape(x)}</th>" for x in entetes)
    tr = "".join("<tr>" + "".join(f"<td>{escape(str(x))}</td>" for x in l) + "</tr>" for l in lignes)
    return (f'<details class="chiffres-fig"><summary>Voir les chiffres du schéma</summary>'
            f'<div class="tableau"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div></details>')


def figure(num, titre, contenu, leg=None, table=None, large=False):
    c = " large" if large else ""
    return (f'<figure class="fig{c}"><figcaption><b>Schéma {num}</b> · {escape(titre)}</figcaption>'
            f'{legende(leg) if leg else ""}{contenu}{table or ""}</figure>')


# =================================================================================================================
# 3. Les schémas
# =================================================================================================================
SCHEMAS = {}


def pastille(x, y, texte_, couleur):
    """Une étiquette sur fond blanc, posée sur une flèche : lisible même quand elle croise un trait."""
    l = 6.3 * len(texte_) + 12
    return (f'<rect x="{x - l / 2:.1f}" y="{y - 9:.1f}" width="{l:.1f}" height="18" rx="9" fill="#fff" stroke="{couleur}" stroke-width="1"/>'
            + T(x, y + 4, texte_, 11, couleur, "middle", gras=True))


def modele(nom, apres):
    """Le modèle des hypothèses : avant le test (toutes à vérifier) ou après (validées / non démontrées / rejetée)."""
    st = {"H1": True, "H2": True, "H3": False, "H4": False, "H5": True, "H6": False, "H7": False, "H8": False}
    idx = lambda hh: 0 if not apres else (1 if st[hh] else 2)
    coul = lambda hh: [BLEU_FONCE, OK, NEUTRE][idx(hh)]
    tir = lambda hh: apres and not st[hh]
    f = lambda hh: f"{nom}-{idx(hh)}"
    def etiq(hh, avant):
        if not apres:
            return avant
        return f"{hh} · " + ("validée" if st[hh] else ("rejetée" if hh == "H3" else "non démontrée"))
    c = [defs_fleches(nom, [BLEU_FONCE, OK, NEUTRE])]
    c.append(boite(20, 150, 150, 64, ["Version B", "Michelin annoncé", "à 50 000 km"], fond=CIEL))
    c.append(boite(225, 24, 170, 56, ["Durée perçue", "question de contrôle, 1 à 7"]))
    c.append(boite(470, 24, 130, 56, ["Marque seule", "version A : plus", "de 50 % ?"], taille=11.5,
                   bord=coul("H3"), fond="#fff" if not apres else "#F1F3F6"))
    c.append(boite(450, 150, 150, 64, ["Choix du Michelin", "à 97,90 € plutôt que", "le Hankook à 81,99 €"], fond=JAUNE))
    c.append(boite(200, 210, 130, 38, ["Kilométrage annuel"], taille=12))
    c.append(boite(225, 330, 115, 50, ["Fidélité", "à Michelin"]))
    c.append(boite(352, 330, 115, 50, ["Qualité", "perçue"]))
    c.append(boite(479, 330, 121, 50, ["Conscience", "du prix"]))
    fl = [("H1", 170, 168, 225, 72, 2), ("H4", 395, 72, 465, 148, 2), ("H2", 170, 182, 448, 182, 3), ("H3", 560, 80, 560, 148, 2),
          ("H7", 265, 210, 265, 186, 2), ("H5", 282, 330, 470, 216, 2), ("H8", 410, 330, 505, 216, 2), ("H6", 545, 330, 545, 216, 2)]
    for hh, x1, y1, x2, y2, ep in fl:
        c.append(fleche(x1, y1, x2, y2, coul(hh), ep, tirets=tir(hh), id_=f(hh)))
    for hh, x, y, avant in [("H1", 197, 120, "H1"), ("H4", 430, 110, "H4"), ("H2", 372, 182, "H2 · l'effet testé"), ("H3", 560, 114, "H3"),
                            ("H7", 273 + (6.3 * len(etiq("H7", "H7")) + 12) / 2, 203, "H7"), ("H5", 357, 284, "H5"), ("H8", 472, 256, "H8"), ("H6", 545, 300, "H6 (−)")]:
        c.append(pastille(x, y, etiq(hh, avant), coul(hh)))
    titre = "Le modèle de nos hypothèses" if not apres else "Le modèle, une fois les hypothèses testées"
    desc = ("Schéma des hypothèses : la version B agit sur la durée perçue (H1) et sur le choix du Michelin (H2) ; la durée perçue "
            "transmet l'effet (H4) ; la fidélité (H5), la qualité perçue (H8) et la conscience du prix (H6) agissent sur le choix ; "
            "le kilométrage modifie l'effet de la version (H7) ; H3 : en version A, plus de la moitié choisit Michelin.")
    if apres:
        desc += " Validées : H1, H2, H5. Rejetée : H3. Non démontrées : H4, H6, H7, H8."
    return svg(nom, 620, 392, titre, desc, "".join(c))


SCHEMAS["modele"] = figure(1, "le modèle de nos hypothèses, avant le test", modele("mod1", False), large=True)
SCHEMAS["modele-apres"] = figure(14, "le même modèle, une fois chaque hypothèse testée", modele("mod2", True), large=True,
                                 leg=[("validée (trait plein)", OK), ("non démontrée ou rejetée (pointillés)", NEUTRE)])


# ---- Schéma 2 : le tirage au sort, profils des deux groupes --------------------------------------------------------
def groupes(nom, panneaux, ymax=1.0, unite="%", hauteur_panneau=150, titre="", desc=""):
    """Colonnes groupées A / B, un panneau par variable ; panneaux = [(titre, [(classe, valA, valB, info)])]."""
    larg, gauche, droite = 520, 46, 506
    H = 34 + len(panneaux) * (hauteur_panneau + 60)
    c = []
    y_haut = 26
    for titre_p, lignes in panneaux:
        base = y_haut + hauteur_panneau
        c.append(T(gauche, y_haut - 8, titre_p, 12.5, BLEU_FONCE, gras=True))
        for g in (0, 0.25, 0.5, 0.75, 1.0):
            v = g * ymax
            y = base - hauteur_panneau * g
            c.append(L(gauche, y, droite, y))
            c.append(T(gauche - 6, y + 4, f"{fr(100 * v, 0)} %" if unite == "%" else fr(v, 1), 10.5, GRIS, "end"))
        n = len(lignes)
        pas = (droite - gauche) / n
        for i, (cl, va, vb, info) in enumerate(lignes):
            cx = gauche + pas * (i + 0.5)
            for j, (v, col, ver) in enumerate([(va, A_, "A"), (vb, B_, "B")]):
                if v is None:
                    continue
                x = cx - 27 + j * 30
                hh = hauteur_panneau * v / ymax
                c.append(barre_v(x, base, max(hh, 1), 24, col, f"Version {ver} · {cl} : {pc(v)}{info[j] if info else ''}"))
                c.append(T(x + 12, base - hh - 5, pc(v), 10.5, ENCRE, "middle", gras=True))
            c.append(T(cx, base + 16, cl, 11.5, ENCRE, "middle"))
            if info and info[2]:
                c.append(T(cx, base + 30, info[2], 10, GRIS, "middle"))
        c.append(L(gauche, base, droite, base, GRIS, 1))
        y_haut = base + 60
    return svg(nom, larg, H, titre, desc, "".join(c))


part = lambda g, col, cl: (g[col] == cl).mean()
pt_age = stats.chi2_contingency(pd.crosstab(d.version, d.tage), correction=False)[1]
pt_km = stats.chi2_contingency(pd.crosstab(d.version, d.tkm), correction=False)[1]
pan = [(f"Classe d'âge (chi², {pval(pt_age)} : pas de différence)", [(cl, part(A, "tage", cl), part(B, "tage", cl), None) for cl in AGES]),
       (f"Kilomètres par an (chi², {pval(pt_km)} : différence)", [(cl, part(A, "tkm", cl), part(B, "tkm", cl), None) for cl in KMS])]
SCHEMAS["tirage"] = figure(
    2, "le tirage au sort a-t-il donné deux groupes semblables ? (en % de chaque version)",
    groupes("tir", pan, ymax=0.8, titre="Profil des deux groupes", desc="Part de chaque classe d'âge et de kilométrage dans les versions A et B."),
    leg=[(f"Version A · Michelin 40 000 km (n = {nA})", A_), (f"Version B · Michelin 50 000 km (n = {nB})", B_)],
    table=tableau(["Classe", "Version A", "Version B"], [(cl, pc(part(A, "tage", cl)), pc(part(B, "tage", cl))) for cl in AGES] +
                  [(cl + " km", pc(part(A, "tkm", cl)), pc(part(B, "tkm", cl))) for cl in KMS]))


# ---- Schéma 3 : le contrôle de manipulation, barres divergentes de 1 à 7 -------------------------------------------
def divergentes(nom):
    larg, centre, ech = 560, 300, 2.4     # 2,4 px par point de %
    c = []
    rang = [("Version A · 40 000 km", A), ("Version B · 50 000 km", B)]
    for g in (-60, -40, -20, 0, 20, 40, 60, 80):
        x = centre + g * ech
        c.append(L(x, 22, x, 150, TRAIT if g else GRIS, 1))
        c.append(T(x, 168, f"{abs(g)} %", 10.5, GRIS, "middle"))
    c.append(T(centre - 8, 16, "← pas d'accord", 11, GRIS, "end"))
    c.append(T(centre + 8, 16, "d'accord →", 11, GRIS, "start"))
    for i, (lib, g) in enumerate(rang):
        y = 40 + i * 58
        parts = [(g.manip_km == k).mean() * 100 for k in range(1, 8)]
        gauche = -(parts[0] + parts[1] + parts[2] + parts[3] / 2)
        x = centre + gauche * ech
        for k, v in enumerate(parts):
            l_ = v * ech
            if l_ > 0:
                c.append(f'<rect x="{x + 1:.1f}" y="{y}" width="{max(l_ - 2, 0.5):.1f}" height="30" fill="{ACCORD[k]}" tabindex="0">'
                         f'<title>{escape(lib)} · réponse {k + 1} : {fr(v, 1)} %</title></rect>')
            x += l_
        dacc, pasacc = sum(parts[4:]), sum(parts[:3])
        c.append(T(centre + gauche * ech - 6, y + 20, f"{fr(pasacc, 0)} %", 12, ENCRE, "end", gras=True))
        c.append(T(x + 6, y + 20, f"{fr(dacc, 0)} %", 12, ENCRE, "start", gras=True))
        c.append(T(8, y + 13, lib.split(" · ")[0], 12, ENCRE, gras=True))
        c.append(T(8, y + 28, f"moyenne {fr(g.manip_km.mean())} sur 7", 11, GRIS))
    return svg(nom, larg, 178, "Réponses à la question de contrôle, de 1 à 7",
               "Barres divergentes centrées sur la réponse neutre 4 : à gauche les réponses 1 à 3, à droite 5 à 7, pour chaque version.", "".join(c))


lignes_m = [(f"Version {v}", *[pc((g.manip_km == k).mean(), 1) for k in range(1, 8)], fr(g.manip_km.mean()))
            for v, g in [("A", A), ("B", B)]]
SCHEMAS["controle"] = figure(
    3, "« Le Michelin m'a semblé durer plus longtemps que le Hankook » : la répartition des réponses",
    divergentes("man"),
    leg=[("1 pas du tout d'accord", ACCORD[0]), ("2", ACCORD[1]), ("3", ACCORD[2]), ("4 neutre", ACCORD[3]), ("5", ACCORD[4]), ("6", ACCORD[5]),
         ("7 tout à fait d'accord", ACCORD[6])],
    table=tableau(["Version", "1", "2", "3", "4", "5", "6", "7", "Moyenne"], lignes_m), large=True)


# ---- Schéma 4 et 7 : les jauges de taille d'effet ------------------------------------------------------------------
def jauge(nom, valeur, seuils, vmax, symbole, titre):
    larg, x0, x1 = 520, 20, 500
    ech = (x1 - x0) / vmax
    zones = [0] + list(seuils) + [vmax]
    noms = ["négligeable", "petit", "moyen", "fort"]
    teintes = ["#E3E9F4", "#BFCDE8", "#8FA6D3", "#5F7FBF"]
    c = []
    for i in range(4):
        xa, xb = x0 + zones[i] * ech, x0 + zones[i + 1] * ech
        c.append(f'<rect x="{xa + 1:.1f}" y="34" width="{xb - xa - 2:.1f}" height="16" fill="{teintes[i]}"/>')
        c.append(T((xa + xb) / 2, 68, noms[i], 11, GRIS, "middle"))
        if i:
            c.append(T(xa, 28, fr(zones[i], 1), 10.5, GRIS, "middle"))
    xv = x0 + min(valeur, vmax) * ech
    c.append(f'<path d="M{xv - 7:.1f},20 L{xv + 7:.1f},20 L{xv:.1f},31 z" fill="{BLEU_FONCE}"/>')
    c.append(L(xv, 31, xv, 52, BLEU_FONCE, 2))
    c.append(T(xv, 14, f"{symbole} = {fr(valeur)}", 12.5, BLEU_FONCE, "middle", gras=True))
    return svg(nom, larg, 76, titre, f"{titre} : {symbole} = {fr(valeur)}, sur une échelle négligeable, petit, moyen, fort (Cohen, 1988).", "".join(c))


SCHEMAS["jauge-d"] = figure(4, "la taille de l'effet du contrôle : un écart fort", jauge("jd", man["d"], (0.2, 0.5, 0.8), 1.2, "d", "d de Cohen du contrôle de manipulation"))
SCHEMAS["jauge-v"] = figure(6, "la taille de l'effet du test A/B : un effet petit, mais réel", jauge("jv", V, (0.1, 0.3, 0.5), 0.6, "V", "V de Cramer du test A/B"))


# ---- Schéma 5 : le choix, avec intervalles de confiance ------------------------------------------------------------
def colonnes_ic(nom):
    larg, haut, gauche, droite, base, plot = 480, 300, 52, 470, 250, 210
    y = lambda v: base - plot * v
    c = []
    for g in (0, 0.25, 0.5, 0.75, 1):
        c.append(L(gauche, y(g), droite, y(g)))
        c.append(T(gauche - 6, y(g) + 4, f"{int(g * 100)} %", 10.5, GRIS, "end"))
    c.append(L(gauche, y(0.5), droite, y(0.5), GRIS, 1.2, tirets=True))
    c.append(T(droite, y(0.5) - 6, "50 % : pas de préférence", 10.5, GRIS, "end"))
    for i, (lib, k, n, p, ic, col) in enumerate([("Version A · 40 000 km", kA, nA, pA, icA, A_), ("Version B · 50 000 km", kB, nB, pB, icB, B_)]):
        cx = 150 + i * 160
        c.append(barre_v(cx - 14, base, plot * p, 28, col, f"{lib} : {pc(p)} ({k} sur {n}), IC 95 % de {pc(ic[0])} à {pc(ic[1])}"))
        c.append(L(cx, y(ic[0]), cx, y(ic[1]), ENCRE, 1.5))
        c.append(L(cx - 7, y(ic[0]), cx + 7, y(ic[0]), ENCRE, 1.5))
        c.append(L(cx - 7, y(ic[1]), cx + 7, y(ic[1]), ENCRE, 1.5))
        c.append(T(cx + 22, y(p) + 5, pc(p), 15, ENCRE, "start", gras=True))
        c.append(T(cx, base + 18, lib, 12, ENCRE, "middle", gras=True))
        c.append(T(cx, base + 34, f"{k} sur {n} · IC de {pc(ic[0])} à {pc(ic[1])}", 10.5, GRIS, "middle"))
    c.append(L(gauche, base, droite, base, GRIS))
    return svg(nom, larg, haut, "Part qui choisit le Michelin, par version",
               f"Version A : {pc(pA)}, version B : {pc(pB)} ; les traits verticaux sont les intervalles de confiance à 95 % (Wilson).", "".join(c))


SCHEMAS["choix"] = figure(
    5, "la part qui choisit le Michelin à 97,90 € plutôt que le Hankook à 81,99 €", colonnes_ic("cho"),
    leg=[("Version A · 40 000 km", A_), ("Version B · 50 000 km", B_)],
    table=tableau(["Version", "Choisissent Michelin", "Répondants", "Part", "IC 95 % (Wilson)"],
                  [("A · 40 000 km", kA, nA, pc(pA, 1), f"{pc(icA[0], 1)} à {pc(icA[1], 1)}"),
                   ("B · 50 000 km", kB, nB, pc(pB, 1), f"{pc(icB[0], 1)} à {pc(icB[1], 1)}")]))

# ---- Tableau 6 : le chi² construit à la main (CM 2) ----------------------------------------------------------------
obs = tab.values
contrib = (obs - attendus) ** 2 / attendus
lignes_chi = []
for i, v in enumerate(["A · 40 000 km", "B · 50 000 km"]):
    lignes_chi.append(f"<tr><td>{v}</td>" + "".join(
        f'<td class="n">{obs[i, j]} <span class="att">(attendu {fr(attendus[i, j], 1)})</span><br><span class="att">écart² ÷ attendu = {fr(contrib[i, j])}</span></td>'
        for j in (1, 0)) + f'<td class="n">{obs[i].sum()}</td></tr>')
SCHEMAS["chi2"] = (
    '<div class="tableau"><table><thead><tr><th>Version</th><th class="n">Choisit Michelin</th><th class="n">Choisit Hankook</th><th class="n">Total</th></tr></thead><tbody>'
    + "".join(lignes_chi)
    + f'<tr class="total"><td>Total</td><td class="n">{obs[:, 1].sum()}</td><td class="n">{obs[:, 0].sum()}</td><td class="n">{N}</td></tr>'
    + f'</tbody></table></div><p class="note">Chi² = somme des quatre cases « écart² ÷ attendu » = {fr(contrib.sum())}, pour 1 degré de liberté : '
      f"au-delà de la valeur critique de 3,84, on rejette l'hypothèse nulle ({pval(p_chi2)}). Toutes les cases attendues dépassent 5 : le chi² s'applique.</p>")


# ---- Schéma 8 : la robustesse, p-values sur échelle logarithmique --------------------------------------------------
def robustesse(nom):
    larg, gauche, droite = 600, 290, 520
    lo, hi = np.log10(0.001), np.log10(1)
    x = lambda p: gauche + (np.log10(max(p, 0.001)) - lo) / (hi - lo) * (droite - gauche)
    H = 40 + len(ROBUSTESSE) * 30 + 34
    c = []
    for t in (0.001, 0.01, 0.1, 1):
        c.append(L(x(t), 26, x(t), H - 30))
        c.append(T(x(t), H - 14, fr(t, 3).rstrip("0").rstrip(",") if t < 1 else "1", 10.5, GRIS, "middle"))
    c.append(f'<rect x="{gauche}" y="26" width="{x(0.05) - gauche:.1f}" height="{H - 56}" fill="{CIEL}"/>')
    c.append(L(x(0.05), 20, x(0.05), H - 30, ALERTE, 1.5, tirets=True))
    c.append(T(x(0.05) + 4, 16, "seuil de 5 %", 11, ALERTE, "start", gras=True))
    c.append(T(gauche + 4, 16, "← significatif", 11, BLEU_FONCE, "start"))
    for i, (lib, p) in enumerate(ROBUSTESSE):
        y = 44 + i * 30
        c.append(T(gauche - 10, y + 4, lib, 11.5, ENCRE, "end"))
        c.append(point(x(p), y, B_ if p < 0.05 else NEUTRE, f"{lib} : {pval(p)}"))
        c.append(T(larg - 6, y + 4, f"p = {fr(p, 3)}", 11, ENCRE, "end", gras=True))
    return svg(nom, larg, H, "La p-value du test A/B selon la façon de le faire",
               "Sept variantes du test, toutes à gauche du seuil de 5 % : le résultat ne dépend pas du test choisi.", "".join(c))


SCHEMAS["robustesse"] = figure(7, "sept façons de faire le test, sept fois le même verdict (p-value, échelle logarithmique)", robustesse("rob"),
                               table=tableau(["Variante", "p"], [(l, fr(p, 4)) for l, p in ROBUSTESSE]), large=True)


# ---- Schéma 9 : la précision de l'écart ----------------------------------------------------------------------------
def precision(nom):
    larg, gauche, droite = 540, 30, 520
    x = lambda v: gauche + (v + 5) / 50 * (droite - gauche)
    c = []
    for t in (0, 10, 20, 30, 40):
        c.append(L(x(t), 30, x(t), 92, GRIS if t == 0 else TRAIT, 1))
        c.append(T(x(t), 108, f"{t}", 10.5, GRIS, "middle"))
    c.append(T(x(0) + 4, 26, "0 : aucun effet", 10.5, GRIS))
    a, b = ic_ecart[0] * 100, ic_ecart[1] * 100
    c.append(f'<rect x="{x(a):.1f}" y="52" width="{x(b) - x(a):.1f}" height="20" rx="4" fill="{B_}" fill-opacity=".14"/>')
    c.append(L(x(a), 62, x(b), 62, B_, 2))
    c.append(L(x(a), 54, x(a), 70, B_, 2))
    c.append(L(x(b), 54, x(b), 70, B_, 2))
    c.append(point(x(ecart * 100), 62, B_, f"Écart mesuré : {fr(ecart * 100, 1)} points ; IC 95 % de {fr(a, 1)} à {fr(b, 1)}", r=6))
    c.append(T(x(ecart * 100), 46, f"écart mesuré : +{fr(ecart * 100, 1)} points", 12, ENCRE, "middle", gras=True))
    c.append(T(x(a), 86, f"+{fr(a, 1)}", 11, ENCRE, "middle"))
    c.append(T(x(b), 86, f"+{fr(b, 1)}", 11, ENCRE, "middle"))
    c.append(T((gauche + droite) / 2, 124, "écart de choix B − A, en points de pourcentage", 10.5, GRIS, "middle"))
    return svg(nom, larg, 130, "L'écart entre B et A et son intervalle de confiance",
               f"Écart de {fr(ecart * 100, 1)} points, intervalle de confiance à 95 % de {fr(a, 1)} à {fr(b, 1)} points : il ne touche pas zéro.", "".join(c))


SCHEMAS["precision"] = figure(8, "l'écart entre B et A, et la marge d'incertitude qui l'entoure", precision("pre"))


# ---- Schéma 10 : la courbe de puissance ----------------------------------------------------------------------------
def courbe_puissance(nom):
    larg, gauche, droite, base, plot = 520, 48, 500, 240, 200
    ns = np.arange(10, 201, 2)
    pw = [POW.power(h, nobs1=n, alpha=0.05, ratio=1) for n in ns]
    x = lambda n: gauche + (n - 10) / 190 * (droite - gauche)
    y = lambda p: base - plot * p
    c = []
    for g in (0, 0.25, 0.5, 0.75, 1):
        c.append(L(gauche, y(g), droite, y(g)))
        c.append(T(gauche - 6, y(g) + 4, f"{int(g * 100)} %", 10.5, GRIS, "end"))
    for n in (25, 50, 100, 150, 200):
        c.append(T(x(n), base + 16, str(n), 10.5, GRIS, "middle"))
    c.append(T((gauche + droite) / 2, base + 32, "répondants par version", 10.5, GRIS, "middle"))
    c.append(L(gauche, y(0.8), droite, y(0.8), ALERTE, 1.2, tirets=True))
    c.append(T(droite, y(0.8) - 6, "80 % : la puissance visée", 10.5, ALERTE, "end"))
    pts = " ".join(f"{x(n):.1f},{y(p):.1f}" for n, p in zip(ns, pw))
    c.append(f'<polyline points="{pts}" fill="none" stroke="{B_}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
    n_nous = (nA + nB) / 2
    c.append(point(x(n_nous), y(puissance), B_, f"Notre test : {nA} et {nB} répondants, puissance {pc(puissance)}"))
    c.append(T(x(n_nous) + 10, y(puissance) + 16, f"nous : {nA} et {nB} → {pc(puissance)}", 11.5, ENCRE, "start", gras=True))
    c.append(point(x(n80), y(0.8), B_, f"{n80} répondants par version : 80 %"))
    c.append(T(x(n80) + 10, y(0.8) + 16, f"{n80} par version → 80 %", 11.5, ENCRE, "start", gras=True))
    c.append(L(gauche, base, droite, base, GRIS))
    return svg(nom, larg, 280, "Puissance du test selon le nombre de répondants",
               f"Pour un écart de la taille observée (h = {fr(h)}), la puissance est de {pc(puissance)} avec nos effectifs et atteint 80 % à {n80} répondants par version.",
               "".join(c))


SCHEMAS["puissance"] = figure(9, "la chance de détecter un écart de cette taille, selon le nombre de répondants", courbe_puissance("pui"))


# ---- Schéma 11 : la régression logistique, odds ratios -------------------------------------------------------------
def foret(nom):
    larg, gauche, droite = 600, 220, 470
    lo, hi = np.log(0.4), np.log(10)
    x = lambda v: gauche + (np.log(v) - lo) / (hi - lo) * (droite - gauche)
    H = 40 + len(FOREST) * 34 + 30
    c = []
    for t in (0.5, 1, 2, 4, 8):
        c.append(L(x(t), 24, x(t), H - 28, GRIS if t == 1 else TRAIT, 1.2 if t == 1 else 1))
        c.append(T(x(t), H - 12, f"×{fr(t, 1).rstrip('0').rstrip(',')}", 10.5, GRIS, "middle"))
    c.append(T(x(1) - 6, 18, "← pousse vers le Hankook", 10.5, GRIS, "end"))
    c.append(T(x(1) + 6, 18, "pousse vers Michelin →", 10.5, GRIS, "start"))
    for i, (lib, orr, b_, h_, p) in enumerate(FOREST):
        y = 44 + i * 34
        sig = p < 0.05
        col = B_ if sig else NEUTRE
        c.append(T(gauche - 10, y + 4, lib, 11.5, ENCRE, "end", gras=sig))
        c.append(L(x(max(b_, 0.4)), y, x(min(h_, 10)), y, col, 2))
        c.append(point(x(orr), y, col, f"{lib} : odds ratio {fr(orr)}, IC 95 % de {fr(b_)} à {fr(h_)}, {pval(p)}"))
        c.append(T(larg - 4, y + 4, f"×{fr(orr)} · {pval(p)}", 11, ENCRE if sig else GRIS, "end", gras=sig))
    return svg(nom, larg, H, "Odds ratios de la régression logistique du choix du Michelin",
               "Version B et fidélité ont un intervalle qui ne touche pas 1 : elles font choisir Michelin ; les autres variables non.", "".join(c))


SCHEMAS["logit"] = figure(10, "ce qui fait choisir Michelin, toutes choses égales par ailleurs (odds ratio et intervalle à 95 %, échelle logarithmique)",
                          foret("for"), leg=[("significatif", B_), ("non significatif", NEUTRE)],
                          table=tableau(["Variable", "Odds ratio", "IC 95 %", "p"], [(l, fr(o), f"{fr(b_)} à {fr(h_)}", fr(p, 3)) for l, o, b_, h_, p in FOREST]),
                          large=True)


# ---- Schéma 12 : la médiation --------------------------------------------------------------------------------------
def mediation(nom):
    c = [defs_fleches(nom, [OK, NEUTRE, BLEU_FONCE])]
    c.append(boite(20, 170, 160, 58, ["Version B", "50 000 km annoncés"], fond=CIEL))
    c.append(boite(215, 20, 170, 58, ["Durée perçue", "contrôle, 1 à 7"]))
    c.append(boite(420, 170, 160, 58, ["Choix du Michelin"], fond=JAUNE))
    c.append(fleche(130, 170, 240, 80, OK, 2.5, id_=f"{nom}-0"))
    c.append(T(118, 118, f"a = +{fr(MED['a'])} point", 12.5, ENCRE, "middle", gras=True))
    c.append(T(118, 134, pval(MED["pa"]) + " · validé", 11, OK, "middle", gras=True))
    c.append(fleche(360, 80, 470, 168, NEUTRE, 2, tirets=True, id_=f"{nom}-1"))
    c.append(T(484, 118, f"b = {fr(MED['b'], 3)}", 12.5, ENCRE, "middle", gras=True))
    c.append(T(484, 134, pval(MED["pb"]) + " · nul", 11, GRIS, "middle", gras=True))
    c.append(fleche(180, 205, 418, 205, BLEU_FONCE, 2.5, id_=f"{nom}-2"))
    c.append(T(300, 196, f"c′ = {fr(MED['c'])} (effet direct, log-odds), {pval(MED['pc'])}", 11.5, ENCRE, "middle", gras=True))
    c.append(f'<rect x="120" y="250" width="360" height="46" rx="10" fill="{CIEL}"/>')
    c.append(T(300, 269, f"effet indirect a × b = {fr(MED['ab'], 3)}", 12.5, BLEU_FONCE, "middle", gras=True))
    c.append(T(300, 287, f"IC 95 % par bootstrap : de {fr(MED['bas'])} à {fr(MED['haut'])} → contient 0", 11.5, ENCRE, "middle"))
    return svg(nom, 600, 306, "La médiation : l'effet passe-t-il par la durée perçue ?",
               "La version B augmente la durée perçue (a), mais la durée perçue ne fait pas choisir Michelin à version égale (b nul) ; l'effet indirect contient zéro.",
               "".join(c))


SCHEMAS["mediation"] = figure(11, "la médiation (PROCESS, modèle 4) : par où passe l'effet ?", mediation("med"), large=True)


# ---- Schéma 13 : la modération, par classe ---------------------------------------------------------------------------
def share(g, col, cl):
    s = g[g[col] == cl]
    return (s.m.mean() if len(s) else None), len(s)


pan_mod = []
for titre_p, col, classes in [(f"Par classe d'âge (interaction version × âge : {pval(p_inter_age)})", "tage", AGES),
                              (f"Par kilométrage (version × plus de 15 000 km : {pval(p_inter_gros)})", "tkm", KMS)]:
    lignes = []
    for cl in classes:
        va, na_ = share(A, col, cl)
        vb, nb_ = share(B, col, cl)
        lignes.append((cl, va, vb, ("", "", f"n = {na_} et {nb_}")))
    pan_mod.append((titre_p, lignes))
SCHEMAS["moderation"] = figure(
    12, "l'effet des 10 000 km selon le profil : une piste, pas une preuve (part qui choisit Michelin)",
    groupes("mod", pan_mod, ymax=1.0, titre="Part qui choisit Michelin par sous-groupe",
            desc="Part de Michelin en version A et B dans chaque classe d'âge et de kilométrage ; effectifs faibles."),
    leg=[("Version A · 40 000 km", A_), ("Version B · 50 000 km", B_)],
    table=tableau(["Sous-groupe", "Michelin en A", "Michelin en B", "Répondants A et B"],
                  [(cl, pc(share(A, col, cl)[0]) if share(A, col, cl)[1] else "—", pc(share(B, col, cl)[0]) if share(B, col, cl)[1] else "—",
                    f"{share(A, col, cl)[1]} et {share(B, col, cl)[1]}") for col, cls in [("tage", AGES), ("tkm", KMS)] for cl in cls]))


# ---- Schéma 14 : les échelles, poids des items -----------------------------------------------------------------------
ITEMS = [("Fidélité", "LO1 · fidèle à Michelin", "likert_lo1"), ("Fidélité", "LO2 · premier choix", "likert_lo2"),
         ("Fidélité", "LO3 · pas d'autre marque", "likert_lo3"), ("Qualité perçue", "QL2 · qualité très élevée", "likert_ql2"),
         ("Qualité perçue", "QL3 · remplit sa fonction", "likert_ql3"), ("Conscience du prix", "PR1 · achète en promotion", "likert_pr1"),
         ("Conscience du prix", "PR2 · choisit les moins chers", "likert_pr2"), ("Conscience du prix", "PR3 · meilleur rapport qualité-prix", "likert_pr3")]


def poids(nom):
    larg, gauche, droite = 600, 250, 560
    x = lambda v: gauche + v * (droite - gauche)
    H = 30 + len(ITEMS) * 30 + 3 * 14 + 30
    c = []
    for t in (0, 0.25, 0.5, 0.75, 1):
        c.append(L(x(t), 18, x(t), H - 26))
        c.append(T(x(t), H - 10, fr(t), 10.5, GRIS, "middle"))
    c.append(L(x(0.7), 12, x(0.7), H - 26, ALERTE, 1.5, tirets=True))
    c.append(T(x(0.7) + 4, 12, "seuil 0,70", 11, ALERTE, "start", gras=True))
    y, prec = 26, None
    for cons, lib, col in ITEMS:
        if cons != prec:
            c.append(T(8, y + 10, cons, 11.5, BLEU_FONCE, gras=True))
            y += 14
            prec = cons
        v = POIDS[col]
        coul = B_ if v >= 0.7 else ALERTE
        c.append(T(gauche - 10, y + 13, lib, 11.5, ENCRE, "end"))
        c.append(barre_h(gauche, y + 2, x(v) - gauche, 18, coul, f"{lib} : poids {fr(v)}"))
        c.append(T(max(x(v), x(0.7)) + 6, y + 15, fr(v) + ("" if v >= 0.7 else " · sous le seuil"), 11, ENCRE, "start", gras=True))
        y += 30
    return svg(nom, larg, H, "Poids standardisé de chaque item dans l'analyse factorielle confirmatoire",
               "Six items dépassent 0,70 ; QL2 (0,60) et PR2 (0,65) restent en dessous.", "".join(c))


SCHEMAS["echelles"] = figure(13, "chaque affirmation mesure-t-elle bien son idée ? (poids standardisé, analyse factorielle confirmatoire)",
                             poids("poi"), leg=[("au-dessus du seuil", B_), ("sous le seuil de 0,70", ALERTE)],
                             table=tableau(["Item", "Poids"], [(lib, fr(POIDS[col])) for _, lib, col in ITEMS]), large=True)


# ---- Schéma 16 : de l'effet à l'argent ---------------------------------------------------------------------------------
def rentabilite(nom):
    larg, gauche, droite, haut, bas = 560, 64, 540, 26, 236
    ymin, ymax = -2.6e6, 3.2e6
    x = lambda e: gauche + e / 45 * (droite - gauche)
    y = lambda v: bas - (v - ymin) / (ymax - ymin) * (bas - haut)
    a, b = ic_ecart[0] * 100, ic_ecart[1] * 100
    c = [f'<rect x="{x(a):.1f}" y="{haut}" width="{x(b) - x(a):.1f}" height="{bas - haut}" fill="{B_}" fill-opacity=".08"/>',
         T((x(a) + x(b)) / 2, bas - 8, "ce que permet notre test (IC 95 %)", 10.5, B_, "middle")]
    for v in (-2e6, -1e6, 0, 1e6, 2e6, 3e6):
        c.append(L(gauche, y(v), droite, y(v), GRIS if v == 0 else TRAIT))
        c.append(T(gauche - 6, y(v) + 4, f"{'+' if v > 0 else ''}{fr(v / 1e6, 0)} M€", 10.5, GRIS, "end"))
    for e in (0, 10, 20, 30, 40):
        c.append(T(x(e), bas + 16, str(e), 10.5, GRIS, "middle"))
    c.append(T((gauche + droite) / 2, bas + 32, "effet réel des 10 000 km sur le choix, en points", 10.5, GRIS, "middle"))
    e_haut = min(45, (ymax + 2_500_000) / (200000 * 20.22 / (ecart * 100)))      # là où la droite sort par le haut
    c.append(f'<polyline points="{x(0):.1f},{y(gain(0)):.1f} {x(e_haut):.1f},{y(gain(e_haut)):.1f}" fill="none" stroke="{B_}" stroke-width="2"/>')
    c.append(L(x(SEUIL_EFFET), haut, x(SEUIL_EFFET), bas, ALERTE, 1.5, tirets=True))
    c.append(T(x(SEUIL_EFFET) - 4, y(1.9e6), f"point mort : {fr(SEUIL_EFFET, 1)} points", 11, ALERTE, "end", gras=True))
    for e, lib in [(a, "bas de l'intervalle"), (ecart * 100, "effet mesuré"), (b, "haut de l'intervalle")]:
        g = gain(e)
        c.append(point(x(e), y(g), B_, f"{lib} : +{fr(e, 1)} points → gain net {fr(g / 1e6, 2)} M€"))
    c.append(T(x(ecart * 100) + 9, y(gain(ecart * 100)) + 16, f"mesuré : +{fr(ecart * 100, 1)} pts → {'+' if gain(ecart * 100) > 0 else ''}{fr(gain(ecart * 100) / 1e6, 2)} M€",
               11.5, ENCRE, "start", gras=True))
    c.append(T(x(a) + 9, y(gain(a)) + 4, f"+{fr(a, 1)} pts → {fr(gain(a) / 1e6, 2)} M€", 11, ENCRE, "start"))
    return svg(nom, larg, 276, "Gain net de la campagne selon l'effet réel de la durée de vie",
               f"Droite du gain net de la campagne de 2,5 M€ selon l'effet réel ; point mort à {fr(SEUIL_EFFET, 1)} points ; effet mesuré {fr(ecart * 100, 1)} points.",
               "".join(c))


SCHEMAS["rentabilite"] = figure(15, "ce que vaut l'effet en euros : le gain net de la campagne selon l'effet réel des 10 000 km", rentabilite("ren"),
                                table=tableau(["Effet réel (points)", "Pneus vendus en plus", "Gain net"],
                                              [(fr(e, 1), fr(200000 * e / (ecart * 100), 0), f"{fr(gain(e), 0)} €")
                                               for e in (0, ic_ecart[0] * 100, SEUIL_EFFET, ecart * 100, ic_ecart[1] * 100)]),
                                large=True)


# ---- Schéma de la synthèse : l'arbre de décision -------------------------------------------------------------------
def decision(nom):
    c = [defs_fleches(nom, [BLEU_FONCE, OK, NEUTRE])]
    c.append(boite(170, 10, 280, 54, ["Notre question de prix", "97,90 € ou 94,90 € ?"], fond=BLEU_FONCE, bord=BLEU_FONCE, texte="#fff"))
    c.append(boite(20, 110, 260, 70, ["Baisser à 94,90 € ?", "il faudrait +12,2 % de ventes ;", "prix non testé par le questionnaire"]))
    c.append(boite(340, 110, 260, 70, ["Garder 97,90 € : avec quel argument ?", "test A/B, 108 répondants"]))
    c.append(boite(20, 230, 260, 56, ["Non : la baisse", "ne se paie pas (partie 4)"], fond="#F1F3F6", bord=NEUTRE))
    c.append(boite(320, 230, 135, 72, ["La marque seule", "45 % en version A", "rejetée"], fond="#F1F3F6", bord=NEUTRE, taille=11.5))
    c.append(boite(465, 230, 135, 72, ["La durée de vie", "67 % en version B", "validée"], fond="#E6F3EC", bord=OK, taille=11.5))
    c.append(boite(170, 350, 430, 70, ["Recommandation : maintenir 97,90 €", "et vendre la durée de vie, chiffrée (km, coût pour 10 000 km)",
                                        f"rentable si l'effet réel dépasse {fr(SEUIL_EFFET, 0)} points (mesuré : {fr(ecart * 100, 0)})"],
                   fond=JAUNE, bord=BLEU_FONCE))
    c.append(fleche(250, 64, 150, 108, id_=f"{nom}-0"))
    c.append(fleche(370, 64, 470, 108, id_=f"{nom}-0"))
    c.append(fleche(150, 180, 150, 228, NEUTRE, id_=f"{nom}-2"))
    c.append(fleche(430, 180, 390, 228, NEUTRE, id_=f"{nom}-2"))
    c.append(fleche(510, 180, 532, 228, OK, 2.5, id_=f"{nom}-1"))
    c.append(fleche(150, 286, 250, 348, NEUTRE, id_=f"{nom}-2"))
    c.append(fleche(532, 302, 480, 348, OK, 2.5, id_=f"{nom}-1"))
    return svg(nom, 620, 430, "L'arbre de décision du dossier",
               "De la question de prix à la recommandation : la baisse ne se paie pas ; à 97,90 €, la marque seule ne suffit pas, la durée de vie si.", "".join(c))


SCHEMAS["decision"] = figure(1, "l'arbre de décision du dossier", decision("dec"), large=True)



# ---- Les trois prix : par les coûts, par la concurrence, par la valeur ---------------------------------------------
# Chaque terme vient d'une source du dossier ; la construction détaillée est écrite dans la partie 4 (proposition.html).
PRIX_ACTUEL, TVA, MARGE_DISTRIBUTEUR = 97.90, 0.20, 0.12          # Allopneus ; TVA ; Bsness (12 % du prix HT)
VENTES_S1, COUT_REVIENT_S1, RD_S1, COMMERCIAUX_S1, GENERAUX_S1 = 13028, 9358, 396, 577, 1215   # M€, rapport semestriel 2025, p. 17
MARGE_CIBLE = 0.117                                               # marge Automobile 2025 de Michelin (communiqué annuel)
PLAFOND, HANKOOK_MARCHE = 93.20, 80.99                            # Continental et Hankook chez Allopneus, 1er octobre 2026
HANKOOK_TEST, KM_HANKOOK, KM_MICHELIN = 81.99, 40000, 50000       # le scénario de notre test A/B (partie 3)

net_actuel = PRIX_ACTUEL / (1 + TVA) * (1 - MARGE_DISTRIBUTEUR)      # ce que Michelin touche par pneu
cout_complet = net_actuel * (COUT_REVIENT_S1 + RD_S1 + COMMERCIAUX_S1 + GENERAUX_S1) / VENTES_S1
cout_revient = net_actuel * COUT_REVIENT_S1 / VENTES_S1
TROIS = {
    "plancher_revient": cout_revient / (1 - MARGE_DISTRIBUTEUR) * (1 + TVA),       # ne couvre que la fabrication
    "plancher_complet": cout_complet / (1 - MARGE_DISTRIBUTEUR) * (1 + TVA),       # couvre tout, marge nulle
    "couts": cout_complet / (1 - MARGE_CIBLE) / (1 - MARGE_DISTRIBUTEUR) * (1 + TVA),  # coût complet + marge cible
    "concurrence": PLAFOND,
    "valeur_usage": HANKOOK_TEST / KM_HANKOOK * KM_MICHELIN,                      # même coût pour 10 000 km que le Hankook
}


def trois_prix(nom):
    """Les trois logiques sur une même échelle en euros, et le prix que nous défendons."""
    larg, gauche, droite, haut, bas = 620, 150, 600, 44, 236
    x = lambda v: gauche + (v - 65) / 40 * (droite - gauche)
    c = []
    for v in range(65, 110, 5):
        c.append(L(x(v), haut, x(v), bas))
        c.append(T(x(v), bas + 16, f"{v} €", 10.5, GRIS, "middle"))
    lignes = [("Par les coûts", 82), ("Par la concurrence", 142), ("Par la valeur", 202)]
    for lib, y in lignes:
        c.append(T(8, y + 4, lib, 12.5, BLEU_FONCE, gras=True))
    # les fourchettes, en bandeau clair, décrites sous la bande (texte calé à droite sur la fin de la bande)
    for a, b, y, texte_ in [(TROIS["plancher_revient"], TROIS["plancher_complet"], 82,
                             f"planchers : {fr(TROIS['plancher_revient'])} € (fabrication) à {fr(TROIS['plancher_complet'])} € (tous les coûts)"),
                            (HANKOOK_MARCHE, PLAFOND, 142, f"concurrents : {fr(HANKOOK_MARCHE)} € (Hankook) à {fr(PLAFOND)} € (Continental)")]:
        c.append(f'<rect x="{x(a):.1f}" y="{y - 6}" width="{x(b) - x(a):.1f}" height="12" rx="6" fill="{CIEL}"/>')
        if texte_:
            c.append(T(x(b), y + 22, texte_, 10.5, GRIS, "end"))
    # le prix défendu, en trait vertical
    xd = x(PRIX_ACTUEL)
    c.append(L(xd, haut - 8, xd, bas, BLEU_FONCE, 2))
    c.append(T(xd - 6, haut - 14, f"{fr(PRIX_ACTUEL)} € : le prix que nous défendons", 12, BLEU_FONCE, "end", gras=True))
    # les points, chacun avec sa pastille (au-dessus ou au-dessous, décalée si besoin pour rester dans le cadre)
    for cle in ("plancher_revient", "plancher_complet"):
        c.append(point(x(TROIS[cle]), 82, NEUTRE, f"plancher : {fr(TROIS[cle])} €", r=4))
    for cle, y, texte_, dy, dx in [("couts", 82, f"{fr(TROIS['couts'])} € · coûts + marge cible", -20, -40),
                                   ("concurrence", 142, f"{fr(PLAFOND)} € · plafond", -20, -30),
                                   ("valeur_usage", 202, f"{fr(TROIS['valeur_usage'])} € · valeur d'usage", -20, -52)]:
        v = TROIS[cle]
        c.append(point(x(v), y, B_, texte_, r=6))
        c.append(pastille(x(v) + dx, y + dy, texte_, ENCRE))
    return svg(nom, larg, 262, "Trois logiques de prix sur une même échelle",
               f"Par les coûts : {fr(TROIS['couts'])} € (planchers {fr(TROIS['plancher_revient'])} et {fr(TROIS['plancher_complet'])} €) ; "
               f"par la concurrence : plafond {fr(PLAFOND)} € ; par la valeur : {fr(TROIS['valeur_usage'])} € d'usage ; "
               f"prix défendu {fr(PRIX_ACTUEL)} €.", "".join(c))


SCHEMAS["trois-prix"] = figure(1, "trois logiques, trois prix, sur une même échelle (prix public TTC du pneu)", trois_prix("tro"),
                               leg=[("prix retenu par chaque logique", B_), ("plancher", NEUTRE)],
                               table=tableau(["Logique", "Prix TTC", "Ce qu'il dit"],
                                             [("Coûts : fabrication seule", f"{fr(TROIS['plancher_revient'])} €", "en dessous, chaque pneu ne paie même pas sa fabrication"),
                                              ("Coûts : coût complet", f"{fr(TROIS['plancher_complet'])} €", "en dessous, Michelin perd de l'argent sur chaque pneu"),
                                              ("Coûts : coût complet + marge cible de 11,7 %", f"{fr(TROIS['couts'])} €", "le prix qui garde la marge du groupe"),
                                              ("Concurrence : plafond", f"{fr(PLAFOND)} €", "le plus cher des concurrents premium (Continental)"),
                                              ("Valeur d'usage", f"{fr(TROIS['valeur_usage'])} €", "même coût pour 10 000 km que le Hankook"),
                                              ("Prix défendu", f"{fr(PRIX_ACTUEL)} €", "le prix actuel, maintenu")]), large=True)


# ---- les versions courtes du code, montrées dans les bandeaux ----------------------------------------------------
INTRO_COURT = ("Le principe, en version courte : d'abord les chiffres, calculés sur les réponses, puis le dessin "
               "(les valeurs en commentaire sont celles du graphique). Le code complet, avec tous les réglages de mise en page, "
               "est dans <a href=\"annexes/fabriquer_schemas.py\">annexes/fabriquer_schemas.py</a>.")


def resume(k):
    """Le code d'un graphique réduit à son principe, en quelques lignes."""
    if k in ("modele", "modele-apres"):
        return """# une boîte par idée, une flèche et une pastille par hypothèse
boite(20, 150, "Version B : Michelin annoncé à 50 000 km")
boite(225, 24, "Durée perçue")
boite(450, 150, "Choix du Michelin")
fleche(version, duree_percue)  ; pastille("H1")
fleche(version, choix, epaisseur=3)  ; pastille("H2 · l'effet testé")
fleche(duree_percue, choix)  ; pastille("H4")
# ... une flèche par hypothèse, de H1 à H8
# après le test : verte et pleine si l'hypothèse est validée, grise en pointillés sinon
couleur = VERT if validee else GRIS"""
    if k == "tirage":
        return f"""# 1. Les chiffres : la part de chaque classe d'âge dans chaque version
A = reponses[reponses.version == "A"]                      # {nA} répondants
B = reponses[reponses.version == "B"]                      # {nB} répondants
part_A = A.classe_age.value_counts(normalize=True)         # 18-24 : {pc(part(A, "tage", "18-24"))}
part_B = B.classe_age.value_counts(normalize=True)         # 18-24 : {pc(part(B, "tage", "18-24"))}

# 2. Le dessin : deux colonnes par classe, hautes de la part (150 pixels = 80 %)
for classe in ["18-24", "25-34", "35-49", "50 et +"]:
    colonne(classe, hauteur=part_A[classe] / 0.8 * 150, couleur=OCRE)   # version A
    colonne(classe, hauteur=part_B[classe] / 0.8 * 150, couleur=BLEU)   # version B
# même chose pour les kilomètres par an"""
    if k == "moderation":
        return f"""# 1. Les chiffres : dans chaque classe d'âge, la part qui choisit Michelin, version par version
michelin = reponses.groupby(["classe_age", "version"]).choix_michelin.mean()
# 18-24 : {pc(share(A, "tage", "18-24")[0])} en A, {pc(share(B, "tage", "18-24")[0])} en B

# 2. Le dessin : deux colonnes par classe, hautes de la part (150 pixels = 100 %)
for classe in ["18-24", "25-34", "35-49", "50 et +"]:
    colonne(classe, hauteur=michelin[classe, "A"] * 150, couleur=OCRE)
    colonne(classe, hauteur=michelin[classe, "B"] * 150, couleur=BLEU)
# même chose pour les kilomètres par an"""
    if k == "controle":
        return f"""# 1. Les chiffres : la part de chaque réponse, de 1 à 7, dans chaque version
parts = reponses.groupby("version").manip_km.value_counts(normalize=True)
# moyenne : {fr(man["moy_A"])} sur 7 en A, {fr(man["moy_B"])} en B

# 2. Le dessin : une barre par version, en 7 morceaux, centrée sur la réponse neutre (4)
for version in ["A", "B"]:
    p = parts[version]
    x = centre - (p[1] + p[2] + p[3] + p[4] / 2) * 240     # « pas d'accord » part vers la gauche
    for reponse in range(1, 8):
        rectangle(x, largeur=p[reponse] * 240, couleur=couleurs[reponse])
        x += p[reponse] * 240                               # le morceau suivant commence où finit celui-ci"""
    if k == "jauge-d":
        return f"""# 1. Le chiffre : l'écart entre les deux versions, en écarts-types (d de Cohen)
d = (moyenne_B - moyenne_A) / ecart_type_commun            # ({fr(man["moy_B"])} − {fr(man["moy_A"])}) ÷ {fr((man["moy_B"] - man["moy_A"]) / man["d"])} = {fr(man["d"])}

# 2. Le dessin : quatre zones (Cohen, 1988), et un repère sur notre valeur
zones = [0, 0.2, 0.5, 0.8, 1.2]                            # négligeable, petit, moyen, fort
for debut, fin in zip(zones, zones[1:]):
    rectangle(x=debut * 400, largeur=(fin - debut) * 400)
triangle(x=d * 400)"""
    if k == "jauge-v":
        return f"""# 1. Le chiffre : la force du lien entre version et choix (V de Cramer)
V = sqrt(chi2 / N)                                          # √({fr(chi2)} ÷ {N}) = {fr(V)}

# 2. Le dessin : quatre zones (Cohen, 1988), et un repère sur notre valeur
zones = [0, 0.1, 0.3, 0.5, 0.6]                            # négligeable, petit, moyen, fort
for debut, fin in zip(zones, zones[1:]):
    rectangle(x=debut * 800, largeur=(fin - debut) * 800)
triangle(x=V * 800)"""
    if k == "choix":
        return f"""# 1. Les chiffres
pA, pB = {kA} / {nA}, {kB} / {nB}                                  # {pc(pA)} et {pc(pB)} choisissent Michelin
icA = proportion_confint({kA}, {nA}, method="wilson")              # de {pc(icA[0])} à {pc(icA[1])}
icB = proportion_confint({kB}, {nB}, method="wilson")              # de {pc(icB[0])} à {pc(icB[1])}

# 2. Le dessin : 0 % en bas (y = 250), 100 % en haut (y = 40)
y = lambda part: 250 - part * 210
colonne(x=150, haut=y(pA), couleur=OCRE)  ;  trait(x=150, de_=y(icA[0]), a=y(icA[1]))
colonne(x=310, haut=y(pB), couleur=BLEU)  ;  trait(x=310, de_=y(icB[0]), a=y(icB[1]))
ligne_pointillee(y(0.5))                                   # 50 % : pas de préférence"""
    if k == "robustesse":
        return f"""# 1. Les chiffres : la p-value du même test A/B, calculée de plusieurs façons
p = {{"Chi² de Pearson": chi2_contingency(tableau, correction=False)[1],     # {fr(ROBUSTESSE[0][1], 3)}
     "Test exact de Fisher": fisher_exact(tableau)[1],                      # {fr(ROBUSTESSE[2][1], 3)}
     "Régression logistique": logit("michelin ~ version").fit().pvalues[1], # {fr(ROBUSTESSE[3][1], 3)}
     "Sans les réponses en double": ...}}

# 2. Le dessin : une échelle logarithmique, de 0,001 à gauche à 1 à droite
x = lambda valeur: 290 + (log10(valeur) + 3) / 3 * 230
for ligne, (variante, valeur) in enumerate(p.items()):
    point(x(valeur), y=44 + ligne * 30)
ligne_pointillee(x(0.05))                                  # le seuil de 5 %"""
    if k == "precision":
        return f"""# 1. Les chiffres : l'écart entre B et A, et sa marge d'incertitude à 95 %
ecart = pB - pA                                                    # +{fr(ecart * 100, 1)} points
marge = 1.96 * sqrt(pA * (1 - pA) / {nA} + pB * (1 - pB) / {nB})        # {fr((ic_ecart[1] - ecart) * 100, 1)} points

# 2. Le dessin : un point sur l'écart, un trait de part et d'autre
point(x(ecart))
trait(de_=x(ecart - marge), a=x(ecart + marge))                    # de +{fr(ic_ecart[0] * 100, 1)} à +{fr(ic_ecart[1] * 100, 1)} points"""
    if k == "puissance":
        return f"""# 1. Les chiffres : la chance de voir l'écart, selon le nombre de répondants
h = 2 * asin(sqrt(pB)) - 2 * asin(sqrt(pA))                # la taille de l'écart : {fr(h)}
points = [(n, NormalIndPower().power(h, nobs1=n, alpha=0.05)) for n in range(10, 201, 2)]

# 2. Le dessin : une courbe qui relie les points, et deux repères
courbe(points)
point({(nA + nB) // 2}, {puissance:.2f})                                  # nous : {pc(puissance)}
point({n80}, 0.80)                                             # 80 % à {n80} répondants par version
ligne_pointillee(0.80)"""
    if k == "logit":
        return f"""# 1. Les chiffres : la régression logistique du choix
modele = smf.logit("michelin ~ version_B + fidelite + qualite + prix + age", reponses).fit()
odds_ratio = exp(modele.params)                    # version B : ×{fr(FOREST[0][1])} ; fidélité : ×{fr(FOREST[1][1])}
intervalle = exp(modele.conf_int())

# 2. Le dessin : une échelle logarithmique, 1 = aucun effet
for variable in odds_ratio.index:
    trait(x(intervalle.loc[variable, 0]), x(intervalle.loc[variable, 1]))
    point(x(odds_ratio[variable]), couleur=BLEU if modele.pvalues[variable] < 0.05 else GRIS)
ligne(x(1))"""
    if k == "mediation":
        return f"""# 1. Les chiffres : les trois chemins
a = smf.ols("duree_percue ~ version_B", reponses).fit().params["version_B"]          # +{fr(MED["a"])}
m = smf.logit("michelin ~ version_B + duree_percue", reponses).fit()
b, c = m.params["duree_percue"], m.params["version_B"]                              # {fr(MED["b"], 3)} et {fr(MED["c"])}
# effet indirect a × b : 5 000 tirages au hasard parmi les répondants (bootstrap)

# 2. Le dessin : trois boîtes, trois flèches
fleche(version, duree_percue, texte=f"a = {{a}}")
fleche(duree_percue, choix, texte=f"b = {{b}}", pointilles=True)    # nul : en gris
fleche(version, choix, texte=f"c′ = {{c}}")"""
    if k == "echelles":
        return f"""# 1. Les chiffres : le poids de chaque affirmation, par analyse factorielle confirmatoire (semopy)
modele = "Fidelite =~ LO1 + LO2 + LO3 ; Qualite =~ QL2 + QL3 ; Prix =~ PR1 + PR2 + PR3"
poids = ...                                                # LO1 : {fr(POIDS["likert_lo1"])} ... PR2 : {fr(POIDS["likert_pr2"])}

# 2. Le dessin : une barre par affirmation, longue de son poids
for item, valeur in poids.items():
    barre(item, longueur=valeur * 310, couleur=BLEU if valeur >= 0.70 else ROUGE)
ligne_pointillee(0.70 * 310)                               # le seuil de 0,70"""
    if k == "rentabilite":
        return f"""# 1. Le calcul : le gain net de la campagne, selon l'effet réel des 10 000 km
def gain(effet):                                   # effet en points
    pneus = 200_000 * effet / {fr(ecart * 100, 1)}               # les ventes suivent l'effet
    return pneus * 20.22 - 2_500_000               # marge brute − coût de la campagne
seuil = 123_614 / 200_000 * {fr(ecart * 100, 1)}                 # gain nul : {fr(SEUIL_EFFET, 1)} points

# 2. Le dessin
droite(de_=(0, gain(0)), a=(45, gain(45)))
bande(de_={fr(ic_ecart[0] * 100, 1)}, a={fr(ic_ecart[1] * 100, 1)})                 # ce que permet notre test
ligne_pointillee(seuil)"""
    if k == "decision":
        return """# des boîtes et des flèches, de la question à la recommandation
boite("Notre question de prix : 97,90 € ou 94,90 € ?")
boite("Baisser à 94,90 € ?")  ;  boite("Garder 97,90 € : avec quel argument ?")
boite("Non : la baisse ne se paie pas")
boite("La marque seule : 45 %")  ;  boite("La durée de vie : 67 %")
fleche(question, baisser)  ;  fleche(question, garder)
fleche(garder, duree_de_vie, couleur=VERT)          # la branche validée par le test A/B
boite("Recommandation : maintenir 97,90 € et vendre la durée de vie")"""
    if k == "trois-prix":
        return f"""# 1. Les trois prix
net = 97.90 / 1.20 * (1 - 0.12)                                    # ce que touche Michelin : {fr(net_actuel)} €
cout_complet = net * (9358 + 396 + 577 + 1215) / 13028             # {fr(cout_complet)} €
prix_couts = cout_complet / (1 - 0.117) / (1 - 0.12) * 1.20        # {fr(TROIS["couts"])} €
prix_concurrence = 93.20                                            # Continental
valeur_usage = 81.99 / 40_000 * 50_000                              # {fr(TROIS["valeur_usage"])} €

# 2. Le dessin : une même échelle, de 65 € à gauche à 105 € à droite
x = lambda prix: 150 + (prix - 65) / 40 * 450
for prix in [prix_couts, prix_concurrence, valeur_usage]:
    point(x(prix))
trait_vertical(x(97.90))                                            # le prix que nous défendons"""
    raise KeyError(k)


def aligne(code):
    """Aligne les commentaires de fin de ligne en une seule colonne, pour que le code se lise d'un coup d'œil."""
    lignes = code.split("\n")
    coupe = [(l.split("  #", 1) if "  #" in l and not l.lstrip().startswith("#") else [l]) for l in lignes]
    large = max((len(c[0].rstrip()) for c in coupe if len(c) == 2), default=0)
    return "\n".join(c[0] if len(c) == 1 else c[0].rstrip().ljust(large) + "   #" + c[1] for c in coupe)


def resume_barres(bloc):
    une = re.search(r'<div class="bar(?: [^"]*)?">.*?</div>', bloc, re.S).group(0)
    return ("<!-- une barre = un <i> dont la largeur (width) est la valeur, rapportée au maximum du graphique -->\n"
            + une + "\n\n/* style.css */\n"
            ".bar .track{background:var(--ciel);height:26px}                  /* la piste */\n"
            ".bar .track i{display:block;height:100%;background:var(--bleu)}  /* la barre */")


def resume_td2(bloc):
    noms = ["coût de revient", "autres coûts", "résultat", "distributeur", "TVA"]
    rects = [re.sub(r"\s*class=\"seg\"|\s*stroke=\"#fff\" stroke-width=\"2\"", "", r) + "/>" for r in re.findall(r'<rect class="seg"[^>]*', bloc)][:5]
    lignes = "\n".join(f"{r}   <!-- {n} -->" for r, n in zip(rects, noms))
    return ("<!-- 3 pixels par euro, 0 € en bas (y = 340) : un segment de 51,57 € fait 154,7 pixels de haut -->\n" + lignes
            + '\n<use href="#col" x="180"/>   <!-- la même colonne, recopiée pour la version B -->\n'
            '<line y1="60.4" y2="60.4" stroke="#C2410C" stroke-dasharray="6 4"/>   <!-- le plafond de Continental, 93,20 € -->')


def resume_graph(bloc):
    chemin = re.search(r"<path [^>]*>", bloc).group(0)
    rond = re.search(r"<circle [^>]*>", bloc).group(0)
    return ("<!-- chaque courbe est un <path> : x = 48 + (prix − 60 €) × 7 ; y = 296 − part × 272 -->\n"
            + chemin + "\n" + rond + "   <!-- un point par prix testé -->")


# =================================================================================================================
# 4. Sous chaque graphique, un bandeau qui montre le code qui l'a dessiné
# =================================================================================================================
import inspect

BRIQUES = [T, L, barre_v, barre_h, point, boite, fleche, defs_fleches, svg, pastille, fr, pc, pval]
CODE = {"modele": [modele], "modele-apres": [modele], "tirage": [groupes], "moderation": [groupes], "controle": [divergentes],
        "jauge-d": [jauge], "jauge-v": [jauge], "choix": [colonnes_ic], "robustesse": [robustesse], "precision": [precision],
        "puissance": [courbe_puissance], "logit": [foret], "mediation": [mediation], "echelles": [poids],
        "rentabilite": [rentabilite], "decision": [decision], "trois-prix": [trois_prix]}


def bandeau(intro, code):
    return (f'<details class="code-fig"><summary>Voir le code de ce graphique</summary><p class="note">{intro}</p>'
            f'<pre class="code"><code>{escape(code)}</code></pre></details>')


def code_python(fonctions):
    """La fonction qui dessine le graphique, puis les briques qu'elle utilise (et celles qu'utilisent ces briques)."""
    src = "\n\n".join(inspect.getsource(f) for f in fonctions)
    vues = list(fonctions)
    while True:
        nouvelles = [b for b in BRIQUES if b not in vues and re.search(rf"\b{b.__name__}\(", src)]
        if not nouvelles:
            break
        vues += nouvelles
        src += "\n\n" + "\n\n".join(inspect.getsource(b) for b in nouvelles)
    return src


INTRO_PY = ("Python, fichier <a href=\"annexes/fabriquer_schemas.py\">annexes/fabriquer_schemas.py</a> : la fonction qui dessine ce graphique, "
            "puis les briques de dessin qu'elle utilise. Les chiffres (parts, tests, intervalles) sont calculés au début du script, "
            "à partir des réponses du questionnaire.")
for k in CODE:
    assert SCHEMAS[k].endswith("</figure>"), k
    SCHEMAS[k] = SCHEMAS[k][:-len("</figure>")] + bandeau(INTRO_COURT, aligne(resume(k))) + "</figure>"


def blocs(html, classe):
    """Les <div class="classe"> ... </div> de la page, avec leurs div imbriquées."""
    out, i, ouvre = [], 0, f'<div class="{classe}">'
    while (a := html.find(ouvre, i)) >= 0:
        prof = 0
        for m in re.finditer(r"<div\b|</div>", html[a:]):
            prof += 1 if m.group().startswith("<div") else -1
            if prof == 0:
                fin = a + m.end()
                break
        out.append((a, fin))
        i = fin
    return out


CSS_BARRES = "\n".join(l for l in (SITE / "style.css").read_text(encoding="utf-8").splitlines()
                       if l.startswith((".bars", ".bar", "@media(max-width:560px){.bar")))
INTRO_BARRES = ("Graphique en HTML et CSS, sans image ni bibliothèque : chaque barre est une balise &lt;i&gt; dont la largeur "
                "(<code>width</code>) est la valeur rapportée au maximum du graphique ; la feuille de style <code>style.css</code> "
                "dessine la piste, la couleur et l'alignement des étiquettes.")
CSS_GRAPH = "\n".join(l for l in (SITE / "style.css").read_text(encoding="utf-8").splitlines() if l.startswith("svg.graph"))
INTRO_GRAPH = ("Graphique SVG écrit directement dans la page : la grille et les axes sont des &lt;line&gt;, chaque courbe est un "
               "&lt;path&gt; dont les points (un prix, une part de répondants) sont convertis en pixels, les points marqués sont des "
               "&lt;circle&gt; et la zone du prix retenu un &lt;rect&gt; ; la feuille de style <code>style.css</code> lui donne son cadre.")
INTRO_TD2 = ("Dessin SVG écrit directement dans la page : chaque segment est un rectangle &lt;rect&gt; dont la hauteur vaut 3 pixels "
             "par euro (0 € en y = 340, 100 € en y = 40) ; la seconde colonne réutilise la première avec &lt;use&gt;.")


# =================================================================================================================
# 5. Placer les schémas dans les pages
# =================================================================================================================
# chaque page reçoit les schémas dont elle porte les balises, numérotés dans l'ordre où ils apparaissent
for chemin in sorted(SITE.glob("*.html")):
    page = chemin.name
    html = chemin.read_text(encoding="utf-8")
    noms = re.findall(r"<!-- schema:([\w-]+) -->", html)
    if not noms:
        continue
    for n in noms:
        motif = re.compile(rf"(<!-- schema:{re.escape(n)} -->)(.*?)(<!-- /schema:{re.escape(n)} -->)", re.S)
        if not motif.search(html):
            raise SystemExit(f"{page} : balises <!-- schema:{n} --> introuvables")
        html = motif.sub(lambda m: m.group(1) + "\n" + SCHEMAS[n] + "\n" + m.group(3), html)
    numero = iter(range(1, 100))
    html = re.sub(r"<figcaption><b>Schéma \d+</b>", lambda m: f"<figcaption><b>Schéma {next(numero)}</b>", html)
    chemin.write_text(html, encoding="utf-8")
    print(f"{page} : {len(noms)} schéma(s) placé(s)")
# les graphiques écrits à la main dans les pages (barres HTML, graphique du TD 2) reçoivent le même bandeau
for chemin in sorted(SITE.glob("*.html")):
    html = chemin.read_text(encoding="utf-8")
    propre = re.sub(r"<!-- code:auto -->.*?<!-- /code:auto -->\n?", "", html, flags=re.S)
    ajouts = []
    for classe in ("bars", "td2", "graph"):
        for a, b in (blocs(propre, classe) if classe != "graph" else
                     [(m.start(), propre.index("</svg>", m.start()) + 6) for m in re.finditer(r'<svg class="graph"', propre)]):
            bloc = propre[a:b]
            if classe == "bars":
                code = resume_barres(bloc)
                intro = INTRO_BARRES
            elif classe == "graph":
                code = resume_graph(bloc)
                intro = INTRO_GRAPH
            else:
                style = re.search(r"<style>(.*?)</style>", propre, re.S).group(1).strip()
                code, intro = resume_td2(bloc), INTRO_TD2
            ajouts.append((b, "\n<!-- code:auto -->" + bandeau(intro, code) + "<!-- /code:auto -->"))
    for b, texte_ in sorted(ajouts, reverse=True):
        propre = propre[:b] + texte_ + propre[b:]
    if propre != html:
        chemin.write_text(propre, encoding="utf-8")
        print(f"{chemin.name} : {len(ajouts)} graphique(s) HTML avec leur code")
print(f"Test A/B : {pc(pA)} contre {pc(pB)}, {pval(p_chi2)} ; puissance {pc(puissance)} ; point mort de l'effet {fr(SEUIL_EFFET, 1)} points")
