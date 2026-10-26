# Spécification frontend

Statut : conception cible et feuille de route frontend.

Propriétaire : worktree frontend.

Ce fichier est la source de vérité de l'interface, des parcours utilisateur, du contrat API consommé et de la feuille de route frontend.

## Consigne pour l'agent

- Lire d'abord `spec/README.md`, `spec/02-concepts.md` et `spec/03-regles-metier.md`.
- Ce fichier est la source de vérité du worktree frontend.
- Le contrat API de la section 3 est un miroir figé de `backend/spec.md`.
- Ne pas modifier `spec/`, `backend/spec.md`, `README.md` ni `AGENTS.md`.
- Ne pas implémenter de code backend.
- Mettre à jour uniquement la checklist d'implémentation frontend de ce fichier.
- Laisser les changements non commités sauf demande explicite de l'utilisateur.

## 1. Objet et périmètre

Construire l'application web de CHAOURS. Elle permet de :

- consulter un dashboard de simulations sous forme de cartes ;
- créer une simulation ;
- ouvrir une simulation et voir ses tranches ;
- visualiser une timeline par tranche ;
- modifier les arrêts, les modulations et la configuration d'une tranche ;
- modifier les paramètres d'une simulation ;
- consulter les alertes de tranche sur la timeline ;
- consulter les alertes nationales dans une barre latérale.

Le frontend ne calcule pas les résultats métier. Il appelle le backend FastAPI et affiche `ResultatSimulation`.

## 2. Stack, commandes et arborescence

Stack :

- Vue 3 avec `<script setup>` et TypeScript.
- Vite.
- Pinia pour l'état applicatif.
- Tailwind CSS v4.
- Vitest pour les tests.
- Interface en français.
- Navigateurs desktop.

Commandes :

```sh
pnpm -C frontend install
pnpm -C frontend dev
pnpm -C frontend test
pnpm -C frontend build
```

Arborescence cible :

```text
frontend/
  src/
    main.ts
    App.vue
    router.ts
    style.css
    api/
      client.ts
      types.ts
    stores/
      simulations.ts
    views/
      DashboardView.vue
      SimulationView.vue
    components/
      SimulationCard.vue
      AddSimulationCard.vue
      CreateSimulationDialog.vue
      SimulationSettingsDialog.vue
      TrancheTimeline.vue
      TrancheEditor.vue
      NationalAlertsSidebar.vue
      AlertPopover.vue
    lib/
      timeline.ts
      timeline.test.ts
      couleurs.ts
      couleurs.test.ts
      format.ts
      format.test.ts
```

## 3. Contrat API consommé

Le backend est la source de vérité. Toute évolution doit être reportée ici et dans `backend/spec.md` avant de poursuivre le travail parallèle.

URL de base :

- variable `VITE_API_BASE_URL` ;
- valeur par défaut : `http://localhost:8000`.

Erreurs :

- `404` : simulation ou tranche inconnue.
- `422` : validation Pydantic. Le corps contient `detail`.
- Afficher les messages en français dans l'interface.

Types TypeScript :

