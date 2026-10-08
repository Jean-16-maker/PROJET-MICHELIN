# Mode d'emploi : questionnaire et serveur PHP

Le dépôt contient :
- le dossier Michelin CrossClimate 3 (`index.html` et les pages suivantes), publié sur GitHub Pages ;
- le questionnaire (`questionnaire.html`), lui aussi publié sur GitHub Pages ;
- le dossier `serveur/`, en PHP, qui enregistre les réponses et permet de les extraire.

**GitHub Pages n'exécute pas le PHP.** Le dossier `serveur/` doit donc être déposé chez un hébergeur qui accepte le PHP (version 7.4 ou plus récente). Le questionnaire reste sur GitHub Pages et envoie chaque réponse à ce serveur.

Tant que l'adresse du serveur n'est pas réglée, le questionnaire tourne en **mode essai** : rien n'est envoyé.

## Ce que mesure le questionnaire

Chaque répondant voit deux pneus 4 saisons en 205/55 R16 : le **Michelin CrossClimate 3** et le pneu d'**une autre grande marque, à 93 €** (le prix plafond relevé chez les concurrents directs).

- **Test A/B**, tiré au sort : la version B ajoute seulement la durée de vie (Michelin environ 50 000 km, l'autre environ 40 000 km, soit 10 000 km de plus). C'est la seule différence entre A et B.
- **Van Westendorp** : les 4 prix (trop bon marché, bon marché, cher, trop cher) du Michelin.
- **Gabor-Granger en choix** : « le Michelin à X € ou l'autre à 93 € ? ». X descend de 119,90 € à 92,90 €, et le questionnaire s'arrête au premier choix du Michelin.
  - `gg_prix_max_michelin` = le prix le plus élevé auquel le répondant choisit encore le Michelin.
  - `prime_max` = ce prix moins 93 € : la prime qu'il accepte de payer pour le Michelin.
- **Le résultat clé** : la prime en B moins la prime en A, soit ce que valent les 10 000 km de plus aux yeux des répondants.

La présentation du questionnaire est volontairement neutre (pas la charte Michelin du dossier), pour ne pas avantager une marque.

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
- les premiers résultats par version A / B : prix maximum et prime acceptés pour le Michelin, part qui choisit le Michelin à chaque prix, médianes Van Westendorp, taux de réussite du contrôle ;
- des boutons de téléchargement :
  - **Excel** : séparateur `;`, virgule décimale, accents corrects ;
  - **CSV standard** : séparateur `,`, point décimal, pour R ou Python ;
  - toutes les réponses, ou seulement les **exploitables** (hors essais, dans la cible, Van Westendorp cohérent).

## Les colonnes

| Colonne | Contenu |
|---|---|
| `test` | 1 = essai, à écarter |
| `version` | A (sans durée de vie) ou B (avec 50 000 km contre 40 000 km) |
| `cible` | 0 = hors cible : pas de voiture chaque semaine (arrêt au filtre) ou quelqu'un d'autre choisit les pneus (questionnaire complet, à écarter ou à comparer) |
| `vw_…` | les 4 prix Van Westendorp du Michelin, en euros |
| `vw_coherent` | 0 si les 4 prix ne montent pas : à écarter, en disant combien |
| `gg_119_90` … `gg_92_90` | `michelin` ou `autre` à chaque prix proposé (vide = prix non proposé) |
| `gg_prix_max_michelin` | le prix le plus élevé auquel il choisit le Michelin (« aucun » s'il choisit toujours l'autre) |
| `prime_max` | `gg_prix_max_michelin` − 93 € |
| `controle` | a-t-il vu la durée de vie ? On attend « oui » en B et « non » en A |
| `likert_…` | le Michelin vaut l'écart, est de meilleure qualité, inspire plus confiance (1 à 5) |
| `pneus_actuels`, `dernier_prix`, `gamme_marque` | le marché : type de pneus actuels, dernier prix payé, gamme de marque envisagée |

## Si vous modifiez le questionnaire

Ajoutez toute nouvelle colonne **à la fin** de `COLONNES` dans `serveur/colonnes.php`, et déposez le fichier sur l'hébergeur. Si vous changez les prix proposés, changez-les aux deux endroits : `PRIX_GG` dans `questionnaire.html` et dans `serveur/colonnes.php`. Ne changez rien une fois la collecte lancée.
