/**
 * ContactDetailPage — Energy provider contact dashboard (editable).
 *
 * Layout (single viewport, no scrolling):
 *   Top:    Save button + user info bar
 *   Middle: Compact editable contact fields (three-column grid)
 *   Bottom: Full-width electricity & gas usage charts (12 months)
 *
 * Reads `?id=<guid>` from URL. Falls back to Chris Walker if no ID.
 * All mj_ fields are editable — text fields use Input, booleans use
 * toggleable Switch, choice fields use Dropdown.
 */

import { useEffect, useState, useCallback, useMemo } from "react";
import {
  makeStyles,
  tokens,
  shorthands,
  Spinner,
  MessageBar,
  MessageBarBody,
  Caption1,
  Input,
  Switch,
  Dropdown,
  Option,
  Button,
  Tooltip,
} from "@fluentui/react-components";
import { SaveRegular, CheckmarkCircleRegular } from "@fluentui/react-icons";
import { getContext } from "@microsoft/power-apps/app";
import { EnergyUsageCharts } from "../components/EnergyUsageCharts";
import { getContactById, updateContact } from "../services/contactService";
import type { Contact } from "../types";

/* ── Choice field option maps ─────────────────────────────────── */

const BOILER_MAKE_OPTIONS: { value: number; label: string }[] = [
  { value: 124610000, label: "Worcester Bosch" },
  { value: 124610001, label: "Vaillant" },
  { value: 124610002, label: "Ideal" },
  { value: 124610003, label: "Baxi" },
  { value: 124610004, label: "Other/Unknown" },
];

const ENERGY_TARIFF_OPTIONS: { value: number; label: string }[] = [
  { value: 124610000, label: "Fixed" },
  { value: 124610001, label: "Variable" },
  { value: 124610002, label: "EV Tariff" },
  { value: 124610003, label: "Other" },
];

const HOMECARE_TYPE_OPTIONS: { value: number; label: string }[] = [
  { value: 124610000, label: "Boiler Only" },
  { value: 124610001, label: "Complete" },
  { value: 124610002, label: "Plumbing & Drain" },
  { value: 124610003, label: "Electrical" },
];

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    backgroundColor: tokens.colorNeutralBackground2,
    overflow: "hidden",
  },
  userBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    ...shorthands.padding("6px", "20px"),
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    columnGap: "12px",
    flexShrink: 0,
  },
  userBarLeft: {
    display: "flex",
    alignItems: "center",
    columnGap: "8px",
  },
  userBarRight: {
    display: "flex",
    alignItems: "center",
    columnGap: "6px",
  },
  versionBadge: {
    fontSize: "11px",
    color: tokens.colorNeutralForeground3,
    fontWeight: 500,
    backgroundColor: tokens.colorNeutralBackground3,
    padding: "2px 8px",
    borderRadius: "4px",
  },
  saveBtn: {
    minWidth: "80px",
  },
  savedMsg: {
    display: "flex",
    alignItems: "center",
    columnGap: "4px",
    fontSize: "12px",
    color: "#107c10",
    fontWeight: 500,
  },
  dirtyDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    backgroundColor: tokens.colorPaletteYellowBackground3,
    flexShrink: 0,
  },

  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
  },
  /* ── Contact details — compact top section ─────────────────── */
  contactSection: {
    flexShrink: 0,
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.padding("12px", "20px", "8px"),
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    boxShadow: tokens.shadow2,
  },
  detailsGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: "1px 20px",
  },
  detailItem: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    minHeight: "30px",
    fontSize: "12px",
  },
  detailLabel: {
    color: tokens.colorNeutralForeground3,
    minWidth: "70px",
    flexShrink: 0,
    fontSize: "12px",
  },
  detailValue: {
    color: tokens.colorNeutralForeground1,
    fontWeight: 500,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  conversationRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    minHeight: "30px",
    fontSize: "12px",
    gridColumn: "span 2",
  },
  /* ── Charts — capped height for D365 IFrame compatibility ──── */
  chartsSection: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.padding("8px", "16px", "8px"),
    /* Do NOT use flex:1 — D365 IFrames have no height constraint */
  },
  /* ── Inline editable field styles ──────────────────────────── */
  compactInput: {
    minWidth: 0,
    maxWidth: "160px",
    fontSize: "12px",
  },
  compactSwitch: {
    /* Override Fluent Switch padding for compact rows */
  },
  compactDropdown: {
    minWidth: "110px",
    maxWidth: "160px",
    fontSize: "12px",
  },
  conversationInput: {
    flex: 1,
    fontSize: "12px",
  },
});

