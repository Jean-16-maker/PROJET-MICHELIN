<?php
/**
 * Colonnes du questionnaire, dans l'ordre de l'export.
 * Une ligne par répondant ; ne pas changer les colonnes une fois la collecte lancée
 * (ajouter une nouvelle question à la fin de la liste).
 */
const COLONNES = [
    'horodatage', 'id', 'test', 'version', 'duree_s',
    'consentement', 'age', 'voiture', 'cible', 'km_an',
    'choix_pneu',
    // Likert 1 à 5, Yoo et Donthu (2001) : fidélité à la marque (LO1-LO3), qualité perçue (QL2-QL3) ; prix = item du groupe
    'likert_lo1', 'likert_lo2', 'likert_lo3', 'likert_ql2', 'likert_ql3', 'likert_prix',
    'achat_garage', 'achat_specialiste', 'achat_centre_auto', 'achat_internet', 'achat_reparateur_rapide',
];

/* Mêmes valeurs que dans questionnaire.html.
   Variante A (notoriété) : Hankook 40 000 km contre Michelin 40 000 km.
   Variante B (durée de vie) : Hankook 40 000 km contre Michelin 50 000 km. */
const PRIX_HANKOOK = 81.99;
const PRIX_MICHELIN = 97.90;
