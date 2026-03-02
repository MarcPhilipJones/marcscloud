/**
 * EnergyUsageCharts — Fictional 12-month gas & electricity usage charts.
 *
 * Two area charts stacked vertically:
 *   1. Electricity (blue/teal) — slight uptick in last 2-3 months (EV charging)
 *   2. Gas (amber/orange) — seasonal pattern, higher in winter
 *
 * All data is completely fictional / hardcoded for demo purposes.
 */

import { useRef, useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { makeStyles, tokens } from "@fluentui/react-components";

// ── Dynamic 12-month data generation ─────────────────────────────
// Generates the trailing 12 months relative to the current date.
// If demoed in July, the x-axis shows Aug (last year) → Jul (this year).

const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

/** Seasonal baseline electricity (kWh) by calendar month (0=Jan). */
const ELEC_SEASONAL: Record<number, number> = {
  0: 370,
  1: 355,
  2: 310,
  3: 275,
  4: 240,
  5: 210,
  6: 195,
  7: 205,
  8: 260,
  9: 305,
  10: 340,
  11: 385,
};

/** Seasonal gas (kWh) by calendar month (0=Jan) — UK heating pattern. */
const GAS_SEASONAL: Record<number, number> = {
  0: 1340,
  1: 1180,
  2: 980,
  3: 720,
  4: 410,
  5: 180,
  6: 120,
  7: 130,
  8: 380,
  9: 680,
  10: 1050,
  11: 1280,
};

/**
 * Build a 12-element array of { month, kWh } ending with
 * the most recently completed month (relative to `now`).
 *
 * For electricity, the last 2 months get an EV-charging uplift
 * (~+120 kWh) and the month before that gets a smaller bump (~+50 kWh).
 */
function generateData(
  seasonal: Record<number, number>,
  evUplift: boolean,
): { month: string; kWh: number }[] {
  const now = new Date();
  const data: { month: string; kWh: number }[] = [];

  for (let i = 11; i >= 0; i--) {
    // Walk backwards from the previous month
    const d = new Date(now.getFullYear(), now.getMonth() - 1 - i, 1);
    const m = d.getMonth(); // 0-11
    const yy = String(d.getFullYear()).slice(-2); // "25", "26", etc.
    const label = `${MONTH_NAMES[m]} ${yy}`;
    let kWh = seasonal[m];

    if (evUplift) {
      const pos = 11 - i; // 0 = oldest … 11 = newest
      if (pos >= 10)
        kWh += 120; // last 2 months — big EV bump
      else if (pos === 9) kWh += 50; // month before — small ramp
    }

    // Add slight random jitter (±3%) for realism, seeded by month index
    const jitter = 1 + (((m * 7 + 3) % 11) - 5) / 100;
    kWh = Math.round(kWh * jitter);

    data.push({ month: label, kWh });
  }
  return data;
}

const ELECTRICITY_DATA = generateData(ELEC_SEASONAL, true);
const GAS_DATA = generateData(GAS_SEASONAL, false);

// ── Colours ──────────────────────────────────────────────────────

const ELEC_COLOUR = "#0078d4"; // Blue (Microsoft brand blue)
const GAS_COLOUR = "#e67700"; // Amber/orange

// ── Styles ───────────────────────────────────────────────────────

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    gap: "4px",
    /* Do NOT use flex:1 — inside a D365 IFrame there is no height
       constraint, so flex:1 expands to infinity. Use explicit heights. */
  },
  chartSection: {
    display: "flex",
    flexDirection: "column",
    backgroundColor: tokens.colorNeutralBackground1,
    borderRadius: "8px",
    padding: "12px 16px 4px 8px",
    boxShadow: tokens.shadow4,
  },
  chartHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "4px",
    paddingLeft: "8px",
  },
  chartTitle: {
    fontSize: "13px",
    fontWeight: 600,
    color: tokens.colorNeutralForeground1,
  },
  badge: {
    fontSize: "10px",
    fontWeight: 600,
    padding: "1px 8px",
    borderRadius: "10px",
    color: "#fff",
  },
  badgeElec: {
    backgroundColor: ELEC_COLOUR,
  },
  badgeGas: {
    backgroundColor: GAS_COLOUR,
  },
  evHint: {
    fontSize: "11px",
    color: tokens.colorNeutralForeground3,
    marginLeft: "auto",
    fontStyle: "italic",
  },
  chartContainer: {
    /* Height set dynamically via JS to cope with D365 IFrame */
    minHeight: 0,
    overflow: "hidden",
  },
});

