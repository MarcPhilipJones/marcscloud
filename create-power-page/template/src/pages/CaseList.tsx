import { useEffect, useState, useCallback } from "react";
import { getMyCases } from "../services/cases";
import type { CaseRecord } from "../types";
import {
  CASE_STATUS_LABELS,
  CASE_PRIORITY_LABELS,
  CASE_ORIGIN_LABELS,
} from "../types";

function displayValue(
  record: CaseRecord,
  field: string,
  map: Record<number, string>,
): string {
  const annotation =
    record[
      `${field}@OData.Community.Display.V1.FormattedValue` as keyof CaseRecord
    ];
  if (typeof annotation === "string") return annotation;
  const raw = record[field as keyof CaseRecord];
  if (typeof raw === "number" && map[raw]) return map[raw];
  return "—";
}

function statusBadgeClass(statecode: number): string {
  if (statecode === 2) return "badge cancelled";
  if (statecode === 1) return "badge resolved";
  return "badge active";
}

function priorityBadgeClass(prioritycode: number): string {
  if (prioritycode === 1) return "badge high";
  if (prioritycode === 3) return "badge low";
  return "badge normal";
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function getContactId(): string {
  if (import.meta.env.DEV) return "00000000-0000-0000-0000-000000000000";
  const portal = (window as unknown as Record<string, unknown>)["Microsoft"] as
    | { Dynamic365?: { Portal?: { User?: Record<string, string> } } }
    | undefined;
  return portal?.Dynamic365?.Portal?.User?.contactId ?? "";
}

export default function CaseList() {
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState<string | null>(null);

  const loadCases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const contactId = getContactId();
      if (!contactId) {
        setError("Please sign in to view your cases.");
        setLoading(false);
        return;
      }
      let filter: string | undefined;
      if (statusFilter === "active") filter = "statecode eq 0";
      else if (statusFilter === "resolved") filter = "statecode eq 1";
      else if (statusFilter === "cancelled") filter = "statecode eq 2";

      const result = await getMyCases(contactId, { filter });
      setCases(result.value);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cases");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadCases();
  }, [loadCases]);

  const filtered = cases.filter((c) => {
    if (!searchTerm) return true;
    const q = searchTerm.toLowerCase();
    return (
      c.title?.toLowerCase().includes(q) ||
      c.ticketnumber?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="page">
      {import.meta.env.DEV && (
        <div className="alert alert-warning">
          Dev mode — showing mock data. Deploy to Power Pages for live cases.
        </div>
      )}

      <div className="page-header">
        <h1>My Cases</h1>
        <p>Support cases linked to your account</p>
      </div>

      <div className="case-toolbar">
        <div className="search-bar">
          <input
            type="text"
            className="form-input"
            placeholder="Search by title or ticket number…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="case-status-filters">
          {[
            { label: "All", value: null },
            { label: "Active", value: "active" },
            { label: "Resolved", value: "resolved" },
            { label: "Cancelled", value: "cancelled" },
          ].map((f) => (
            <button
              key={f.label}
              className={`btn btn-ghost ${statusFilter === f.value ? "active-filter" : ""}`}
              onClick={() => setStatusFilter(f.value)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="spinner" />}

      {error && <div className="alert alert-error">{error}</div>}

      {!loading && !error && filtered.length === 0 && (
        <div className="empty-state">
          <h3>No cases found</h3>
          <p>
            {searchTerm ? "Try adjusting your search" : "You have no cases yet"}
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="card table-card">
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ticket #</th>
                  <th>Title</th>
                  <th>Status</th>
                  <th>Priority</th>
                  <th>Origin</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c) => (
                  <tr key={c.incidentid}>
                    <td className="ticket-number">{c.ticketnumber}</td>
                    <td>{c.title}</td>
                    <td>
                      <span className={statusBadgeClass(c.statecode)}>
                        {displayValue(c, "statuscode", CASE_STATUS_LABELS)}
                      </span>
                    </td>
                    <td>
                      <span className={priorityBadgeClass(c.prioritycode)}>
                        {displayValue(c, "prioritycode", CASE_PRIORITY_LABELS)}
                      </span>
                    </td>
                    <td>
                      {displayValue(c, "caseorigincode", CASE_ORIGIN_LABELS)}
                    </td>
                    <td>{formatDate(c.createdon)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="case-count">
            Showing {filtered.length} of {cases.length} case
            {cases.length !== 1 ? "s" : ""}
          </div>
        </div>
      )}
    </div>
  );
}
