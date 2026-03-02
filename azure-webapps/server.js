require("dotenv").config();
const express = require("express");
const os = require("os");
const { DataverseClient } = require("./dataverse-client");

const app = express();
const PORT = process.env.PORT || 3000;

// ---------------------------------------------------------------------------
// Dataverse client (lazy – only created when ContactDemo is hit)
// ---------------------------------------------------------------------------
let dvClient = null;
function getDataverseClient() {
  if (!dvClient) {
    const {
      DATAVERSE_BASE_URL,
      DATAVERSE_TENANT_ID,
      DATAVERSE_CLIENT_ID,
      DATAVERSE_CLIENT_SECRET,
    } = process.env;
    if (
      !DATAVERSE_BASE_URL ||
      !DATAVERSE_TENANT_ID ||
      !DATAVERSE_CLIENT_ID ||
      !DATAVERSE_CLIENT_SECRET
    ) {
      throw new Error("Missing Dataverse env vars — check .env file");
    }
    dvClient = new DataverseClient({
      baseUrl: DATAVERSE_BASE_URL,
      tenantId: DATAVERSE_TENANT_ID,
      clientId: DATAVERSE_CLIENT_ID,
      clientSecret: DATAVERSE_CLIENT_SECRET,
    });
  }
  return dvClient;
}

// ---------------------------------------------------------------------------
// Shared HTML helpers
// ---------------------------------------------------------------------------

