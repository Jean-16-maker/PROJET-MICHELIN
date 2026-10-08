# Mode d'emploi : questionnaire et serveur PHP

Le dépôt contient :
- le dossier Michelin CrossClimate 3 (`index.html` et les pages suivantes), publié sur GitHub Pages ;
- le questionnaire (`questionnaire.html`), lui aussi publié sur GitHub Pages ;
- le dossier `serveur/`, en PHP, qui enregistre les réponses et permet de les extraire.

**GitHub Pages n'exécute pas le PHP.** Le dossier `serveur/` doit donc être déposé chez un hébergeur qui accepte le PHP (version 7.4 ou plus récente). Le questionnaire reste sur GitHub Pages et envoie chaque réponse à ce serveur.

Tant que l'adresse du serveur n'est pas réglée, le questionnaire tourne en **mode essai** : rien n'est envoyé.

## Ce que mesure le questionnaire

**La question : combien le client paierait-il en plus pour un pneu qui dure 10 000 km de plus, et le nom Michelin change-t-il ce montant ?**

Le questionnaire prend environ 2 minutes : une question par écran, et un clic sur une grande case suffit pour passer à la suite.

| Écran | Contenu |
|---|---|
| 1 | Accueil. Cliquer sur « C'est parti » vaut accord (anonymat, 18 ans et plus) |
| 2 | Qui choisit les pneus de votre voiture ? Moi / Quelqu'un d'autre / Je n'ai pas de voiture |
| 3 | Les deux pneus : pneu 1, 50 000 km, prix « ? » ; pneu 2, une grande marque, 40 000 km, 93 € |
| 4 | La jauge : au maximum, combien paieriez-vous [le pneu 1 / le Michelin] ? De 60 à 140 € |
| 5 | Paieriez-vous 15 € de plus par pneu pour le faire monter à domicile ? Oui / Non |
| 6 | Votre avis, de 1 à 5, sur trois phrases (10 000 km valent un prix plus élevé ; je crois à la durée annoncée ; confiance pour la sécurité) |
| 7 | Ce qui compte le plus pour choisir des pneus (5 cases) |
| 8-10 | Âge (5 cases), kilomètres par an (4 cases), lieu d'achat habituel (6 cases) |

**Test A/B**, tiré au sort, avec une seule différence :
- **version A** : le pneu 1 est « une grande marque », sans nom ;
- **version B** : le pneu 1 est le **Michelin CrossClimate 3**.

Ce qu'on lit :
- la **version A** donne ce que valent 10 000 km de plus, sans la marque ;
- la **version B** donne la même chose pour le Michelin ;
- **B − A** donne ce qu'ajoute le nom Michelin, d'abord sur le prix moyen de la jauge.

La question des 15 € mesure l'intérêt pour un service de **montage à domicile** ; elle est posée dans les deux versions.

La jauge ne montre aucun prix tant que le curseur n'a pas bougé, et « Valider » reste grisé : on ne suggère pas de prix de départ.

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
- les premiers résultats par version A / B : prix moyen et médian de la jauge, répartition des prix, part prête à payer 15 € pour le montage à domicile, avis moyens, critère principal, durée de réponse ;
- des boutons de téléchargement :
  - **Excel** : séparateur `;`, virgule décimale, accents corrects ;
  - **CSV standard** : séparateur `,`, point décimal, pour R ou Python ;
  - toutes les réponses, ou seulement les **exploitables** (hors essais, et la personne choisit elle-même ses pneus).

## Les colonnes

| Colonne | Contenu |
|---|---|
| `test` | 1 = essai, à écarter |
| `version` | A (pneu 1 sans marque) ou B (pneu 1 = Michelin CrossClimate 3) |
| `duree_s` | temps de réponse, en secondes |
| `filtre_decide` | `moi`, `autre` ou `sans_voiture` |
| `cible` | 1 = choisit lui-même ses pneus ; 0 = hors cible, à écarter ou à comparer |
| `prix_max_pneu1` | le prix maximum choisi sur la jauge, de 60 à 140 € (60 = « 60 € ou moins », 140 = « 140 € ou plus ») |
| `montage_domicile_15` | `oui` ou `non` : prêt à payer 15 € de plus par pneu pour le montage à domicile |
| `likert_…` | avis de 1 à 5 : 10 000 km valent un prix plus élevé, croit à la durée annoncée, confiance pour la sécurité |
| `critere_principal` | prix, sécurité, durée de vie, marque ou conseil |
| `age`, `km_an`, `canal_achat` | profil |

## Si vous modifiez le questionnaire

Ajoutez toute nouvelle colonne **à la fin** de `COLONNES` dans `serveur/colonnes.php`, et déposez le fichier sur l'hébergeur. Si vous changez le supplément ou le prix du pneu 2, changez-les aux deux endroits : `SUPPLEMENT` et `PRIX_AUTRE` dans `questionnaire.html` et dans `serveur/colonnes.php`. Ne changez rien une fois la collecte lancée.
