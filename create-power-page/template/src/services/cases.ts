import { getRecords } from "./api";
import type { CaseRecord, ODataResponse } from "../types";

const ENTITY_SET = "incidents";

const DEFAULT_SELECT = [
  "incidentid",
  "title",
  "ticketnumber",
  "createdon",
  "modifiedon",
  "statuscode",
  "statecode",
  "prioritycode",
  "caseorigincode",
  "_customerid_value",
  "_subjectid_value",
].join(",");

export interface CaseQueryOptions {
  filter?: string;
  top?: number;
}

function buildParams(opts: CaseQueryOptions = {}): Record<string, string> {
  const params: Record<string, string> = {
    $select: DEFAULT_SELECT,
    $orderby: "createdon desc",
    $top: String(opts.top ?? 50),
  };
  if (opts.filter) params.$filter = opts.filter;
  return params;
}

export async function getMyCases(
  contactId: string,
  opts: CaseQueryOptions = {},
): Promise<ODataResponse<CaseRecord>> {
  const contactFilter = `_customerid_value eq ${contactId}`;
  const combined = opts.filter
    ? `(${contactFilter}) and (${opts.filter})`
    : contactFilter;
  return getRecords<CaseRecord>(
    ENTITY_SET,
    buildParams({ ...opts, filter: combined }),
  );
}
