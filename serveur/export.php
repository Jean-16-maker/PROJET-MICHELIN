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

/* Exploitable : pas un essai, dans la cible, réponses Van Westendorp cohérentes. */
function exploitable(array $r): bool
{
    return (string) ($r['test'] ?? '') === '0' && (string) ($r['cible'] ?? '') === '1'
        && (string) ($r['vw_coherent'] ?? '') === '1';
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
    return $n % 2 ? $x[intdiv($n, 2)] : ($x[$n / 2 - 1] + $x[$n / 2]) / 2;
}
function nb($x, int $dec = 2): string { return $x === null ? '—' : number_format((float) $x, $dec, ',', ' '); }
function pct(int $a, int $b): string { return $b ? number_format(100 * $a / $b, 0, ',', ' ') . ' %' : '—'; }

$stats = null;
if ($connecte) {
    $toutes = lire_reponses();
    $stats = [
        'total' => count($toutes),
        'test' => count(array_filter($toutes, fn($r) => (string) ($r['test'] ?? '') === '1')),
        'hors_cible' => count(array_filter($toutes, fn($r) => (string) ($r['test'] ?? '') === '0' && (string) ($r['cible'] ?? '') === '0')),
        'incoherents' => count(array_filter($toutes, fn($r) => (string) ($r['test'] ?? '') === '0' && (string) ($r['cible'] ?? '') === '1' && (string) ($r['vw_coherent'] ?? '') === '0')),
        'versions' => [],
    ];
    $propres = array_filter($toutes, 'exploitable');
    foreach (['A', 'B'] as $v) {
        $g = array_values(array_filter($propres, fn($r) => ($r['version'] ?? '') === $v));
        $max = array_values(array_filter(array_map(fn($r) => $r['gg_prix_max_michelin'] ?? '', $g), 'is_numeric'));
        $max = array_map('floatval', $max);
        $controle_ok = count(array_filter($g, fn($r) => ($r['controle'] ?? '') === ($v === 'B' ? 'oui' : 'non')));
        $parPrix = [];
        foreach (PRIX_GG as $p) {
            // Arrêt au premier choix du Michelin : il l'aurait aussi choisi à tous les prix plus bas.
            $parPrix[number_format($p, 2, ',', '')] = pct(count(array_filter($max, fn($m) => $m >= $p - 0.001)), count($g));
        }
        $stats['versions'][$v] = [
            'n' => count($g),
            'controle_ok' => pct($controle_ok, count($g)),
            'max_moy' => moyenne($max),
            'max_med' => mediane($max),
            'prime_moy' => moyenne(array_map(fn($m) => $m - PRIX_AUTRE, $max)),
            'jamais' => count($g) - count($max),
            'par_prix' => $parPrix,
            'vw_cher_med' => mediane(array_map(fn($r) => (float) $r['vw_cher'], $g)),
            'vw_trop_cher_med' => mediane(array_map(fn($r) => (float) $r['vw_trop_cher'], $g)),
        ];
    }
}
?>
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Réponses du questionnaire</title>
<style>
:root{--accent:#2F5D62;--fond:#F5F6F7;--carte:#fff;--encre:#1D2327;--gris:#5C6670;--trait:#D7DCE0;--alerte:#B3261E}
@media (prefers-color-scheme: dark){:root{--accent:#7FB7BC;--fond:#15191C;--carte:#1F2529;--encre:#E7EAEC;--gris:#A3ADB5;--trait:#36404A;--alerte:#F2857D}}
*{box-sizing:border-box}
body{margin:0;font:16px/1.55 "Helvetica Neue","Segoe UI",system-ui,Arial,sans-serif;color:var(--encre);background:var(--fond)}
main{max-width:900px;margin:0 auto;padding:24px 16px 60px}
h1{font-size:1.6rem;margin:0 0 6px} h2{font-size:1.2rem;margin:28px 0 10px}
.carte{background:var(--carte);border:1px solid var(--trait);border-radius:12px;padding:16px 18px;margin:0 0 14px}
.chiffres{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.chiffres b{display:block;font-size:1.8rem;color:var(--accent)} .chiffres span{color:var(--gris);font-size:.88rem}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
th,td{border-bottom:1px solid var(--trait);padding:7px 8px;text-align:left} td.n,th.n{text-align:right}
.tableau{overflow-x:auto}
.note{color:var(--gris);font-size:.88rem}
form.inline{display:inline}
button,.bouton{display:inline-block;font:700 .95rem/1 inherit;padding:11px 16px;border-radius:999px;border:0;background:var(--accent);color:#fff;text-decoration:none;cursor:pointer;margin:4px 6px 4px 0}
.second{background:transparent;color:var(--accent);border:1px solid var(--trait)}
input[type=password]{font:inherit;padding:10px 12px;border:1px solid var(--trait);border-radius:10px;width:100%;max-width:320px;background:var(--carte);color:var(--encre)}
.erreur{color:var(--alerte);font-weight:700}
</style>
</head>
<body>
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
<div><b><?= $stats['hors_cible'] ?></b><span>hors cible</span></div>
<div><b><?= $stats['incoherents'] ?></b><span>Van Westendorp incohérent, écartés</span></div>
<div><b><?= $stats['versions']['A']['n'] + $stats['versions']['B']['n'] ?></b><span>réponses exploitables</span></div>
</div>

<h2>Télécharger</h2>
<div class="carte">
<a class="bouton" href="?telecharger=1&amp;format=excel&amp;quoi=exploitables">Réponses exploitables · Excel</a>
<a class="bouton" href="?telecharger=1&amp;format=excel&amp;quoi=tout">Toutes les réponses · Excel</a>
<a class="bouton second" href="?telecharger=1&amp;format=csv&amp;quoi=tout">Toutes · CSV standard (R, Python)</a>
<p class="note">Excel : séparateur « ; » et virgule décimale. CSV standard : séparateur « , » et point décimal. Exploitables = hors essais, dans la cible, Van Westendorp cohérent.</p>
</div>

<h2>Premiers résultats (réponses exploitables)</h2>
<div class="carte tableau">
<table>
<thead><tr><th></th><th class="n">Version A<br><span class="note">sans durée de vie</span></th><th class="n">Version B<br><span class="note">+ 10 000 km annoncés</span></th></tr></thead>
<tbody>
<tr><td>Répondants</td><td class="n"><?= $stats['versions']['A']['n'] ?></td><td class="n"><?= $stats['versions']['B']['n'] ?></td></tr>
<tr><td>Contrôle réussi (B : a vu les km ; A : ne les a pas vus)</td><td class="n"><?= $stats['versions']['A']['controle_ok'] ?></td><td class="n"><?= $stats['versions']['B']['controle_ok'] ?></td></tr>
<tr><td>Prix maximum accepté pour le Michelin, moyenne</td><td class="n"><?= nb($stats['versions']['A']['max_moy']) ?> €</td><td class="n"><?= nb($stats['versions']['B']['max_moy']) ?> €</td></tr>
<tr><td>Prix maximum accepté pour le Michelin, médiane</td><td class="n"><?= nb($stats['versions']['A']['max_med']) ?> €</td><td class="n"><?= nb($stats['versions']['B']['max_med']) ?> €</td></tr>
<tr><td>Prime moyenne acceptée sur l'autre pneu (<?= PRIX_AUTRE ?> €)</td><td class="n"><?= nb($stats['versions']['A']['prime_moy']) ?> €</td><td class="n"><?= nb($stats['versions']['B']['prime_moy']) ?> €</td></tr>
<tr><td>Choisissent l'autre pneu même avec le Michelin à 92,90 €</td><td class="n"><?= $stats['versions']['A']['jamais'] ?></td><td class="n"><?= $stats['versions']['B']['jamais'] ?></td></tr>
<?php foreach (array_keys($stats['versions']['A']['par_prix']) as $p): ?>
<tr><td>Choisissent le Michelin à <?= h($p) ?> €</td><td class="n"><?= $stats['versions']['A']['par_prix'][$p] ?></td><td class="n"><?= $stats['versions']['B']['par_prix'][$p] ?></td></tr>
<?php endforeach; ?>
<tr><td>Van Westendorp, « cher » (médiane)</td><td class="n"><?= nb($stats['versions']['A']['vw_cher_med']) ?> €</td><td class="n"><?= nb($stats['versions']['B']['vw_cher_med']) ?> €</td></tr>
<tr><td>Van Westendorp, « trop cher » (médiane)</td><td class="n"><?= nb($stats['versions']['A']['vw_trop_cher_med']) ?> €</td><td class="n"><?= nb($stats['versions']['B']['vw_trop_cher_med']) ?> €</td></tr>
</tbody>
</table>
<p class="note">Lecture : l'écart entre B et A sur la prime mesure ce que vaut, pour les répondants, l'argument des 10 000 km de plus. Avec peu de répondants par version, un petit écart peut être dû au hasard : les tests statistiques se feront en Analyse de données.</p>
</div>

<form method="post" class="inline"><button class="second" name="deconnexion" value="1">Se déconnecter</button></form>
<?php endif; ?>
</main>
</body>
</html>
