/**
 * FieldRow — A single D365-style field row with emoji label + value.
 *
 * Renders: [emoji] Label Name ────── value
 * Matches the Dynamics 365 form field layout.
 */

import {
  makeStyles,
  tokens,
  shorthands,
  Switch,
  Input,
  Dropdown,
  Option,
} from "@fluentui/react-components";

const useStyles = makeStyles({
  row: {
    display: "flex",
    alignItems: "center",
    minHeight: "36px",
    ...shorthands.padding("2px", "0"),
    borderBottom: `1px solid ${tokens.colorNeutralStroke3}`,
    ":hover": {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
  labelCell: {
    display: "flex",
    alignItems: "center",
    width: "180px",
    minWidth: "180px",
    flexShrink: 0,
    columnGap: "6px",
    ...shorthands.padding("4px", "8px"),
  },
  emoji: {
    fontSize: "14px",
    lineHeight: "1",
    width: "18px",
    textAlign: "center" as const,
    flexShrink: 0,
  },
  label: {
    fontSize: "12px",
    color: tokens.colorNeutralForeground3,
    fontWeight: 400,
    lineHeight: "16px",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  requiredDot: {
    color: "#d13438",
    marginLeft: "2px",
    fontWeight: 700,
    fontSize: "14px",
  },
  valueCell: {
    flex: 1,
    ...shorthands.padding("4px", "8px"),
    fontSize: "13px",
    color: tokens.colorNeutralForeground1,
    lineHeight: "18px",
    minWidth: 0,
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  emptyValue: {
    color: tokens.colorNeutralForeground4,
  },
  linkValue: {
    color: tokens.colorBrandForegroundLink,
    cursor: "pointer",
    ":hover": {
      textDecoration: "underline",
    },
  },
  lookupValue: {
    display: "inline-flex",
    alignItems: "center",
    columnGap: "4px",
    backgroundColor: tokens.colorNeutralBackground3,
    ...shorthands.padding("2px", "8px"),
    ...shorthands.borderRadius("4px"),
    fontSize: "13px",
    color: tokens.colorBrandForegroundLink,
    cursor: "pointer",
  },
  lookupClose: {
    fontSize: "11px",
    color: tokens.colorNeutralForeground3,
    cursor: "pointer",
    marginLeft: "4px",
    ":hover": {
      color: tokens.colorNeutralForeground1,
    },
  },
  lookupSearch: {
    fontSize: "12px",
    color: tokens.colorNeutralForeground3,
    cursor: "pointer",
    marginLeft: "4px",
  },
});

// ── Text field ───────────────────────────────────────────────────

interface FieldRowProps {
  emoji: string;
  label: string;
  value?: string | null;
  required?: boolean;
  isLink?: boolean;
  linkHref?: string;
}

export function FieldRow({
  emoji,
  label,
  value,
  required,
  isLink,
  linkHref,
}: FieldRowProps) {
  const styles = useStyles();
  const display = value?.trim() || "---";
  const isEmpty = !value?.trim();

  return (
    <div className={styles.row}>
      <div className={styles.labelCell}>
        <span className={styles.emoji}>{emoji}</span>
        <span className={styles.label}>
          {label}
          {required && <span className={styles.requiredDot}>*</span>}
        </span>
      </div>
      <div
        className={`${styles.valueCell} ${isEmpty ? styles.emptyValue : ""} ${isLink && !isEmpty ? styles.linkValue : ""}`}
        onClick={
          isLink && linkHref ? () => window.open(linkHref, "_blank") : undefined
        }
      >
        {display}
      </div>
    </div>
  );
}

// ── Toggle (Switch) field ────────────────────────────────────────

interface ToggleFieldRowProps {
  emoji: string;
  label: string;
  checked?: boolean;
}

export function ToggleFieldRow({ emoji, label, checked }: ToggleFieldRowProps) {
  const styles = useStyles();

  return (
    <div className={styles.row}>
      <div className={styles.labelCell}>
        <span className={styles.emoji}>{emoji}</span>
        <span className={styles.label}>{label}</span>
      </div>
      <div className={styles.valueCell}>
        <Switch
          checked={checked ?? false}
          label={checked ? "Yes" : "No"}
          disabled
          style={{ opacity: 1 }}
        />
      </div>
    </div>
  );
}

// ── Lookup field (Account Name style) ────────────────────────────

interface LookupFieldRowProps {
  emoji: string;
  label: string;
  displayName?: string | null;
}

export function LookupFieldRow({
  emoji,
  label,
  displayName,
}: LookupFieldRowProps) {
  const styles = useStyles();

  if (!displayName?.trim()) {
    return (
      <div className={styles.row}>
        <div className={styles.labelCell}>
          <span className={styles.emoji}>{emoji}</span>
          <span className={styles.label}>{label}</span>
        </div>
        <div className={`${styles.valueCell} ${styles.emptyValue}`}>---</div>
      </div>
    );
  }

  return (
    <div className={styles.row}>
      <div className={styles.labelCell}>
        <span className={styles.emoji}>{emoji}</span>
        <span className={styles.label}>{label}</span>
      </div>
      <div className={styles.valueCell}>
        <span className={styles.lookupValue}>
          🔗 {displayName}
          <span className={styles.lookupClose}>✕</span>
          <span className={styles.lookupSearch}>🔍</span>
        </span>
      </div>
    </div>
  );
}

// ── Dropdown field (read-only display) ───────────────────────────

interface DropdownFieldRowProps {
  emoji: string;
  label: string;
  value?: string | null;
  options?: string[];
}

export function DropdownFieldRow({
  emoji,
  label,
  value,
  options,
}: DropdownFieldRowProps) {
  const styles = useStyles();
  const _opts = options ?? [];

  return (
    <div className={styles.row}>
      <div className={styles.labelCell}>
        <span className={styles.emoji}>{emoji}</span>
        <span className={styles.label}>{label}</span>
      </div>
      <div className={styles.valueCell}>
        {_opts.length > 0 ? (
          <Dropdown
            value={value ?? ""}
            selectedOptions={value ? [value] : []}
            disabled
            style={{ minWidth: "120px", opacity: 1 }}
            size="small"
          >
            {_opts.map((opt) => (
              <Option key={opt} value={opt}>
                {opt}
              </Option>
            ))}
          </Dropdown>
        ) : (
          <span className={!value ? styles.emptyValue : ""}>
            {value ?? "---"}
          </span>
        )}
      </div>
    </div>
  );
}

// ── Input field (read-only display matching D365 editable look) ──

interface InputFieldRowProps {
  emoji: string;
  label: string;
  value?: string | null;
  required?: boolean;
  type?: "text" | "email" | "tel";
  suffix?: React.ReactNode;
}

export function InputFieldRow({
  emoji,
  label,
  value,
  required,
  type,
  suffix,
}: InputFieldRowProps) {
  const styles = useStyles();

  return (
    <div className={styles.row}>
      <div className={styles.labelCell}>
        <span className={styles.emoji}>{emoji}</span>
        <span className={styles.label}>
          {label}
          {required && <span className={styles.requiredDot}>*</span>}
        </span>
      </div>
      <div className={styles.valueCell}>
        <Input
          value={value ?? ""}
          type={type ?? "text"}
          disabled
          style={{ opacity: 1, minWidth: "120px" }}
          size="small"
          contentAfter={suffix ? <span>{suffix}</span> : undefined}
        />
      </div>
    </div>
  );
}
