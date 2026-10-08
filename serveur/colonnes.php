<?php
/**
 * Colonnes du questionnaire, dans l'ordre de l'export.
 * Une ligne par répondant ; ne pas changer les colonnes une fois la collecte lancée
 * (ajouter une nouvelle question à la fin de la liste).
 */
const COLONNES = [
    'horodatage', 'id', 'test', 'version', 'duree_s',
    'consentement', 'filtre_voiture', 'filtre_decide', 'cible',
    'vw_trop_bon_marche', 'vw_bon_marche', 'vw_cher', 'vw_trop_cher', 'vw_coherent',
    'gg_119_90', 'gg_109_90', 'gg_104_90', 'gg_99_90', 'gg_97_90', 'gg_94_90', 'gg_92_90',
    'gg_prix_max_michelin', 'prime_max',
    'controle', 'likert_vaut_ecart', 'likert_qualite', 'likert_confiance', 'critere_principal',
    'pneus_actuels', 'dernier_prix', 'gamme_marque',
    'age', 'km_an', 'canal_achat',
];

/* Prix du Michelin proposés dans Gabor-Granger, face à l'autre pneu à PRIX_AUTRE. */
const PRIX_GG = [119.90, 109.90, 104.90, 99.90, 97.90, 94.90, 92.90];
const PRIX_AUTRE = 93;
