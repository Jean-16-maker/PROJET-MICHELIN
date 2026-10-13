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
    // Likert 1 à 5 : Yoo et Donthu (2001), fidélité (LO1-LO3) et qualité perçue (QL2-QL3) ;
    // Sproles et Kendall (1986), conscience du prix « value for money » (PR1-PR3)
    'likert_lo1', 'likert_lo2', 'likert_lo3', 'likert_ql2', 'likert_ql3', 'likert_pr1', 'likert_pr2', 'likert_pr3',
    'achat_garage', 'achat_specialiste', 'achat_centre_auto', 'achat_internet', 'achat_reparateur_rapide',
];

/* Mêmes valeurs que dans questionnaire.html.
   Variante A (notoriété) : Hankook 40 000 km contre Michelin 40 000 km.
   Variante B (durée de vie) : Hankook 40 000 km contre Michelin 50 000 km. */
const PRIX_HANKOOK = 81.99;
const PRIX_MICHELIN = 97.90;
