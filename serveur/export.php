<?php
/**
 * Extraction des réponses du questionnaire, protégée par mot de passe (config.php).
 * - un tableau de bord : nombre de réponses et premiers résultats par version A / B ;
 * - le téléchargement en CSV, pour Excel (« ; » et virgule décimale) ou standard (« , »),
 *   avec toutes les réponses ou seulement les réponses exploitables.
 */
declare(strict_types=1);
date_default_timezone_set('Europe/Paris');
require __DIR__ . '/config.php';
require __DIR__ . '/colonnes.php';

session_start();
header('X-Robots-Tag: noindex');

function h($s): string { return htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8'); }

/* ---------- Connexion ---------- */
$erreur = '';
if (isset($_POST['deconnexion'])) {
    $_SESSION = [];
    session_destroy();
    header('Location: export.php');
    exit;
}
if (isset($_POST['mot_de_passe'])) {
    if (MOT_DE_PASSE_EXPORT !== 'a-changer' && strlen(MOT_DE_PASSE_EXPORT) >= 12
        && hash_equals(MOT_DE_PASSE_EXPORT, (string) $_POST['mot_de_passe'])) {
        session_regenerate_id(true);
        $_SESSION['export_ok'] = true;
        header('Location: export.php');
        exit;
    }
    sleep(2); // ralentit les essais de mot de passe
    $erreur = MOT_DE_PASSE_EXPORT === 'a-changer' || strlen(MOT_DE_PASSE_EXPORT) < 12
        ? 'Changez d’abord le mot de passe dans config.php (12 caractères au moins).'
        : 'Mot de passe incorrect.';
}
$connecte = !empty($_SESSION['export_ok']);

/* ---------- Lecture des réponses ---------- */
function lire_reponses(): array
{
    $fichier = DOSSIER_DONNEES . '/reponses.jsonl';
    if (!is_file($fichier)) return [];
    $lignes = [];
    foreach (file($fichier, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $l) {
        $d = json_decode($l, true);
        if (is_array($d)) $lignes[] = $d;
    }
    return $lignes;
}

/* Exploitable : pas un essai, et la personne choisit elle-même ses pneus. */
function exploitable(array $r): bool
{
    return (string) ($r['test'] ?? '') === '0' && (string) ($r['cible'] ?? '') === '1';
}

/* ---------- Téléchargement CSV ---------- */
if ($connecte && isset($_GET['telecharger'])) {
    $excel = ($_GET['format'] ?? 'excel') === 'excel';
    $propres = ($_GET['quoi'] ?? 'tout') === 'exploitables';
    $reponses = lire_reponses();
    if ($propres) $reponses = array_values(array_filter($reponses, 'exploitable'));

    $sep = $excel ? ';' : ',';
    $nom = 'reponses-questionnaire-' . ($propres ? 'exploitables-' : '') . date('Y-m-d') . '.csv';
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="' . $nom . '"');
    $out = fopen('php://output', 'wb');
    if ($excel) fwrite($out, "\xEF\xBB\xBF"); // BOM : Excel lit l'UTF-8 et les accents
    fputcsv($out, COLONNES, $sep, '"', '');
    foreach ($reponses as $r) {
        $ligne = [];
        foreach (COLONNES as $c) {
            $v = $r[$c] ?? '';
            if ($excel && (is_float($v) || is_int($v))) $v = str_replace('.', ',', (string) $v);
            if (is_string($v) && preg_match('/^[=+\-@]/', $v)) $v = "'" . $v; // pas de formule dans Excel
            $ligne[] = $v;
        }
        fputcsv($out, $ligne, $sep, '"', '');
    }
    fclose($out);
    exit;
}

/* ---------- Statistiques du tableau de bord ---------- */
function moyenne(array $x): ?float { return $x ? array_sum($x) / count($x) : null; }
function mediane(array $x): ?float
{
    if (!$x) return null;
    sort($x);
    $n = count($x);
    return (float) ($n % 2 ? $x[intdiv($n, 2)] : ($x[$n / 2 - 1] + $x[$n / 2]) / 2);
}
function nb($x, int $dec = 0): string { return $x === null ? '—' : number_format((float) $x, $dec, ',', ' '); }
function pct(int $a, int $b): string { return $b ? number_format(100 * $a / $b, 0, ',', ' ') . ' %' : '—'; }

/* Paliers de la jauge pour la répartition des prix maximum. */
const LIKERT = ['likert_vaut_supplement' => '« 10 000 km de plus valent un prix plus élevé »', 'likert_croit_duree' => '« Je crois à la durée de vie annoncée »', 'likert_confiance' => '« Confiance pour la sécurité »'];
const CRITERES = ['prix' => 'le prix', 'securite' => 'la sécurité', 'duree_de_vie' => 'la durée de vie', 'marque' => 'la marque', 'conseil' => 'le conseil du vendeur'];
const PALIERS = [[60, 89, 'moins de 90 €'], [90, 99, '90 à 99 €'], [100, 107, '100 à 107 €'], [108, 119, '108 à 119 €'], [120, 140, '120 € et plus']];

$stats = null;
if ($connecte) {
    $toutes = lire_reponses();
    $stats = [
        'total' => count($toutes),
        'test' => count(array_filter($toutes, fn($r) => (string) ($r['test'] ?? '') === '1')),
        'hors_cible' => count(array_filter($toutes, fn($r) => (string) ($r['test'] ?? '') === '0' && (string) ($r['cible'] ?? '') === '0')),
        'versions' => [],
    ];
    $propres = array_filter($toutes, 'exploitable');
    foreach (['A', 'B'] as $v) {
        $g = array_values(array_filter($propres, fn($r) => ($r['version'] ?? '') === $v));
        $prix = array_map('floatval', array_values(array_filter(array_map(fn($r) => $r['prix_max_pneu1'] ?? '', $g), 'is_numeric')));
        $oui = count(array_filter($g, fn($r) => ($r['montage_domicile_15'] ?? '') === 'oui'));
        $repartition = [];
        foreach (PALIERS as [$min, $max, $libelle]) {
            $repartition[$libelle] = pct(count(array_filter($prix, fn($x) => $x >= $min && $x <= $max)), count($prix));
        }
        $stats['versions'][$v] = [
            'n' => count($g),
            'oui' => $oui,
            'oui_pct' => pct($oui, count($g)),
            'prix_moy' => moyenne($prix),
            'prix_med' => mediane($prix),
            'prime_moy' => $prix ? moyenne($prix) - PRIX_AUTRE : null,
            'repartition' => $repartition,
            'likert' => array_combine(array_keys(LIKERT), array_map(fn($col) => moyenne(array_map('floatval', array_values(array_filter(array_map(fn($r) => $r[$col] ?? '', $g), 'is_numeric')))), array_keys(LIKERT))),
            'critere' => array_combine(array_keys(CRITERES), array_map(fn($k) => pct(count(array_filter($g, fn($r) => ($r['critere_principal'] ?? '') === $k)), count($g)), array_keys(CRITERES))),
            'duree_med' => mediane(array_map('floatval', array_values(array_filter(array_map(fn($r) => $r['duree_s'] ?? '', $g), 'is_numeric')))),
        ];
    }
}
$A = $stats['versions']['A'] ?? null;
$B = $stats['versions']['B'] ?? null;
?>
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Réponses du questionnaire</title>
<style>
:root{--bleu:#27509B;--bleu-fonce:#0F2A5C;--jaune:#FCE500;--fond:#F6F8FC;--carte:#fff;--encre:#10203F;--gris:#566179;--trait:#D5DDEC;--alerte:#C2410C}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 "Helvetica Neue","Segoe UI",system-ui,Arial,sans-serif;color:var(--encre);background:var(--fond)}
header{background:var(--bleu);color:#fff;border-bottom:4px solid var(--jaune);padding:14px 16px;font-weight:800;letter-spacing:.04em;text-transform:uppercase}
main{max-width:900px;margin:0 auto;padding:24px 16px 60px}
h1{font-size:1.6rem;margin:0 0 6px;color:var(--bleu)} h2{font-size:1.2rem;margin:28px 0 10px;color:var(--bleu-fonce)}
.carte{background:var(--carte);border:1px solid var(--trait);border-radius:12px;padding:16px 18px;margin:0 0 14px}
.chiffres{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.chiffres b{display:block;font-size:1.8rem;color:var(--bleu)} .chiffres span{color:var(--gris);font-size:.88rem}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{border-bottom:1px solid var(--trait);padding:7px 8px;text-align:left} td.n,th.n{text-align:right}
tr.cle td{font-weight:700;background:#FFFBD1}
.tableau{overflow-x:auto}
.note{color:var(--gris);font-size:.88rem}
form.inline{display:inline}
button,.bouton{display:inline-block;font:700 .95rem/1 inherit;padding:11px 16px;border-radius:999px;border:0;background:var(--jaune);color:var(--bleu-fonce);text-decoration:none;cursor:pointer;margin:4px 6px 4px 0}
.second{background:#fff;color:var(--bleu);border:1px solid var(--trait)}
input[type=password]{font:inherit;padding:10px 12px;border:1px solid var(--trait);border-radius:10px;width:100%;max-width:320px}
.erreur{color:var(--alerte);font-weight:700}
</style>
</head>
<body>
<header>Questionnaire Michelin · réponses</header>
<main>
<?php if (!$connecte): ?>
<h1>Réponses du questionnaire</h1>
<p class="note">Accès réservé au groupe.</p>
<form method="post" class="carte">
<p><label for="mdp"><b>Mot de passe</b></label></p>
<p><input id="mdp" type="password" name="mot_de_passe" autocomplete="current-password" required autofocus></p>
<?php if ($erreur): ?><p class="erreur"><?= h($erreur) ?></p><?php endif; ?>
<button type="submit">Entrer</button>
</form>
<?php else: ?>
<h1>Réponses du questionnaire</h1>
<p class="note">Mis à jour à chaque ouverture de la page · <?= h(date('d/m/Y H:i')) ?></p>

<div class="carte chiffres">
<div><b><?= $stats['total'] ?></b><span>réponses enregistrées</span></div>
<div><b><?= $stats['test'] ?></b><span>essais (test = 1)</span></div>
<div><b><?= $stats['hors_cible'] ?></b><span>hors cible (ne choisit pas ses pneus, ou sans voiture)</span></div>
<div><b><?= $A['n'] + $B['n'] ?></b><span>réponses exploitables</span></div>
</div>

<h2>Télécharger</h2>
<div class="carte">
<a class="bouton" href="?telecharger=1&amp;format=excel&amp;quoi=exploitables">Réponses exploitables · Excel</a>
<a class="bouton" href="?telecharger=1&amp;format=excel&amp;quoi=tout">Toutes les réponses · Excel</a>
<a class="bouton second" href="?telecharger=1&amp;format=csv&amp;quoi=tout">Toutes · CSV standard (R, Python)</a>
<p class="note">Excel : séparateur « ; » et virgule décimale. CSV standard : séparateur « , » et point décimal. Exploitables = hors essais, et la personne choisit elle-même ses pneus.</p>
</div>

<h2>Premiers résultats (réponses exploitables)</h2>
<div class="carte tableau">
<table>
<thead><tr><th></th><th class="n">Version A<br><span class="note">pneu 1 sans marque</span></th><th class="n">Version B<br><span class="note">pneu 1 Michelin</span></th></tr></thead>
<tbody>
<tr><td>Répondants</td><td class="n"><?= $A['n'] ?></td><td class="n"><?= $B['n'] ?></td></tr>
<tr class="cle"><td>Jauge : prix maximum pour le pneu 1, moyenne</td><td class="n"><?= nb($A['prix_moy'], 1) ?> €</td><td class="n"><?= nb($B['prix_moy'], 1) ?> €</td></tr>
<tr><td>Jauge : prix maximum, médiane</td><td class="n"><?= nb($A['prix_med']) ?> €</td><td class="n"><?= nb($B['prix_med']) ?> €</td></tr>
<tr><td>Supplément moyen accepté par rapport au pneu 2 (<?= PRIX_AUTRE ?> €)</td><td class="n"><?= nb($A['prime_moy'], 1) ?> €</td><td class="n"><?= nb($B['prime_moy'], 1) ?> €</td></tr>
<?php foreach (array_keys($A['repartition']) as $l): ?>
<tr><td>Jauge : <?= h($l) ?></td><td class="n"><?= $A['repartition'][$l] ?></td><td class="n"><?= $B['repartition'][$l] ?></td></tr>
<?php endforeach; ?>
<tr class="cle"><td>Prêts à payer <?= SUPPLEMENT ?> € de plus par pneu pour le montage à domicile</td><td class="n"><?= $A['oui_pct'] ?> <span class="note">(<?= $A['oui'] ?>)</span></td><td class="n"><?= $B['oui_pct'] ?> <span class="note">(<?= $B['oui'] ?>)</span></td></tr>
<?php foreach (LIKERT as $col => $libelle): ?>
<tr><td>Avis <?= h($libelle) ?>, moyenne sur 5</td><td class="n"><?= nb($A['likert'][$col], 1) ?></td><td class="n"><?= nb($B['likert'][$col], 1) ?></td></tr>
<?php endforeach; ?>
<?php foreach (CRITERES as $k => $libelle): ?>
<tr><td>Critère principal : <?= h($libelle) ?></td><td class="n"><?= $A['critere'][$k] ?></td><td class="n"><?= $B['critere'][$k] ?></td></tr>
<?php endforeach; ?>
<tr><td>Durée de réponse, médiane</td><td class="n"><?= nb($A['duree_med']) ?> s</td><td class="n"><?= nb($B['duree_med']) ?> s</td></tr>
</tbody>
</table>
<p class="note">Lecture : la version A mesure ce que valent 10 000 km de plus pour un pneu sans marque ; la version B, pour le Michelin. L'écart entre B et A mesure ce qu'ajoute le nom Michelin. Avec peu de répondants par version, un petit écart peut être dû au hasard : les tests statistiques se feront en Analyse de données.</p>
</div>

<form method="post" class="inline"><button class="second" name="deconnexion" value="1">Se déconnecter</button></form>
<?php endif; ?>
</main>
</body>
</html>
