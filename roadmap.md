## Phase 1: Core Calculation Engine (Python + NumPy)

**Goal:** Build and isolate the high-performance simulation engine. It must remain pure Python with zero dependencies on web frameworks or databases.

- **Step 1.1: Data Structures & Scenario Initialization**
  - Accept a dynamic `horizon_days` parameter (defaulting to 365) to support both 1-year and variable horizons.
  - Initialize 1D arrays for Spot prices (`float64`) and national demand (`float64`).
  - Store each plant's initial JEPP stock and nominal power ($MW$).
  - Store maintenances (ASR, VP, VD) and manual modulations as typed records, without assuming one stop per plant.
  - Compose the full scenario from plants, maintenances, modulations, and simulation parameters.

- **Step 1.2: Economic Monitoring (Spot Price vs Usage Value)**
  - Keep the Usage Value (VU) as a static scalar per plant for the MVP. EDF computes it as a dynamic time series in production, but the scalar keeps the frontend to one input per reactor.
  - Store VU values in the scenario as a mapping keyed by plant ID, so the association never depends on array order.
  - Compare both values in €/MWh: the daily Spot price array against each plant's Usage Value (VU).
  - Raise one `SPOT_BELOW_USAGE_VALUE` alert per plant and day where the Spot price is below the VU.
  - Keep the comparison broadcasting-friendly so a future daily VU vector can replace the scalar without rewriting the alert logic.
  - Never apply automatic modulation or modify production factors. The VU alert is informational only.

- **Step 1.3: Production Envelope & Manual Modulation**
  - Start from a nominal factor of $1.0$ for every plant and day when no modulation exists.
  - Apply manual modulation windows as target factors between $0.0$ and $1.0$.
  - Build a 2D boolean mask (`bool_`) representing scheduled maintenance outages (ASR, VP, VD).
  - Apply the maintenance mask last, so production is $0.0$ on outage days and stops always win over modulation.
  - Keep the factor envelope free of any automatic power reduction.

- **Step 1.4: JEPP Cycles, Recharge & Hard Stock Cutoff**
  - A cycle starts at day $0$ or at a stop `end_day`, and ends at the next stop `end_day` or at the horizon.
  - Production is zero during `[start_day, end_day)`, and stock stays constant during the stop.
  - Stock resets to `initial_jepp` at every stop `end_day`, before production on that day; each ASR, VP, and VD stop creates an independent cycle.
  - Compute cumulative requested consumption per cycle with `np.cumsum`.
  - The first day where requested consumption exceeds the stock is the deficit day of that cycle.
  - On the deficit day, clip production to the remaining stock, then report zero until the next recharge.
  - Apply no automatic stretch-out. The stock limit is hard.
  - Raise a `NEUTRONIC_ANOMALY` alert asking for manual modulation after a depletion.
  - Raise an alert when depletion occurs with no future stop.
  - Record the first deficit day of each affected cycle in `depletion_days`.

- **Step 1.5: Energy Aggregation, National Deficit & REMIT**
  - Convert 2D production factors to daily energy with $\text{energy} = \text{factor} \times P_{\text{nominal}} \times 24$.
  - Sum national supply across plants using `np.sum(axis=0)`.
  - Compare national supply against national demand day by day to flag `RTE_DEFICIT` alerts.
  - Compute REMIT per plant and per day from the absolute day-over-day power variation in MW.
  - Flag a `REMIT_UMM` alert when the absolute variation exceeds $100\text{ MW}$.
  - Include planned stop boundaries in the REMIT variation.
  - Report the alert on the second day of the variation.

- **Step 1.6: Engine Orchestration, CLI & Benchmark**
  - Encapsulate the logic in a pure Python class (`NucliEngine`).
  - Run the pipeline in order: nominal factors, manual modulation, maintenance mask, JEPP cycles, energy aggregation, alerts.
  - Build a CLI script to run simulations against mock data.
  - Benchmark execution using `timeit` to ensure total computation stays well under the $40\text{ ms}$ threshold.

---

## Phase 2: Data Schemas & API Contracts (Pydantic v2)

**Goal:** Define strict data contracts for input validation, API request/response serialization, and compliance with AI Act traceability requirements.

- **Step 2.1: Input Schemas**
  - `PlantConfig`: `id`, `eic_code`, `nominal_power_mw`, `initial_jepp`.

  - `MaintenanceSchedule`: `plant_id`, `kind` (ASR, VP, VD), `start_day`, `end_day`.

  - `ModulationConsigne`: `plant_id`, `start_day`, `end_day`, `factor` ($0.0 - 1.0$).

  - `SimulationParameters`: `scenario_id`, `horizon_days`, `spot_prices`, `demand_mwh`, `usage_values_eur_mwh`.

  - The full input schema composes `plants`, `maintenances`, `modulations`, and `parameters`, matching the engine `Scenario` contract field by field.

- **Step 2.2: Output & Alert Schemas**
  - `PlantTrajectory`: `plant_id`, `production_factors`, `energy_mwh`, `remaining_jepp`, `depletion_days`.

  - `ComplianceAlert`: `kind`, `day`, `plant_id`, `message`, `severity`. Alert kinds: `NEUTRONIC_ANOMALY`, `REMIT_UMM`, `RTE_DEFICIT`, `SPOT_BELOW_USAGE_VALUE`.

  - `SimulationResult`: `scenario_id`, `execution_time_ms`, `plants`, flat `national_supply_mwh`, flat `demand_mwh`, flat `deficit_days`, `alerts`.

