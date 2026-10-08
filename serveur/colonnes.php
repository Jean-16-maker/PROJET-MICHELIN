<?php
/**
 * Colonnes du questionnaire, dans l'ordre de l'export.
 * Une ligne par répondant ; ne pas changer les colonnes une fois la collecte lancée
 * (ajouter une nouvelle question à la fin de la liste).
 */
const COLONNES = [
    'horodatage', 'id', 'test', 'version', 'duree_s',
    'consentement', 'age', 'voiture', 'cible',
    'prix_max', 'accepte_plus_10',
    'likert_justifie_prix', 'likert_croit_duree', 'likert_economie', 'critere_principal',
    'km_an',
];

/* Mêmes valeurs que dans questionnaire.html. Version A : 40 000 km ; version B : 50 000 km. */
const PRIX_ACTUEL = 97.90;   // prix relevé du CrossClimate 3
const HAUSSE = 10;           // hausse testée, par pneu
