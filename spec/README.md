# Spécification du projet Nuclear Planing

Ce dossier contient les concepts et les règles métier de CHAOURS. Il ne décrit ni l'architecture technique, ni les routes API, ni les composants d'interface.

## Objet

CHAOURS est un simulateur interactif d'aide à la décision pour la programmation des tranches nucléaires. Il permet de tester des simulations isolées, de calculer l'épuisement du combustible (JEPP), de comparer la valeur d'usage au prix spot et de vérifier la sécurité d'approvisionnement électrique nationale.

## Hiérarchie documentaire

- `spec/` est la source de vérité métier.
- `backend/spec.md` est la source de vérité de l'architecture backend, du schéma de données, de l'API et de la feuille de route backend.
- `frontend/spec.md` est la source de vérité de l'interface, des parcours utilisateur et de la feuille de route frontend.
- `README.md` donne la vue d'ensemble du projet et les commandes de démarrage.

Une évolution du contrat API doit être reportée dans `backend/spec.md` et dans le miroir du contrat de `frontend/spec.md`.

## Navigation

- [01 - Contexte](01-contexte.md) : acteurs, objectifs, cadre institutionnel.
- [02 - Concepts](02-concepts.md) : JEPP, valeur d'usage, simulation, tranche, arrêts et modulation.
- [03 - Règles métier](03-regles-metier.md) : calculs de trajectoire, cycles JEPP, arbitrage, modulation manuelle, agrégation et critères d'acceptation métier.
- [Spécification backend](../backend/spec.md) : architecture, schéma SQLite, repository, API FastAPI et feuille de route backend.
- [Spécification frontend](../frontend/spec.md) : dashboard, détail de simulation, timeline, éditeurs, alertes et feuille de route frontend.

## Glossaire

- Alerte nationale : alerte qui concerne toute la simulation, sans tranche associée. Exemples : déficit national, prix spot sous la valeur d'usage.
- Alerte tranche : alerte rattachée à une tranche et à un jour. Exemples : anomalie neutronique, variation REMIT.
- ASN : Autorité de Sûreté Nucléaire.
- ASR : Arrêt Simple pour Rechargement, environ 30 à 45 jours.
- Cycle JEPP : période entre deux rechargements, du jour 0 ou du `jour_fin` d'un arrêt jusqu'au `jour_fin` de l'arrêt suivant ou à la fin de l'horizon.
- DOAAT : Direction Optimisation Amont-Aval et Trading.
- EIC : Energy Identification Code, code standard européen d'identification d'une tranche.
- GPM : Pôle Gestion Portefeuille et Marchés.
- JEPP : Jour Équivalent Pleine Puissance, unité d'énergie consommée par une tranche à 100 % de sa puissance nominale pendant 24 heures.
- Rechargement : remise du stock JEPP à `jepp_initial` au `jour_fin` d'un arrêt ASR, VP ou VD.
- REMIT : règlement européen sur l'intégrité et la transparence du marché de l'énergie.
- RTE : Réseau de Transport d'Électricité.
- Simulation : ensemble isolé composé d'un nom, d'un horizon, de séries journalières nationales et de tranches avec leurs arrêts et modulations.
- Stretch-out : prolongation manuelle d'une campagne par une modulation de puissance décidée par l'utilisateur ; ce n'est pas un ajustement automatique du moteur.
- Tranche : configuration d'une unité nucléaire dans une simulation, avec son identifiant, son code EIC, sa puissance nominale, son stock JEPP initial et ses calendriers.
- UMM : Urgent Market Message, message de transparence destiné au marché.
- VD : Visite Décennale, environ 3 à 6 mois.
- VP : Visite Partielle, environ 60 à 90 jours.
- VU : Valeur d'Usage, coût d'opportunité d'un MWh nucléaire conservé en stock, en €/MWh. Dans le MVP, c'est une série temporelle journalière nationale unique pour toute la simulation.
