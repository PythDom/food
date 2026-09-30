# Forkful

Valeurs nutritionnelles et journal alimentaire, en français et en anglais.
Application web installable sur téléphone (PWA), utilisable hors connexion pour la table CIQUAL.

*Nutrition lookup and food log in French and English. Installable on phones (PWA); the CIQUAL table works offline.*

## Sources

| Source | Contenu | Fonctionne |
|---|---|---|
| **ANSES-CIQUAL 2020** | ~3 100 aliments génériques, noms FR/EN | hors connexion, fichier `data/ciqual.json` inclus |
| **USDA FoodData Central** | aliments génériques américains, noms en anglais | en ligne |
| **Open Food Facts** | produits de marque, par code-barres ou par nom | code-barres : partout · recherche par nom : avec `server.py` |

Open Food Facts bloque la recherche par nom depuis un navigateur ; `server.py` la relaie.
La recherche par **code-barres** passe directement et fonctionne donc aussi sur la version hébergée.

## Lancer en local

```
python server.py
```

Puis ouvrir http://localhost:8765 (port au choix : `python server.py 8080`).

## Sur téléphone

La caméra et l'installation exigent HTTPS. Le plus simple est GitHub Pages
(Settings → Pages → Branch `main`, dossier `/`), puis ouvrir
`https://pythdom.github.io/food/` sur le téléphone et :

- **Android (Chrome)** : menu ⋮ → *Installer l'application*
- **iPhone (Safari)** : Partager → *Sur l'écran d'accueil*

Le scanner utilise le détecteur de codes-barres du navigateur quand il existe (Chrome Android),
sinon la bibliothèque ZXing (iPhone, ordinateur). Le bouton *Prendre une photo* marche partout.

## Mettre à jour CIQUAL

```
python tools/build_ciqual.py
```

Télécharge la table ANSES et régénère `data/ciqual.json`. Quand l'énergie manque dans la table,
elle est estimée à partir des protéines, glucides et lipides (facteurs UE) et signalée dans l'app.
Pensez à changer `VERSION` dans `sw.js` pour que les téléphones rechargent le fichier.

## Données

- ANSES-CIQUAL 2020 — Licence Ouverte Etalab 2.0 — https://ciqual.anses.fr
- USDA FoodData Central — domaine public — https://fdc.nal.usda.gov
- Open Food Facts — ODbL — https://world.openfoodfacts.org

Le journal et les réglages sont enregistrés dans le navigateur (localStorage), sur l'appareil.
