---
name: Scientific Workstation Light
colors:
  surface: '#f7f9ff'
  surface-dim: '#c4dcfa'
  surface-bright: '#f7f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eef4ff'
  surface-container: '#e4efff'
  surface-container-high: '#daeaff'
  surface-container-highest: '#cfe5ff'
  on-surface: '#021d33'
  on-surface-variant: '#3f4850'
  inverse-surface: '#1a3249'
  inverse-on-surface: '#e9f1ff'
  outline: '#707881'
  outline-variant: '#bfc7d2'
  surface-tint: '#006398'
  primary: '#006194'
  on-primary: '#ffffff'
  primary-container: '#007bb9'
  on-primary-container: '#fdfcff'
  inverse-primary: '#93ccff'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#00685f'
  on-tertiary: '#ffffff'
  tertiary-container: '#008378'
  on-tertiary-container: '#f4fffc'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cce5ff'
  primary-fixed-dim: '#93ccff'
  on-primary-fixed: '#001d31'
  on-primary-fixed-variant: '#004b73'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#89f5e7'
  tertiary-fixed-dim: '#6bd8cb'
  on-tertiary-fixed: '#00201d'
  on-tertiary-fixed-variant: '#005049'
  background: '#f7f9ff'
  on-background: '#021d33'
  surface-variant: '#cfe5ff'
  canvas-bg: '#F0F5FA'
  sidebar-bg: '#E2ECF5'
  surface-white: '#FFFFFF'
  surface-panel-soft: '#F4F8FC'
  border-grid: '#CBD9E8'
  border-subtle: '#D5E1EE'
  text-primary: '#0F1E2E'
  text-secondary: '#4E657E'
  status-success: '#059669'
  status-warning: '#D97706'
  status-critical: '#DC2626'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 22px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: -0.005em
  body-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  body-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
  data-display-lg:
    fontFamily: JetBrains Mono
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 26px
    letterSpacing: -0.02em
  data-display-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  data-mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
  label-caps:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.06em
  unit-label:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '400'
    lineHeight: 14px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 0.5rem
  gutter-sm: 0.25rem
  margin: 0.75rem
  margin-mobile: 0.5rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system translates rigorous scientific telemetry and process engineering into a daylight-optimized, high-clarity laboratory workstation environment. Designed for chemical research engineers, plant operators, and scientific ML practitioners, it shifts from high-fatigue dark rooms to an immaculate, daylight-calibrated workstation aesthetic.

### Design Movement: High-Precision Laboratory Modernism
The visual language draws inspiration from precision analytical instrumentation (spectrometers, chromatography consoles, cleanroom telemetry monitors) and modern engineering CAD workbenches:
- **Atmospheric Clarity:** An icy light blue and structured slate-blue foundation that eliminates harsh monitor glare while keeping contrast pin-sharp.
- **Deterministic Information Density:** Compact UI real estate, zero decorative flairs, rigid structural dividing lines, and dedicated tabular arrangements.
- **Controlled Energetic Accents:** Vivid technical cyan and rich cobalt blue deployed selectively for state transitions, convergence trajectories, and execution setpoints.
- **High-Acuity Contrast:** Strict slate-navy typography ensuring legibility across high-frequency numeric streams and dense multi-panel viewports.

## Colors

The palette establishes an immaculate, light-mode scientific substrate with calibrated cyan and cobalt engineering accents.

### Color Distribution Strategy
- **Workspace Canvas Base (`canvas-bg`, `#F0F5FA`):** The primary workstation canvas. Cool, low-glare icy blue tint that frames floating analytical tools.
- **Structural Sidebar (`sidebar-bg`, `#E2ECF5`):** Docked telemetry drawers, system hierarchies, and directory navigation panes.
- **Primary Workstation Panels (`surface-white`, `#FFFFFF` & `surface-panel-soft`, `#F4F8FC`): High-clarity cards, chart matrices, parameter inspectors, and tabular displays.
- **Structural Separation (`border-grid`, `#CBD9E8` & `border-subtle`, `#D5E1EE`):** Crisp 1px perimeter outlines and inner data division rules; drop shadows are strictly avoided.
- **Primary Text (`text-primary`, `#0F1E2E`):** Deep slate-navy for authoritative contrast, razor-sharp numerical readouts, and header clarity.
- **Secondary Text (`text-secondary`, `#4E657E`):** Muted slate blue for metric keys, physical engineering units, and axis indices.

### Engineering & Semantic Accents
- **Primary Engineering Accent (`#0284C7`):** Interactive setpoints, active vector tracers, primary run triggers, and live controller feedback.
- **Secondary Accent (`#2563EB`):** Neural twin trajectories, surrogate model curves, and categorical telemetry badges.
- **Equilibrium / Stable State (`status-success`, `#059669`):** Convergence, normal operating tolerances, verified process safety.
- **Thermal / Drift Warning (`status-warning`, `#D97706`):** Boundary excursion alerts, numerical stiffness warnings, sensor noise drift.
- **Emergency / Boundary Violation (`status-critical`, `#DC2626`):** Emergency stops (ESD), kinetic thermal runaway, NaN losses, unstable equilibria.

## Typography

The typographical scale emphasizes operational scan speed, absolute glyph disambiguation, and numeric stabilization under high update frequencies.

