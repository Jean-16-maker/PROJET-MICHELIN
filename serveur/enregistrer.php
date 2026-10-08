<?php
/**
 * Reçoit une réponse du questionnaire (POST, corps JSON) et l'ajoute à donnees/reponses.jsonl.
 * Une ligne JSON par répondant. L'adresse IP n'est pas enregistrée.
 */
declare(strict_types=1);
date_default_timezone_set('Europe/Paris');
require __DIR__ . '/config.php';
require __DIR__ . '/colonnes.php';

function repondre(int $code, array $corps): void
{
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($corps);
    exit;
}

$origine = $_SERVER['HTTP_ORIGIN'] ?? '';
if (in_array($origine, ORIGINES_AUTORISEES, true)) {
    header('Access-Control-Allow-Origin: ' . $origine);
    header('Vary: Origin');
}

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: POST');
    header('Access-Control-Allow-Headers: Content-Type');
    http_response_code(204);
    exit;
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    repondre(405, ['ok' => false, 'erreur' => 'POST attendu']);
}

$brut = file_get_contents('php://input', false, null, 0, 20000);
if ($brut === false || $brut === '' || strlen($brut) >= 20000) {
    repondre(400, ['ok' => false, 'erreur' => 'corps vide ou trop long']);
}
$recu = json_decode($brut, true);
if (!is_array($recu) || !isset($recu['id'], $recu['version'])) {
    repondre(400, ['ok' => false, 'erreur' => 'JSON invalide']);
}

/* On ne garde que les colonnes prévues, avec des valeurs courtes. */
$ligne = [];
foreach (COLONNES as $c) {
    if ($c === 'horodatage') {
        $ligne[$c] = date('Y-m-d H:i:s');
        continue;
    }
    $v = $recu[$c] ?? '';
    if (is_int($v) || is_float($v)) {
        $ligne[$c] = $v;
    } elseif (is_string($v)) {
        $ligne[$c] = substr(trim($v), 0, 100);
    } else {
        $ligne[$c] = '';
    }
}

if (!is_dir(DOSSIER_DONNEES) && !mkdir(DOSSIER_DONNEES, 0700, true)) {
    repondre(500, ['ok' => false, 'erreur' => 'dossier de données impossible à créer']);
}
$f = fopen(DOSSIER_DONNEES . '/reponses.jsonl', 'ab');
if ($f === false || !flock($f, LOCK_EX)) {
    repondre(500, ['ok' => false, 'erreur' => 'fichier de données inaccessible']);
}
fwrite($f, json_encode($ligne, JSON_UNESCAPED_UNICODE) . "\n");
fflush($f);
flock($f, LOCK_UN);
fclose($f);

repondre(200, ['ok' => true]);
