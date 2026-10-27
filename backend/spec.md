# Backend Specification

This file is the source of truth for the backend architecture, persistence schema, API contract, and backend delivery checklist.

## 1. Purpose and scope

Build the FastAPI backend for the CHAOURS multi-simulation web app.

The backend:

- persists simulation inputs in SQLite;
- exposes REST endpoints for simulation cards, simulation settings, tranche configuration, outages, and modulations;
- validates all input with Pydantic v2;
- computes results on demand with the NumPy engine;
- returns computed results without persisting them.

## 2. Architecture and file map

Required modules:

```text
backend/
  api/
    __init__.py
    app.py
    config.py
    schemas.py
    routers/
      __init__.py
      simulations.py
  core/
    __init__.py
    models.py
    engine/
      __init__.py
      pipeline.py
      production.py
      jepp.py
      aggregation.py
      alerts.py
  services/
    __init__.py
    simulations.py
  db/
    __init__.py
    config.py
    database.py
    tables.py
    repository.py
    seed.py
  main.py
  cli.py
  tests/
    unit/
      domain/
        test_models.py
        test_aggregates.py
      engine/
        test_engine.py
        test_production.py
        test_jepp.py
        test_aggregation.py
        test_alerts.py
      test_config.py
    integration/
      simulations/
        test_repository.py
        test_service.py
      api/
        test_simulations.py
```

The backend uses four packages:

- `core/` holds the domain: input models, result models, shared domain building blocks, and the calculation engine.
- `services/` holds the application use cases: orchestration, missing-data error translation, and the engine call.
- `api/` holds the HTTP adapter: the FastAPI application, API configuration, request and response schemas, and routers.
- `db/` holds persistence: settings, engine and session construction, SQLModel tables, the repository implementation, and the demo seed.

`main.py` starts uvicorn. `cli.py` runs the local simulation CLI.

Dependency direction:

- `core.models` depends only on Pydantic, NumPy, and the standard library.
- `core.engine` depends on `core.models`.
- `api.schemas` depends on `core.models` only. It must not import FastAPI, `services`, or `db`.
- `services.simulations` depends on `core.models`, `core.engine`, `api.schemas`, and `db.repository`.
- `db.config` depends only on Pydantic Settings.
- `db.database` depends on `db.config`, SQLAlchemy or SQLModel, and FastAPI only for request dependencies. It never imports a service or router.
- `db.tables` depends on `core.models`.
- `db.repository` depends on `core.models`, `api.schemas`, and `db.tables`.
- `db.seed` depends on `core.models`, `api.schemas`, `db.database`, and `db.repository`.
- `api.routers` depends on `api.schemas`, `services.simulations`, `core`, and `db`.
- `api.app` depends on `api.routers`, `api.config`, `core.models`, `db.database`, `db.tables`, and `db.seed`.
- `cli` depends on `core.models` and `core.engine`. It must not import `api.app` or the routers.
- `core.models` must not depend on FastAPI, SQLModel, or SQLAlchemy.
- The engine must not depend on SQLAlchemy.
- Keep `api/__init__.py` and `services/__init__.py` empty so imports have no application side effects.

## 3. Stack and commands

- Python 3.12.
- NumPy.
- Pydantic v2.
- Pydantic Settings.
- FastAPI.
- SQLModel and SQLite.
- uv.
- pytest.
- mypy.

Commands:

```sh
direnv exec . just backend-check
direnv exec . uv run --directory backend pytest tests/integration/api/test_simulations.py
direnv exec . uv run --directory backend python cli.py
direnv exec . just backend-api
```

## 4. Domain models

All domain models live in `backend/core/models.py`. Entity models, result models, enums, constants, NumPy array aliases, and domain errors are in `core/models.py`. API and service contracts live in `backend/api/schemas.py`.

Use `ConfigDict(extra="forbid", validate_assignment=True)` on domain and result models.

### 4.1 Enums

- `TypeArret`: `ASR`, `VP`, `VD`.
- `TypeAlerte`: `NEUTRONIC_ANOMALY`, `REMIT_UMM`, `RTE_DEFICIT`, `SPOT_BELOW_USAGE_VALUE`.

