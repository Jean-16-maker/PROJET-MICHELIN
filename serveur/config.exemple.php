<?php
/**
 * Copier ce fichier en « config.php » sur l'hébergement, puis y mettre l'empreinte du mot de passe.
 * config.php n'est jamais publié sur GitHub (voir .gitignore) : le dépôt est public.
 */

/* Empreinte SHA-256 du mot de passe de la page d'extraction (export.php), en hexadécimal.
   Le mot de passe lui-même n'est écrit nulle part sur le serveur. Pour la calculer :
   printf '%s' 'votre-mot-de-passe' | shasum -a 256   (sur Mac)   ou   sha256sum   (sous Linux) */
const MOT_DE_PASSE_EXPORT_SHA256 = '';

/* Sites autorisés à envoyer des réponses : l'adresse GitHub Pages du questionnaire, sans chemin. */
const ORIGINES_AUTORISEES = ['https://jean-16-maker.github.io'];

/* Dossier où sont écrites les réponses. Par défaut serveur/donnees/, protégé par un .htaccess.
   Mieux encore : un dossier hors du site web, si l'hébergeur le permet. */
const DOSSIER_DONNEES = __DIR__ . '/donnees';
