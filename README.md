# Forkful

Recherche d'aliments et journal alimentaire, en français et en anglais.
Food search and daily log, in French and English.

## Lancer / Run

```
python server.py
```

Puis ouvrir / then open http://localhost:8765

## Sources

- **USDA FoodData Central** (Foundation + SR Legacy): generic foods, lab values. English names only.
  The shared `DEMO_KEY` allows about 10 searches an hour; get a free key at
  https://fdc.nal.usda.gov/api-key-signup and paste it under *Objectifs et réglages*.
- **Open Food Facts**: packaged products, search or barcode. Called through `server.py`,
  because Open Food Facts blocks search requests made directly from a browser.

The log and settings are saved in the browser (localStorage), per day.