```ts
type TypeArret = "ASR" | "VP" | "VD";

type TypeAlerte =
  | "NEUTRONIC_ANOMALY"
  | "REMIT_UMM"
  | "RTE_DEFICIT"
  | "SPOT_BELOW_USAGE_VALUE";

type Gravite = "INFO" | "WARNING" | "CRITICAL";

interface Tranche {
  identifiant: string;
  code_eic: string;
  puissance_nominale_mw: number;
  jepp_initial: number;
}

interface Arret {
  type_arret: TypeArret;
  jour_debut: number;
  jour_fin: number;
}

interface Modulation {
  jour_debut: number;
  jour_fin: number;
  facteur: number;
}

interface Simulation {
  tranche: Tranche;
  arrets: Arret[];
  modulations: Modulation[];
}

interface Scenario {
  simulation_id: string;
  nom: string;
  cree_le: string;
  horizon_jours: number;
  prix_spot_eur_mwh: number[];
  demande_nationale_mwh: number[];
  valeur_usage_eur_mwh: number[];
  tranches: Simulation[];
}

interface SimulationResume {
  simulation_id: string;
  nom: string;
  cree_le: string;
  horizon_jours: number;
  nombre_tranches: number;
}

interface ScenarioCreation {
  nom: string;
  horizon_jours: number;
  prix_spot_eur_mwh: number[];
  demande_nationale_mwh: number[];
  valeur_usage_eur_mwh: number[];
  tranches: Simulation[];
}

interface ParametresSimulation {
  nom: string;
  horizon_jours: number;
  prix_spot_eur_mwh: number[];
  demande_nationale_mwh: number[];
  valeur_usage_eur_mwh: number[];
}

interface ConfigurationTranche {
  code_eic: string;
  puissance_nominale_mw: number;
  jepp_initial: number;
}

interface ResultatTranche {
  tranche_id: string;
  facteurs_production: number[];
  energie_mwh: number[];
  jepp_restant: number[];
  jours_epuisement: number[];
}

interface Alerte {
  type_alerte: TypeAlerte;
  jour: number | null;
  tranche_id: string | null;
  message: string;
  gravite: Gravite;
}

interface ResultatSimulation {
  simulation_id: string;
  duree_execution_ms: number;
  tranches: ResultatTranche[];
  offre_nationale_mwh: number[];
  demande_mwh: number[];
  jours_deficit: number[];
  alertes: Alerte[];
}
```

Endpoints :

- `GET /simulations/` : renvoie `SimulationResume[]`.
- `POST /simulations/` : reçoit `ScenarioCreation`, renvoie `Scenario`, statut `201`.
- `GET /simulations/{simulation_id}` : renvoie `Scenario`.
- `PUT /simulations/{simulation_id}` : reçoit `ParametresSimulation`, renvoie `Scenario`.
- `DELETE /simulations/{simulation_id}` : statut `204`.
- `PUT /simulations/{simulation_id}/plants/{plant_id}` : reçoit `ConfigurationTranche`, renvoie `Scenario`.
- `PUT /simulations/{simulation_id}/plants/{plant_id}/maintenances` : reçoit `Arret[]`, renvoie `Scenario`.
- `PUT /simulations/{simulation_id}/plants/{plant_id}/modulations` : reçoit `Modulation[]`, renvoie `Scenario`.
- `POST /simulations/{simulation_id}/run` : renvoie `ResultatSimulation`.

Le paramètre `plant_id` est l'`identifiant` de la tranche. Il est immuable.

## 4. Routes et navigation

Routes :

- `/` : dashboard des simulations.
- `/simulations/:simulation_id` : détail d'une simulation.

Navigation :

- clic sur une carte de simulation : ouvre `/simulations/:simulation_id` ;
- clic sur le bouton retour du détail : retour au dashboard ;
- rechargement direct d'une URL de simulation : charge la simulation depuis l'API.

## 5. Store Pinia et client API

Créer un store `simulations` avec :

- `simulations: SimulationResume[]` ;
- `currentScenario: Scenario | null` ;
- `currentResult: ResultatSimulation | null` ;
- `loading` ;
- `error` ;
- actions de chargement, création, mise à jour, suppression et exécution.

Le client API doit :

- centraliser l'URL de base ;
- convertir les erreurs HTTP en erreurs lisibles ;
- exposer des fonctions typées pour chaque endpoint ;
- ne pas calculer de résultats métier.

Après chaque modification réussie :

1. remplacer `currentScenario` par la réponse du `PUT` ;
2. appeler `POST /simulations/{simulation_id}/run` ;
3. remplacer `currentResult` ;
4. mettre à jour la timeline et la barre latérale.

## 6. Dashboard

Charger `GET /simulations/`.

Afficher :

- une grille de cartes de simulation ;
- une carte `+` pour créer une simulation ;
- un état vide si aucune simulation n'existe ;
- un état de chargement ;
- un état d'erreur avec bouton de réessai.

Carte de simulation :

- nom ;
- horizon en jours ;
- date de création formatée en français ;
- nombre de tranches ;
- clic vers le détail.

Création :

- la carte `+` ouvre `CreateSimulationDialog` ;
- champs : nom, horizon, identifiant de la première tranche, code EIC, puissance nominale, JEPP initial ;
- valeurs par défaut : horizon 365 jours, prix spot 80 €/MWh, demande nationale 0 MWh, VU 60 €/MWh ;
- les séries sont plates sur tout l'horizon ;
- après création, fermer le dialogue et naviguer vers la simulation créée.

