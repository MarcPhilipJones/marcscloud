"""
Find all Dataverse cases (incidents) without a subject and assign
the most appropriate existing subject based on the case title.
"""

import os
import sys

os.chdir(
    r"c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\mcp-dataverse-server"
)
sys.path.insert(0, "src")

import httpx
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings

# ── authenticate ──────────────────────────────────────────────
settings = load_settings()
tp = TokenProvider(
    tenant_id=settings.dataverse_tenant_id,
    client_id=settings.dataverse_client_id,
    client_secret=settings.dataverse_client_secret,
    resource=settings.dataverse_base_url,
)
token = tp.get_access_token()
base = settings.dataverse_base_url.rstrip("/")
api = f"{base}/api/data/{settings.dataverse_api_version}"
headers = {
    "Authorization": f"Bearer {token}",
    "OData-MaxVersion": "4.0",
    "OData-Version": "4.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Prefer": 'odata.include-annotations="*"',
}

client = httpx.Client(timeout=30.0, headers=headers)

# ── 1  Get all subjects ──────────────────────────────────────
print("=" * 60)
print("STEP 1: Loading all subjects...")
resp = client.get(f"{api}/subjects?$select=subjectid,title&$orderby=title asc&$top=100")
resp.raise_for_status()
subjects = resp.json()["value"]
print(f"  Found {len(subjects)} subjects")

subject_map = {s["subjectid"]: s["title"] for s in subjects}
for sid, stitle in subject_map.items():
    print(f"    {stitle:45s}  {sid}")

# ── 2  Get cases WITHOUT a subject ──────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Finding cases without a subject...")
resp = client.get(
    f"{api}/incidents"
    "?$select=incidentid,title,description,caseorigincode,casetypecode,ticketnumber"
    "&$filter=_subjectid_value eq null"
    "&$orderby=createdon desc"
    "&$top=200"
)
resp.raise_for_status()
no_subject_cases = resp.json()["value"]
print(f"  Found {len(no_subject_cases)} cases without a subject\n")

if not no_subject_cases:
    print("All cases already have subjects assigned. Nothing to do!")
    sys.exit(0)

for c in no_subject_cases:
    print(f"  [{c['ticketnumber']}] {c['title']}")

# ── 3  Mapping rules: title keywords → best subject ─────────
# Build a keyword→subject mapping based on the available subjects
KEYWORD_RULES = [
    # Pension / Finance
    (["pension", "retirement", "annuity", "severance"], "Pensions"),
    (["late payment", "payment delay", "missed payment"], "Late Payments"),
    (["tax", "contribution", "relief"], "Tax and Contributions"),
    (["transfer", "transfer value"], "Transfers"),
    (["death benefit", "nomination"], "Death Benefits"),
    (["statement", "benefit statement", "document"], "Statements and Documents"),
    (["personal detail", "address change"], "Personal Details"),
    (["complaint", "service delay"], "Complaints"),
    (["forecast", "integration"], "Finance"),
    # Utilities - Gas
    (["gas leak", "smell of gas", "gas emergency"], "Gas Leak (Household)"),
    (["gas"], "Gas"),
    # Utilities - Water
    (["water leak", "burst pipe", "water main"], "Water"),
    (["water pressure", "no water", "low pressure"], "Water"),
    (["discolour", "brown water", "discolor"], "Discoloured Water"),
    (["pumping station", "pump"], "Water"),
    (["mineral", "water supply", "calcium"], "Water"),
    # Utilities - Electric
    (["power loss", "power cut", "blackout", "electricity"], "Electric"),
    (["solar", "inverter", "energy credit", "surplus"], "Electric"),
    (["transformer", "overheating alarm"], "Electric"),
    # Utilities - Heating / Boiler
    (
        ["heating", "boiler", "warmth", "radiator", "no heat"],
        "No Heating Household (Boiler Problems)",
    ),
    (["temperature", "thermostat", "hot enough", "threshold"], "Temperature"),
    # ITSM / IT
    (
        [
            "laptop",
            "computer",
            "it ",
            "api ",
            "401",
            "unauthorized",
            "csv",
            "upload",
            "meter reading",
            "syncing",
            "portal",
            "training session",
            "account access",
            "blocked",
            "historical data",
            "restore",
        ],
        "ITSM",
    ),
    # Smart / Energy
    (["smart meter", "tariff", "off-peak", "energy"], "Electric"),
    # Coffee machines (legacy demo)
    (
        [
            "coffee",
            "coffeemaker",
            "cafe ",
            "brew",
            "airpot",
            "quickpot",
            "autodrip",
            "espresso",
            "tamp",
            "grind",
            "milk",
            "drip",
        ],
        "General",
    ),
    (["clog", "tube", "calcium build"], "Clogged tubes"),
    (["shutdown", "shutting down"], "Unexpected shutdown"),
    (["air bubble", "bubble"], "General"),
    (["cleaning", "technique", "suggestion"], "Suggestions"),
    (["machine part", "fitting", "container"], "General"),
    # Moving / Home
    (["moving home", "relocation"], "Moving Home"),
    (["home", "house"], "Home"),
    # Building
    (["carpet", "painting", "snagging", "building", "repair"], "Building Development"),
    # Broadband
    (["broadband", "internet", "wifi", "wi-fi"], "Broadband"),
]

