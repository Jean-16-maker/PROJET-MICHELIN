<?php
/**
 * Colonnes du questionnaire, dans l'ordre de l'export.
 * Une ligne par répondant ; ne pas changer les colonnes une fois la collecte lancée
 * (ajouter une nouvelle question à la fin de la liste).
 */
const COLONNES = [
    'horodatage', 'id', 'test', 'version', 'duree_s',
    'consentement', 'filtre_decide', 'cible',
    'prix_max_pneu1', 'montage_domicile_15',
    'likert_vaut_supplement', 'likert_croit_duree', 'likert_confiance', 'critere_principal',
    'age', 'km_an', 'canal_achat',
];

/* Mêmes valeurs que dans questionnaire.html. */
const PRIX_AUTRE = 93;   // pneu 2, 40 000 km
const SUPPLEMENT = 15;   // montage à domicile, par pneu