## 7. Vue simulation

Charger :

- `GET /simulations/{simulation_id}` ;
- puis `POST /simulations/{simulation_id}/run`.

Afficher :

- en-tête avec le nom de la simulation, l'horizon et la date de création ;
- bouton `Paramètres` ;
- bouton retour vers le dashboard ;
- liste des tranches ;
- une timeline par tranche ;
- barre latérale des alertes nationales.

Chaque ligne de tranche affiche :

- identifiant, code EIC, puissance nominale et JEPP initial ;
- timeline ;
- légende locale ou infobulle ;
- bouton ou zone cliquable pour ouvrir `TrancheEditor`.

## 8. Timeline

La timeline représente les jours `0` à `horizon_jours - 1`.

Hauteur des barres :

- la hauteur est proportionnelle à `facteurs_production[jour]`, entre 0 et 1 ;
- un jour sans production a une hauteur nulle ;
- un jour de maintenance affiche un bloc gris pleine hauteur, même si le facteur vaut 0.

Couleur JEPP :

- ratio = `jepp_restant[jour] / jepp_initial` ;
- vert si ratio supérieur ou égal à 0.50 ;
- jaune si ratio supérieur ou égal à 0.20 ;
- orange si ratio supérieur ou égal à 0.05 ;
- rouge si ratio inférieur à 0.05 ;
- si `jepp_initial` vaut 0, utiliser rouge.

Modulation :

- un jour couvert par une modulation est marqué visuellement, par exemple avec un liseré supérieur bleu ;
- la hauteur reste celle du facteur de production réel ;
- la maintenance reste grise et prioritaire sur le marquage de modulation.

Alertes de tranche :

- filtrer `currentResult.alertes` par `tranche_id` et `jour` ;
- afficher une icône d'avertissement cliquable sur le jour concerné ;
- l'icône ouvre `AlertPopover` avec le message, le jour et la gravité ;
- les alertes sans jour ne sont pas placées sur la timeline.

Infobulle :

- jour ;
- facteur de production ;
- énergie ;
- JEPP restant ;
- modulation appliquée si présente ;
- arrêt en cours si présent.

Légende :

- hauteur = production ;
- gris = maintenance ;
- vert, jaune, orange, rouge = niveau de JEPP ;
- icône = alerte de tranche.

Interaction :

- clic sur la timeline ouvre `TrancheEditor` pour la tranche ;
- la timeline est accessible au clavier : les jours et les alertes ont des libellés accessibles ;
- aucune information ne dépend uniquement de la couleur.

## 9. Éditeur de tranche

Ouvrir `TrancheEditor` depuis la timeline.

Champs de configuration :

- code EIC ;
- puissance nominale en MW ;
- JEPP initial ;
- identifiant affiché mais non modifiable.

Arrêts :

- ajouter, modifier et supprimer des arrêts ;
- type ASR, VP ou VD ;
- `jour_debut`, `jour_fin` ;
- afficher les erreurs de chevauchement ou de dépassement d'horizon en français.

Modulations :

- ajouter, modifier et supprimer des modulations ;
- `jour_debut`, `jour_fin`, `facteur` entre 0 et 1 ;
- afficher les erreurs de chevauchement ou de dépassement d'horizon en français.

Enregistrement :

1. appeler `PUT /simulations/{simulation_id}/plants/{plant_id}` ;
2. appeler `PUT /simulations/{simulation_id}/plants/{plant_id}/maintenances` ;
3. appeler `PUT /simulations/{simulation_id}/plants/{plant_id}/modulations` ;
4. recharger le scénario ou utiliser la dernière réponse ;
5. appeler `/run`.

Si un appel échoue, afficher l'erreur, recharger le scénario depuis l'API et ne pas afficher de résultat incohérent.

## 10. Paramètres de simulation

Ouvrir `SimulationSettingsDialog` depuis le bouton `Paramètres`.

Champs :

- nom ;
- horizon en jours ;
- série de prix spot ;
- série de demande nationale ;
- série de valeur d'usage.

Édition des séries :