/** App version — increment on each deployment. */
const APP_VERSION = "0.5.2";

/** Editable form state — only the mj_ fields we display. */
interface FormState {
  mj_boilermake: number | undefined;
  mj_boilermodel: string;
  mj_installationdate: string;
  mj_homecarecover: boolean;
  mj_homecaretypeofcover: number | undefined;
  mj_energytariff: number | undefined;
  mj_smartmeter: boolean;
  mj_doyouhaveahivethermostat: boolean;
  mj_doyouhavesmartradiatorvalves: boolean;
  mj_utility_ev_owner: boolean;
  mj_homeevcharger: boolean;
  mj_priorityregister: boolean;
  mj_repairedrecently: boolean;
  mj_conversationpoints: string;
}

function buildFormState(c: Contact): FormState {
  return {
    mj_boilermake: c.mj_boilermake ?? undefined,
    mj_boilermodel: c.mj_boilermodel ?? "",
    mj_installationdate: c.mj_installationdate ?? "",
    mj_homecarecover: c.mj_homecarecover ?? false,
    mj_homecaretypeofcover: c.mj_homecaretypeofcover ?? undefined,
    mj_energytariff: c.mj_energytariff ?? undefined,
    mj_smartmeter: c.mj_smartmeter ?? c.mj_doyouhaveasmartmeter ?? false,
    mj_doyouhaveahivethermostat: c.mj_doyouhaveahivethermostat ?? false,
    mj_doyouhavesmartradiatorvalves: c.mj_doyouhavesmartradiatorvalves ?? false,
    mj_utility_ev_owner: c.mj_utility_ev_owner ?? false,
    mj_homeevcharger: c.mj_homeevcharger ?? false,
    mj_priorityregister: c.mj_priorityregister ?? false,
    mj_repairedrecently: c.mj_repairedrecently ?? false,
    mj_conversationpoints: c.mj_conversationpoints ?? "",
  };
}

