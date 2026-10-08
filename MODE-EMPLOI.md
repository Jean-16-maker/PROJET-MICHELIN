# Mode d'emploi : questionnaire et serveur PHP

Le dépôt contient :
- le dossier Michelin CrossClimate 3 (`index.html` et les pages suivantes), publié sur GitHub Pages ;
- le questionnaire (`questionnaire.html`), lui aussi publié sur GitHub Pages ;
- le dossier `serveur/`, en PHP, qui enregistre les réponses et permet de les extraire.

**GitHub Pages n'exécute pas le PHP.** Le dossier `serveur/` doit donc être déposé chez un hébergeur qui accepte le PHP (version 7.4 ou plus récente). Le questionnaire reste sur GitHub Pages et envoie chaque réponse à ce serveur.

Tant que l'adresse du serveur n'est pas réglée, le questionnaire tourne en **mode essai** : rien n'est envoyé.

## Ce que mesure le questionnaire

**La question : les gens sont-ils prêts à payer plus pour un pneu qui dure 10 000 km de plus ?** Michelin met en avant pour le CrossClimate 3 une durée de vie supérieure à celle de ses concurrents.

**Test A/B**, tiré au sort à l'ouverture : le même **Michelin CrossClimate 3** (4 saisons, 205/55 R16, homologué hiver) est présenté avec une durée de vie annoncée de
- **40 000 km** en version A ;
- **50 000 km** en version B.

C'est la seule différence entre les deux versions. L'écart entre B et A mesure ce que valent 10 000 km de plus.

Le questionnaire prend environ 1 min 30 : une question par écran, un clic sur une grande case pour avancer, et un bouton « Retour » sur chaque écran.

| Écran | Contenu |
|---|---|
| 1 | Accueil. Cliquer sur « C'est parti » vaut accord (anonymat) |
| 2 | Âge : **moins de 18 ans → fin du questionnaire** |
| 3 | Avez-vous une voiture ? **Non → fin du questionnaire** |
| 4 | Le pneu : Michelin CrossClimate 3, durée de vie annoncée 40 000 km (A) ou 50 000 km (B), sans prix |
| 5 | La jauge : au maximum, combien paieriez-vous ce pneu ? De 60 à 140 €, montage non compris |
| 6 | « Ce pneu coûte 97,90 €. Le paieriez-vous 10 € de plus, soit 107,90 € ? » Oui / Non |
| 7-9 | Votre avis, de 1 à 5 : cette durée de vie justifie un prix plus élevé ; je crois à la durée annoncée ; un pneu qui dure plus fait faire des économies |
| 10 | Ce qui compte le plus : prix, durée de vie, sécurité ou marque |
| 11 | Kilomètres par an |

La jauge ne montre aucun prix tant que le curseur n'a pas bougé, et le prix de 97,90 € n'apparaît qu'après la jauge : on ne suggère pas de prix de départ.

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
- les premiers résultats par version A / B : part prête à payer 10 € de plus, prix moyen et médian de la jauge, répartition des prix, avis moyens, critère principal, durée de réponse ;
- des boutons de téléchargement :
  - **Excel** : séparateur `;`, virgule décimale, accents corrects ;
  - **CSV standard** : séparateur `,`, point décimal, pour R ou Python ;
  - toutes les réponses, ou seulement les **exploitables** (hors essais, 18 ans ou plus, avec une voiture).

## Les colonnes

| Colonne | Contenu |
|---|---|
| `test` | 1 = essai, à écarter |
| `version` | A (40 000 km annoncés) ou B (50 000 km annoncés) |
| `duree_s` | temps de réponse, en secondes |
| `age` | `<18`, `18-24`, `25-34`, `35-49`, `50-64` ou `65+` |
| `voiture` | `oui` ou `non` |
| `cible` | 1 = 18 ans ou plus et a une voiture ; 0 = arrêté au filtre |
| `prix_max` | le prix maximum choisi sur la jauge, de 60 à 140 € (60 = « 60 € ou moins », 140 = « 140 € ou plus ») |
| `accepte_plus_10` | `oui` ou `non` : paierait 107,90 € au lieu de 97,90 € |
| `likert_…` | avis de 1 à 5 : la durée justifie un prix plus élevé, croit à la durée annoncée, économies |
| `critere_principal` | prix, durée de vie, sécurité ou marque |
| `km_an` | kilomètres par an |

## Si vous modifiez le questionnaire

Ajoutez toute nouvelle colonne **à la fin** de `COLONNES` dans `serveur/colonnes.php`, et déposez le fichier sur l'hébergeur. Si vous changez le prix actuel ou la hausse testée, changez-les aux deux endroits : `PRIX_ACTUEL` et `HAUSSE` dans `questionnaire.html` et dans `serveur/colonnes.php`. Ne changez rien une fois la collecte lancée.
