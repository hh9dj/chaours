# Nuclear Planing

CHAOURS est un simulateur interactif d'aide à la décision pour la programmation des tranches nucléaires. Il permet de tester les calendriers d'arrêt, de calculer l'épuisement du combustible (JEPP), de signaler les écarts entre valeur d'usage et prix spot, et de vérifier la sécurité d'approvisionnement électrique.

## Documentation

- [Concepts et règles métier](./spec/README.md)
- [Spécification backend](./backend/spec.md)
- [Spécification frontend](./frontend/spec.md)

## Vue d'ensemble

L'application web est organisée autour de simulations isolées :

- un dashboard liste les simulations sous forme de cartes et permet d'en créer une nouvelle ;
- chaque simulation contient un horizon, des séries journalières nationales et plusieurs tranches ;
- chaque tranche possède une timeline qui montre la production, les arrêts, les modulations et le niveau de JEPP ;
- les alertes de tranche sont affichées sur la timeline ;
- les alertes nationales sont regroupées dans une barre latérale.

Les résultats de calcul, comme les alertes, les jours de déficit, les jours d'épuisement JEPP et l'offre journalière, sont recalculés et ne sont pas persistés.

## Prérequis

- Nix avec les flakes activés.
- direnv pour charger le shell de développement défini dans `flake.nix`.

## Installation

1. Autoriser le fichier `.envrc` :

```sh
direnv allow
```

Le shell de développement fournit Node.js 22, pnpm, Python 3.12, uv, SQLite, ruff et just.

## Backend

Lancer le CLI de simulation :

```sh
just backend-run
```

Lancer l'API FastAPI en développement :

```sh
just backend-api
```

L'API stocke les scénarios dans SQLite. Par défaut, la base est `./chaours.db`. La variable d'environnement `CHAOURS_DATABASE_URL` permet de changer l'URL, par exemple `sqlite:///./data/chaours.db`.