function pageShell(title, bgColour, accentColour, bodyContent) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} — Azure Web Apps</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: ${bgColour};
      display: flex; justify-content: center; align-items: center;
      min-height: 100vh; padding: 24px;
      color: #1e1e1e;
    }
    .card {
      background: #fff; border-radius: 12px;
      box-shadow: 0 4px 24px rgba(0,0,0,.12);
      max-width: 560px; width: 100%; padding: 40px 36px;
    }
    h1 { font-size: 1.8rem; margin-bottom: 8px; color: ${accentColour}; }
    h2 { font-size: 1.1rem; margin: 24px 0 12px; color: #444; }
    p, li { line-height: 1.6; }
    .meta { font-size: .85rem; color: #666; margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; }
    td { padding: 6px 10px; border-bottom: 1px solid #eee; font-size: .9rem; }
    td:first-child { font-weight: 600; width: 45%; color: #555; }
    a { color: ${accentColour}; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .links { margin-top: 24px; display: flex; gap: 12px; flex-wrap: wrap; }
    .links a {
      display: inline-block; padding: 8px 18px;
      border: 2px solid ${accentColour}; border-radius: 6px;
      font-weight: 600; transition: .15s;
    }
    .links a:hover { background: ${accentColour}; color: #fff; text-decoration: none; }
  </style>
</head>
<body>
  <div class="card">
    ${bodyContent}
  </div>
</body>
</html>`;
}

function nodeInfoTable() {
  return `
    <h2>Node.js Runtime Info</h2>
    <table>
      <tr><td>Node.js Version</td><td>${process.version}</td></tr>
      <tr><td>Process Uptime</td><td>${Math.round(process.uptime())} s</td></tr>
      <tr><td>Server Timestamp</td><td>${new Date().toISOString()}</td></tr>
      <tr><td>Hostname</td><td>${os.hostname()}</td></tr>
    </table>`;
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

// Landing page
app.get("/", (_req, res) => {
  const html = pageShell(
    "Home",
    "#f0f4f8",
    "#0078d4",
    `
    <h1>Azure Web Apps Demo</h1>
    <p class="meta">A minimal multi-customer Node.js application</p>
    <p>Select a customer portal below:</p>
    <div class="links">
      <a href="/CustomerA">Customer A</a>
      <a href="/CustomerB">Customer B</a>
      <a href="/ContactDemo">Contact Demo</a>
    </div>
    ${nodeInfoTable()}
  `,
  );
  res.send(html);
});

// Customer A — teal / green theme
app.get("/CustomerA", (_req, res) => {
  const html = pageShell(
    "Customer A",
    "#e0f2f1",
    "#00796b",
    `
    <h1>Customer A Portal</h1>
    <p class="meta">Welcome to the Customer A experience</p>
    <p>This page is served with a <strong>teal</strong> background to distinguish it from Customer B.</p>
    ${nodeInfoTable()}
    <div class="links">
      <a href="/">Home</a>
      <a href="/CustomerB">Customer B</a>
    </div>
  `,
  );
  res.send(html);
});

// Customer B — warm amber / orange theme
app.get("/CustomerB", (_req, res) => {
  const html = pageShell(
    "Customer B",
    "#fff3e0",
    "#e65100",
    `
    <h1>Customer B Portal</h1>
    <p class="meta">Welcome to the Customer B experience</p>
    <p>This page is served with an <strong>amber</strong> background to distinguish it from Customer A.</p>
    ${nodeInfoTable()}
    <div class="links">
      <a href="/">Home</a>
      <a href="/CustomerA">Customer A</a>
    </div>
  `,
  );
  res.send(html);
});

// Health endpoint (JSON)
app.get("/health", (_req, res) => {
  res.json({ status: "ok", node: process.version });
});

// ---------------------------------------------------------------------------
// ContactDemo – API endpoint (fetches contact from Dataverse)
// ---------------------------------------------------------------------------
const CONTACT_SELECT = [
  // Identity
  "fullname",
  "firstname",
  "middlename",
  "lastname",
  "salutation",
  "suffix",
  "nickname",
  "jobtitle",
  "department",
  // Contact info
  "emailaddress1",
  "emailaddress2",
  "emailaddress3",
  "telephone1",
  "telephone2",
  "mobilephone",
  "fax",
  "websiteurl",
  // Address 1
  "address1_line1",
  "address1_line2",
  "address1_line3",
  "address1_city",
  "address1_stateorprovince",
  "address1_postalcode",
  "address1_country",
  "address1_telephone1",
  // Address 2
  "address2_line1",
  "address2_line2",
  "address2_line3",
  "address2_city",
  "address2_stateorprovince",
  "address2_postalcode",
  "address2_country",
  // Personal
  "birthdate",
  "anniversary",
  "gendercode",
  "familystatuscode",
  "numberofchildren",
  "spousesname",
  // Company / org (parentcustomerid is polymorphic – returned automatically as _parentcustomerid_value)
  "managername",
  "managerphone",
  "assistantname",
  "assistantphone",
  // Communication prefs
  "donotemail",
  "donotphone",
  "donotfax",
  "donotbulkemail",
  "donotpostalmail",
  "preferredcontactmethodcode",
  // Custom – Utility / Energy
  "mj_boilermake",
  "mj_boilermodel",
  "mj_installationdate",
  "mj_energytariff",
  "mj_homecarecover",
  "mj_homecaretypeofcover",
  "mj_doyouhaveahivethermostat",
  "mj_doyouhaveasmartmeter",
  "mj_doyouhavesmartradiatorvalves",
  "mj_smartmeter",
  "mj_homeevcharger",
  "mj_utility_ev_owner",
  "mj_priorityregister",
  // Analysis
  "mj_conversationpoints",
  "mj_conversationlogic",
  "mj_analysislastrun",
  // GDPR
  "msdyn_gdproptout",
  // System
  "createdon",
  "modifiedon",
  "statecode",
  "statuscode",
].join(",");

app.get("/api/contact/:id", async (req, res) => {
  try {
    const id = req.params.id.replace(/[{}]/g, "");
    if (!/^[0-9a-f-]{36}$/i.test(id)) {
      return res.status(400).json({ error: "Invalid contact ID format" });
    }
    const client = getDataverseClient();
    const data = await client.getById(
      "contacts",
      id,
      `$select=${CONTACT_SELECT}`,
    );
    res.json(data);
  } catch (err) {
    console.error("ContactDemo API error:", err.message);
    const status = err.status || 500;
    res.status(status).json({ error: err.message });
  }
});

// ---------------------------------------------------------------------------
// ContactDemo – Photo endpoint (returns image or 404)
// ---------------------------------------------------------------------------
app.get("/api/contact/:id/photo", async (req, res) => {
  try {
    const id = req.params.id.replace(/[{}]/g, "");
    if (!/^[0-9a-f-]{36}$/i.test(id)) {
      return res.status(400).json({ error: "Invalid contact ID" });
    }
    const client = getDataverseClient();
    const token = await client.getToken();
    const url = `${client.apiUrl}/contacts(${id})/entityimage/$value`;
    const response = await globalThis.fetch(url, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "image/*",
      },
    });
    if (!response.ok) {
      return res.status(404).json({ error: "No photo available" });
    }
    const contentType = response.headers.get("content-type") || "image/jpeg";
    const buffer = Buffer.from(await response.arrayBuffer());
    res.set("Content-Type", contentType);
    res.set("Cache-Control", "public, max-age=300");
    res.send(buffer);
  } catch (err) {
    console.error("Photo API error:", err.message);
    res.status(404).json({ error: "No photo available" });
  }
});

// ---------------------------------------------------------------------------
// ContactDemo – HTML page (receives ?id=<guid> or &id=<guid>)
// ---------------------------------------------------------------------------
app.get("/ContactDemo", (_req, res) => {
  res.send(contactDemoHTML());
});

function contactDemoHTML() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Contact Details — Azure Web Apps</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: #f5f6fa;
      color: #1e1e1e;
      padding: 24px;
      min-height: 100vh;
    }

    /* Header banner */
    .header {
      background: linear-gradient(135deg, #0078d4 0%, #005a9e 100%);
      color: #fff;
      padding: 28px 32px;
      border-radius: 12px;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      gap: 20px;
      box-shadow: 0 4px 20px rgba(0,120,212,.25);
    }
    .header .avatar {
      width: 72px; height: 72px;
      background: rgba(255,255,255,.2);
      border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.8rem; font-weight: 700;
      flex-shrink: 0;
      border: 3px solid rgba(255,255,255,.4);
      overflow: hidden;
    }
    .header .avatar img {
      width: 100%; height: 100%;
      object-fit: cover;
    }
    .header h1 { font-size: 1.6rem; font-weight: 600; }
    .header .subtitle { font-size: .95rem; opacity: .85; margin-top: 4px; }
    .header .badge {
      display: inline-block; padding: 3px 12px;
      border-radius: 20px; font-size: .75rem; font-weight: 600;
      margin-top: 6px;
    }
    .badge-active { background: #27ae60; color: #fff; }
    .badge-inactive { background: #e74c3c; color: #fff; }

    /* Card grid */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 20px;
    }
    .card {
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 2px 12px rgba(0,0,0,.06);
      overflow: hidden;
      transition: box-shadow .2s;
    }
    .card:hover { box-shadow: 0 4px 20px rgba(0,0,0,.10); }
    .card-header {
      padding: 14px 20px;
      font-weight: 600;
      font-size: .9rem;
      border-bottom: 1px solid #eef0f4;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #0078d4;
    }
    .card-header svg { width: 18px; height: 18px; flex-shrink: 0; }
    .card-body { padding: 6px 20px 16px; }
    .field-row {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #f5f5f5;
      gap: 12px;
    }
    .field-row:last-child { border-bottom: none; }
    .field-label {
      font-size: .82rem;
      color: #666;
      font-weight: 500;
      min-width: 140px;
      flex-shrink: 0;
    }
    .field-value {
      font-size: .88rem;
      color: #1e1e1e;
      text-align: right;
      word-break: break-word;
    }
    .field-value.empty { color: #bbb; font-style: italic; }
    .field-value a { color: #0078d4; text-decoration: none; }
    .field-value a:hover { text-decoration: underline; }

    /* Boolean pills */
    .pill { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: .78rem; font-weight: 600; }
    .pill-yes { background: #e8f5e9; color: #2e7d32; }
    .pill-no { background: #fce4ec; color: #c62828; }

    /* Loading / error states */
    .status-msg {
      text-align: center;
      padding: 60px 20px;
      color: #666;
      font-size: 1rem;
    }
    .status-msg.error { color: #c62828; }
    .spinner {
      width: 40px; height: 40px;
      border: 4px solid #e0e0e0;
      border-top: 4px solid #0078d4;
      border-radius: 50%;
      animation: spin .8s linear infinite;
      margin: 0 auto 16px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }

    /* Full-width card */
    .card-full { grid-column: 1 / -1; }

    /* Responsive */
    @media (max-width: 480px) {
      .grid { grid-template-columns: 1fr; }
      .header { flex-direction: column; text-align: center; }
    }
  </style>
</head>
<body>
  <div id="app">
    <div class="status-msg">
      <div class="spinner"></div>
      Loading contact details&hellip;
    </div>
  </div>

  <script>
    // -----------------------------------------------------------------------
    // Field definitions grouped into cards
    // -----------------------------------------------------------------------
    const CARDS = [
      {
        title: "Personal Information",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
        fields: [
          { key: "salutation", label: "👤 Salutation" },
          { key: "firstname", label: "🅰️ First Name" },
          { key: "middlename", label: "🔤 Middle Name" },
          { key: "lastname", label: "🅱️ Last Name" },
          { key: "suffix", label: "🏷️ Suffix" },
          { key: "nickname", label: "😊 Nickname" },
          { key: "jobtitle", label: "💼 Job Title" },
          { key: "department", label: "🏢 Department" },
          { key: "gendercode", label: "⚧️ Gender", type: "formatted" },
          { key: "birthdate", label: "🎂 Date of Birth", type: "date" },
          { key: "anniversary", label: "💍 Anniversary", type: "date" },
          { key: "familystatuscode", label: "💑 Marital Status", type: "formatted" },
          { key: "spousesname", label: "❤️ Spouse/Partner" },
          { key: "numberofchildren", label: "👶 No. of Children" },
        ]
      },
      {
        title: "Contact Details",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.362 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.338 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg>',
        fields: [
          { key: "emailaddress1", label: "📧 Email (Primary)", type: "email" },
          { key: "emailaddress2", label: "📨 Email (Secondary)", type: "email" },
          { key: "emailaddress3", label: "✉️ Email (Other)", type: "email" },
          { key: "telephone1", label: "☎️ Business Phone", type: "phone" },
          { key: "telephone2", label: "🏠 Home Phone", type: "phone" },
          { key: "mobilephone", label: "📱 Mobile Phone", type: "phone" },
          { key: "fax", label: "📠 Fax" },
          { key: "websiteurl", label: "🌐 Website", type: "url" },
        ]
      },
      {
        title: "Primary Address",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        fields: [
          { key: "address1_line1", label: "🏠 Street 1" },
          { key: "address1_line2", label: "🏠 Street 2" },
          { key: "address1_line3", label: "🏠 Street 3" },
          { key: "address1_city", label: "🏙️ City" },
          { key: "address1_stateorprovince", label: "📍 County / State" },
          { key: "address1_postalcode", label: "📮 Postcode" },
          { key: "address1_country", label: "🌍 Country" },
          { key: "address1_telephone1", label: "📞 Address Phone", type: "phone" },
        ]
      },
      {
        title: "Secondary Address",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        fields: [
          { key: "address2_line1", label: "🏠 Street 1" },
          { key: "address2_line2", label: "🏠 Street 2" },
          { key: "address2_line3", label: "🏠 Street 3" },
          { key: "address2_city", label: "🏙️ City" },
          { key: "address2_stateorprovince", label: "📍 County / State" },
          { key: "address2_postalcode", label: "📮 Postcode" },
          { key: "address2_country", label: "🌍 Country" },
        ]
      },
      {
        title: "Company & Management",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>',
        fields: [
          { key: "_parentcustomerid_value", label: "🏛️ Company", type: "formatted" },
          { key: "managername", label: "👔 Manager" },
          { key: "managerphone", label: "📞 Manager Phone", type: "phone" },
          { key: "assistantname", label: "🤝 Assistant" },
          { key: "assistantphone", label: "📞 Assistant Phone", type: "phone" },
        ]
      },
      {
        title: "Boiler & Heating",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
        fields: [
          { key: "mj_boilermake", label: "🔧 Boiler Make", type: "formatted" },
          { key: "mj_boilermodel", label: "🏭 Boiler Model" },
          { key: "mj_installationdate", label: "📅 Installation Date", type: "date" },
          { key: "mj_repairedrecently", label: "🔨 Repaired Recently", type: "bool" },
          { key: "mj_homecarecover", label: "🛡️ HomeCare Cover", type: "bool" },
          { key: "mj_homecaretypeofcover", label: "📋 HomeCare Type", type: "formatted" },
        ]
      },
      {
        title: "Energy & Smart Home",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
        fields: [
          { key: "mj_energytariff", label: "💡 Energy Tariff", type: "formatted" },
          { key: "mj_doyouhaveasmartmeter", label: "📊 Smart Meter", type: "bool" },
          { key: "mj_doyouhaveahivethermostat", label: "🌡️ Hive Thermostat", type: "bool" },
          { key: "mj_doyouhavesmartradiatorvalves", label: "🔆 Smart Radiator Valves", type: "bool" },
          { key: "mj_homeevcharger", label: "🔌 Home EV Charger", type: "bool" },
          { key: "mj_utility_ev_owner", label: "🚗 EV Owner", type: "bool" },
          { key: "mj_priorityregister", label: "⭐ Priority Register", type: "bool" },
        ]
      },
      {
        title: "Communication Preferences",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
        fields: [
          { key: "preferredcontactmethodcode", label: "💬 Preferred Method", type: "formatted" },
          { key: "donotemail", label: "🚫 Do Not Email", type: "bool" },
          { key: "donotphone", label: "🚫 Do Not Phone", type: "bool" },
          { key: "donotfax", label: "🚫 Do Not Fax", type: "bool" },
          { key: "donotbulkemail", label: "🚫 Do Not Bulk Email", type: "bool" },
          { key: "donotpostalmail", label: "🚫 Do Not Post", type: "bool" },
          { key: "msdyn_gdproptout", label: "🔒 GDPR Opt-out", type: "bool" },
        ]
      },
      {
        title: "Analysis & Notes",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
        fullWidth: true,
        fields: [
          { key: "mj_conversationpoints", label: "💬 Conversation Points", type: "memo" },
          { key: "mj_conversationlogic", label: "🧠 Conversation Logic", type: "memo" },
          { key: "mj_analysislastrun", label: "🕐 Analysis Last Run" },
        ]
      },
      {
        title: "System",
        icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9c.2.65.76 1.09 1.44 1.09H21a2 2 0 010 4h-.09c-.68 0-1.24.44-1.44 1.09z"/></svg>',
        fields: [
          { key: "statecode", label: "🟢 Status", type: "formatted" },
          { key: "statuscode", label: "📌 Status Reason", type: "formatted" },
          { key: "createdon", label: "📅 Created On", type: "datetime" },
          { key: "modifiedon", label: "✏️ Modified On", type: "datetime" },
        ]
      },
    ];

    // -----------------------------------------------------------------------
    // Render helpers
    // -----------------------------------------------------------------------
    function getContactId() {
      const params = new URLSearchParams(window.location.search);
      return params.get("id") || params.get("contactid");
    }

    function esc(str) {
      if (!str) return "";
      const d = document.createElement("div");
      d.textContent = str;
      return d.innerHTML;
    }

    function formatValue(contact, field) {
      const { key, type } = field;

      // Formatted values from OData annotations (picklists, lookups, etc.)
      const fmtKey = key + "@OData.Community.Display.V1.FormattedValue";

      if (type === "formatted") {
        const v = contact[fmtKey] || contact[key];
        return v != null ? esc(String(v)) : null;
      }

      if (type === "bool") {
        const fmtVal = contact[fmtKey];
        const rawVal = contact[key];
        if (rawVal === true || fmtVal === "Yes")
          return '<span class="pill pill-yes">Yes</span>';
        if (rawVal === false || fmtVal === "No")
          return '<span class="pill pill-no">No</span>';
        return null;
      }

      if (type === "date") {
        const v = contact[fmtKey] || contact[key];
        if (!v) return null;
        try { return esc(new Date(v).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })); }
        catch { return esc(String(v)); }
      }

      if (type === "datetime") {
        const v = contact[fmtKey] || contact[key];
        if (!v) return null;
        try { return esc(new Date(v).toLocaleString("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })); }
        catch { return esc(String(v)); }
      }

      if (type === "email") {
        const v = contact[key];
        return v ? \`<a href="mailto:\${esc(v)}">\${esc(v)}</a>\` : null;
      }

      if (type === "phone") {
        const v = contact[key];
        return v ? \`<a href="tel:\${esc(v)}">\${esc(v)}</a>\` : null;
      }

      if (type === "url") {
        const v = contact[key];
        if (!v) return null;
        const href = v.startsWith("http") ? v : "https://" + v;
        return \`<a href="\${esc(href)}" target="_blank">\${esc(v)}</a>\`;
      }

      if (type === "memo") {
        const v = contact[key];
        return v ? \`<div style="white-space:pre-wrap;font-size:.85rem;max-height:200px;overflow:auto;">\${esc(v)}</div>\` : null;
      }

      const v = contact[fmtKey] || contact[key];
      return v != null && v !== "" ? esc(String(v)) : null;
    }

    function initials(name) {
      if (!name) return "?";
      return name.split(/\\s+/).filter(Boolean).map(w => w[0]).slice(0, 2).join("").toUpperCase();
    }

    // -----------------------------------------------------------------------
    // Render the page
    // -----------------------------------------------------------------------
    function renderContact(contact) {
      const fullName = contact.fullname || [contact.firstname, contact.lastname].filter(Boolean).join(" ") || "Unknown";
      const jobLine = [contact.jobtitle, contact._parentcustomerid_value ? contact["_parentcustomerid_value@OData.Community.Display.V1.FormattedValue"] : null].filter(Boolean).join(" at ");
      const isActive = contact.statecode === 0;

      let html = \`
        <div class="header">
          <div class="avatar" id="contact-avatar">\${initials(fullName)}</div>
          <div>
            <h1>\${esc(fullName)}</h1>
            \${jobLine ? \`<div class="subtitle">\${esc(jobLine)}</div>\` : ""}
            <div class="badge \${isActive ? "badge-active" : "badge-inactive"}">\${isActive ? "Active" : "Inactive"}</div>
          </div>
        </div>
        <div class="grid">
      \`;

      for (const card of CARDS) {
        // Check if card has any non-empty values
        const rendered = card.fields.map(f => ({ ...f, html: formatValue(contact, f) }));
        const hasData = rendered.some(f => f.html !== null);
        if (!hasData) continue;

        html += \`<div class="card\${card.fullWidth ? " card-full" : ""}">
          <div class="card-header">\${card.icon} \${esc(card.title)}</div>
          <div class="card-body">\`;

        for (const f of rendered) {
          html += \`<div class="field-row">
            <div class="field-label">\${esc(f.label)}</div>
            <div class="field-value\${f.html === null ? " empty" : ""}">\${f.html !== null ? f.html : "&mdash;"}</div>
          </div>\`;
        }

        html += "</div></div>";
      }

      html += "</div>";
      document.getElementById("app").innerHTML = html;
    }

    function renderError(msg) {
      document.getElementById("app").innerHTML = \`
        <div class="status-msg error">
          <h2 style="margin-bottom:8px;">Unable to load contact</h2>
          <p>\${esc(msg)}</p>
          <p style="margin-top:16px;font-size:.85rem;color:#888;">
            Pass <code>?id=&lt;contact-guid&gt;</code> in the URL to view a contact.
          </p>
        </div>\`;
    }

    // -----------------------------------------------------------------------
    // Boot
    // -----------------------------------------------------------------------
    (async () => {
      const id = getContactId();
      if (!id) return renderError("No contact ID provided.");
      try {
        const resp = await fetch("/api/contact/" + encodeURIComponent(id));
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(err.error || resp.statusText);
        }
        const contact = await resp.json();
        renderContact(contact);

        // Try to load contact photo — replace initials if available
        const img = new Image();
        img.onload = () => {
          const avatar = document.getElementById("contact-avatar");
          if (avatar) { avatar.textContent = ""; avatar.appendChild(img); }
        };
        img.src = "/api/contact/" + encodeURIComponent(id) + "/photo";
      } catch (e) {
        renderError(e.message);
      }
    })();
  </script>
</body>
</html>`;
}

// ---------------------------------------------------------------------------
// EnergyDashboard – HTML page (receives ?id=<guid> or &id=<guid>)
// Designed for IFrame embedding on D365 Contact form "App" tab.
// ---------------------------------------------------------------------------
app.get("/EnergyDashboard", (_req, res) => {
  res.send(energyDashboardHTML());
});

function energyDashboardHTML() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Energy Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      background: #f3f2f1;
      color: #1e1e1e;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* ── Top: contact fields ───────────────────────────────── */
    .fields-section {
      flex-shrink: 0;
      background: #fff;
      padding: 12px 20px 8px;
      border-bottom: 1px solid #e1dfdd;
      box-shadow: 0 1px 3px rgba(0,0,0,.06);
    }
    .fields-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 1px 24px;
    }
    .field-row {
      display: flex;
      align-items: center;
      gap: 6px;
      min-height: 26px;
      font-size: 12px;
    }
    .field-label {
      color: #605e5c;
      min-width: 90px;
      flex-shrink: 0;
    }
    .field-value {
      color: #1e1e1e;
      font-weight: 500;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .pill {
      font-size: 10px;
      font-weight: 600;
      padding: 1px 8px;
      border-radius: 10px;
      color: #fff;
    }
    .pill-yes { background: #107c10; }
    .pill-no { background: #a4262c; }
    .conversation-row {
      display: flex;
      align-items: flex-start;
      gap: 6px;
      font-size: 12px;
      margin-top: 4px;
    }
    .conversation-value {
      color: #1e1e1e;
      font-weight: 500;
      font-size: 12px;
      line-height: 16px;
      word-break: break-word;
    }

    /* ── Bottom: charts ────────────────────────────────────── */
    .charts-section {
      display: flex;
      flex-direction: column;
      padding: 6px 16px;
      gap: 4px;
      overflow: hidden;
    }
    .chart-card {
      background: #fff;
      border-radius: 8px;
      padding: 6px 12px 2px;
      box-shadow: 0 1px 4px rgba(0,0,0,.08);
      overflow: hidden;
    }
    .chart-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
    }
    .chart-title {
      font-size: 13px;
      font-weight: 600;
    }
    .badge {
      font-size: 10px;
      font-weight: 600;
      padding: 1px 8px;
      border-radius: 10px;
      color: #fff;
    }
    .badge-elec { background: #0078d4; }
    .badge-gas { background: #e67700; }
    .ev-hint {
      font-size: 11px;
      color: #605e5c;
      margin-left: auto;
      font-style: italic;
    }
    .chart-container {
      position: relative;
      width: 100%;
    }

    /* Loading / error states */
    .loading-state {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      font-size: 16px;
      color: #605e5c;
    }
    .error-msg {
      background: #fde7e9;
      color: #a4262c;
      padding: 12px 20px;
      border-radius: 6px;
      margin: 20px;
      font-size: 14px;
    }
  </style>
</head>
<body>
  <div id="app-loading" class="loading-state">Loading contact…</div>
  <div id="app-content" style="display:none; height:100vh; flex-direction:column;">

    <!-- Fields -->
    <div class="fields-section">
      <div class="fields-grid" id="fields-grid"></div>
      <div id="conversation-row"></div>
    </div>

    <!-- Charts -->
    <div class="charts-section">
      <div class="chart-card">
        <div class="chart-header">
          <span class="badge badge-elec">⚡</span>
          <span class="chart-title">Electricity Usage (kWh) — 12 Months</span>
          <span class="ev-hint">📈 Recent uptick — possible EV charging</span>
        </div>
        <div class="chart-container"><canvas id="elecChart"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <span class="badge badge-gas">🔥</span>
          <span class="chart-title">Gas Usage (kWh) — 12 Months</span>
        </div>
        <div class="chart-container"><canvas id="gasChart"></canvas></div>
      </div>
    </div>
  </div>

  <script>
    // ── Size charts to fit viewport ──────────────────────
    function sizeCharts() {
      var fields = document.querySelector('.fields-section');
      if (!fields) return;
      var fieldsH = fields.offsetHeight;
      // In a D365 IFrame, innerHeight can be unreliable. Use a sensible cap.
      var vh = Math.min(window.innerHeight, 700);
      var headerPadding = 60; // chart headers + card padding + section padding
      var available = vh - fieldsH - headerPadding;
      var perChart = Math.max(100, Math.floor(available / 2));
      perChart = Math.min(perChart, 200); // hard cap — never taller than 200px
      var containers = document.querySelectorAll('.chart-container');
      containers.forEach(function(c) { c.style.height = perChart + 'px'; });
      // Also set canvas height attributes for Chart.js
      var canvases = document.querySelectorAll('.chart-container canvas');
      canvases.forEach(function(cv) {
        cv.setAttribute('height', perChart);
        cv.style.height = perChart + 'px';
        cv.style.maxHeight = perChart + 'px';
      });
    }
    // ── Get contact ID from URL (D365 appends &id=<guid>) ────
    function getContactId() {
      var params = new URLSearchParams(window.location.search);
      return params.get('id');
    }

    // ── Render a text field ──────────────────────────────────
    function textField(label, value) {
      return '<div class="field-row">'
        + '<span class="field-label">' + label + '</span>'
        + '<span class="field-value">' + (value || '—') + '</span>'
        + '</div>';
    }

    // ── Render a boolean pill ────────────────────────────────
    function boolField(label, value) {
      var cls = value ? 'pill-yes' : 'pill-no';
      var text = value ? 'Yes' : 'No';
      return '<div class="field-row">'
        + '<span class="field-label">' + label + '</span>'
        + '<span class="pill ' + cls + '">' + text + '</span>'
        + '</div>';
    }

    // ── Get OData formatted value ────────────────────────────
    function fv(contact, field) {
      return contact[field + '@OData.Community.Display.V1.FormattedValue'] || null;
    }

    // ── Render contact fields ────────────────────────────────
    function renderFields(c) {
      var html = '';
      // Column 1 — Boiler & Heating
      html += textField('Boiler Make', fv(c, 'mj_boilermake'));
      html += textField('Boiler Model', c.mj_boilermodel);
      html += textField('Installation', c.mj_installationdate);
      html += boolField('HomeCare', c.mj_homecarecover);
      html += textField('Cover Type', fv(c, 'mj_homecaretypeofcover'));
      // Column 2 — Energy & Smart Home
      html += textField('Energy Tariff', fv(c, 'mj_energytariff'));
      html += boolField('Smart Meter', c.mj_smartmeter != null ? c.mj_smartmeter : c.mj_doyouhaveasmartmeter);
      html += boolField('Hive Thermostat', c.mj_doyouhaveahivethermostat);
      html += boolField('Smart TRVs', c.mj_doyouhavesmartradiatorvalves);
      html += boolField('EV Owner', c.mj_utility_ev_owner);
      // Column 3 — EV & Service
      html += boolField('EV Charger', c.mj_homeevcharger);
      html += boolField('Priority Register', c.mj_priorityregister);
      html += boolField('Repaired Recently', c.mj_repairedrecently);

      document.getElementById('fields-grid').innerHTML = html;

      // Conversation Points — full width
      if (c.mj_conversationpoints) {
        document.getElementById('conversation-row').innerHTML =
          '<div class="conversation-row">'
          + '<span class="field-label">Conversation Pts</span>'
          + '<span class="conversation-value">' + c.mj_conversationpoints + '</span>'
          + '</div>';
      }
    }

    // ── Generate dynamic 12-month chart data ─────────────────
    function generateMonthlyData(seasonal, evUplift) {
      var MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      var now = new Date();
      var labels = [];
      var values = [];
      for (var i = 11; i >= 0; i--) {
        var d = new Date(now.getFullYear(), now.getMonth() - 1 - i, 1);
        var m = d.getMonth();
        var yy = String(d.getFullYear()).slice(-2);
        labels.push(MONTHS[m] + ' ' + yy);
        var kWh = seasonal[m];
        if (evUplift) {
          var pos = 11 - i;
          if (pos >= 10) kWh += 120;
          else if (pos === 9) kWh += 50;
        }
        var jitter = 1 + (((m * 7 + 3) % 11) - 5) / 100;
        kWh = Math.round(kWh * jitter);
        values.push(kWh);
      }
      return { labels: labels, values: values };
    }

    // ── Render charts ────────────────────────────────────────
    function renderCharts() {
      var ELEC = {0:370,1:355,2:310,3:275,4:240,5:210,6:195,7:205,8:260,9:305,10:340,11:385};
      var GAS  = {0:1340,1:1180,2:980,3:720,4:410,5:180,6:120,7:130,8:380,9:680,10:1050,11:1280};

      var elecData = generateMonthlyData(ELEC, true);
      var gasData = generateMonthlyData(GAS, false);

      function makeChart(canvasId, data, colour) {
        var ctx = document.getElementById(canvasId).getContext('2d');
        new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.labels,
            datasets: [{
              data: data.values,
              borderColor: colour,
              backgroundColor: colour + '22',
              fill: true,
              tension: 0.3,
              pointRadius: 3,
              pointBackgroundColor: colour,
              borderWidth: 2,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function(ctx) { return ctx.parsed.y.toLocaleString() + ' kWh'; }
                }
              }
            },
            scales: {
              x: { ticks: { font: { size: 11 } }, grid: { display: false } },
              y: { ticks: { font: { size: 11 } }, grid: { color: '#e0e0e0' } }
            }
          }
        });
      }

      makeChart('elecChart', elecData, '#0078d4');
      makeChart('gasChart', gasData, '#e67700');
    }

    // ── Main ─────────────────────────────────────────────────
    async function init() {
      var contactId = getContactId();
      if (!contactId) {
        document.getElementById('app-loading').innerHTML =
          '<div class="error-msg">No contact ID provided. This page should be loaded from a D365 contact form.</div>';
        return;
      }

      try {
        var resp = await fetch('/api/contact/' + contactId);
        if (!resp.ok) throw new Error('API returned ' + resp.status);
        var contact = await resp.json();

        document.getElementById('app-loading').style.display = 'none';
        var content = document.getElementById('app-content');
        content.style.display = 'flex';

        renderFields(contact);
        sizeCharts();
        renderCharts();
        window.addEventListener('resize', function() { sizeCharts(); });
      } catch (err) {
        document.getElementById('app-loading').innerHTML =
          '<div class="error-msg">Failed to load contact: ' + err.message + '</div>';
      }
    }

    init();
  </script>
</body>
</html>`;
}

// 404 catch-all
app.use((_req, res) => {
  const html = pageShell(
    "Not Found",
    "#fce4ec",
    "#c62828",
    `
    <h1>404 — Page Not Found</h1>
    <p>The page you requested does not exist.</p>
    <div class="links">
      <a href="/">Back to Home</a>
    </div>
  `,
  );
  res.status(404).send(html);
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
  console.log(
    `Node ${process.version} | PID ${process.pid} | ${os.hostname()}`,
  );
});