Keep enum string values unchanged because they are protocol and UI codes.

### 4.2 Input models

`Tranche`

- `identifiant: str` with `min_length=1`.
- `code_eic: str` with `min_length=1`.
- `puissance_nominale_mw: float` with `gt=0`.
- `jepp_initial: float` with `ge=0`.

`Arret`

- `type_arret: TypeArret`.
- `jour_debut: int` with `ge=0`.
- `jour_fin: int` with `ge=1`.
- `jour_fin > jour_debut`.

`Modulation`

- `jour_debut: int` with `ge=0`.
- `jour_fin: int` with `ge=1`.
- `facteur: float` with `0.0 <= facteur <= 1.0`.
- `jour_fin > jour_debut`.

`SimulationTranche`

- This is the per-tranche simulation entry.
- `tranche: Tranche`.
- `arrets: list[Arret]`, default empty.
- `modulations: list[Modulation]`, default empty.
- No overlapping outage windows for the same tranche.
- No overlapping modulation windows for the same tranche.
- Touching windows are allowed: `next.jour_debut == previous.jour_fin` is not an overlap.

`Simulation`

- `simulation_id: UUID` with `uuid4` default factory.
- `nom: str` with `min_length=1`, `max_length=200`.
- `cree_le: datetime` with UTC default factory.
- `horizon_jours: int` with `1 <= horizon_jours <= 7305`.
- `prix_spot_eur_mwh: list[float]`.
- `demande_nationale_mwh: list[float]`.
- `valeur_usage_eur_mwh: list[float]`.
- `tranches: list[SimulationTranche]`.

`SimulationResume`

- `simulation_id: UUID`.
- `nom: str`.
- `cree_le: datetime`.
- `horizon_jours: int`.
- `nombre_tranches: int`.

`SimulationCreation`

- `nom: str`.
- `horizon_jours: int`.
- `prix_spot_eur_mwh: list[float]`.
- `demande_nationale_mwh: list[float]`.
- `valeur_usage_eur_mwh: list[float]`.
- `tranches: list[SimulationTranche]`.

`ParametresSimulation`

- `nom: str`.
- `horizon_jours: int`.
- `prix_spot_eur_mwh: list[float]`.
- `demande_nationale_mwh: list[float]`.
- `valeur_usage_eur_mwh: list[float]`.

`ConfigurationTranche`

- `code_eic: str`.
- `puissance_nominale_mw: float`.
- `jepp_initial: float`.

### 4.3 Result models

`ResultatTranche`

- `tranche_id: str`.
- `facteurs_production: list[float]`.
- `energie_mwh: list[float]`.
- `jepp_restant: list[float]`.
- `jours_epuisement: list[int]`.

`Alerte`

- `type_alerte: TypeAlerte`.
- `jour: int | None`.
- `tranche_id: str | None`.
- `message: str`.

`ResultatSimulation`

- `simulation_id: UUID`.
- `duree_execution_ms: float`.
- `tranches: list[ResultatTranche]`.
- `offre_nationale_mwh: list[float]`.
- `demande_mwh: list[float]`.
- `jours_deficit: list[int]`.
- `alertes: list[Alerte]`.

### 4.4 Grouping properties

`Simulation`

- `arrets_par_tranche -> dict[str, tuple[Arret, ...]]`

## 5. Validation rules

All validation lives in Pydantic. The engine and computation modules assume validated input.

`Simulation` validation:

- `horizon_jours` between 1 and 7305.
- The tranche list may be empty, including at creation.
- Unique tranche `identifiant` when tranches are present.
- `prix_spot_eur_mwh`, `demande_nationale_mwh`, and `valeur_usage_eur_mwh` have exactly `horizon_jours` values.
- All series values are finite.
- Demand values are non-negative.
- Every outage and modulation window is inside `[0, horizon_jours]`.
- No overlapping outages and no overlapping modulations per tranche.

Result validation:

