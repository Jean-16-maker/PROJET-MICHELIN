# Mode d'emploi : questionnaire et serveur PHP

Le dépôt contient :
- le dossier Michelin CrossClimate 3 (`index.html` et les pages suivantes), publié sur GitHub Pages ;
- le questionnaire (`questionnaire.html`), lui aussi publié sur GitHub Pages ;
- le dossier `serveur/`, en PHP, qui enregistre les réponses et permet de les extraire.

**GitHub Pages n'exécute pas le PHP.** Le dossier `serveur/` doit donc être déposé chez un hébergeur qui accepte le PHP (version 7.4 ou plus récente). Le questionnaire reste sur GitHub Pages et envoie chaque réponse à ce serveur.

Tant que l'adresse du serveur n'est pas réglée, le questionnaire tourne en **mode essai** : rien n'est envoyé.

## Ce que mesure le questionnaire

**Deux questions en une : la marque Michelin vaut-elle son prix, et 10 000 km de durée de vie en plus changent-ils le choix ?**

Après les filtres, chaque répondant choisit entre deux pneus 4 saisons 205/55 R16, homologués hiver, en touchant celui qu'il achèterait. Le tirage au sort, à l'ouverture, décide de la variante :

| | Hankook Kinergy 4S 94H XL | Michelin CrossClimate 3 | Ce qu'on mesure |
|---|---|---|---|
| **Variante A** | 40 000 km · 81,99 € | **40 000 km** · 97,90 € | la notoriété : à durée égale, paie-t-on 16 € de plus pour Michelin ? |
| **Variante B** | 40 000 km · 81,99 € | **50 000 km** · 97,90 € | la durée de vie : 10 000 km de plus font-ils choisir Michelin ? |

La seule différence entre A et B est la durée de vie du Michelin. Avant et après cette question, le parcours est le même pour tous, quelles que soient les réponses :

| Écran | Contenu |
|---|---|
| 1 | Accueil : « Questionnaire en moins d'une minute », « Vos réponses sont anonymes » |
| 2 | Âge exact : **moins de 18 ans → écran de remerciement** |
| 3 | Avez-vous une voiture ? **Non → écran de remerciement** |
| 4 | Kilomètres par an : curseur de 0 à 50 000 km |
| 5 | **La question A/B** : Hankook ou Michelin ? Chaque carte montre la photo de la fiche du pneu |
| 6-9 | Échelle de Likert à 5 points, une affirmation par écran : « Pour choisir mes pneus, le prix / la marque / la durée de vie / la performance compte beaucoup » (1 = pas du tout d'accord … 5 = tout à fait d'accord) |
| 10 | Lieux où la personne a déjà acheté des pneus : oui / non pour 5 lieux |

Une fois l'écran de fin atteint, on ne peut plus revenir aux questions : le bouton Retour disparaît, et recharger la page ramène à la fin. Pour refaire un essai, ouvrez un **nouvel onglet**.

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
- les premiers résultats par version A / B : part qui choisit Michelin plutôt que Hankook, part d'accord (4 ou 5) et moyenne sur 5 pour chaque affirmation Likert, lieux d'achat, âge, kilomètres, durée de réponse ;
- des boutons de téléchargement :
  - **Excel** : séparateur `;`, virgule décimale, accents corrects ;
  - **CSV standard** : séparateur `,`, point décimal, pour R ou Python ;
  - toutes les réponses, ou seulement les **exploitables** (hors essais, 18 ans ou plus, avec une voiture).

## Les colonnes

| Colonne | Contenu |
|---|---|
| `test` | 1 = essai, à écarter |
| `version` | A (Michelin annoncé à 40 000 km, notoriété) ou B (Michelin annoncé à 50 000 km, durée de vie) |
| `duree_s` | temps de réponse, en secondes |
| `age` | âge en années |
| `voiture` | `oui` ou `non` |
| `cible` | 1 = 18 ans ou plus et a une voiture ; 0 = arrêté au filtre |
| `choix_pneu` | `hankook` ou `michelin` |
| `importance_…` | Likert de 1 (pas du tout d'accord) à 5 (tout à fait d'accord) : « … compte beaucoup » pour le prix, la marque, la durée de vie, la performance |
| `km_an` | kilomètres par an (curseur, par pas de 1 000 ; 50 000 = « 50 000 ou plus ») |
| `achat_…` | `oui` ou `non` pour chaque lieu : garage, spécialiste, centre auto, Internet, réparateur rapide |

## Si vous modifiez le questionnaire

Ajoutez toute nouvelle colonne **à la fin** de `COLONNES` dans `serveur/colonnes.php`, et déposez le fichier sur l'hébergeur. Si vous changez les prix, changez-les aux deux endroits : `PRIX_HANKOOK` et `PRIX_MICHELIN` dans `questionnaire.html` et dans `serveur/colonnes.php`. Ne changez rien une fois la collecte lancée.