- **Step 2.3: Validation Rules**
  - Enforce Pydantic v2 `@field_validator` checks (e.g., ensuring modulation factors stay between $0.0$ and $1.0$, and maintenance start days precede end days).
  - Pydantic validates transport input at the API boundary, while the engine keeps minimal guards for direct calls (array dimensions, negative consumption, invalid windows).
  - Do not invent alternate API field names for engine fields that already exist.

---

## Phase 3: Database & Persistence Layer (SQLModel + SQLite)

**Goal:** Persist simulation states, plant configurations, and user scenarios while enabling fully isolated "what-if" sessions.

- **Step 3.1: SQLModel Database Models**
  - `SimulationScenario`: Primary key `simulation_id` (UUID), scenario name, created timestamp, horizon days.
  - `PlantModel`: Plant ID, EIC code, nominal capacity, baseline JEPP.

  - `MaintenanceModel`: Foreign key to `SimulationScenario` and `PlantModel`, outage type, start day, end day.

  - `ModulationModel`: Foreign key to `SimulationScenario` and `PlantModel`, start day, end day, target ratio.

- **Step 3.2: SQLite Database Initialization**
  - Set up lightweight SQLite storage (`chaours.db`) using SQLModel/SQLAlchemy engine.
  - Write database migrations or auto-table creation scripts (`SQLModel.metadata.create_all`).

- **Step 3.3: Repository Layer**
  - Implement CRUD functions to load, save, duplicate, and delete simulation scenarios by their unique `simulation_id`.

---

## Phase 4: API Backend (FastAPI)

**Goal:** Expose high-performance REST endpoints connecting the SQLite database, Pydantic schemas, and the NumPy engine.

- **Step 4.1: Fast-API Application Setup**
  - Initialize FastAPI app with CORS middleware (enabling communication with the Vue.js frontend).
  - Configure automatic OpenAPI / Swagger documentation generation.

- **Step 4.2: Scenario Management Endpoints**
  - `POST /simulations/`: Create a new isolated simulation session.
  - `GET /simulations/{simulation_id}`: Retrieve scenario parameters and current state.
  - `DELETE /simulations/{simulation_id}`: Clean up old scenarios.

- **Step 4.3: Configuration Endpoints**
  - `PUT /simulations/{simulation_id}/maintenances`: Update or move maintenance blocks (ASR/VP/VD).
  - `PUT /simulations/{simulation_id}/modulations`: Update manual user modulation inputs.

- **Step 4.4: The Execution Endpoint (`POST /simulations/{simulation_id}/run`)**
  - Fetch scenario state from SQLite.
  - Convert stored configurations into dense NumPy matrices.
  - Pass matrices into `NucliEngine`.
  - Serialize outputs via Pydantic (`SimulationResult`) and return JSON to the client.

---

## Phase 5: Frontend Interface (Vue.js + Pinia + Gantt)

**Goal:** Provide an interactive dashboard for GPM planners, featuring interactive Gantt timeline manipulation and real-time visual feedback.

- **Step 5.1: Vue Project Setup & State Management**
  - Set up Vue 3 project with Pinia for global state management.
  - Create a Pinia store (`useSimulationStore`) holding current `simulation_id`, plant states, trajectories, and active alerts.

- **Step 5.2: Interactive Gantt Chart Component**
  - Integrate a Gantt library (e.g., Frappe Gantt or dhtmlxGantt).
  - Render horizontal bars for each nuclear plant representing ASR, VP, and VD outages.
  - Implement Drag-and-Drop functionality for moving or extending outage blocks.

- **Step 5.3: Real-Time Event Handling & Debouncing**
  - Attach an `onDragEnd` listener to Gantt items.
  - Debounce user actions (e.g., waiting $100\text{ ms}$ after drag stop) before dispatching a `PUT` request to update maintenance dates and triggering `/run`.

- **Step 5.4: Visualization Dashboards**
  - Integrate Chart.js or Plotly.js.
  - **JEPP Depletion Chart:** Plot daily remaining fuel stock per plant over time.
  - **National Balance Chart:** Overlay total aggregated nuclear generation against national demand to visually highlight deficit areas.

- **Step 5.5: Compliance & Alert Panel**
  - Build a dedicated sidebar or notification banner displaying alerts returned by the backend.
  - Color-code alerts: **Red** for Neutronic Anomalies / Deficits, **Yellow** for REMIT/UMM 100 MW threshold triggers.

---

## Phase 6: Integration, E2E Testing & Optimization

**Goal:** Verify full system cohesion, real-time UI responsiveness, and data consistency.

- **Step 6.1: End-to-End Latency Verification**
- Test complete round-trip time: Drag item on Gantt $\rightarrow$ HTTP request $\rightarrow$ FastAPI $\rightarrow$ NumPy calculation $\rightarrow$ Database write $\rightarrow$ JSON response $\rightarrow$ UI Chart re-render.
- Ensure total round-trip stays well under human-perceptible delay ($< 150\text{ ms}$ total, keeping backend compute under $40\text{ ms}$).

- **Step 6.2: Isolated Session Verification**
- Open two parallel browser sessions with different `simulation_id`s to ensure edits in one scenario do not bleed into or affect the other.