// ── Tooltip formatter ────────────────────────────────────────────

function formatTooltip(value: number | undefined) {
  return [`${(value ?? 0).toLocaleString()} kWh`, "Usage"];
}

// ── Component ────────────────────────────────────────────────────

/** Hard cap per chart (px). Inside a D365 IFrame the viewport height
 *  is unreliable, so we clamp each chart to a sensible max. */
const MAX_CHART_PX = 200;
const MIN_CHART_PX = 120;

function computeChartHeight(): number {
  const vh = Math.min(window.innerHeight, 700);
  const overhead = 60;
  const available = vh - overhead;
  let perChart = Math.max(MIN_CHART_PX, Math.floor(available / 2));
  perChart = Math.min(perChart, MAX_CHART_PX);
  return perChart;
}

export function EnergyUsageCharts() {
  const styles = useStyles();
  const rootRef = useRef<HTMLDivElement>(null);
  const [chartH, setChartH] = useState(() => computeChartHeight());

  useEffect(() => {
    const onResize = () => setChartH(computeChartHeight());
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <div className={styles.root} ref={rootRef}>
      {/* ── Electricity chart ─────────────────────────────────── */}
      <div className={styles.chartSection}>
        <div className={styles.chartHeader}>
          <span className={`${styles.badge} ${styles.badgeElec}`}>⚡</span>
          <span className={styles.chartTitle}>
            Electricity Usage (kWh) — 12 Months
          </span>
          <span className={styles.evHint}>
            📈 Recent uptick — possible EV charging
          </span>
        </div>
        <div className={styles.chartContainer} style={{ height: chartH }}>
          <ResponsiveContainer width="100%" height={chartH}>
            <AreaChart
              data={ELECTRICITY_DATA}
              margin={{ top: 4, right: 12, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="elecGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={ELEC_COLOUR} stopOpacity={0.3} />
                  <stop
                    offset="95%"
                    stopColor={ELEC_COLOUR}
                    stopOpacity={0.02}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} width={45} />
              <Tooltip formatter={formatTooltip} />
              <Area
                type="monotone"
                dataKey="kWh"
                stroke={ELEC_COLOUR}
                strokeWidth={2}
                fill="url(#elecGrad)"
                dot={{ r: 3, fill: ELEC_COLOUR }}
                activeDot={{ r: 5, fill: ELEC_COLOUR }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Gas chart ─────────────────────────────────────────── */}
      <div className={styles.chartSection}>
        <div className={styles.chartHeader}>
          <span className={`${styles.badge} ${styles.badgeGas}`}>🔥</span>
          <span className={styles.chartTitle}>Gas Usage (kWh) — 12 Months</span>
        </div>
        <div className={styles.chartContainer} style={{ height: chartH }}>
          <ResponsiveContainer width="100%" height={chartH}>
            <AreaChart
              data={GAS_DATA}
              margin={{ top: 4, right: 12, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="gasGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={GAS_COLOUR} stopOpacity={0.3} />
                  <stop
                    offset="95%"
                    stopColor={GAS_COLOUR}
                    stopOpacity={0.02}
                  />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
              <XAxis dataKey="month" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} width={45} />
              <Tooltip formatter={formatTooltip} />
              <Area
                type="monotone"
                dataKey="kWh"
                stroke={GAS_COLOUR}
                strokeWidth={2}
                fill="url(#gasGrad)"
                dot={{ r: 3, fill: GAS_COLOUR }}
                activeDot={{ r: 5, fill: GAS_COLOUR }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