- `offre_nationale_mwh` and `demande_mwh` have the same length.
- Every `ResultatTranche` array has the result horizon length.
- Production factors are finite and between 0.0 and 1.0.
- Energy and remaining JEPP are finite and non-negative.
- `jours_epuisement` is ascending.
- Deficit days, depletion days, and present alert days are inside the horizon.
- Tranche identifiers in results are unique.
- `duree_execution_ms >= 0`.

## 6. Database schema

Tables use French names and columns. Use SQLModel table models in `backend/db/tables.py`.

`simulations`

- `simulation_id: UUID`, primary key.
- `nom: str`.
- `cree_le: datetime`.
- `horizon_jours: int`.

`donnees_journalieres`

- `simulation_id: UUID`, part of the primary key, foreign key to `simulations.simulation_id` with `ON DELETE CASCADE`.
- `jour: int`, part of the primary key.
- `prix_spot_eur_mwh: float`.
- `demande_nationale_mwh: float`.
- `valeur_usage_eur_mwh: float`.
- Primary key: `(simulation_id, jour)`.

`tranches`

- `simulation_id: UUID`, part of the primary key, foreign key to `simulations.simulation_id` with `ON DELETE CASCADE`.
- `identifiant: str`, part of the primary key.
- `code_eic: str`.
- `jepp_initial: float`.
- `puissance_nominale_mw: float`.
- Primary key: `(simulation_id, identifiant)`.

`arrets`

- `id: int`, surrogate primary key.
- `simulation_id: UUID`.
- `tranche_id: str`.
- `type_arret: TypeArret`.
- `jour_debut: int`.
- `jour_fin: int`.
- Composite foreign key `(simulation_id, tranche_id)` to `tranches(simulation_id, identifiant)` with `ON DELETE CASCADE`.
- Index on `(simulation_id, tranche_id)`.

`modulations`

- `id: int`, surrogate primary key.
- `simulation_id: UUID`.
- `tranche_id: str`.
- `jour_debut: int`.
- `jour_fin: int`.
- `facteur: float`.
- Composite foreign key `(simulation_id, tranche_id)` to `tranches(simulation_id, identifiant)` with `ON DELETE CASCADE`.
- Index on `(simulation_id, tranche_id)`.

Indexes:

- `simulations.simulation_id`: primary-key index. Used by simulation lookup, update and delete, and by child foreign-key checks.
- `donnees_journalieres (simulation_id, jour)`: composite primary-key index. Loads one simulation's daily rows in day order and supports foreign-key cascade checks. The day-row integrity check reads exactly this range.
- `tranches (simulation_id, identifiant)`: composite primary-key index. Resolves a tranche inside its simulation and provides the parent key required by the composite child foreign keys.
- `arrets (simulation_id, tranche_id)`: explicit composite index. SQLite does not automatically index child foreign-key columns. This index serves schedule loads per simulation and tranche and cascade checks. The surrogate `id` primary key cannot serve these predicates.
- `modulations (simulation_id, tranche_id)`: explicit composite index, for the same reasons as `arrets`.
- `arrets.id` and `modulations.id`: integer primary keys used as stable ordering tie-breakers. They are rowid aliases, so they do not add a separate index.

Columns not indexed:

- `type_arret`, `jour_debut`, `jour_fin`, `facteur`, the daily series values, `nom`, `cree_le`, and `horizon_jours`.
- No current query filters on these columns. They are read after an indexed lookup.
- Adding indexes would increase write cost without a measured read benefit.
- Revisit `cree_le` if the simulation list grows large enough for its ordering to matter, or if new filters are introduced.

Schema rules:

- No JSON columns.
- No result tables.
- Enable SQLite foreign keys on every connection with `PRAGMA foreign_keys=ON`.
- Create tables with `SQLModel.metadata.create_all`.
- Use `StaticPool` for in-memory SQLite test databases.
- The local `chaours.db` must be deleted after the schema change because `create_all` does not migrate old JSON columns.

## 7. Persisted versus computed data

Persisted:

- simulation header;
- daily spot, demand, and VU series;
- tranches;
- outages;
- modulations.

Computed and never persisted:

- production factors;
- energy;
- remaining JEPP;
- depletion days;
- national supply;
- deficit days;
- alerts;
- execution time.

