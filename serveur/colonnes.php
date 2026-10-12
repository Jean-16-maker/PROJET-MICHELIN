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
    'importance_prix', 'importance_marque', 'importance_duree', 'importance_performance',
    'achat_garage', 'achat_specialiste', 'achat_centre_auto', 'achat_internet', 'achat_reparateur_rapide',
];

/* Mêmes valeurs que dans questionnaire.html.
   Variante A (notoriété) : Hankook 40 000 km contre Michelin 40 000 km.
   Variante B (durée de vie) : Hankook 40 000 km contre Michelin 50 000 km. */
const PRIX_HANKOOK = 81.99;
const PRIX_MICHELIN = 97.90;
