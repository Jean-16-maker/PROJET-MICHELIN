# Mode d'emploi : questionnaire et serveur PHP

Le dépôt contient :
- le dossier Michelin CrossClimate 3 (`index.html` et les pages suivantes), publié sur GitHub Pages ;
- le questionnaire (`questionnaire.html`), lui aussi publié sur GitHub Pages ;
- le dossier `serveur/`, en PHP, qui enregistre les réponses et permet de les extraire.

**GitHub Pages n'exécute pas le PHP.** Le dossier `serveur/` doit donc être déposé chez un hébergeur qui accepte le PHP (version 7.4 ou plus récente). Le questionnaire reste sur GitHub Pages et envoie chaque réponse à ce serveur.

Tant que l'adresse du serveur n'est pas réglée, le questionnaire tourne en **mode essai** : rien n'est envoyé.

## Ce que mesure le questionnaire

**La question : les gens sont-ils prêts à payer plus cher pour un pneu qui dure 10 000 km de plus ?**

Chaque répondant voit deux versions du même pneu, côte à côte :
- **Michelin CrossClimate 3** : durée de vie annoncée 40 000 km, **97,90 €** le pneu ;
- **Michelin CrossClimate 3 renforcé** : durée de vie annoncée **50 000 km**, prix à déterminer.

Les deux ont les mêmes caractéristiques : 4 saisons, 205/55 R16, étiquette européenne carburant B, pluie B, bruit 72 dB, homologation hiver 3PMSF. La version « renforcée » est un **scénario** : elle n'existe pas dans le catalogue Michelin.

**Test A/B**, tiré au sort, avec une seule différence, la présentation des 15 € (effet de cadrage, CM 2) :
- **version A** : « Soit 112,90 € au lieu de 97,90 €, ou 60 € de plus pour 4 pneus » ;
- **version B** : « Soit 112,90 € au lieu de 97,90 € : à peine 1,50 € tous les 1 000 km parcourus en plus ».

| Écran | Contenu |
|---|---|
| 1 | Accueil. Cliquer sur « C'est parti » vaut accord (anonymat) |
| 2 | Âge exact, en années : **moins de 18 ans → fin du questionnaire** |
| 3 | Avez-vous une voiture ? **Non → fin du questionnaire** |
| 4 | Les deux pneus côte à côte |
| 5 | « Paieriez-vous 15 € de plus par pneu pour la version renforcée, qui dure 10 000 km de plus ? » Oui / Non |
| 6 | La jauge : au maximum, combien paieriez-vous la version renforcée ? De 80 à 150 € |
| 7-9 | Votre avis, de 1 à 5 : 10 000 km justifient de payer plus ; je crois à la durée annoncée ; un pneu qui dure plus fait faire des économies |
| 10 | Ce qui compte le plus (9 choix) |
| 11 | Kilomètres par an : curseur de 0 à 50 000 km |
| 12 | Lieux où la personne a déjà acheté des pneus : oui / non pour 6 lieux |

## 1. Héberger le dossier `serveur/` (une seule fois)

N'importe quel hébergeur PHP convient. La méthode la plus simple passe par **alwaysdata** (français, offre gratuite, sans carte bancaire).

### Avec alwaysdata, en une commande

1. Créez un compte gratuit sur alwaysdata.com. Le **nom du compte** donne l'adresse du site : `https://NOMDUCOMPTE.alwaysdata.net`.
2. Dans l'administration, ouvrez **Accès distant › SSH**, modifiez l'utilisateur SSH et cochez **« Activer la connexion par mot de passe »**. Ouvrez ensuite la console SSH dans le navigateur (lien **« Web SSH »** de cette page) et connectez-vous.
3. Collez cette commande, puis appuyez sur Entrée :

