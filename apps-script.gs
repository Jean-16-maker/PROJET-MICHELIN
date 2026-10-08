/**
 * Réception des réponses du questionnaire (questionnaire.html) dans Google Sheets.
 * À coller dans Extensions > Apps Script de la feuille, puis à déployer en « Application web »
 * (Exécuter en tant que : moi ; Qui a accès : tout le monde). Voir MODE-EMPLOI.md.
 *
 * Une ligne par répondant, des colonnes qui ne changent pas en cours de route.
 * L'adresse IP n'est pas transmise à Apps Script : rien ne permet d'identifier un répondant.
 */
var ONGLET = 'reponses';
var COLONNES = [
  'horodatage', 'id', 'test', 'version', 'duree_s',
  'consentement', 'filtre_voiture', 'filtre_decide', 'cible',
  'vw_trop_bon_marche', 'vw_bon_marche', 'vw_cher', 'vw_trop_cher', 'vw_coherent',
  'gg_104_90', 'gg_99_90', 'gg_97_90', 'gg_94_90', 'gg_92_90', 'gg_89_90', 'gg_84_90', 'gg_79_90', 'gg_74_90',
  'gg_prix_max_accepte',
  'controle', 'likert_valeur', 'likert_qualite', 'likert_confiance', 'critere_principal',
  'age', 'km_an', 'canal_achat'
];

function doPost(e) {
  var verrou = LockService.getScriptLock();
  verrou.waitLock(10000);
  try {
    var d = JSON.parse(e.postData.contents);
    var classeur = SpreadsheetApp.getActiveSpreadsheet();
    var feuille = classeur.getSheetByName(ONGLET) || classeur.insertSheet(ONGLET);
    if (feuille.getLastRow() === 0) {
      feuille.appendRow(COLONNES);
      feuille.setFrozenRows(1);
    }
    var ligne = COLONNES.map(function (c) {
      if (c === 'horodatage') return new Date();
      var v = d[c];
      if (v === undefined || v === null) return '';
      if (typeof v === 'number') return v;
      v = String(v).slice(0, 100);
      // Empêche une réponse d'être lue comme une formule par Sheets.
      return /^[=+\-@]/.test(v) ? "'" + v : v;
    });
    feuille.appendRow(ligne);
    return ContentService.createTextOutput('ok');
  } catch (err) {
    return ContentService.createTextOutput('erreur');
  } finally {
    verrou.releaseLock();
  }
}

/* Ouvrir l'URL de l'application web dans un navigateur affiche ce message : utile pour vérifier le déploiement. */
function doGet() {
  return ContentService.createTextOutput('Le script du questionnaire fonctionne.');
}
