# Nucliplan Frontend Specification

Status: implemented POC, browser-only calculation.

## 1. Purpose and scope

The frontend is a single-page planning simulator for one nuclear unit. It lets the user:

- configure a simulation horizon;
- set the initial JEPP stock;
- define a default discharge factor;
- define modulation periods with their own discharge factor;
- define planned stops with ASR, VP, or VD type;
- view the JEPP trajectory and key indicators;
- edit modulation and stop periods directly on the chart with the mouse.

The application has one static unit, `Tranche 1 — 900 MW`. It does not load plant data, persist scenarios, aggregate a fleet, or call a backend.

## 2. Stack and commands

- Vue 3 with `<script setup>` and TypeScript.
- Vite build tooling.
- Tailwind CSS v4 through `@tailwindcss/vite`.
- Vitest for unit tests.
- No charting library. The chart is custom inline SVG.
- No state-management library. State is local Vue state.

Root `Justfile` commands:

```text
just setup    pnpm install in frontend/
just dev      Vite development server
just test     Vitest run
just build    vue-tsc and production build
just check    test then build
just clean    remove node_modules and dist
```

Package scripts in `frontend/package.json`:

```text
dev, build, preview, test, test:watch, typecheck
```

## 3. File structure

```text
frontend/
  index.html
  src/
    main.ts
    App.vue
    style.css
    components/
      TrancheCard.vue
      TrajectoireChart.vue
    lib/
      jepp.ts
      jepp.test.ts
      chronologie.ts
      chronologie.test.ts
      couleurs.ts
      couleurs.test.ts
      planification.ts
```

## 4. Domain model

### 4.1 JEPP and discharge

JEPP means day-equivalent full power.

- 1 JEPP is the energy consumed by running at 100 % nominal power for 24 hours.
- The default discharge factor is a percentage from 0 to 100.
- 100 % consumes 1 JEPP per day. 50 % consumes 0.5 JEPP per day.
- A modulation period overrides the default factor on every calendar day inside its start and end dates, inclusive.
- Outside modulation periods, the default factor applies.
- A stop freezes consumption. The JEPP value at stop start stays constant during the stop.
- The stop end is a recharge point. The stock resets to the initial JEPP value.
- Consumption resumes after the recharge point.
- Multiple stops and multiple modulation periods are supported.
- Stops are processed in chronological order.
- Modulations may overlap stops. The stop color and stop behavior take priority.

### 4.2 Dates

- Dates use the `YYYY-MM-DD` representation.
- Date arithmetic uses UTC midnight to avoid timezone and daylight-saving drift.
- The simulation starts at the current local date, normalized to UTC midnight.
- The simulation horizon ends at the same calendar date plus the configured number of years.
- Start and end dates of modulation periods are inclusive.
- A stop ends at `start date + stop duration`.
- Rotation or aggregation of dates is day-based. There is no hourly granularity.

### 4.3 Stop types

```text
ASR  Arrêt simple pour rechargement  45 days
VP   Visite partielle                90 days
VD   Visite décennale                180 days
```

The stop duration is fixed by type. Stops can be moved on the chart but cannot be resized there. The type can be changed from the popover if the new duration stays inside the horizon and does not overlap another stop.

### 4.4 Horizon

- Minimum: 1 year.
- Maximum: 20 years.
- Default: 5 years.
- Horizon end is calculated from the current date.
- Any modulation or stop must fit inside the horizon.

### 4.5 Simulation result

The simulation function returns:

- validation errors;
- horizon end date;
- normalized modulation periods, sorted by start date;
- normalized stops, sorted by start date, with `jeppAvant` for each stop;
- first stop and the JEPP value before it;
- days until the first stop;
- autonomy in days;
- exhaustion alert flag;
- first stop reached with an empty stock;
- daily trajectory points.

Trajectory point phases:

```text
production     stock decreases according to the effective factor
arret          stock stays constant during the stop
rechargement  stock resets to the initial value at stop end
```

The trajectory is daily from today through horizon end, inclusive.

### 4.6 Autonomy

