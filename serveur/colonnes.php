<?php
/**
 * Colonnes du questionnaire, dans l'ordre de l'export.
 * Une ligne par répondant ; ne pas changer les colonnes une fois la collecte lancée
 * (ajouter une nouvelle question à la fin de la liste).
 */
const COLONNES = [
    'horodatage', 'id', 'test', 'version', 'duree_s',
    'consentement', 'filtre_decide', 'cible',
    'sup_15', 'prix_max_pneu1',
    'controle', 'age', 'km_an',
];

/* Mêmes valeurs que dans questionnaire.html. */
const PRIX_AUTRE = 93;   // pneu 2, 40 000 km
const SUPPLEMENT = 15;   // proposé pour le pneu 1, 50 000 km