# Resolve subject names to IDs
name_to_id = {}
for s in subjects:
    name_to_id[s["title"].lower()] = s["subjectid"]


def choose_subject(case_title: str, case_desc: str | None) -> tuple[str, str] | None:
    """Return (subject_id, subject_name) for the best-matching subject."""
    text = (case_title + " " + (case_desc or "")).lower()
    for keywords, subject_name in KEYWORD_RULES:
        for kw in keywords:
            if kw in text:
                sid = name_to_id.get(subject_name.lower())
                if sid:
                    return sid, subject_name
    return None


# ── 4  Assign subjects ──────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 3: Assigning subjects...\n")

# Default fallback
default_subject_id = name_to_id.get("default subject")
updates = []

for case in no_subject_cases:
    title = case["title"]
    desc = case.get("description")
    ticket = case["ticketnumber"]
    cid = case["incidentid"]

    match = choose_subject(title, desc)
    if match:
        sid, sname = match
    elif default_subject_id:
        sid, sname = default_subject_id, "Default Subject"
    else:
        print(f"  SKIP [{ticket}] {title} — no matching subject found")
        continue

    updates.append((cid, ticket, title, sid, sname))
    print(f"  [{ticket}] {title}")
    print(f"          → {sname}")

# ── 5  Apply updates ────────────────────────────────────────
print("\n" + "=" * 60)
print(f"STEP 4: Applying {len(updates)} updates to Dataverse...\n")

success = 0
failed = 0
for cid, ticket, title, sid, sname in updates:
    try:
        resp = client.patch(
            f"{api}/incidents({cid})",
            json={"subjectid@odata.bind": f"/subjects({sid})"},
        )
        resp.raise_for_status()
        print(f"  ✓ [{ticket}] → {sname}")
        success += 1
    except Exception as e:
        print(f"  ✗ [{ticket}] FAILED: {e}")
        failed += 1

# ── 6  Summary ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print(f"  Cases without subject found: {len(no_subject_cases)}")
print(f"  Successfully updated:        {success}")
print(f"  Failed:                       {failed}")
print(f"  Skipped (no match):           {len(no_subject_cases) - len(updates)}")

# ── 7  Verify ───────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 5: Verifying — checking for remaining cases without subjects...")
resp = client.get(
    f"{api}/incidents"
    "?$select=incidentid,title,ticketnumber"
    "&$filter=_subjectid_value eq null"
    "&$top=200"
)
resp.raise_for_status()
remaining = resp.json()["value"]
if remaining:
    print(f"  WARNING: {len(remaining)} cases still without a subject:")
    for c in remaining:
        print(f"    [{c['ticketnumber']}] {c['title']}")
else:
    print("  ✓ ALL cases now have a subject assigned!")

client.close()
