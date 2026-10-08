# Mode d'emploi : questionnaire et serveur PHP

Le dépôt contient :
- le dossier Michelin CrossClimate 3 (`index.html` et les pages suivantes), publié sur GitHub Pages ;
- le questionnaire (`questionnaire.html`), lui aussi publié sur GitHub Pages ;
- le dossier `serveur/`, en PHP, qui enregistre les réponses et permet de les extraire.

**GitHub Pages n'exécute pas le PHP.** Le dossier `serveur/` doit donc être déposé chez un hébergeur qui accepte le PHP (version 7.4 ou plus récente). Le questionnaire reste sur GitHub Pages et envoie chaque réponse à ce serveur.

Tant que l'adresse du serveur n'est pas réglée, le questionnaire tourne en **mode essai** : rien n'est envoyé.

## Ce que mesure le questionnaire

**La question : combien le client paierait-il en plus pour un pneu qui dure 10 000 km de plus, et le nom Michelin change-t-il ce montant ?**

Chaque répondant voit deux pneus 4 saisons en 205/55 R16 :
- **pneu 1** : durée de vie annoncée d'environ 50 000 km, prix à déterminer ;
- **pneu 2** : une grande marque, environ 40 000 km, **93 €** (le prix plafond relevé chez les concurrents directs).

Les 10 000 km de plus apparaissent dans les deux versions. **Test A/B**, tiré au sort, avec une seule différence :
- **version A** : le pneu 1 n'a pas de nom (« un pneu 4 saisons d'une grande marque ») ;
- **version B** : le pneu 1 est le **Michelin CrossClimate 3**.

Les mesures :
- **Le supplément**, une seule question : « Seriez-vous prêt(e) à payer 15 € de plus par pneu pour [le pneu 1 / le Michelin CrossClimate 3], qui dure 10 000 km de plus ? Soit 108 € par pneu au lieu de 93 € », avec une réponse oui ou non (colonne `sup_15`).
- **Van Westendorp en 5 tranches**, pour le pneu 1 : quatre questions (trop bon marché, bon marché, cher, trop cher), avec les cases moins de 80 €, 80 à 90 €, 90 à 100 €, 100 à 110 € et plus de 110 €.

Ce qu'on lit :
- la **version A** donne la part prête à payer 15 € de plus pour 10 000 km de plus, sans marque ;
- la **version B** donne la même part pour le Michelin ;
- **B − A** donne ce qu'ajoute le nom Michelin.

Le questionnaire reprend la charte bleu et jaune du dossier.

## 1. Héberger le dossier `serveur/` (une seule fois)

N'importe quel hébergeur PHP convient : un hébergement fourni par l'université, ou un hébergeur gratuit, comme alwaysdata.com (offre gratuite à vérifier lors de l'inscription).

1. Créez le compte et le site chez l'hébergeur.
2. Déposez le dossier `serveur/` (gestionnaire de fichiers de l'hébergeur ou FTP), avec `colonnes.php`, `enregistrer.php`, `export.php`, `config.exemple.php` et `donnees/.htaccess`.
3. Sur l'hébergeur, **copiez `config.exemple.php` en `config.php`**, puis réglez :
   - `MOT_DE_PASSE_EXPORT` : un mot de passe d'au moins 12 caractères, à garder dans le groupe ;
   - `ORIGINES_AUTORISEES` : laissez `https://jean-16-maker.github.io`.
4. Ouvrez `https://VOTRE-HEBERGEMENT/serveur/export.php` : la page de mot de passe doit s'afficher.

`config.php` et les réponses ne sont jamais envoyés sur GitHub : le dépôt est public (voir `.gitignore`).

## 2. Brancher le questionnaire sur le serveur

Dans `questionnaire.html`, remplacez :

```js
var ENDPOINT = '';
```

par :

```js
var ENDPOINT = 'https://VOTRE-HEBERGEMENT/serveur/enregistrer.php';
```

Vous pouvez aussi donner l'adresse à Claude, qui fera la modification. Faites ensuite un commit, puis **Push origin** dans GitHub Desktop.

## 3. Tester avant de diffuser (avant le 12 octobre)

- `questionnaire.html?test=1` : les réponses sont enregistrées avec `test = 1` et écartées de l'analyse.
- `?test=1&v=A` ou `?test=1&v=B` : force une version, pour vérifier les deux.
- `?debug=1` : affiche à la fin les données envoyées.
- Le cours demande un essai auprès de **quelques personnes extérieures au groupe**.
- Après un Push, attendez 2 minutes et rechargez avec **Cmd + Maj + R** : sinon le navigateur peut afficher l'ancienne version.

## 4. Diffuser (du 12 au 21 octobre)

Diffusez **uniquement** `https://jean-16-maker.github.io/PROJET-MICHELIN/questionnaire.html`, sans `?test=1`.
Ne diffusez pas le lien du dossier : les répondants y verraient nos prix et notre hypothèse.

## 5. Extraire les données

Ouvrez `https://VOTRE-HEBERGEMENT/serveur/export.php` et entrez le mot de passe. La page affiche :
- le nombre de réponses : essais, hors cible, incohérentes, exploitables ;
- les premiers résultats par version A / B : part prête à payer 15 € de plus, tranches médianes de Van Westendorp, taux de réussite du contrôle ;
- des boutons de téléchargement :
  - **Excel** : séparateur `;`, virgule décimale, accents corrects ;
  - **CSV standard** : séparateur `,`, point décimal, pour R ou Python ;
  - toutes les réponses, ou seulement les **exploitables** (hors essais, dans la cible, Van Westendorp cohérent).

## Les colonnes

| Colonne | Contenu |
|---|---|
| `test` | 1 = essai, à écarter |
| `version` | A (pneu 1 sans marque) ou B (pneu 1 = Michelin CrossClimate 3) |
| `cible` | 0 = hors cible : pas de voiture chaque semaine (arrêt au filtre) ou quelqu'un d'autre choisit les pneus (questionnaire complet, à écarter ou à comparer) |
| `sup_15` | `oui` ou `non` : prêt à payer 15 € de plus par pneu pour 10 000 km de plus |
| `vw_…` | les 4 tranches Van Westendorp du pneu 1 : `<80`, `80-90`, `90-100`, `100-110` ou `>110` |
| `vw_coherent` | 0 si les 4 tranches ne montent pas : à écarter, en disant combien |
| `controle` | a-t-il vu un nom de marque ? On attend « oui » en B et « non » en A |
| `likert_…` | 10 000 km valent un prix plus élevé, croit à la durée annoncée, confiance pour la sécurité (1 à 5) |
| `critere_principal`, `age`, `km_an`, `canal_achat` | critère de choix et profil |

## Si vous modifiez le questionnaire

Ajoutez toute nouvelle colonne **à la fin** de `COLONNES` dans `serveur/colonnes.php`, et déposez le fichier sur l'hébergeur. Si vous changez le supplément ou les tranches, changez-les aux deux endroits : `SUPPLEMENT` et `TRANCHES` dans `questionnaire.html` et dans `serveur/colonnes.php`. Ne changez rien une fois la collecte lancée.
