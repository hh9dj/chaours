# Nuclear Planing

CHAOURS est un simulateur interactif d'aide à la décision pour la programmation des tranches nucléaires. Il permet de tester les calendriers d'arrêt, de calculer l'épuisement du combustible (JEPP), de signaler les écarts entre valeur d'usage et prix spot, et de vérifier la sécurité d'approvisionnement électrique.

La spécification complète est disponible dans [spec/README.md](./spec/README.md).

## Prérequis

- Nix avec les flakes activés.
- direnv pour charger le shell de développement défini dans `flake.nix`.

## Installation

1. Autoriser le fichier `.envrc` :

```sh
direnv allow
```

Le shell de développement fournit Node.js 22, pnpm, Python 3.12, uv, SQLite, ruff et just.