```bash
cd ~/www && curl -sL https://github.com/Jean-16-maker/PROJET-MICHELIN/archive/refs/heads/main.tar.gz | tar xz --strip-components=1 PROJET-MICHELIN-main/serveur && if [ ! -f serveur/config.php ]; then MDP=$(openssl rand -hex 8) && sed "s/^const MOT_DE_PASSE_EXPORT_SHA256 = '';/const MOT_DE_PASSE_EXPORT_SHA256 = '$(printf '%s' "$MDP" | sha256sum | cut -c1-64)';/" serveur/config.exemple.php > serveur/config.php && echo "Mot de passe de la page export : $MDP"; fi
```

   La commande télécharge le dossier `serveur/` depuis GitHub, crée `config.php` et choisit un mot de passe au hasard. Ce mot de passe s'affiche une seule fois : notez-le et gardez-le dans le groupe. Le serveur n'en garde que l'empreinte SHA-256.
4. Ouvrez `https://NOMDUCOMPTE.alwaysdata.net/serveur/export.php` : la page de mot de passe doit s'afficher.
5. Envoyez l'adresse `https://NOMDUCOMPTE.alwaysdata.net/serveur/enregistrer.php` à Claude, ou faites l'étape 2 ci-dessous.

Pour mettre à jour le serveur après une modification sur GitHub, relancez la même commande. `config.php` et les réponses déjà enregistrées ne sont pas touchés.

### Avec un autre hébergeur

1. Créez le compte et le site chez l'hébergeur.
2. Déposez le dossier `serveur/` (gestionnaire de fichiers de l'hébergeur ou FTP), avec `colonnes.php`, `enregistrer.php`, `export.php`, `config.exemple.php` et `donnees/.htaccess`.
3. Sur l'hébergeur, **copiez `config.exemple.php` en `config.php`**, puis réglez :
   - `MOT_DE_PASSE_EXPORT_SHA256` : l'empreinte SHA-256 du mot de passe choisi (`printf '%s' 'mot-de-passe' | shasum -a 256` sur Mac) ;
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
- les premiers résultats par version A / B : part prête à payer 15 € de plus, prix moyen et médian de la jauge, supplément moyen accepté, avis moyens, critère principal, lieux d'achat, âge, kilomètres, durée de réponse ;
- des boutons de téléchargement :
  - **Excel** : séparateur `;`, virgule décimale, accents corrects ;
  - **CSV standard** : séparateur `,`, point décimal, pour R ou Python ;
  - toutes les réponses, ou seulement les **exploitables** (hors essais, 18 ans ou plus, avec une voiture).

## Les colonnes

| Colonne | Contenu |
|---|---|
| `test` | 1 = essai, à écarter |
| `version` | A (« 60 € de plus pour 4 pneus ») ou B (« 1,50 € tous les 1 000 km ») |
| `duree_s` | temps de réponse, en secondes |
| `age` | âge en années |
| `voiture` | `oui` ou `non` |
| `cible` | 1 = 18 ans ou plus et a une voiture ; 0 = arrêté au filtre |
| `accepte_plus_15` | `oui` ou `non` : paierait 112,90 € pour la version renforcée au lieu de 97,90 € |
| `prix_max_renforce` | le prix maximum choisi sur la jauge pour la version renforcée, de 80 à 150 € |
| `likert_…` | avis de 1 à 5 : 10 000 km justifient de payer plus, croit à la durée annoncée, économies |
| `critere_principal` | prix, durée de vie, freinage, hiver, marque, carburant, bruit, avis ou conseil |
| `km_an` | kilomètres par an (curseur, par pas de 1 000 ; 50 000 = « 50 000 ou plus ») |
| `achat_…` | `oui` ou `non` pour chaque lieu : garage, spécialiste, centre auto, Internet, réparateur rapide, grande surface |

## Si vous modifiez le questionnaire

Ajoutez toute nouvelle colonne **à la fin** de `COLONNES` dans `serveur/colonnes.php`, et déposez le fichier sur l'hébergeur. Si vous changez le prix ou la hausse testée, changez-les aux deux endroits : `PRIX_STANDARD` et `HAUSSE` dans `questionnaire.html` et dans `serveur/colonnes.php`. Ne changez rien une fois la collecte lancée.
