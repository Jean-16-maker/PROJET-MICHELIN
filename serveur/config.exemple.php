<?php
/**
 * Copier ce fichier en « config.php » sur l'hébergement, puis changer le mot de passe.
 * config.php n'est jamais publié sur GitHub (voir .gitignore) : le dépôt est public.
 */

/* Mot de passe de la page d'extraction (export.php). Au moins 12 caractères. */
const MOT_DE_PASSE_EXPORT = 'a-changer';

/* Sites autorisés à envoyer des réponses : l'adresse GitHub Pages du questionnaire, sans chemin. */
const ORIGINES_AUTORISEES = ['https://jean-16-maker.github.io'];

/* Dossier où sont écrites les réponses. Par défaut serveur/donnees/, protégé par un .htaccess.
   Mieux encore : un dossier hors du site web, si l'hébergeur le permet. */
const DOSSIER_DONNEES = __DIR__ . '/donnees';