Autonomy estimates the number of days needed to consume the initial stock using the effective factors from today.

- It ignores stops and recharges.
- It uses modulation factors when the current date is inside a modulation period.
- It returns `null` when no positive factor exists or the stock is not exhausted within 36,500 simulated days.
- A `null` value is displayed as `∞`.

### 4.7 Validation rules

Simulation is rejected when any rule below fails. Errors are shown in French and the chart is not rendered.

- Initial JEPP must be a finite number greater than or equal to zero.
- Default discharge factor must be between 0 % and 100 %.
- Horizon must be an integer between 1 and 20 years.
- Each modulation period must have a valid start and end date.
- A modulation start cannot be before today.
- A modulation end cannot be after horizon end.
- A modulation end cannot be before its start.
- A modulation factor must be between 0 % and 100 %.
- Modulation periods cannot overlap. The next start must be after the previous end.
- Each stop must have a valid start date.
- A stop start cannot be before today or after horizon end.
- A stop must not extend beyond horizon end.
- The stop type must be a known type.
- Stops cannot overlap. The next start must be after the previous end.
- Modulations and stops may overlap each other.

## 5. Page layout

- The application uses the full viewport width.
- Header: `Nucliplan`, subtitle, and logo block.
- Main title: `Planification tranche`.
- A single card contains the unit header, the input panel, and the results panel.
- On large screens the card uses two columns: 340 px fixed input column and a flexible results column.
- On smaller screens the columns stack.
- The interface language is French.
- The unit header displays `Tranche 1 — 900 MW` and `Simulation indicative`.

## 6. Inputs

### 6.1 Horizon

Number input labelled `Horizon (années)`.

- Default: 5.
- Step: 1.
- Range: 1 to 20.

### 6.2 Initial stock

Number input labelled `JEPP initial`.

- Default: 90.
- Minimum: 0.
- Step: 1.

### 6.3 Default discharge factor

Range slider labelled `Facteur par défaut`.

- Default: 100 %.
- Range: 0 to 100.
- Step: 5.
- The current value is shown in a green badge.
- Help text states it applies outside modulation periods and that 100 % equals 1 JEPP per day.

### 6.4 Modulation periods

Section `Périodes de modulation`.

- Empty state: `Aucune période. Le facteur par défaut s'applique sur tout l'horizon.`
- `+ Ajouter une période` creates a new modulation.
- The first new modulation starts today.
- Later new modulations start after the latest existing modulation end, plus one day.
- Default duration is 30 days.
- Default factor is 50 %.
- Dates are clamped to the horizon when a new period is added.
- Each card shows a colored left border, a colored dot, `Période N`, and a remove button.
- Editable fields: start date, end date, factor.
- Clicking a card selects it and highlights the matching chart band.
- The selected card gets a colored outline.
- Deleting the selected item clears the selection.

### 6.5 Planned stops

Section `Arrêts planifiés`.

- Empty state: `Aucun arrêt planifié. La trajectoire montre uniquement la consommation sur l'horizon.`
- `+ Ajouter un arrêt` creates a new stop.
- The first new stop starts 90 days from today.
- Later new stops start after the latest existing stop end, plus 30 days.
- Dates are clamped to the horizon.
- New stop type is ASR.
- Each card shows a colored left border, a colored dot, `Arrêt N`, and a remove button.
- Editable fields: start date and stop type.
- The card displays the type description and duration.
- Clicking a card selects it and highlights the matching chart band.
- The selected card gets a colored outline.
- Deleting the selected item clears the selection.

## 7. Summary and alerts

The results column shows one of four banners.

- Red error block when simulation validation fails.
- Amber `Épuisement avant un arrêt` when the stock reaches zero before a stop, or when the initial stock is zero.
- Neutral `Aucun arrêt planifié` when no stop exists.
- Green `Stock suffisant pour les arrêts planifiés` otherwise. The banner shows the minimum JEPP value before any stop.

The summary grid shows:

- number of stops;
- first stop date;
- JEPP before the first stop;
- autonomy in days, or `∞`.