export function ContactDetailPage() {
  const styles = useStyles();
  const [contact, setContact] = useState<Contact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Debug info — shown on error/not-found screens
  const [debugInfo, setDebugInfo] = useState<Record<string, unknown>>({});

  // Editable form state
  const [form, setForm] = useState<FormState | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Snapshot of original state (to detect dirty)
  const [originalForm, setOriginalForm] = useState<FormState | null>(null);

  const isDirty = useMemo(() => {
    if (!form || !originalForm) return false;
    return JSON.stringify(form) !== JSON.stringify(originalForm);
  }, [form, originalForm]);

  const loadContact = useCallback(async () => {
    setLoading(true);
    setError(null);
    const debug: Record<string, unknown> = {
      timestamp: new Date().toISOString(),
      href: window.location.href,
      search: window.location.search,
      origin: window.location.origin,
      pathname: window.location.pathname,
      hash: window.location.hash,
      windowParams: Object.fromEntries(
        new URLSearchParams(window.location.search),
      ),
      isInIframe: window.self !== window.top,
    };
    try {
      // ── Step 1: Get query params via the Power Apps SDK context ──
      // The Power Apps host strips URL params from the inner iframe;
      // getContext().app.queryParams is the correct way to read them.
      let sdkQueryParams: Record<string, string> = {};
      let sdkUser = "(not available)";
      let sdkEnvId = "(not available)";
      let sdkAppId = "(not available)";
      try {
        const ctx = await getContext();
        sdkQueryParams = (ctx.app?.queryParams as Record<string, string>) ?? {};
        sdkUser =
          ctx.user?.fullName ?? ctx.user?.userPrincipalName ?? "(unknown)";
        sdkEnvId = ctx.app?.environmentId ?? "(unknown)";
        sdkAppId = ctx.app?.appId ?? "(unknown)";
        debug.sdkContext = {
          user: sdkUser,
          envId: sdkEnvId,
          appId: sdkAppId,
          queryParams: sdkQueryParams,
        };
      } catch (ctxErr) {
        debug.sdkContextError =
          ctxErr instanceof Error ? ctxErr.message : String(ctxErr);
      }

      // ── Step 2: Resolve contact ID from multiple sources ──
      // Priority: SDK queryParams > window.location.search > fallback
      const sdkId =
        sdkQueryParams["id"] ??
        sdkQueryParams["Id"] ??
        sdkQueryParams["ID"] ??
        null;
      const windowParams = new URLSearchParams(window.location.search);
      const windowId = windowParams.get("id");
      const rawId = sdkId ?? windowId;
      const idParam = rawId ? rawId.replace(/[{}]/g, "") : null;

      debug.sdkIdParam = sdkId;
      debug.windowIdParam = windowId;
      debug.resolvedRawId = rawId;
      debug.cleanedId = idParam;
      debug.usingFallback = !idParam;
      debug.fallbackId = "7fba73b9-2461-ef11-bfe2-002248a36d0e (Chris Walker)";
      debug.finalIdUsed = idParam ?? "7fba73b9-2461-ef11-bfe2-002248a36d0e";

      console.log("[ContactDetailPage] Debug:", JSON.stringify(debug, null, 2));

      // ── Step 3: Fetch the contact via the SDK ──
      const data = await getContactById(idParam ?? undefined);
      // Capture SDK debug info stored by contactService
      const sdkDebug = (window as unknown as Record<string, unknown>)
        .__sdkDebug;
      debug.sdkResultShape = sdkDebug ?? "(not captured)";
      debug.apiReturnedNull = data === null;
      debug.apiReturnedContactId = data?.contactid ?? null;
      debug.apiReturnedName = data?.fullname ?? null;
      setDebugInfo(debug);
      setContact(data);
      if (data) {
        const fs = buildFormState(data);
        setForm(fs);
        setOriginalForm(fs);
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      const errStack = err instanceof Error ? err.stack : undefined;
      debug.errorMessage = errMsg;
      debug.errorStack = errStack;
      debug.errorRaw = JSON.stringify(
        err,
        Object.getOwnPropertyNames(err ?? {}),
      );
      setDebugInfo(debug);
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadContact();
  }, [loadContact]);

  // ── Helpers to update individual fields ────────────────────────

  const setField = useCallback(
    <K extends keyof FormState>(key: K, value: FormState[K]) => {
      setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
      // Clear any previous save feedback
      setSaveSuccess(false);
      setSaveError(null);
    },
    [],
  );

  // ── Save handler ───────────────────────────────────────────────
  const [saveDebug, setSaveDebug] = useState<string | null>(null);

  const handleSave = useCallback(async () => {
    if (!contact || !form) {
      setSaveDebug("Save blocked: contact or form is null");
      return;
    }
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    setSaveDebug(null);

    const changesPayload = {
      mj_boilermake: form.mj_boilermake,
      mj_boilermodel: form.mj_boilermodel,
      mj_installationdate: form.mj_installationdate,
      mj_homecarecover: form.mj_homecarecover,
      mj_homecaretypeofcover: form.mj_homecaretypeofcover,
      mj_energytariff: form.mj_energytariff,
      mj_smartmeter: form.mj_smartmeter,
      mj_doyouhaveahivethermostat: form.mj_doyouhaveahivethermostat,
      mj_doyouhaveasmartmeter: form.mj_smartmeter,
      mj_doyouhavesmartradiatorvalves: form.mj_doyouhavesmartradiatorvalves,
      mj_utility_ev_owner: form.mj_utility_ev_owner,
      mj_homeevcharger: form.mj_homeevcharger,
      mj_priorityregister: form.mj_priorityregister,
      mj_repairedrecently: form.mj_repairedrecently,
      mj_conversationpoints: form.mj_conversationpoints,
    };

    try {
      setSaveDebug(
        `Saving to ${contact.contactid}...\nPayload: ${JSON.stringify(changesPayload, null, 2)}`,
      );
      await updateContact(contact.contactid, changesPayload);
      const sdkSaveDebug = (window as unknown as Record<string, unknown>)
        .__sdkSaveDebug;
      setOriginalForm({ ...form });
      setSaveSuccess(true);
      setSaveDebug(
        `SAVED OK at ${new Date().toISOString()}\nPayload: ${JSON.stringify(changesPayload, null, 2)}\nSDK: ${JSON.stringify(sdkSaveDebug, null, 2)}`,
      );
      setTimeout(() => setSaveSuccess(false), 5000);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : String(err);
      const sdkSaveDebug = (window as unknown as Record<string, unknown>)
        .__sdkSaveDebug;
      setSaveError(errMsg);
      setSaveDebug(
        `SAVE FAILED: ${errMsg}\nPayload: ${JSON.stringify(changesPayload, null, 2)}\nSDK: ${JSON.stringify(sdkSaveDebug, null, 2)}`,
      );
    } finally {
      setSaving(false);
    }
  }, [contact, form]);

  // ── Render ─────────────────────────────────────────────────────

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spinner size="large" label="Loading contact..." />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: 20, fontFamily: "Segoe UI, sans-serif" }}>
        <MessageBar intent="error">
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
        <div style={{ marginTop: 8, fontSize: 11, color: "#666" }}>
          App v{APP_VERSION}
        </div>
        <details open style={{ marginTop: 16, fontSize: 12 }}>
          <summary
            style={{ cursor: "pointer", fontWeight: 600, marginBottom: 8 }}
          >
            Debug Information
          </summary>
          <pre
            style={{
              background: "#f5f5f5",
              padding: 12,
              borderRadius: 4,
              overflow: "auto",
              maxHeight: 400,
            }}
          >
            {JSON.stringify(debugInfo, null, 2)}
          </pre>
        </details>
      </div>
    );
  }

  if (!contact || !form) {
    return (
      <div style={{ padding: 20, fontFamily: "Segoe UI, sans-serif" }}>
        <MessageBar intent="warning">
          <MessageBarBody>Contact not found.</MessageBarBody>
        </MessageBar>
        <div style={{ marginTop: 8, fontSize: 11, color: "#666" }}>
          App v{APP_VERSION}
        </div>
        <details open style={{ marginTop: 16, fontSize: 12 }}>
          <summary
            style={{ cursor: "pointer", fontWeight: 600, marginBottom: 8 }}
          >
            Debug Information — Why no contact loaded?
          </summary>
          <table
            style={{ borderCollapse: "collapse", width: "100%", fontSize: 12 }}
          >
            <tbody>
              {Object.entries(debugInfo).map(([key, val]) => (
                <tr key={key} style={{ borderBottom: "1px solid #e0e0e0" }}>
                  <td
                    style={{
                      padding: "4px 8px",
                      fontWeight: 600,
                      verticalAlign: "top",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {key}
                  </td>
                  <td style={{ padding: "4px 8px", wordBreak: "break-all" }}>
                    {typeof val === "object"
                      ? JSON.stringify(val, null, 2)
                      : String(val ?? "(empty)")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      </div>
    );
  }

  return (
    <div className={styles.root}>
      {/* ── Top bar — Save button (left) + User info (right) ──── */}
      <div className={styles.userBar}>
        <div className={styles.userBarLeft}>
          <Tooltip
            content={isDirty ? "Save changes" : "No unsaved changes"}
            relationship="description"
          >
            <Button
              className={styles.saveBtn}
              appearance="primary"
              icon={<SaveRegular />}
              size="small"
              disabled={!isDirty || saving}
              onClick={() => void handleSave()}
            >
              {saving ? "Saving…" : "Save"}
            </Button>
          </Tooltip>
          {isDirty && (
            <span className={styles.dirtyDot} title="Unsaved changes" />
          )}
          {saveSuccess && (
            <span className={styles.savedMsg}>
              <CheckmarkCircleRegular fontSize={14} /> Saved
            </span>
          )}
          {saveError && (
            <Caption1 style={{ color: "#a4262c" }}>{saveError}</Caption1>
          )}
        </div>
        <div className={styles.userBarRight}>
          <span className={styles.versionBadge}>v{APP_VERSION}</span>
        </div>
      </div>

      {/* ── Save debug panel (temporary) ──────────────────── */}
      {saveDebug && (
        <details
          open
          style={{
            margin: "0 20px",
            fontSize: 11,
            background: "#fffbe6",
            border: "1px solid #d4b106",
            borderRadius: 4,
            padding: 8,
          }}
        >
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>
            Save Debug (v{APP_VERSION})
          </summary>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              wordBreak: "break-all",
              maxHeight: 200,
              overflow: "auto",
            }}
          >
            {saveDebug}
          </pre>
        </details>
      )}

      {/* ── Editable contact fields — three-column grid ─────── */}
      <div className={styles.contactSection}>
        <div className={styles.detailsGrid}>
          {/* Column 1 — Boiler & Heating */}
          <ChoiceItem
            label="Boiler Make"
            value={form.mj_boilermake}
            options={BOILER_MAKE_OPTIONS}
            onChange={(v) => setField("mj_boilermake", v)}
          />
          <TextItem
            label="Boiler Model"
            value={form.mj_boilermodel}
            onChange={(v) => setField("mj_boilermodel", v)}
          />
          <DateItem
            label="Installation"
            value={form.mj_installationdate}
            onChange={(v) => setField("mj_installationdate", v)}
          />
          <BoolItem
            label="HomeCare"
            value={form.mj_homecarecover}
            onChange={(v) => setField("mj_homecarecover", v)}
          />
          <ChoiceItem
            label="Cover Type"
            value={form.mj_homecaretypeofcover}
            options={HOMECARE_TYPE_OPTIONS}
            onChange={(v) => setField("mj_homecaretypeofcover", v)}
          />

          {/* Column 2 — Energy & Smart Home */}
          <ChoiceItem
            label="Energy Tariff"
            value={form.mj_energytariff}
            options={ENERGY_TARIFF_OPTIONS}
            onChange={(v) => setField("mj_energytariff", v)}
          />
          <BoolItem
            label="Smart Meter"
            value={form.mj_smartmeter}
            onChange={(v) => setField("mj_smartmeter", v)}
          />
          <BoolItem
            label="Hive Thermostat"
            value={form.mj_doyouhaveahivethermostat}
            onChange={(v) => setField("mj_doyouhaveahivethermostat", v)}
          />
          <BoolItem
            label="Smart TRVs"
            value={form.mj_doyouhavesmartradiatorvalves}
            onChange={(v) => setField("mj_doyouhavesmartradiatorvalves", v)}
          />
          <BoolItem
            label="EV Owner"
            value={form.mj_utility_ev_owner}
            onChange={(v) => setField("mj_utility_ev_owner", v)}
          />

          {/* Column 3 — EV & Service */}
          <BoolItem
            label="EV Charger"
            value={form.mj_homeevcharger}
            onChange={(v) => setField("mj_homeevcharger", v)}
          />
          <BoolItem
            label="Priority Register"
            value={form.mj_priorityregister}
            onChange={(v) => setField("mj_priorityregister", v)}
          />
          <BoolItem
            label="Repaired Recently"
            value={form.mj_repairedrecently}
            onChange={(v) => setField("mj_repairedrecently", v)}
          />

          {/* Conversation Points — inline on same row as Repaired Recently */}
          <div className={styles.conversationRow}>
            <span className={styles.detailLabel}>Conversation Pts</span>
            <Input
              className={styles.conversationInput}
              size="small"
              value={form.mj_conversationpoints}
              onChange={(_e, data) =>
                setField("mj_conversationpoints", data.value)
              }
              placeholder="Enter conversation points…"
            />
          </div>
        </div>
      </div>

      {/* ── Energy usage charts — fills remaining viewport ───── */}
      <div className={styles.chartsSection}>
        <EnergyUsageCharts />
      </div>
    </div>
  );
}

/* ── Inline helper sub-components (editable) ──────────────────── */

/** Editable text field row */
function TextItem({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  const styles = useStyles();
  return (
    <div className={styles.detailItem}>
      <span className={styles.detailLabel}>{label}</span>
      <Input
        className={styles.compactInput}
        size="small"
        value={value}
        onChange={(_e, data) => onChange(data.value)}
        placeholder={placeholder ?? label}
      />
    </div>
  );
}

/**
 * Date field row — displays date in UK format (dd/MM/yyyy) and uses
 * an HTML date input for editing.  Stores/sends YYYY-MM-DD for Dataverse.
 */
function DateItem({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const styles = useStyles();

  // Format the raw ISO / YYYY-MM-DD value into UK locale display
  const formatForDisplay = (raw: string): string => {
    if (!raw) return "";
    // Strip trailing time component if present (e.g. "2022-03-15T00:00:00Z" → "2022-03-15")
    const dateOnly = raw.includes("T") ? raw.split("T")[0] : raw;
    const [y, m, d] = dateOnly.split("-").map(Number);
    if (!y || !m || !d) return raw;
    const dt = new Date(y, m - 1, d); // local date — no timezone shift
    return dt.toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    }); // e.g. "15 March 2022"
  };

  // The <input type="date"> needs YYYY-MM-DD as its value
  const isoValue = value?.includes("T") ? value.split("T")[0] : (value ?? "");

  const [editing, setEditing] = useState(false);

  if (editing) {
    return (
      <div className={styles.detailItem}>
        <span className={styles.detailLabel}>{label}</span>
        <input
          type="date"
          value={isoValue}
          onChange={(e) => onChange(e.target.value)}
          onBlur={() => setEditing(false)}
          autoFocus
          style={{ fontSize: "12px", padding: "2px 6px" }}
        />
      </div>
    );
  }

  return (
    <div
      className={styles.detailItem}
      onClick={() => setEditing(true)}
      style={{ cursor: "pointer" }}
    >
      <span className={styles.detailLabel}>{label}</span>
      <span style={{ fontSize: "12px" }}>
        {formatForDisplay(value) || (
          <span style={{ color: "#999" }}>Click to set date</span>
        )}
      </span>
    </div>
  );
}

/** Toggleable Yes / No boolean field row */
function BoolItem({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  const styles = useStyles();
  return (
    <div className={styles.detailItem}>
      <span className={styles.detailLabel}>{label}</span>
      <Switch
        className={styles.compactSwitch}
        checked={value}
        onChange={(_e, data) => onChange(data.checked)}
        label={value ? "Yes" : "No"}
        style={{ fontSize: "12px" }}
      />
    </div>
  );
}

/** Choice / Dropdown field row */
function ChoiceItem({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: number | undefined;
  options: { value: number; label: string }[];
  onChange: (v: number | undefined) => void;
}) {
  const styles = useStyles();
  const selected = options.find((o) => o.value === value);

  return (
    <div className={styles.detailItem}>
      <span className={styles.detailLabel}>{label}</span>
      <Dropdown
        className={styles.compactDropdown}
        size="small"
        value={selected?.label ?? ""}
        selectedOptions={selected ? [String(selected.value)] : []}
        onOptionSelect={(_e, data) => {
          const numVal = data.optionValue
            ? Number(data.optionValue)
            : undefined;
          onChange(numVal);
        }}
        placeholder={`Select ${label}`}
      >
        {options.map((opt) => (
          <Option key={opt.value} value={String(opt.value)}>
            {opt.label}
          </Option>
        ))}
      </Dropdown>
    </div>
  );
}
