/**
 * ContactHeader — Top header bar matching D365 form header.
 *
 * Shows: contact avatar+name, form type, quick info (job title, phone, email),
 * owner/status, and a command bar with action buttons.
 */

import {
  Avatar,
  Badge,
  Body1,
  Body1Strong,
  Caption1,
  makeStyles,
  shorthands,
  tokens,
  Toolbar,
  ToolbarButton,
  Divider,
} from "@fluentui/react-components";
import {
  SaveRegular,
  ArrowLeftRegular,
  DeleteRegular,
  ArrowSyncRegular,
  PersonRegular,
} from "@fluentui/react-icons";
import type { Contact } from "../types";

const useStyles = makeStyles({
  root: {
    backgroundColor: tokens.colorNeutralBackground1,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
  },
  commandBar: {
    display: "flex",
    alignItems: "center",
    ...shorthands.padding("4px", "16px"),
    backgroundColor: tokens.colorNeutralBackground3,
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    minHeight: "40px",
  },
  headerMain: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    ...shorthands.padding("12px", "20px"),
    minHeight: "56px",
  },
  identity: {
    display: "flex",
    alignItems: "center",
    columnGap: "12px",
  },
  nameBlock: {
    display: "flex",
    flexDirection: "column",
  },
  contactName: {
    fontSize: "18px",
    fontWeight: 600,
    color: tokens.colorNeutralForeground1,
    lineHeight: "24px",
  },
  formType: {
    fontSize: "12px",
    color: tokens.colorNeutralForeground3,
    lineHeight: "16px",
  },
  quickInfo: {
    display: "flex",
    alignItems: "center",
    columnGap: "24px",
  },
  quickInfoItem: {
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
  },
  quickInfoLabel: {
    color: tokens.colorNeutralForeground3,
    fontSize: "11px",
    lineHeight: "14px",
  },
  quickInfoValue: {
    color: tokens.colorNeutralForeground1,
    fontSize: "13px",
    lineHeight: "18px",
  },
  owner: {
    display: "flex",
    alignItems: "center",
    columnGap: "8px",
    ...shorthands.padding("4px", "8px"),
    ...shorthands.borderRadius("4px"),
    backgroundColor: tokens.colorNeutralBackground3,
  },
  tabBar: {
    display: "flex",
    alignItems: "center",
    ...shorthands.padding("0", "20px"),
    columnGap: "0",
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    backgroundColor: tokens.colorNeutralBackground1,
  },
  tab: {
    ...shorthands.padding("10px", "16px"),
    fontSize: "13px",
    color: tokens.colorNeutralForeground2,
    cursor: "pointer",
    borderBottom: "2px solid transparent",
    transition: "all 0.15s ease",
    ":hover": {
      color: tokens.colorNeutralForeground1,
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
  tabActive: {
    ...shorthands.padding("10px", "16px"),
    fontSize: "13px",
    fontWeight: 600,
    color: tokens.colorBrandForeground1,
    cursor: "pointer",
    borderBottom: `2px solid ${tokens.colorBrandStroke1}`,
  },
  statusBadge: {
    marginLeft: "8px",
  },
});

interface ContactHeaderProps {
  contact: Contact;
}

export function ContactHeader({ contact }: ContactHeaderProps) {
  const styles = useStyles();

  const initials =
    `${contact.firstname?.[0] ?? ""}${contact.lastname?.[0] ?? ""}`.toUpperCase();
  const statusText = contact.statecode === 0 ? "Active" : "Inactive";

  return (
    <div className={styles.root}>
      {/* Command Bar */}
      <div className={styles.commandBar}>
        <Toolbar size="small">
          <ToolbarButton icon={<ArrowLeftRegular />} appearance="subtle">
            Back
          </ToolbarButton>
          <ToolbarButton icon={<SaveRegular />} appearance="subtle">
            Save
          </ToolbarButton>
          <ToolbarButton icon={<ArrowSyncRegular />} appearance="subtle">
            Refresh
          </ToolbarButton>
          <ToolbarButton icon={<DeleteRegular />} appearance="subtle">
            Delete
          </ToolbarButton>
        </Toolbar>
      </div>

      {/* Header Main */}
      <div className={styles.headerMain}>
        <div className={styles.identity}>
          <Avatar
            name={
              contact.fullname ?? `${contact.firstname} ${contact.lastname}`
            }
            initials={initials}
            size={40}
            color="brand"
            icon={<PersonRegular />}
          />
          <div className={styles.nameBlock}>
            <span className={styles.contactName}>
              {contact.fullname ?? `${contact.firstname} ${contact.lastname}`} -
              Saved
              <Badge
                className={styles.statusBadge}
                appearance="tint"
                color={contact.statecode === 0 ? "success" : "danger"}
                size="small"
              >
                {statusText}
              </Badge>
            </span>
            <span className={styles.formType}>
              Contact &nbsp;›&nbsp; Contact for Utilities (Interactive)
            </span>
          </div>
        </div>

        <div className={styles.quickInfo}>
          <div className={styles.quickInfoItem}>
            <Caption1 className={styles.quickInfoLabel}>Job Title</Caption1>
            <Body1 className={styles.quickInfoValue}>
              {contact.jobtitle ?? "—"}
            </Body1>
          </div>
          <div className={styles.quickInfoItem}>
            <Caption1 className={styles.quickInfoLabel}>
              Business Phone
            </Caption1>
            <Body1 className={styles.quickInfoValue}>
              {contact.telephone1 ?? "—"}
            </Body1>
          </div>
          <div className={styles.quickInfoItem}>
            <Caption1 className={styles.quickInfoLabel}>Email</Caption1>
            <Body1 className={styles.quickInfoValue}>
              {contact.emailaddress1 ?? "—"}
            </Body1>
          </div>
          <Divider vertical style={{ height: "36px" }} />
          <div className={styles.owner}>
            <Avatar name="Marc Jones" size={24} />
            <div>
              <Caption1 className={styles.quickInfoLabel}>Owner</Caption1>
              <Body1Strong style={{ fontSize: "12px", display: "block" }}>
                Marc Jones
              </Body1Strong>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <div className={styles.tabBar}>
        <div className={styles.tabActive}>Summary</div>
        <div className={styles.tab}>Details</div>
        <div className={styles.tab}>Contact 360</div>
        <div className={styles.tab}>App</div>
        <div className={styles.tab}>Related</div>
      </div>
    </div>
  );
}