Numbers use French formatting with at most one decimal.

## 8. Interactive JEPP chart

### 8.1 Geometry and axes

- Inline SVG, viewBox `800 × 260`.
- Plot padding: 28 px horizontal, 34 px top, 34 px bottom.
- Y scale starts at 0 and ends at the maximum JEPP value in the trajectory.
- A dashed horizontal line marks zero.
- Five X-axis ticks are generated from the visible window.
- Tick format depends on the visible duration:
  - 120 days or less: day and short month;
  - 1100 days or less: short month and year;
  - longer: year.
- The chart is clipped to the plot area.
- All chart colors come from the item colors.

### 8.2 Curve and bands

The JEPP curve is split into colored segments:

1. A date inside a stop uses the stop color.
2. Otherwise, a date inside a modulation uses the modulation color.
3. Otherwise, the default color is emerald `#059669`.

Adjacent segments share the boundary point to avoid visual gaps. Stops take priority over modulations.

Chart overlays:

- modulation bands, normal opacity 0.11, selected opacity 0.26;
- stop bands, normal opacity 0.18, selected opacity 0.32;
- `M1`, `M2` labels for modulations;
- `A1`, `A2` labels for stops;
- a neutral gray area fill under the curve.

A legend below the chart lists:

- `Hors période` with the default color;
- each modulation with label, dates, and factor;
- each stop with label, dates, and type.

### 8.3 Hover tooltip

- Moving the pointer over the chart shows a dashed vertical crosshair.
- A colored dot marks the nearest trajectory point.
- A tooltip shows the date and JEPP value at that point.
- The tooltip stays inside the chart area.
- It hides when the pointer leaves, during a drag, and when zoom changes.
- The tooltip uses the closest daily point, not interpolated values.

### 8.4 Selection and popover

- Selecting a band highlights its card and its band.
- Selecting a card highlights its band.
- A selected band opens a popover if it is visible in the current view.
- The popover is hidden when the selected item is outside the current zoom window.
- Modulation popover: dates and a factor number input from 0 to 100, step 5.
- Stop popover: dates and a type select.
- Stop type changes are rejected if the new duration exceeds the horizon or overlaps another stop.
- The popover has a close button.

### 8.5 Editing modes

Toolbar buttons:

```text
Sélection
+ Modulation
+ Arrêt
```

Selection mode:

- Click empty chart space to clear selection.
- Drag empty chart space to pan when zoomed.
- Drag a modulation band body to move it.
- Drag modulation edge handles to resize it.
- Drag a stop band body to move it.
- Stops have no resize handles.
- The hint `Glissez le fond du graphique pour déplacer la vue...` appears when zoomed.

Modulation creation mode:

- Drag on empty chart space to create a modulation range.
- Single click creates a 30-day modulation at the clicked date.
- The new modulation factor is 50 %.
- The item is selected after creation.
- The toolbar returns to selection mode.

Stop creation mode:

- Click or drag to place an ASR stop at the pointer date.
- The stop duration is 45 days.
- The item is selected after creation.
- The toolbar returns to selection mode.

Invalid creation:

- The preview turns red.
- An inline message explains the overlap or horizon violation.
- No item is created.

### 8.6 Move and resize constraints

- Dates snap to whole days.
- Modulation moves preserve their duration.
- Modulation edge resizing changes only the start or end date.
- Stop moves preserve the duration fixed by their type.
- Items are clamped inside the horizon.
- Items are clamped against same-type neighbors.
- Modulations and stops may overlap each other.
- Moving and resizing update the forms and simulation live.
- `Escape` cancels the active move, resize, creation, or pan and restores the original state.
- `pointercancel` clears the interaction.
- Modulation edge handles are thin 1.25-unit colored lines.
- Each edge has an invisible hit zone of 4 to 10 chart units, based on band width.
- Handles are hidden for bands narrower than 6 chart units.

### 8.7 Zoom and pan

Zoom presets:

```text
Tout    full horizon
5 ans   1825 days, capped to the horizon
1 an    365 days, capped to the horizon
3 mois  91 days, capped to the horizon
```

