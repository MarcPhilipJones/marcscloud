/**
 * ContactListPage — Lists contacts from Dataverse in a table.
 */

import { useEffect, useState } from "react";
import {
  makeStyles,
  tokens,
  shorthands,
  Spinner,
  MessageBar,
  MessageBarBody,
  Title3,
  Body1,
  Button,
  Input,
} from "@fluentui/react-components";
import { SearchRegular, ArrowSyncRegular } from "@fluentui/react-icons";
import { useNavigate } from "react-router-dom";
import { getAllContacts } from "../services/contactService";
import type { Contact } from "../types";

const useStyles = makeStyles({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    backgroundColor: tokens.colorNeutralBackground2,
    ...shorthands.padding("20px"),
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
  },
  toolbar: {
    display: "flex",
    alignItems: "center",
    columnGap: "8px",
    marginBottom: "16px",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse" as const,
  },
  th: {
    textAlign: "left" as const,
    fontSize: "12px",
    fontWeight: 600,
    color: tokens.colorNeutralForeground3,
    ...shorthands.padding("8px", "12px"),
    borderBottom: `2px solid ${tokens.colorNeutralStroke1}`,
  },
  td: {
    fontSize: "13px",
    ...shorthands.padding("10px", "12px"),
    borderBottom: `1px solid ${tokens.colorNeutralStroke2}`,
    cursor: "pointer",
  },
  row: {
    ":hover": {
      backgroundColor: tokens.colorNeutralBackground1Hover,
    },
  },
  loading: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    height: "100%",
  },
  empty: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.padding("40px"),
    color: tokens.colorNeutralForeground3,
  },
});

export function ContactListPage() {
  const styles = useStyles();
  const navigate = useNavigate();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllContacts(
        search ? { filter: `contains(fullname,'${search}')` } : undefined,
      );
      setContacts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load contacts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className={styles.loading}>
        <Spinner size="large" label="Loading contacts..." />
      </div>
    );
  }

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <Title3>Active Contacts</Title3>
        <Button
          icon={<ArrowSyncRegular />}
          appearance="subtle"
          onClick={() => void load()}
        >
          Refresh
        </Button>
      </div>

      <div className={styles.toolbar}>
        <Input
          placeholder="Search contacts..."
          contentBefore={<SearchRegular />}
          size="small"
          value={search}
          onChange={(_e, data) => setSearch(data.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") void load();
          }}
          style={{ minWidth: "280px" }}
        />
        <Button size="small" appearance="primary" onClick={() => void load()}>
          Search
        </Button>
      </div>

      {error && (
        <MessageBar intent="error" style={{ marginBottom: 12 }}>
          <MessageBarBody>{error}</MessageBarBody>
        </MessageBar>
      )}

      {contacts.length === 0 ? (
        <div className={styles.empty}>
          <Body1>No contacts found.</Body1>
        </div>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.th}>Full Name</th>
              <th className={styles.th}>Email</th>
              <th className={styles.th}>Phone</th>
              <th className={styles.th}>Company</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((c) => (
              <tr
                key={c.contactid}
                className={styles.row}
                onClick={() =>
                  navigate(`/contacts/${c.contactid}?id=${c.contactid}`)
                }
              >
                <td className={styles.td}>{c.fullname}</td>
                <td className={styles.td}>{c.emailaddress1}</td>
                <td className={styles.td}>{c.telephone1}</td>
                <td className={styles.td}>{c.companyname}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