### Type Pairings & Behavioral Directives
- **Inter:** Manages spatial navigation, panel titles, operational messages, table column headers, and UI states.
- **JetBrains Mono:** Dedicated to dynamic numeric telemetry, mathematical expressions, physical dimensions ($T_j$, $C_{in}$, $\dot{V}$), sensor time stamps, and array matrices. Tabular figures (`font-variant-numeric: tabular-nums`) must be enforced globally to guarantee that high-speed numerical updates do not introduce horizontal visual jitter.
- **Letter Spacing & Casing:** Micro-labels and telemetry keys utilize uppercase styling (`label-caps`) with open tracking (`0.06em`) for instantaneous recognition at a distance.

## Elevation & Depth

Visual hierarchy in this workstation is established purely through structural tone layering and crisp 1px borders. Drop shadows, diffuse blurs, and glassmorphic filters are rejected to preserve strict edge definition and prevent visual softening of dense data.

### Structural Depth Tiers
- **Substrate (Level 0):** Canvas base `#F0F5FA`. The foundational workbench surface.
- **Structural Shelf (Level 1):** Sidebar and secondary docks at `#E2ECF5`, defined by a 1px solid right border in `#CBD9E8`.
- **Primary Panel / Instrument Card (Level 2):** `#FFFFFF` or `#F4F8FC`, bounded by a sharp 1px border in `#CBD9E8`.
- **Focused / Elevated Inspector (Level 3):** `#FFFFFF` with a 1px active outline in technical cyan `#0284C7` and a zero-blur crisp border highlight (`box-shadow: 0 0 0 1px #0284C7`).
- **Critical Interruption / Modal (Level 4):** Pure `#FFFFFF` surface framed with a double-ring perimeter: 1px `#D5E1EE` surrounded by a crisp 2px `#DC2626` outline during emergency boundary interruptions.

## Shapes

The geometric framework reflects precision laboratory apparatus, precision-machined brackets, and calibrated digital hardware interfaces.

### Corner Radii Guidelines
- **Soft Precision (`roundedness: 1`):** Structural borders and operational modules use an architectural 4px radius (`0.25rem`).
- **Micro-Controls:** Input steppers, status badges, buttons, and tab switchers utilize a subtle 3px to 4px radius.
- **Panels Anchored to Screen Edges:** Form flush zero-radius seams (`0px`) with the display boundaries.
- **Pill Shapes:** Strictly prohibited for functional UI containers; only reserved for circular telemetry status pings (`rounded-full`, 6px indicator dots).

## Components

### Buttons & Operational Triggers
- **Primary Execution Button:** Solid precision cyan (`#0284C7`) background, crisp white (`#FFFFFF`) bold text, 4px border radius. Hover: `#0369A1`. Active: `#075985`. Used for critical operations like "Commit Setpoint" or "Solve Trajectory".
- **Secondary Tool Button:** Pure white (`#FFFFFF`) surface, 1px `#CBD9E8` border, deep slate (`#0F1E2E`) text. Hover: `#F0F5FA` background with `#0284C7` border.
- **Critical Action Button:** Crisp white background with a `#DC2626` 1px border and `#DC2626` text. Expands to solid `#DC2626` with `#FFFFFF` text on armed state for Emergency Shutdown (ESD).

### Telemetry Cards & Metric Chips
- **Instrument Panel Card:** Solid `#FFFFFF` or `#F4F8FC` body enclosed in a 1px `#CBD9E8` border. Header bar separated with a 1px `#D5E1EE` horizontal divider.
- **Parameter Readout Chip:** `#E2ECF5` container, 1px `#CBD9E8` border. Displays an uppercase label in `#4E657E` alongside a high-contrast numeric value in `#0F1E2E` rendered in tabular JetBrains Mono.

### Data Tables & Matrix Views
- **Header Cells:** `#E2ECF5` background, 26px height, uppercase Inter (`label-caps`), text in `#4E657E`.
- **Data Rows:** Compact 28px height with alternate row striping using `#FFFFFF` and `#F4F8FC`. Bottom border 1px `#D5E1EE`. Monospaced tabular numerals right-aligned with fixed vertical alignment lines.

### Inputs & Engineering Steppers
- **Numerical Inputs:** High-contrast `#FFFFFF` fill, 1px `#CBD9E8` border, `#0F1E2E` JetBrains Mono text. Physical engineering units (e.g., `kPa`, `mol/m³`, `K`) pinned inside the right margin in `#4E657E`.
- **Focus State:** Border shifts directly to `#0284C7` with a matching 1px inward ring; zero offset.

### Checkboxes & Segmented Selectors
- **Segmented Mode Switchers:** Contained in a `#E2ECF5` frame with 1px `#CBD9E8` border. Active item is pure `#FFFFFF` with `#0F1E2E` bold text and a subtle 1px border.
- **Checkboxes & Radios:** 14px square/round controls with a 1px `#CBD9E8` perimeter; active state renders with a solid `#0284C7` fill and white checkmark icon.

### Scientific Telemetry & Chart Displays
- **Plot Background:** `#FFFFFF` or `#F4F8FC` plotting area with crisp 1px `#CBD9E8` outer bounding box.
- **Coordinate Grid:** Thin 1px grid ticks in `#D5E1EE` at major intervals; `#F0F5FA` at minor intervals.
- **Signal Traces:** Ground-truth process traces render as a 1.5px solid `#0284C7` curve. Neural twin / surrogate model predictions render as a 1.5px dashed `#2563EB` curve.