- The visible window is always clamped inside the horizon.
- Panning is available by dragging empty chart space in selection mode.
- Panning is clamped to the horizon.
- Changing zoom clears the hover tooltip.
- The visible window drives curve geometry, bands, ticks, tooltips, and date conversion.

## 9. Colors

Default curve color: emerald `#059669`.

Modulation palette:

```text
#0284c7 #4f46e5 #0891b2 #2563eb #7c3aed #475569
```

Stop palette:

```text
#d97706 #ea580c #dc2626 #e11d48 #9333ea #92400e
```

Rules:

- A color is assigned when an item is created.
- The color is stored in the form object, so removing another item does not recolor it.
- The palettes cycle after six items.
- The same color is used for the card border, card dot, chart band, and curve segment.
- Stop color wins over modulation color when dates overlap.

## 10. State and data flow

Source of truth:

- `initialJepp`
- `facteurDefaut`
- `horizonAnnees`
- `arrets`
- `modulations`

Derived state:

- `dateFinHorizon`
- `result = simulate(...)`
- summary values
- chart geometry and chart legend

Interaction flow:

1. `TrancheCard.vue` owns the forms and simulation state.
2. `TrajectoireChart.vue` owns chart display state: mode, zoom, visible window, hover, drag, preview, and messages.
3. The chart emits selection, date updates, factor updates, type updates, and creation events.
4. `TrancheCard.vue` applies those events to the forms.
5. The simulation recomputes.
6. The chart re-renders from the new trajectory and forms.

All state is in memory. Reloading the page resets everything. There is no persistence, URL state, or backend.

## 11. Accessibility and UX details

- Form controls have labels and focus styles.
- Chart bands have pointer cursors: grab, crosshair, or resize.
- The chart uses `touch-action: none` to support pointer dragging.
- The chart has an ARIA label.
- Escape is supported during chart interactions.
- Keyboard editing of chart bands is not implemented. The side cards remain the accessible editing fallback.
- Colors are accompanied by labels, dots, and card context, not used alone to convey meaning.

## 12. Tests

Current test suite: 51 tests across three files.

`jepp.test.ts` covers:

- date parsing and timezone-safe arithmetic;
- French date formatting;
- stock depletion at stop start;
- modulation factors and custom periods;
- default factor behavior outside periods;
- zero-factor behavior;
- horizon usage;
- recharge reset;
- post-recharge consumption;
- multiple stops;
- overlapping modulation and stop rejection;
- horizon violations;
- past dates;
- invalid stock, factor, or horizon;
- empty stock alert;
- trajectory without stops.

`chronologie.test.ts` covers:

- zoom window duration and clamping;
- pixel-to-date and date-to-pixel conversion;
- tick generation;
- move clamping against neighbors and horizon;
- resize clamping;
- creation range validation;
- pan clamping.

`couleurs.test.ts` covers:

- palette cycling;
- default color outside periods;
- modulation color selection;
- stop priority over modulation;
- inclusive date boundaries;
- segment grouping and shared boundary points.

## 13. Known limitations

Not implemented:

- multiple nuclear units or fleet aggregation;
- plant reference data, EIC codes, nominal MW, or regional constraints;
- demand curve comparison;
- spot prices, Valeur d’Usage, or market arbitrage;
- national MW production aggregation;
- REMIT UMM generation;
- backend API, database, persistence, scenarios, or revisions;
- user accounts, permissions, or collaboration;
- undo/redo history beyond cancelling the current drag with Escape;
- custom stop durations by resizing;
- automatic zoom on selection;
- pinch zoom or multi-touch gestures;
- keyboard movement of chart bands;
- scenario export or import;
- save, share, or URL-encoded state.

Behavioral limitations:

- Simulation runs entirely in the browser.
- Invalid side-card values remove the chart from the page until corrected.
- Colors repeat after six items in each palette.
- The chart uses daily resolution only.
- The unit name and power are static.
- The chart tooltip reads the nearest daily point; it does not interpolate between days.
