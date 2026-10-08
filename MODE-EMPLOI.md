# Mode d'emploi : questionnaire, Google Sheets et GitHub Pages

Le site contient le dossier Michelin CrossClimate 3 (`index.html` et les pages suivantes) et le questionnaire (`questionnaire.html`).
Le questionnaire envoie chaque réponse dans une feuille Google Sheets grâce au petit script `apps-script.gs`.

Tant que l'URL Google Sheets n'est pas réglée, le questionnaire tourne en **mode essai** : rien n'est envoyé, et les réponses s'affichent à la fin.

## 1. Créer la feuille Google Sheets (5 minutes, une seule fois)

1. Avec le compte Google du groupe, créez une feuille vide nommée par exemple « Questionnaire CrossClimate 3 ».
2. Ouvrez le menu **Extensions › Apps Script**.
3. Effacez le code proposé, collez tout le contenu de `apps-script.gs`, puis enregistrez (icône disquette).
4. Cliquez sur **Déployer › Nouveau déploiement**. Avec la roue dentée, choisissez le type **Application web**.
   - Exécuter en tant que : **Moi**
   - Qui a accès : **Tout le monde**
5. Cliquez sur **Déployer** et autorisez l'accès. Google affiche « Application non validée » : cliquez sur **Paramètres avancés**, puis sur **Accéder au projet**. C'est normal pour un script que vous avez écrit vous-même.
6. Copiez l'**URL de l'application web**, celle qui se termine par `/exec`.
   Ouvrez-la dans un navigateur : le message « Le script du questionnaire fonctionne. » doit s'afficher.

## 2. Brancher le questionnaire sur la feuille

Dans `questionnaire.html`, remplacez la ligne :

```js
var ENDPOINT = '';
```

par votre URL :

```js
var ENDPOINT = 'https://script.google.com/macros/s/…/exec';
```

Vous pouvez aussi donner l'URL à Claude, qui fera la modification.

## 3. Publier sur GitHub Pages

1. Dans GitHub Desktop, choisissez **File › Add local repository**, puis sélectionnez le dossier `site`.
2. Cliquez sur **Publish repository**, avec le nom `michelin-prix` par exemple. **Décochez** « Keep this code private » : GitHub Pages gratuit exige un dépôt public.
3. Sur github.com, ouvrez le dépôt, puis **Settings › Pages**. Choisissez Source : *Deploy from a branch*, Branch : `main`, dossier `/ (root)`, puis cliquez sur **Save**.
4. Une à deux minutes plus tard, le site est en ligne :
   - dossier : `https://jean-16-maker.github.io/michelin-prix/`
   - questionnaire : `https://jean-16-maker.github.io/michelin-prix/questionnaire.html`

Pour chaque modification ultérieure : faites un commit dans GitHub Desktop, puis **Push origin**.

## 4. Tester avant de diffuser (avant le 12 octobre)

- Ajoutez `?test=1` à l'adresse du questionnaire. Les réponses arrivent dans la feuille avec `test = 1` et seront écartées à l'analyse.
- `?test=1&v=A` ou `?test=1&v=B` force une version, pour vérifier les deux.
- Le cours demande un essai auprès de **quelques personnes extérieures au groupe**, pour repérer ce qui est mal compris.

## 5. Diffuser (du 12 au 21 octobre)

Diffusez **uniquement** le lien `…/questionnaire.html`, sans `?test=1`.
Ne diffusez pas le lien du dossier : les répondants y verraient nos prix et notre hypothèse.

## 6. Ce que contient la feuille

Elle compte une ligne par répondant, dans l'onglet `reponses`. Les colonnes principales :

| Colonne | Contenu |
|---|---|
| `test` | 1 = essai, à écarter |
| `version` | A (fiche simple) ou B (fiche + durée de vie et coût au km) |
| `cible` | 0 = hors cible (pas de voiture chaque semaine, ou ne choisit pas les pneus) |
| `vw_…` | les 4 prix Van Westendorp, en euros |
| `vw_coherent` | 0 si les 4 prix ne montent pas : à écarter, en disant combien |
| `gg_104_90` … `gg_74_90` | réponses oui / non à chaque prix (vide = prix non proposé) |
| `gg_prix_max_accepte` | le prix le plus élevé accepté (« aucun » si tous refusés) |
| `controle` | a-t-il vu la durée de vie ? On attend « oui » en B et « non » en A |
| `likert_…` | valeur, qualité, confiance perçues (1 à 5) |

Gabor-Granger présente les prix du plus cher au moins cher et s'arrête au premier « oui ». Un répondant qui accepte 97,90 € est donc compté comme acceptant aussi tous les prix plus bas.

## Si vous modifiez le script

Dans Apps Script, ouvrez **Déployer › Gérer les déploiements**, cliquez sur le crayon, choisissez **Version : nouvelle version**, puis **Déployer**. L'URL ne change pas.
Si vous ajoutez une question, ajoutez sa colonne **à la fin** de la liste `COLONNES` du script. Ne changez pas les colonnes une fois la collecte lancée.
