export interface ODataResponse<T> {
  value: T[];
  "@odata.count"?: number;
}

export interface CaseRecord {
  incidentid: string;
  title: string;
  ticketnumber: string;
  createdon: string;
  modifiedon: string;
  statuscode: number;
  statecode: number;
  prioritycode: number;
  caseorigincode?: number;
  "statuscode@OData.Community.Display.V1.FormattedValue"?: string;
  "prioritycode@OData.Community.Display.V1.FormattedValue"?: string;
  "caseorigincode@OData.Community.Display.V1.FormattedValue"?: string;
  _customerid_value?: string;
  "_customerid_value@OData.Community.Display.V1.FormattedValue"?: string;
  _subjectid_value?: string;
  "_subjectid_value@OData.Community.Display.V1.FormattedValue"?: string;
}

export const CASE_STATUS_LABELS: Record<number, string> = {
  1: "In Progress",
  2: "On Hold",
  3: "Waiting for Details",
  4: "Researching",
  5: "Problem Solved",
  6: "Cancelled",
  1000: "Information Provided",
  2000: "Merged",
};

export const CASE_PRIORITY_LABELS: Record<number, string> = {
  1: "High",
  2: "Normal",
  3: "Low",
};

export const CASE_ORIGIN_LABELS: Record<number, string> = {
  1: "Phone",
  2: "Email",
  3: "Web",
  2483: "Facebook",
  3986: "Twitter",
  700610000: "IoT",
};