- utiliser une zone de texte ou un éditeur de liste avec une valeur par ligne ;
- valider les nombres et la longueur côté client ;
- afficher le nombre de valeurs attendu ;
- autoriser le copier-coller de séries.

Changement d'horizon :

- redimensionner les trois séries côté client ;
- tronquer si l'horizon diminue ;
- étendre avec la dernière valeur si l'horizon augmente ;
- demander à l'utilisateur de vérifier avant l'enregistrement.

Enregistrement :

- envoyer les trois séries complètes et redimensionnées à `PUT /simulations/{simulation_id}` ;
- un planning hors horizon produit `422` ;
- afficher les erreurs en français ;
- appeler `/run` après succès.

## 11. Alertes

Alertes de tranche :

- `NEUTRONIC_ANOMALY` ;
- `REMIT_UMM`.

Alertes nationales :

- `RTE_DEFICIT` ;
- `SPOT_BELOW_USAGE_VALUE`.

La barre latérale `NationalAlertsSidebar` ne montre que les alertes nationales. Elle ne doit jamais afficher une alerte avec `tranche_id` non nul.

Chaque alerte affiche :

- un titre lisible en français ;
- le jour concerné ;
- la gravité ;
- le message du backend ;
- pour une alerte de tranche, l'identifiant de la tranche.

Couleurs de gravité :

- `CRITICAL` : rouge ;
- `WARNING` : ambre ;
- `INFO` : neutre.

Les couleurs sont accompagnées d'un libellé.

## 12. États, erreurs et accessibilité

- État de chargement pour le dashboard et le détail.
- État vide pour le dashboard.
- État vide pour une simulation sans alerte nationale.
- Erreur API avec bouton de réessai.
- Erreur de validation `422` affichée dans le dialogue concerné.
- Messages et libellés en français.
- Labels explicites pour les champs.
- Navigation clavier pour les cartes, les boutons et les icônes d'alerte.
- Focus visible.
- Les alertes ne sont pas signalées uniquement par la couleur.
- Cible desktop, sans dégradation majeure sur tablette.

## 13. Tests et critères d'acceptation

Tests Vitest :

- hauteur de barre = facteur de production ;
- seuils de couleur JEPP ;
- maintenance grise prioritaire ;
- marquage des modulations ;
- filtrage des alertes de tranche et nationales ;
- redimensionnement des séries lors d'un changement d'horizon ;
- client API et gestion des erreurs `404` et `422`.

Critères d'acceptation :

- le dashboard liste les simulations et permet d'en créer une ;
- une simulation s'ouvre par URL directe ;
- chaque tranche affiche une timeline de jour 0 à la fin de l'horizon ;
- les arrêts sont gris ;
- la hauteur suit la production réelle ;
- les couleurs JEPP respectent les seuils ;
- les alertes de tranche sont cliquables sur la timeline ;
- les alertes nationales apparaissent uniquement dans la barre latérale ;
- les éditeurs mettent à jour le backend et relancent le calcul ;
- les erreurs de validation sont visibles en français ;
- `pnpm -C frontend test` et `pnpm -C frontend build` passent.

## 14. Feuille de route frontend

- [ ] Mettre en place le router, le store Pinia et le client API.
- [ ] Définir les types TypeScript du contrat API.
- [ ] Implémenter le dashboard et les cartes de simulation.
- [ ] Implémenter le dialogue de création.
- [ ] Implémenter la vue simulation et le chargement du résultat.
- [ ] Implémenter la timeline et ses calculs.
- [ ] Implémenter l'éditeur de tranche.
- [ ] Implémenter les paramètres de simulation.
- [ ] Implémenter la barre latérale des alertes nationales.
- [ ] Implémenter les popovers d'alerte de tranche.
- [ ] Ajouter les états de chargement, vide et erreur.
- [ ] Écrire les tests Vitest.
- [ ] Vérifier `pnpm -C frontend test`.
- [ ] Vérifier `pnpm -C frontend build`.
- [ ] Laisser les changements non commités.

## 15. Hors périmètre

- authentification et gestion des utilisateurs ;
- collaboration temps réel ;
- historique de versions ou annulation globale ;
- persistance des résultats ;
- export ou import de simulation ;
- glisser-déposer sur la timeline dans cette première version ;
- application mobile ;
- calcul métier dans le navigateur.
