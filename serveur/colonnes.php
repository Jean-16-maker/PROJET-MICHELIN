<?php
/**
 * Colonnes du questionnaire, dans l'ordre de l'export.
 * Une ligne par répondant ; ne pas changer les colonnes une fois la collecte lancée
 * (ajouter une nouvelle question à la fin de la liste).
 */
const COLONNES = [
    'horodatage', 'id', 'test', 'version', 'duree_s',
    'consentement', 'filtre_voiture', 'filtre_decide', 'cible',
    'sup_30', 'sup_25', 'sup_20', 'sup_15', 'sup_10', 'sup_5',
    'supplement_max', 'prix_max_pneu1',
    'vw_trop_bon_marche', 'vw_bon_marche', 'vw_cher', 'vw_trop_cher', 'vw_coherent',
    'controle', 'likert_vaut_supplement', 'likert_croit_duree', 'likert_confiance', 'critere_principal',
    'age', 'km_an', 'canal_achat',
];

/* Mêmes valeurs que dans questionnaire.html. */
const PRIX_AUTRE = 93;                         // pneu 2, 40 000 km
const SUPPLEMENTS = [30, 25, 20, 15, 10, 5];   // proposés pour le pneu 1, 50 000 km
const TRANCHES = ['<60', '60-70', '70-80', '80-90', '90-100', '100-110', '110-120', '120-130', '>130'];
