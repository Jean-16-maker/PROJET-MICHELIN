<?php
/**
 * Colonnes du questionnaire, dans l'ordre de l'export.
 * Une ligne par répondant ; ne pas changer les colonnes une fois la collecte lancée
 * (ajouter une nouvelle question à la fin de la liste).
 */
const COLONNES = [
    'horodatage', 'id', 'test', 'version', 'duree_s',
    'consentement', 'age', 'voiture', 'cible', 'km_an',
    'accepte_plus_15',
    'likert_justifie_prix',
    'importance_prix', 'importance_marque', 'importance_duree', 'importance_performance',
    'achat_garage', 'achat_specialiste', 'achat_centre_auto', 'achat_internet', 'achat_reparateur_rapide',
];

/* Mêmes valeurs que dans questionnaire.html.
   Version A : « 15 € de plus par pneu » ; version B : la même hausse, ramenée à 1,50 € tous les 1 000 km. */
const PRIX_STANDARD = 97.90;   // CrossClimate 3, 40 000 km
const HAUSSE = 15;             // hausse testée pour la version renforcée, 50 000 km