Results are recomputed by `POST /simulations/{simulation_id}/run` after loading the persisted simulation.

## 8. Repository layer

Implement `SimulationRepository` in `backend/db/repository.py`. The service layer in `backend/services/simulations.py` owns use cases and translates missing data into `SimulationNotFoundError` or `TrancheNotFoundError`.

Repository methods:

- `list_all() -> list[SimulationResume]`
- `create(payload: SimulationCreation, simulation_id: UUID | None = None) -> Simulation`
- `get(simulation_id: UUID) -> Simulation | None`
- `update(simulation_id: UUID, payload: ParametresSimulation) -> Simulation | None`
- `update_tranche(simulation_id: UUID, plant_id: str, payload: ConfigurationTranche) -> Simulation | None`
- `add_tranche(simulation_id: UUID, payload: SimulationTranche) -> Simulation | None`
- `replace_arrets(simulation_id: UUID, plant_id: str, arrets: list[Arret]) -> Simulation | None`
- `replace_modulations(simulation_id: UUID, plant_id: str, modulations: list[Modulation]) -> Simulation | None`
- `delete(simulation_id: UUID) -> bool`

Repository rules:

- Convert explicitly between Pydantic models and SQLModel rows.
- Reconstruct and validate the full `Simulation` on every read.
- Verify that `donnees_journalieres` rows are exactly `0 .. horizon_jours - 1`. Reject gaps, duplicates, missing days, and out-of-horizon days.
- `create` generates `simulation_id` and `cree_le`.
- `update` replaces name, horizon, and all three series. The client must send complete resized series.
- `update_tranche` does not allow changing `identifiant`.
- Schedule replacement rebuilds the full simulation, validates it with Pydantic, then persists it. No out-of-horizon or overlapping schedule may be persisted.
- `delete` returns `False` for an unknown id and relies on database cascade for children.
- Do not mutate nested lists in place.

## 9. API contract

Use sync FastAPI endpoints and sync SQLModel sessions.

Application factory:

- `create_app(database_url: str | None = None) -> FastAPI` in `backend/api/app.py`.
- Module-level `app = create_app()` for uvicorn.
- Build a typed `AppContext` during lifespan startup.
- Create tables during lifespan startup.
- Seed the demonstration simulation with a fixed id when it is absent.
- Dispose the SQLAlchemy engine during lifespan shutdown.
- Expose the context and sessions only through FastAPI dependencies. Route handlers must not read `app.state` directly.
- Add CORS for local Vue development origins from `backend/api/config.py`.
- Include the simulations router from `backend/api/routers/simulations.py`.
- Register a Pydantic `ValidationError` handler that returns `422`.
- Use `CHAOURS_DATABASE_URL` with fallback `sqlite:///./chaours.db`, read through `Settings` in `backend/db/config.py`.

Path convention:

- Use `/simulations` and `/plants` path segments.
- Use `{simulation_id}` for the simulation identifier.
- `{plant_id}` maps to the tranche `identifiant`.
- Request and response JSON field names are French as defined above.

Endpoints:

`GET /simulations/`

- Response: `list[SimulationResume]`.
- Status: `200`.

`POST /simulations/`

- Request: `SimulationCreation`.
- Server generates `simulation_id` and `cree_le`.
- Response: `Simulation`.
- Status: `201`.

`GET /simulations/{simulation_id}`

- Response: `Simulation`.
- Status: `200`.
- Unknown simulation: `404`.

`PUT /simulations/{simulation_id}`

- Request: `ParametresSimulation`.
- Response: updated `Simulation`.
- Status: `200`.
- Unknown simulation: `404`.
- Invalid horizon or series length: `422`.
- Existing schedules outside the new horizon: `422`; do not silently remove them.

`DELETE /simulations/{simulation_id}`

- Status: `204`.
- Unknown simulation: `404`.

`POST /simulations/{simulation_id}/plants`

- Request: `SimulationTranche`.
- Response: updated `Simulation`.
- Status: `201`.
- Unknown simulation: `404`.
- Duplicate tranche identifier or invalid schedule: `422`.

