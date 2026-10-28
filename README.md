# Nuclear Planing

CHAOURS is an interactive decision-support simulator for scheduling nuclear unit outages. It lets you test outage calendars, compute fuel depletion (JEPP), report deviations between usage value and spot price, and check electricity supply security.

## Documentation

- [Concepts and business rules](./spec/README.md)
- [Backend specification](./backend/spec.md)
- [Frontend specification](./frontend/spec.md)

## Overview

The web application is organized around isolated simulations:

- a dashboard lists simulations as cards and lets you create a new one;
- each simulation contains a horizon, national daily series, and several units;
- each unit has a timeline that shows production, outages, modulations, and the JEPP level;
- unit alerts are shown on the timeline;
- national alerts are grouped in a sidebar.

Computation results, such as alerts, deficit days, JEPP depletion days, and daily supply, are recomputed and not persisted.

## Prerequisites

- Nix with flakes enabled.
- direnv to load the development shell defined in `flake.nix`.

## Installation

1. Install Nix:

```sh
sh <(curl -L https://nixos.org/nix/install) --daemon
```

2. Enable flakes:

```sh
mkdir -p ~/.config/nix
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
```

3. Load the development shell, with direnv:

```sh
direnv allow
```

or without direnv, for each session:

```sh
nix develop
```

The development shell provides Node.js 22, pnpm, Python 3.12, uv, SQLite, ruff, and just.

## Backend

Run the simulation CLI:

```sh
just backend-run
```

Run the FastAPI API in development:

```sh
just backend-api
```

The API stores scenarios in SQLite. By default, the database is `./chaours.db`. The environment variable `CHAOURS_DATABASE_URL` changes the URL, for example `sqlite:///./data/chaours.db`.
