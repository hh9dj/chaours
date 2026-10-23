## Phase 1: Core Calculation Engine (Python + NumPy)

**Goal:** Build and isolate the high-performance simulation engine. It must remain pure Python with zero dependencies on web frameworks or databases.

- **Step 1.1: Dynamic Data Structures & State Initialization**
  - Accept a dynamic `horizon_days` parameter (defaulting to 365) to support both 1-year and variable horizons.
  - Initialize 1D arrays for Spot prices (`float64`) and national demand (`float64`).
  - Initialize 1D arrays for each plant's initial JEPP stock and Nominal Power ($MW$).

  - Create a 2D boolean mask (`bool_`) representing scheduled maintenance outages (ASR, VP, VD).

- **Step 1.2: Economic Arbitrage (The Modulation Engine)**
  - Compare the Spot price array against each plant's Usage Value (VU).

  - Use `np.where` to generate a 2D matrix of targeted production factors ($0.0 \le \text{factor} \le 1.0$).

  - Apply the maintenance mask to force production factors to $0.0$ on outage days.

- **Step 1.3: JEPP Depletion & Automatic Stretch-Out (Physical Limits)**
  - Calculate cumulative JEPP consumption using `np.cumsum(production_factors, axis=1)`.

  - Implement the stretch-out limit: detect if a plant's stock reaches $0\text{ JEPP}$ before its scheduled maintenance date.

  - Overwrite targeted factors with a degraded stretch-out factor where physical limits are reached.

  - Flag a **Neutronic Anomaly** if stretch-out is insufficient to reach the maintenance date.

- **Step 1.4: Aggregation & Compliance Alerts**
  - Convert 2D production factors to daily energy ($\text{Factor} \times P_n \times 24\text{h}$).

  - Sum national production across all plants using `np.sum(axis=0)`.

  - Compare aggregated supply against national demand to flag **Deficit/Load-Shedding Alerts**.

  - Calculate day-over-day production variations (`np.diff`). If $\Delta P > 100\text{ MW}$, flag a **REMIT/UMM Transparency Alert**.

- **Step 1.5: CLI Wrapper & Performance Benchmarking**
  - Encapsulate the logic in a pure Python class (e.g., `NucliEngine`).
  - Build a CLI script to run simulations against mock data.
  - Benchmark execution using `timeit` to ensure total computation stays well under the $40\text{ ms}$ threshold.

---

## Phase 2: Data Schemas & API Contracts (Pydantic v2)

**Goal:** Define strict data contracts for input validation, API request/response serialization, and compliance with AI Act traceability requirements.

- **Step 2.1: Input Schemas**
  - `PlantConfig`: Plant ID, EIC code, nominal power ($MW$), initial JEPP stock.

  - `MaintenanceSchedule`: Maintenance type (ASR, VP, VD), start day, end day.

  - `ModulationConsigne`: Start day, end day, target power ratio ($0.0 - 1.0$).

  - `SimulationParameters`: Scenario ID, time horizon ($days$), Spot price vector, Demand vector.

- **Step 2.2: Output & Alert Schemas**
  - `PlantTrajectory`: Plant ID, daily JEPP trajectory array, daily production MW array.

  - `AggregatedOutput`: Daily national production vector, daily demand vector, total deficit MW.

  - `ComplianceAlert`: Alert type (`NEUTRONIC_ANOMALY`, `REMIT_UMM`, `RTE_DEFICIT`), day index, plant ID, message, severity level.

  - `SimulationResult`: Scenario ID, execution time ($ms$), list of `PlantTrajectory`, `AggregatedOutput`, list of `ComplianceAlert`.

- **Step 2.3: Validation Rules**
  - Enforce Pydantic v2 `@field_validator` checks (e.g., ensuring modulation ratios stay between $0.0$ and $1.0$, and maintenance start dates precede end dates).

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