`PUT /simulations/{simulation_id}/plants/{plant_id}`

- Request: `ConfigurationTranche`.
- Response: updated `Simulation`.
- Status: `200`.
- Unknown simulation or tranche: `404`.
- Invalid configuration: `422`.

`PUT /simulations/{simulation_id}/plants/{plant_id}/maintenances`

- Request: `list[Arret]`.
- Response: updated `Simulation`.
- Status: `200`.
- Unknown simulation or tranche: `404`.
- Cross-field validation errors: `422`.

`PUT /simulations/{simulation_id}/plants/{plant_id}/modulations`

- Request: `list[Modulation]`.
- Response: updated `Simulation`.
- Status: `200`.
- Unknown simulation or tranche: `404`.
- Cross-field validation errors: `422`.

`POST /simulations/{simulation_id}/run`

- Loads and validates the persisted `Simulation`.
- Runs `SimulationEngine`.
- Response: `ResultatSimulation`.
- Status: `200`.
- Unknown simulation: `404`.

Do not duplicate validation in routes or repository. Reconstruct Pydantic models and let them validate.

## 10. Engine integration

Update `backend/core/engine/` and its computation modules:

- Rename model references to the French classes and fields.
- Convert the three national Pydantic lists to NumPy arrays internally.
- Return lists in `ResultatSimulation` and `ResultatTranche`.
- Compute one national `SPOT_BELOW_USAGE_VALUE` alert per day where spot is below VU.
- Keep `NEUTRONIC_ANOMALY` and `REMIT_UMM` as per-tranche alerts.
- Keep `RTE_DEFICIT` as a national alert.
- Keep `duree_execution_ms` as core engine compute time.

## 11. CLI and local configuration

Update `backend/cli.py`:

- Build `Simulation` and `SimulationTranche` models directly.
- Use the French fields.
- Use flat national series for spot, demand, and VU.
- Update the mock simulation.
- Keep `python cli.py`.

Local database:

- Default URL: `sqlite:///./chaours.db`.
- Override with `CHAOURS_DATABASE_URL`.
- Delete the local database after the schema change.

## 12. Testing

Required tests:

- `unit/domain/test_models.py`: all Pydantic validation rules, national VU series, result consistency.
- `unit/engine/test_engine.py`: computation and integration with the new models.
- `unit/engine/test_production.py`, `test_jepp.py`, `test_aggregation.py`, `test_alerts.py`: computation behavior without duplicate validation tests.
- `unit/test_config.py`: settings defaults, environment override, explicit argument precedence.
- `integration/simulations/test_repository.py`: CRUD, list summaries, cascade deletion, day-row integrity, round-trip, tranche update, schedule replacement, validation failure, isolation.
- `integration/simulations/test_service.py`: service use cases and missing-data errors.
- `integration/api/test_simulations.py`: list, create, get, add tranche, update settings, update tranche config, update outages, update modulations, run, delete, `404`, `422`.

Use in-memory SQLite for repository and API tests. Use FastAPI `TestClient`.

## 13. Backend implementation checklist

- [x] Replace `PlantPlan` with `SimulationTranche`.
- [x] Rename the aggregate `Scenario` to `Simulation`.
- [x] Replace `scenario_id` with `simulation_id` everywhere.
- [x] Rename Pydantic classes and fields to French names.
- [x] Replace per-tranche VU mapping with national VU series.
- [x] Update validation rules and result models.
- [x] Update engine, alerts, production, JEPP, aggregation, and CLI.
- [x] Replace JSON table models with normalized tables.
- [x] Implement composite keys, foreign keys, and cascade deletes.
- [x] Implement repository functions and day-row integrity checks.
- [x] Implement list and update API endpoints.
- [x] Implement the add-tranche endpoint.
- [x] Update all backend tests.
- [x] Allow simulations with an empty tranche list.
- [x] Add a typed application context and lifespan-managed engine.
- [x] Seed the demonstration simulation at startup.
- [x] Delete the local old `chaours.db`.
- [x] Run `just backend-check`.
- [x] Run the CLI.
- [x] Remove alert gravity levels from the API.
- [x] Leave changes uncommitted.
