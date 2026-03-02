/**
 * Contact type definition — mirrors the Dataverse contact entity.
 *
 * After running `pac code add-data-source -a dataverse -t contact`,
 * the SDK generates `ContactsModel.ts` in `src/generated/models/`.
 * This local type mirrors the generated model so the app compiles
 * before code-generation has run. Once the generated model exists,
 * you can switch imports to `'../generated/models/ContactsModel'`.
 */

export interface Contact {
  /** Primary key — GUID */
  contactid: string;

  // ── Core identity ─────────────────────────────────────────────
  firstname?: string;
  lastname?: string;
  fullname?: string;
  jobtitle?: string;
  department?: string;
  birthdate?: string;
  gendercode?: number;
  familystatuscode?: number;

  // ── Contact details ───────────────────────────────────────────
  emailaddress1?: string;
  emailaddress2?: string;
  telephone1?: string; // Business Phone
  telephone2?: string; // Home Phone
  mobilephone?: string;
  fax?: string;
  websiteurl?: string;
  preferredcontactmethodcode?: number; // 1=Any, 2=Email, 3=Phone, 4=Fax, 5=Mail

  // ── Primary address ───────────────────────────────────────────
  address1_line1?: string;
  address1_line2?: string;
  address1_line3?: string;
  address1_city?: string;
  address1_stateorprovince?: string;
  address1_postalcode?: string;
  address1_country?: string;

  // ── Secondary address ─────────────────────────────────────────
  address2_line1?: string;
  address2_line2?: string;
  address2_city?: string;
  address2_stateorprovince?: string;
  address2_postalcode?: string;
  address2_country?: string;

  // ── Company / parent customer ─────────────────────────────────
  _parentcustomerid_value?: string;
  /** OData formatted display name for parentcustomerid */
  "_parentcustomerid_value@OData.Community.Display.V1.FormattedValue"?: string;
  companyname?: string;

  // ── Custom mj_ energy/utility fields ──────────────────────────
  mj_analysislastrun?: string;
  mj_boilermake?: number; // Choice: Worcester Bosch (124610000), Vaillant (124610001), Ideal (124610002), Baxi (124610003), Other/Unknown (124610004)
  "mj_boilermake@OData.Community.Display.V1.FormattedValue"?: string;
  mj_boilermodel?: string;
  mj_conversationlogic?: string;
  mj_conversationpoints?: string;
  mj_doyouhaveahivethermostat?: boolean;
  mj_doyouhaveasmartmeter?: boolean;
  mj_doyouhavesmartradiatorvalves?: boolean;
  mj_energytariff?: number; // Choice: Fixed (124610000), Variable (124610001), EV Tariff (124610002), Other (124610003)
  "mj_energytariff@OData.Community.Display.V1.FormattedValue"?: string;
  mj_homecarecover?: boolean;
  mj_homecaretypeofcover?: number; // Choice: Boiler Only (124610000), Complete (124610001), Plumbing & Drain (124610002), Electrical (124610003)
  "mj_homecaretypeofcover@OData.Community.Display.V1.FormattedValue"?: string;
  mj_homeevcharger?: boolean;
  mj_initiateoutboundcall?: boolean;
  mj_installationdate?: string; // DATE ONLY
  mj_primarystore?: string; // Lookup GUID
  "mj_primarystore@OData.Community.Display.V1.FormattedValue"?: string;
  mj_priorityregister?: boolean;
  mj_refreshanalysis?: boolean;
  mj_repairedrecently?: boolean;
  mj_smartmeter?: boolean;
  mj_utility_ev_owner?: boolean;

  // ── Legacy aliases (kept for backward compat) ─────────────────
  /** @deprecated Use mj_priorityregister */
  msdyn_priorityregister?: boolean;
  /** @deprecated Use mj_smartmeter */
  msdyn_smartmeter?: boolean;

  // ── Management / assistant ────────────────────────────────────
  managername?: string;
  assistantname?: string;
  assistantphone?: string;

  // ── Communication preferences ─────────────────────────────────
  donotemail?: boolean;
  donotphone?: boolean;
  donotfax?: boolean;
  donotpostalmail?: boolean;
  donotbulkemail?: boolean;

  // ── Status ────────────────────────────────────────────────────
  statecode?: number;
  statuscode?: number;

  // ── System timestamps ─────────────────────────────────────────
  createdon?: string;
  modifiedon?: string;

  // ── Owner ─────────────────────────────────────────────────────
  _ownerid_value?: string;
  "_ownerid_value@OData.Community.Display.V1.FormattedValue"?: string;
}

/**
 * Preferred contact method lookup.
 */
export const CONTACT_METHOD_LABELS: Record<number, string> = {
  1: "Any",
  2: "Email",
  3: "Phone",
  4: "Fax",
  5: "Mail",
};

/**
 * Payload for creating/updating a contact.
 * Excludes read-only system fields.
 */
export type ContactFormData = Omit<
  Contact,
  | "contactid"
  | "fullname"
  | "createdon"
  | "modifiedon"
  | "_parentcustomerid_value"
  | '"_parentcustomerid_value@OData.Community.Display.V1.FormattedValue"'
  | "_ownerid_value"
  | '"_ownerid_value@OData.Community.Display.V1.FormattedValue"'
  | "statecode"
  | "statuscode"
>;
