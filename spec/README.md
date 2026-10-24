# Spécification du projet Nuclear Planing

Ce dossier regroupe la spécification fonctionnelle et métier de CHAOURS, le simulateur d'aide à la décision pour la programmation des tranches nucléaires.

## Objet

CHAOURS permet de tester et valider les calendriers d'arrêt des tranches nucléaires. Il calcule la capacité physique des tranches à partir de l'épuisement du combustible (JEPP), signale les écarts entre la valeur d'usage et le prix spot, et vérifie la sécurité d'approvisionnement électrique de la France.

## Navigation

- [01 - Contexte](01-contexte.md) : acteurs, objectifs, cadre institutionnel.
- [02 - Concepts](02-concepts.md) : JEPP, valeur d'usage, types d'arrêt et contraintes de planning.
- [03 - Règles métier](03-regles-metier.md) : calculs de trajectoire, arbitrage, modulation, stretch-out, agrégation et filtres réglementaires.
- [04 - Fonctionnalités](04-fonctionnalites.md) : exigences fonctionnelles, composants de l'interface et critères d'acceptation.

## Glossaire

- ASN : Autorité de Sûreté Nucléaire.
- ASR : Arrêt Simple pour Rechargement, environ 30 à 45 jours.
- DOAAT : Direction Optimisation Amont-Aval et Trading.
- EIC : Energy Identification Code, code standard européen d'identification d'une tranche.
- GPM : Pôle Gestion Portefeuille et Marchés.
- JEPP : Jour Équivalent Pleine Puissance, unité d'énergie consommée par une tranche à 100 % de sa puissance nominale pendant 24 heures.
- REMIT : règlement européen sur l'intégrité et la transparence du marché de l'énergie.
- RTE : Réseau de Transport d'Électricité.
- UMM : Urgent Market Message, message de transparence destiné au marché.
- VD : Visite Décennale, environ 3 à 6 mois.
- VP : Visite Partielle, environ 60 à 90 jours.
- VU : Valeur d'Usage, coût d'opportunité d'un MWh nucléaire conservé en stock, en €/MWh. Scalaire statique par tranche dans le MVP, indexé par identifiant de tranche ; série temporelle dynamique chez EDF.
