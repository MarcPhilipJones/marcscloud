"""Contoso Utilities — Water Field Service Demo Setup.

Creates all Field Service data for a water utility demo:
  Phase 1: Knowledge Articles (5, published)
  Phase 2: Characteristics for Alan Steiner (7)
  Phase 3: Work Order Types (4)
  Phase 4: Service Task Types (20)
  Phase 5: Incident Types (4) + link service tasks
  Phase 6: Products (8)
  Phase 7: Look up existing CW Willowbrook Farm + Chris Walker
  Phase 8: Work Orders (4, one per type) with knowledge article links

Usage:
    cd field-service-wessex
    python setup_contoso_utilities_demo.py
"""

import os
import sys

# Resolve paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "src"))

from field_service_wessex.dataverse_client import DataverseClient, extract_guid
from rich.console import Console
from rich.table import Table

console = Console()

# ─── Alan Steiner bookable resource ID ────────────────────────────────────────
ALAN_STEINER_RESOURCE_ID = "b8dddd9c-3b61-ef11-bfe2-002248a36d0e"

# ─── Inline HTML styles (Dataverse strips <style> blocks) ────────────────────
H1 = 'style="font-family: Segoe UI, sans-serif; font-size: 18pt; color: #2c3e50; margin-bottom: 15px;"'
H2 = 'style="font-family: Segoe UI, sans-serif; font-size: 14pt; color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"'
P = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"'
LI = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; margin-bottom: 8px;"'
UL = 'style="margin: 0 0 15px 20px; padding: 0;"'


# ═════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═════════════════════════════════════════════════════════════════════════════


def find_or_create(
    client: DataverseClient,
    entity_set: str,
    name_field: str,
    name_value: str,
    data: dict,
) -> str:
    """Find existing record by name or create new one. Returns GUID."""
    params = {
        "$filter": f"{name_field} eq '{name_value}'",
        "$top": "1",
    }
    try:
        result = client.get(entity_set, params)
        records = result.get("value", [])
        if records:
            for key in records[0]:
                if key.endswith("id") and key not in (
                    "@odata.etag",
                    "_transactioncurrencyid_value",
                ):
                    if isinstance(records[0][key], str) and len(records[0][key]) == 36:
                        console.print(f"  [yellow]Found:[/yellow] {name_value}")
                        return records[0][key]
    except Exception:
        pass

    data[name_field] = name_value
    result = client.post(entity_set, data)
    if result and "@odata.id" in result:
        guid = extract_guid(result["@odata.id"])
        console.print(f"  [green]Created:[/green] {name_value} ({guid})")
        return guid
    raise RuntimeError(f"Failed to create {name_value} in {entity_set}")


def find_record(
    client: DataverseClient,
    entity_set: str,
    name_field: str,
    name_value: str,
) -> str | None:
    """Find a record by name. Returns GUID or None."""
    params = {"$filter": f"contains({name_field},'{name_value}')", "$top": "1"}
    try:
        result = client.get(entity_set, params)
        records = result.get("value", [])
        if records:
            for key in records[0]:
                if key.endswith("id") and key not in ("@odata.etag",):
                    if isinstance(records[0][key], str) and len(records[0][key]) == 36:
                        return records[0][key]
    except Exception:
        pass
    return None


def validate_count(
    client: DataverseClient,
    entity_set: str,
    name_field: str,
    name_values: list[str],
    label: str,
) -> bool:
    """Validate that all named records exist. Returns True if all found."""
    missing = []
    for name in name_values:
        if not find_record(client, entity_set, name_field, name):
            missing.append(name)
    if missing:
        console.print(
            f"  [red]✗ VALIDATION FAILED for {label} — missing: {missing}[/red]"
        )
        return False
    console.print(
        f"  [green]✓ Validated {label}: all {len(name_values)} records exist[/green]"
    )
    return True


# ═════════════════════════════════════════════════════════════════════════════
#  PHASE 1 — KNOWLEDGE ARTICLES
# ═════════════════════════════════════════════════════════════════════════════

ARTICLES = [
    {
        "title": "Emergency Water Mains Leak Repair - Contoso Utilities",
        "description": "Procedure for responding to reported mains and supply pipe leaks including excavation, repair techniques, and reinstatement",
        "keywords": "water leak, mains repair, pipe burst, excavation, supply pipe, emergency repair, contoso utilities",
        "content": f"""
<p {H1}><strong>Emergency Water Mains Leak Repair</strong></p>
<p {P}>This guide covers the complete procedure for Contoso Utilities field operatives responding to reported water mains and supply pipe leaks. Follow each step carefully and ensure all health and safety requirements are met before commencing work.</p>

<p {H1}><strong>Before You Arrive</strong></p>

<p {H2}><strong>1. Pre-Attendance Checks</strong></p>
<ul {UL}>
<li {LI}>Review the work order details — location, reported symptoms, customer contact information</li>
<li {LI}>Check for known infrastructure in the area (asbestos cement pipes, lead connections)</li>
<li {LI}>Ensure vehicle is stocked: repair clamps, MDPE pipe, fittings, PPE, traffic management equipment</li>
<li {LI}>Confirm NRSWA (Street Works) permit if excavation is on the public highway</li>
</ul>

<p {H2}><strong>2. PPE Requirements</strong></p>
<ul {UL}>
<li {LI}>Hi-visibility jacket/trousers (EN ISO 20471 Class 2 minimum)</li>
<li {LI}>Safety boots with steel toe and midsole protection</li>
<li {LI}>Hard hat if working near plant or excavation</li>
<li {LI}>Gloves — waterproof and cut-resistant</li>
<li {LI}>Eye protection for cutting/grinding operations</li>
</ul>

<p {H1}><strong>On-Site Procedure</strong></p>

<p {H2}><strong>Step 1 — Site Assessment &amp; Traffic Management</strong></p>
<p {P}>On arrival, assess the leak location and severity. Set up appropriate traffic management (Chapter 8 signage for highway works). Identify the pipe route using service plans and CAT scanner. Mark the excavation area and check for other buried services (gas, electric, telecoms).</p>

<p {H2}><strong>Step 2 — Isolate Water Supply</strong></p>
<p {P}>Locate the nearest upstream and downstream stop valves. Operate valves to isolate the affected section. For supply pipe leaks, use the boundary stop tap. Notify affected customers of temporary supply interruption via door cards or phone.</p>

<p {H2}><strong>Step 3 — Excavate to Expose Pipe</strong></p>
<p {P}>Excavate carefully using hand tools within 500mm of known services. Machine excavation is permitted for bulk removal outside the exclusion zone. Support trench sides if depth exceeds 1.2m. Keep spoil at least 1m from the trench edge.</p>

<p {H2}><strong>Step 4 — Repair or Replace Pipe Section</strong></p>
<p {P}>Assess the damage and select the appropriate repair method:</p>
<ul {UL}>
<li {LI}><strong>Repair clamp:</strong> For small splits or pinholes on iron or PE pipe</li>
<li {LI}><strong>Slip coupling:</strong> For clean breaks where pipe ends are accessible</li>
<li {LI}><strong>Cut and replace:</strong> For severely corroded sections — use MDPE with electrofusion or mechanical fittings</li>
<li {LI}><strong>Lead to PE conversion:</strong> If the leak is on a lead supply pipe, replace the full length with 25mm MDPE</li>
</ul>

<p {H2}><strong>Step 5 — Pressure Test &amp; Flush</strong></p>
<p {P}>Slowly restore supply by opening the downstream valve first, then upstream. Check the repair for leaks under pressure. Flush the main by opening a hydrant or tap downstream until water runs clear. Take a chlorine residual reading — must be ≥0.2 mg/l before restoring customer supply.</p>

<p {H2}><strong>Step 6 — Reinstate &amp; Customer Notification</strong></p>
<p {P}>Backfill the excavation in layers, compacting each layer. Apply temporary reinstatement (cold-lay tarmac for carriageway, paving slabs for footpath). Record GPS coordinates of the repair. Notify customers that supply is restored. Leave a door card with contact details if customer is not home.</p>

<p {H1}><strong>Troubleshooting</strong></p>
<ul {UL}>
<li {LI}><strong>Cannot isolate:</strong> If stop valves are seized, use a squeeze-off tool on PE pipe (maximum 2 hours)</li>
<li {LI}><strong>Contamination risk:</strong> If the trench fills with sewage or surface water, flush extensively and take bacteriological samples</li>
<li {LI}><strong>Asbestos cement pipe:</strong> Do NOT cut with power tools. Use hand snap tool and follow asbestos procedures. Bag all waste.</li>
<li {LI}><strong>Persistent air locks:</strong> Open highest point in the network to vent trapped air</li>
</ul>
""",
    },
    {
        "title": "Smart Meter Installation Guide - Contoso Utilities",
        "description": "Step-by-step guide for installing or upgrading residential smart water meters",
        "keywords": "smart meter, water meter, meter installation, AMI, commissioning, meter replacement, contoso utilities",
        "content": f"""
<p {H1}><strong>Residential Smart Meter Installation Guide</strong></p>
<p {P}>Contoso Utilities is upgrading all customer meters to smart meters as part of our 10-year programme. This guide covers the complete installation process for field operatives fitting new smart meters at residential properties.</p>

<p {H1}><strong>Before You Arrive</strong></p>

<p {H2}><strong>1. Pre-Visit Preparation</strong></p>
<ul {UL}>
<li {LI}>Review the work order — check if this is a new installation or meter swap</li>
<li {LI}>Confirm meter type and size required (typically 15mm for domestic properties)</li>
<li {LI}>Check whether the property currently has a meter or is on unmetered supply</li>
<li {LI}>Ensure smart meter stock, tools, and mobile device are ready</li>
<li {LI}>Check for any access notes (locked gate, aggressive dog, vulnerable customer)</li>
</ul>

<p {H2}><strong>2. Equipment Checklist</strong></p>
<ul {UL}>
<li {LI}>Smart water meter unit (correct size)</li>
<li {LI}>Meter box lid (replacement if damaged)</li>
<li {LI}>Fitting kit: washers, O-rings, PTFE tape, compression fittings</li>
<li {LI}>Meter key and stop tap key</li>
<li {LI}>Mobile device with commissioning app</li>
<li {LI}>Customer welcome pack and literature</li>
</ul>

<p {H1}><strong>Installation Procedure</strong></p>

<p {H2}><strong>Step 1 — Locate Meter Chamber &amp; Stop Tap</strong></p>
<p {P}>Locate the existing meter box or external stop tap. Meter boxes are typically at the property boundary near the front gate or path. Lift the lid carefully and assess the condition of the chamber, pipework, and existing meter. If the chamber is flooded, pump out before working.</p>

<p {H2}><strong>Step 2 — Remove Existing Meter</strong></p>
<p {P}>Record the final reading from the old meter (photograph it for records). Turn off the supply at the boundary stop tap. Disconnect the old meter noting the flow direction. Inspect the pipe ends for corrosion or damage — clean or cut back as needed.</p>

<p {H2}><strong>Step 3 — Install Smart Meter Unit</strong></p>
<p {P}>Fit the new smart meter ensuring correct flow direction (arrow on body). Use new washers and fittings — never reuse old washers. Hand-tighten connections then use a spanner for a quarter turn. Do not over-tighten as this can crack plastic fittings. Ensure the smart module (antenna) is oriented upward for best signal.</p>

<p {H2}><strong>Step 4 — Commission &amp; Signal Test</strong></p>
<p {P}>Turn on the supply slowly and check all connections for leaks. Open the commissioning app on your mobile device and scan the meter barcode. Verify the meter ID matches the work order. Run the signal strength test — minimum 3 bars required for reliable daily reads. If signal is weak, try repositioning the antenna or fitting a signal booster.</p>

<p {H2}><strong>Step 5 — Verify Readings &amp; Leak Check</strong></p>
<p {P}>Compare the initial smart meter reading with zero. Run water inside the property (ask customer to open a tap) and confirm the meter registers flow. Stop the tap and verify the meter stops — if it continues to register, there may be an existing leak on the customer's pipework.</p>

<p {H2}><strong>Step 6 — Customer Handover</strong></p>
<p {P}>Explain the smart meter to the customer:</p>
<ul {UL}>
<li {LI}>Readings are collected automatically — no more estimated bills</li>
<li {LI}>They can view their water usage online or via the Contoso Utilities app</li>
<li {LI}>Smart data helps us detect leaks faster, potentially saving them money</li>
<li {LI}>Leave the welcome pack with FAQs and contact details</li>
<li {LI}>If the customer is not home, post the welcome pack through the letterbox</li>
</ul>

<p {H1}><strong>Troubleshooting</strong></p>
<ul {UL}>
<li {LI}><strong>Seized stop tap:</strong> Use penetrating oil and allow 10 minutes before re-attempting. If still seized, raise a follow-up job for stop tap replacement.</li>
<li {LI}><strong>No signal:</strong> Check antenna orientation. Ensure lid is not metal (replace with plastic if needed). Try alternative meter position within chamber.</li>
<li {LI}><strong>Leak at connections:</strong> Undo, check washer seating, re-tighten. If pipe ends are corroded, cut back and use new compression fittings.</li>
<li {LI}><strong>Customer refuses:</strong> Do not force. Record the refusal in the app, leave literature, and mark work order as unable to complete.</li>
</ul>
""",
    },
    {
        "title": "Sewer Blockage Investigation and Clearance - Contoso Utilities",
        "description": "Procedure for investigating and clearing blockages on the public sewer network",
        "keywords": "sewer blockage, drain clearance, jetting, CCTV survey, blocked drain, wastewater, contoso utilities",
        "content": f"""
<p {H1}><strong>Sewer Blockage Investigation &amp; Clearance</strong></p>
<p {P}>This guide covers the procedure for Contoso Utilities drainage operatives responding to reports of sewer blockages on the public network. Blockages can cause flooding and pollution and must be cleared promptly.</p>

<p {H1}><strong>Before You Arrive</strong></p>

<p {H2}><strong>1. Pre-Attendance Checks</strong></p>
<ul {UL}>
<li {LI}>Review the work order — location, symptoms reported, whether it is internal or external flooding</li>
<li {LI}>Check sewer records for pipe material, diameter, depth, and any known issues</li>
<li {LI}>Ensure jetting unit is serviceable, CCTV van is equipped, and PPE is available</li>
<li {LI}>Check for confined space requirements (deep manholes, pumping stations)</li>
</ul>

<p {H2}><strong>2. PPE Requirements</strong></p>
<ul {UL}>
<li {LI}>Waterproof overalls and wellington boots</li>
<li {LI}>Chemical-resistant gloves (minimum nitrile)</li>
<li {LI}>Eye protection — splash risk from sewage</li>
<li {LI}>Respiratory protection if working in confined spaces</li>
<li {LI}>Hepatitis A and tetanus vaccinations must be current</li>
</ul>

<p {H1}><strong>On-Site Procedure</strong></p>

<p {H2}><strong>Step 1 — Site Assessment &amp; Blockage Location</strong></p>
<p {P}>Interview the customer about symptoms (slow drainage, gurgling, sewage backing up). Lift manhole covers upstream and downstream of the reported location. Identify which section is blocked by finding the manhole where flow stops. Check neighbours if multiple properties are affected.</p>

<p {H2}><strong>Step 2 — CCTV Drain Survey</strong></p>
<p {P}>Deploy the CCTV crawler or push-rod camera into the sewer from the nearest accessible manhole. Record the survey noting pipe condition, blockage type (fat/grease, roots, debris, collapse), and exact distance from the manhole. Save footage to the job record.</p>

<p {H2}><strong>Step 3 — High-Pressure Jetting</strong></p>
<p {P}>Position the jetting unit at the upstream manhole. Feed the hose downstream towards the blockage. Use appropriate nozzle for the blockage type (penetrating nozzle for fat, cutting nozzle for roots). Gradually increase pressure. Flush debris downstream to the next manhole and remove from the system. Take care not to damage pipe joints.</p>

<p {H2}><strong>Step 4 — Post-Clearance CCTV &amp; Report</strong></p>
<p {P}>Run a second CCTV survey to confirm the blockage is fully cleared. Record pipe condition and flag any structural defects (cracks, displaced joints, root ingress, deformation) for future rehabilitation. Update the work order with findings and recommendations. If the blockage was on the customer's private pipework, advise them of their responsibility.</p>

<p {H1}><strong>Troubleshooting</strong></p>
<ul {UL}>
<li {LI}><strong>Blockage will not clear:</strong> Try a larger nozzle or higher pressure. If still blocked, it may be a collapse — arrange a CCTV survey from both directions to assess.</li>
<li {LI}><strong>Root ingress:</strong> Use root-cutting nozzle. If roots are severe, raise a rehabilitation job for relining or replacement.</li>
<li {LI}><strong>Fat/grease:</strong> Use hot water jetting if available. Advise customer on proper fat disposal (do not pour down drains).</li>
<li {LI}><strong>Pollution risk:</strong> If sewage has entered a watercourse, notify the Environment Agency immediately and your supervisor. Set up containment if possible.</li>
</ul>
""",
    },
    {
        "title": "Water Quality Investigation Procedures - Contoso Utilities",
        "description": "Guide for investigating customer reports of discoloured water, taste or smell issues, and low pressure",
        "keywords": "water quality, discoloured water, water sampling, pressure test, taste smell, turbidity, contoso utilities",
        "content": f"""
<p {H1}><strong>Water Quality Investigation Procedures</strong></p>
<p {P}>This guide covers the procedure for Contoso Utilities field operatives investigating customer complaints about water quality, including discolouration, unusual taste or smell, and low pressure. Prompt investigation protects public health and customer confidence.</p>

<p {H1}><strong>Before You Arrive</strong></p>

<p {H2}><strong>1. Pre-Visit Preparation</strong></p>
<ul {UL}>
<li {LI}>Review the work order — what did the customer report? (colour, taste, smell, pressure)</li>
<li {LI}>Check if there are other complaints in the same area (may indicate a mains issue)</li>
<li {LI}>Check for recent network work (mains repairs, new connections, hydrant use) that could explain the issue</li>
<li {LI}>Ensure sampling kit is complete and within calibration dates</li>
</ul>

<p {H2}><strong>2. Equipment Checklist</strong></p>
<ul {UL}>
<li {LI}>Sterile sample bottles (bacteriological, chemical, metals)</li>
<li {LI}>Portable chlorine and pH meter (calibrated)</li>
<li {LI}>Turbidity meter</li>
<li {LI}>Pressure gauge with adaptor for kitchen tap</li>
<li {LI}>Thermometer</li>
<li {LI}>Sample submission forms and cool box with ice packs</li>
</ul>

<p {H1}><strong>Investigation Procedure</strong></p>

<p {H2}><strong>Step 1 — Customer Interview &amp; Visual Inspection</strong></p>
<p {P}>Speak with the customer to understand the issue. Ask when it started, whether it is constant or intermittent, which taps are affected, and whether neighbours are experiencing the same. Inspect affected taps — run cold kitchen tap, check hot water system, look at internal plumbing for lead or corroded pipework.</p>

<p {H2}><strong>Step 2 — Pressure &amp; Flow Testing</strong></p>
<p {P}>Attach the pressure gauge to the cold kitchen tap (the tap closest to the incoming supply). Record static pressure and flow pressure. Contoso Utilities target is 1.0 bar minimum at the boundary stop tap. If pressure is low, check the stop tap is fully open. Test at the boundary to compare internal vs external pressure.</p>

<p {H2}><strong>Step 3 — Water Sampling &amp; On-Site Testing</strong></p>
<p {P}>Collect samples following the standard protocol:</p>
<ul {UL}>
<li {LI}><strong>First draw:</strong> Run tap for 5 seconds, collect in sterile bottle (tests standing water in pipes)</li>
<li {LI}><strong>Flushed sample:</strong> Run tap for 2 minutes, then collect (tests incoming mains water)</li>
<li {LI}>Record chlorine residual (flushed sample should be ≥0.2 mg/l)</li>
<li {LI}>Record pH (acceptable range 6.5 – 9.5)</li>
<li {LI}>Record turbidity (drinking water standard ≤4 NTU)</li>
<li {LI}>Record temperature</li>
<li {LI}>Note any visible discolouration, particles, or odour</li>
</ul>

<p {H2}><strong>Step 4 — Flushing &amp; Resolution</strong></p>
<p {P}>If discolouration is from sediment disturbance, flush the supply pipe via the customer's outside tap or nearest hydrant. Continue flushing until water runs clear and chlorine residual is ≥0.2 mg/l. If the issue is internal (lead, corroded copper), advise the customer to contact a plumber. Pack samples in the cool box and dispatch to the laboratory within 4 hours.</p>

<p {H1}><strong>Troubleshooting</strong></p>
<ul {UL}>
<li {LI}><strong>Brown/orange water:</strong> Usually iron from disturbed mains sediment. Flush at the nearest hydrant to clear. If persistent, may need mains flushing programme.</li>
<li {LI}><strong>White/cloudy water:</strong> Usually dissolved air — fill a glass and wait 30 seconds. If it clears from the bottom up, it is harmless air. Advise customer.</li>
<li {LI}><strong>Chlorine taste/smell:</strong> Can occur after mains work. Advise customer to fill a jug and leave in fridge for 1 hour — chlorine will dissipate.</li>
<li {LI}><strong>Zero chlorine:</strong> Indicates potential contamination or dead-end main. Escalate immediately to network operations for mains flushing and bacteriological sampling.</li>
<li {LI}><strong>Blue/green water:</strong> Usually from corroded copper pipes. This is an internal plumbing issue — advise customer to contact a plumber.</li>
</ul>
""",
    },
    {
        "title": "Field Operative Health and Safety Guide - Contoso Utilities",
        "description": "Cross-cutting health and safety procedures for all Contoso Utilities field work including PPE, confined spaces, excavation, and lone working",
        "keywords": "health safety, PPE, confined space, excavation safety, lone working, risk assessment, contoso utilities",
        "content": f"""
<p {H1}><strong>Field Operative Health &amp; Safety Guide</strong></p>
<p {P}>All Contoso Utilities field operatives must follow these health and safety procedures on every job. This guide covers the core requirements that apply across all work types — leak repair, meter installation, drainage work, and water quality investigations.</p>

<p {H1}><strong>Personal Protective Equipment (PPE)</strong></p>

<p {H2}><strong>Minimum PPE for All Field Work</strong></p>
<ul {UL}>
<li {LI}><strong>Hi-visibility clothing:</strong> EN ISO 20471 Class 2 minimum at all times when working on or near the highway</li>
<li {LI}><strong>Safety footwear:</strong> Steel toe cap and midsole, ankle support, waterproof</li>
<li {LI}><strong>Gloves:</strong> Appropriate to the task — waterproof for leak work, chemical-resistant for drainage</li>
<li {LI}><strong>Hard hat:</strong> Required near excavations, plant, or overhead hazards</li>
<li {LI}><strong>Eye protection:</strong> Required when cutting, grinding, or risk of splash</li>
</ul>

<p {H2}><strong>Additional PPE by Task</strong></p>
<ul {UL}>
<li {LI}><strong>Drainage work:</strong> Waterproof overalls, nitrile gloves, face shield, RPE for confined spaces</li>
<li {LI}><strong>Excavation:</strong> Hard hat, ear defenders near breakers, dust mask near dry cutting</li>
<li {LI}><strong>Asbestos cement pipe:</strong> Type 5/6 coverall, FFP3 mask, decontamination bag</li>
</ul>

<p {H1}><strong>Excavation Safety</strong></p>

<p {H2}><strong>Before You Dig</strong></p>
<ul {UL}>
<li {LI}>Obtain service plans for the area (gas, electric, telecoms, water, sewer)</li>
<li {LI}>Use a CAT scanner and signal generator to locate buried services</li>
<li {LI}>Hand dig within 500mm of any known service</li>
<li {LI}>Mark the excavation area with spray paint</li>
</ul>

<p {H2}><strong>During Excavation</strong></p>
<ul {UL}>
<li {LI}>Support trench sides if depth exceeds 1.2m (use trench sheets or battering)</li>
<li {LI}>Keep spoil at least 1m from the trench edge</li>
<li {LI}>Provide safe access/egress (ladder within 6m of any point in the trench)</li>
<li {LI}>Never enter an unsupported trench</li>
</ul>

<p {H1}><strong>Confined Space Entry</strong></p>
<p {P}>Manholes, chambers, and pumping stations deeper than 1.2m are classified as confined spaces. Entry requires:</p>
<ul {UL}>
<li {LI}>Valid confined space entry permit (CSEP)</li>
<li {LI}>Atmospheric monitoring — test for O2, H2S, CO, and LEL before entry</li>
<li {LI}>Minimum 2-person team (1 entrant, 1 top-person)</li>
<li {LI}>Rescue plan and rescue equipment available on-site</li>
<li {LI}>Communication maintained at all times</li>
</ul>

<p {H1}><strong>Traffic Management</strong></p>
<p {P}>All roadside work must comply with Chapter 8 of the Traffic Signs Manual. Requirements depend on road type:</p>
<ul {UL}>
<li {LI}><strong>Footpath only:</strong> Cones, barriers, and pedestrian walkway</li>
<li {LI}><strong>Minor road (30mph):</strong> Advance warning signs, cones, traffic light control on single lane</li>
<li {LI}><strong>Major road (40mph+):</strong> Full Chapter 8 layout with lead-in taper, requires qualified traffic management operative</li>
</ul>

<p {H1}><strong>Lone Working</strong></p>
<ul {UL}>
<li {LI}>Complete a lone working risk assessment before starting</li>
<li {LI}>Check in with your supervisor at agreed intervals</li>
<li {LI}>Carry a charged mobile phone and personal alarm</li>
<li {LI}>Do NOT undertake confined space entry, heavy excavation, or work at height alone</li>
<li {LI}>If you feel unsafe at any point, leave the site and report to your supervisor</li>
</ul>

<p {H1}><strong>Incident Reporting</strong></p>
<p {P}>Report all incidents, near-misses, and unsafe conditions immediately via the Contoso Utilities safety app or by calling the 24/7 safety line. Do not continue work if there is an uncontrolled hazard.</p>
""",
    },
]


# ═════════════════════════════════════════════════════════════════════════════
#  PHASE 2 — CHARACTERISTICS
# ═════════════════════════════════════════════════════════════════════════════

CHARACTERISTICS = [
    # (name, type: 1=Skill, 2=Certification)
    ("Water Mains Repair", 1),
    ("Smart Meter Installation", 1),
    ("Drainage & Sewer Operations", 1),
    ("Water Quality Sampling", 1),
    ("CSCS Card (Water)", 2),
    ("Confined Space Entry", 2),
    ("NRSWA Street Works", 2),
]


# ═════════════════════════════════════════════════════════════════════════════
#  PHASE 3 — WORK ORDER TYPES
# ═════════════════════════════════════════════════════════════════════════════

WORK_ORDER_TYPES = [
    "Water Leak Repair",
    "Smart Meter Installation",
    "Sewer Blockage Clearance",
    "Water Quality Investigation",
]


# ═════════════════════════════════════════════════════════════════════════════
#  PHASE 4 — SERVICE TASK TYPES
# ═════════════════════════════════════════════════════════════════════════════

SERVICE_TASKS = [
    # Water Leak Repair (6)
    (
        "Site Assessment & Traffic Management",
        15,
        "Assess leak location, set up barriers and signage, identify pipe route using service plans and CAT scanner",
    ),
    (
        "Isolate Water Supply",
        10,
        "Locate and operate stop valves to isolate the affected pipe section",
    ),
    (
        "Excavate to Expose Pipe",
        30,
        "Hand or machine dig to expose the damaged pipe section, supporting trench sides as required",
    ),
    (
        "Repair or Replace Pipe Section",
        45,
        "Apply repair clamp, slip coupling, or replace pipe section with MDPE",
    ),
    (
        "Pressure Test & Flush",
        15,
        "Restore supply, pressure test the repair, flush until water runs clear with chlorine reading ≥0.2 mg/l",
    ),
    (
        "Reinstate & Customer Notification",
        20,
        "Backfill excavation, apply temporary or permanent reinstatement, notify affected customers",
    ),
    # Smart Meter Installation (6)
    (
        "Locate Meter Chamber & Stop Tap",
        10,
        "Find existing meter box or stop tap, assess access and chamber condition",
    ),
    (
        "Remove Existing Meter",
        10,
        "Record final meter reading, disconnect and remove old meter",
    ),
    (
        "Install Smart Meter Unit",
        15,
        "Fit new smart meter ensuring correct flow direction, use new washers and fittings",
    ),
    (
        "Commission & Signal Test",
        10,
        "Power on smart module, scan barcode in commissioning app, verify network signal strength",
    ),
    (
        "Verify Readings & Leak Check",
        10,
        "Confirm meter registers flow correctly, check for existing leaks on customer pipework",
    ),
    (
        "Customer Handover",
        10,
        "Explain smart meter benefits, assist with app setup, leave customer welcome pack",
    ),
    # Sewer Blockage Clearance (4)
    (
        "Site Assessment & Blockage Location",
        15,
        "Identify affected manholes, interview customer, assess symptoms and blockage location",
    ),
    (
        "CCTV Drain Survey",
        20,
        "Deploy camera to identify blockage type, material, and exact location in the sewer",
    ),
    (
        "High-Pressure Jetting",
        30,
        "Clear blockage using jetting equipment with appropriate nozzle, remove debris",
    ),
    (
        "Post-Clearance CCTV & Report",
        15,
        "Confirm blockage cleared, record pipe condition, note any structural defects for rehabilitation",
    ),
    # Water Quality Investigation (4)
    (
        "Customer Interview & Visual Inspection",
        10,
        "Discuss symptoms with customer, inspect taps, check internal plumbing condition",
    ),
    (
        "Pressure & Flow Testing",
        10,
        "Test pressure at stop tap and kitchen tap, compare to Contoso Utilities minimum standard of 1.0 bar",
    ),
    (
        "Water Sampling & On-Site Testing",
        15,
        "Collect first-draw and flushed samples, test chlorine, pH, and turbidity on site",
    ),
    (
        "Flushing & Resolution",
        15,
        "Flush supply pipe or mains until water runs clear, confirm improvement, dispatch samples to lab",
    ),
]


# ═════════════════════════════════════════════════════════════════════════════
#  PHASE 5 — INCIDENT TYPES (link to WOTs and tasks)
# ═════════════════════════════════════════════════════════════════════════════

INCIDENT_TYPES = [
    {
        "name": "Emergency Mains Leak",
        "duration": 135,
        "description": "Emergency response to a reported water mains or supply pipe leak requiring excavation and repair",
        "wot": "Water Leak Repair",
        "tasks": [
            "Site Assessment & Traffic Management",
            "Isolate Water Supply",
            "Excavate to Expose Pipe",
            "Repair or Replace Pipe Section",
            "Pressure Test & Flush",
            "Reinstate & Customer Notification",
        ],
    },
    {
        "name": "Residential Smart Meter Installation",
        "duration": 65,
        "description": "Install or upgrade a residential water meter to a smart meter with AMI connectivity",
        "wot": "Smart Meter Installation",
        "tasks": [
            "Locate Meter Chamber & Stop Tap",
            "Remove Existing Meter",
            "Install Smart Meter Unit",
            "Commission & Signal Test",
            "Verify Readings & Leak Check",
            "Customer Handover",
        ],
    },
    {
        "name": "Public Sewer Blockage",
        "duration": 80,
        "description": "Investigate and clear a blockage on the public sewer network using CCTV and jetting",
        "wot": "Sewer Blockage Clearance",
        "tasks": [
            "Site Assessment & Blockage Location",
            "CCTV Drain Survey",
            "High-Pressure Jetting",
            "Post-Clearance CCTV & Report",
        ],
    },
    {
        "name": "Water Quality Customer Complaint",
        "duration": 50,
        "description": "Investigate customer report of discoloured water, taste or smell issues, or low pressure",
        "wot": "Water Quality Investigation",
        "tasks": [
            "Customer Interview & Visual Inspection",
            "Pressure & Flow Testing",
            "Water Sampling & On-Site Testing",
            "Flushing & Resolution",
        ],
    },
]


# ═════════════════════════════════════════════════════════════════════════════
#  PHASE 6 — PRODUCTS
# ═════════════════════════════════════════════════════════════════════════════

PRODUCTS = [
    (
        "MDPE Pipe 25mm (per metre)",
        "Medium density polyethylene pipe for supply repairs",
    ),
    ("Pipe Repair Clamp 25mm", "Stainless steel repair clamp for mains or supply pipe"),
    ("Smart Water Meter Unit", "Smart meter with integrated AMI transmitter module"),
    ("Meter Box Lid", "Replacement plastic meter chamber cover"),
    ("CCTV Survey Report", "Completed drain survey report with footage on USB"),
    ("High-Pressure Jetting (per hour)", "Jetting equipment and operator time"),
    ("Water Sample Kit", "Sterile sample bottles and testing reagents"),
    ("Chlorine Test Strips (pack)", "Pack of 50 on-site chlorine residual test strips"),
]


# ═════════════════════════════════════════════════════════════════════════════
#  PHASE 8 — WORK ORDERS
# ═════════════════════════════════════════════════════════════════════════════

WORK_ORDERS = [
    {
        "wot": "Water Leak Repair",
        "incident": "Emergency Mains Leak",
        "priority": 1,  # High
        "description": (
            "Customer Chris Walker at CW Willowbrook Farm reports water bubbling up "
            "in the front field near the main gate. Possible mains leak on the supply "
            "pipe between the boundary and the farmhouse. Access via farm track off "
            "the B3092. Livestock in adjacent fields — close all gates."
        ),
        "articles": [
            "Emergency Water Mains Leak Repair - Contoso Utilities",
            "Field Operative Health and Safety Guide - Contoso Utilities",
        ],
    },
    {
        "wot": "Smart Meter Installation",
        "incident": "Residential Smart Meter Installation",
        "priority": 2,  # Normal
        "description": (
            "Scheduled smart meter installation at CW Willowbrook Farm. Existing "
            "standard meter in chamber at front boundary. Customer Chris Walker has "
            "been notified of the visit. Check signal strength — rural location may "
            "need antenna repositioning."
        ),
        "articles": [
            "Smart Meter Installation Guide - Contoso Utilities",
            "Field Operative Health and Safety Guide - Contoso Utilities",
        ],
    },
    {
        "wot": "Sewer Blockage Clearance",
        "incident": "Public Sewer Blockage",
        "priority": 1,  # High
        "description": (
            "Chris Walker reports sewage backing up into the yard drain at "
            "CW Willowbrook Farm. Neighbouring properties may also be affected. "
            "Suspected blockage on the 225mm public sewer running along the lane. "
            "Access manhole is on the verge opposite the farm entrance."
        ),
        "articles": [
            "Sewer Blockage Investigation and Clearance - Contoso Utilities",
            "Field Operative Health and Safety Guide - Contoso Utilities",
        ],
    },
    {
        "wot": "Water Quality Investigation",
        "incident": "Water Quality Customer Complaint",
        "priority": 2,  # Normal
        "description": (
            "Chris Walker at CW Willowbrook Farm reports brown discoloured water "
            "from the cold kitchen tap since this morning. No work in progress in "
            "the area. Property is on a long dead-end supply pipe. Collect samples "
            "and check for disturbance on the network."
        ),
        "articles": [
            "Water Quality Investigation Procedures - Contoso Utilities",
            "Field Operative Health and Safety Guide - Contoso Utilities",
        ],
    },
]


# ═════════════════════════════════════════════════════════════════════════════
#  PHASE FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════


def phase1_knowledge_articles(client: DataverseClient) -> dict[str, str]:
    """Phase 1: Create and publish 5 knowledge articles."""
    console.print("\n[bold magenta]═══ Phase 1: Knowledge Articles ═══[/bold magenta]")
    article_ids: dict[str, str] = {}

    for article in ARTICLES:
        title = article["title"]
        # Check if already exists
        existing = find_record(client, "knowledgearticles", "title", title)
        if existing:
            console.print(f"  [yellow]Found:[/yellow] {title}")
            article_ids[title] = existing
        else:
            result = client.post(
                "knowledgearticles",
                {
                    "title": title,
                    "description": article["description"],
                    "keywords": article["keywords"],
                    "content": article["content"],
                },
            )
            if result and "@odata.id" in result:
                aid = extract_guid(result["@odata.id"])
                console.print(f"  [green]Created:[/green] {title} ({aid})")
                article_ids[title] = aid
            else:
                raise RuntimeError(f"Failed to create article: {title}")

    # Publish all articles
    console.print("\n  Publishing articles...")
    for title, aid in article_ids.items():
        try:
            # Check current state
            result = client.get(
                f"knowledgearticles({aid})", {"$select": "statecode,statuscode"}
            )
            if result.get("statecode") == 3:
                console.print(f"  [yellow]Already published:[/yellow] {title}")
                continue
            client.patch(f"knowledgearticles({aid})", {"statecode": 3, "statuscode": 7})
            console.print(f"  [green]Published:[/green] {title}")
        except Exception as e:
            console.print(f"  [red]Publish failed for {title}: {e}[/red]")

    # Validate
    console.print("\n  Validating Phase 1...")
    for title, aid in article_ids.items():
        result = client.get(f"knowledgearticles({aid})", {"$select": "statecode,title"})
        state = result.get("statecode")
        if state != 3:
            console.print(
                f"  [red]✗ {title} — statecode={state}, expected 3 (Published)[/red]"
            )
            raise RuntimeError(f"Article not published: {title}")
    console.print(f"  [green]✓ All {len(article_ids)} articles published[/green]")

    return article_ids


def phase2_characteristics(client: DataverseClient) -> dict[str, str]:
    """Phase 2: Create characteristics and assign to Alan Steiner."""
    console.print(
        "\n[bold magenta]═══ Phase 2: Characteristics for Alan Steiner ═══[/bold magenta]"
    )
    char_ids: dict[str, str] = {}

    for name, char_type in CHARACTERISTICS:
        cid = find_or_create(
            client, "characteristics", "name", name, {"characteristictype": char_type}
        )
        char_ids[name] = cid

    # Assign to Alan Steiner
    console.print(f"\n  Assigning to Alan Steiner ({ALAN_STEINER_RESOURCE_ID})...")
    for name, cid in char_ids.items():
        try:
            # Check if already assigned
            params = {
                "$filter": f"_resource_value eq {ALAN_STEINER_RESOURCE_ID} and _characteristic_value eq {cid}",
                "$top": "1",
            }
            result = client.get("bookableresourcecharacteristics", params)
            if result.get("value"):
                console.print(f"  [yellow]Already assigned:[/yellow] {name}")
                continue

            client.post(
                "bookableresourcecharacteristics",
                {
                    "Resource@odata.bind": f"/bookableresources({ALAN_STEINER_RESOURCE_ID})",
                    "Characteristic@odata.bind": f"/characteristics({cid})",
                },
            )
            console.print(f"  [green]Assigned:[/green] {name}")
        except Exception as e:
            if "duplicate" in str(e).lower() or "already" in str(e).lower():
                console.print(f"  [yellow]Already assigned:[/yellow] {name}")
            else:
                console.print(f"  [red]Error assigning {name}: {e}[/red]")

    # Validate
    console.print("\n  Validating Phase 2...")
    result = client.get(
        "bookableresourcecharacteristics",
        {
            "$filter": f"_resource_value eq {ALAN_STEINER_RESOURCE_ID}",
            "$select": "bookableresourcecharacteristicid",
        },
    )
    count = len(result.get("value", []))
    expected = len(CHARACTERISTICS)
    # Alan may have pre-existing characteristics too, so check >= expected
    if count >= expected:
        console.print(
            f"  [green]✓ Alan Steiner has {count} characteristics (≥{expected} required)[/green]"
        )
    else:
        console.print(
            f"  [yellow]⚠ Alan Steiner has {count} characteristics, expected ≥{expected}[/yellow]"
        )

    return char_ids


def phase3_work_order_types(client: DataverseClient) -> dict[str, str]:
    """Phase 3: Create 4 Work Order Types."""
    console.print("\n[bold magenta]═══ Phase 3: Work Order Types ═══[/bold magenta]")
    wot_ids: dict[str, str] = {}

    for name in WORK_ORDER_TYPES:
        wot_ids[name] = find_or_create(
            client,
            "msdyn_workordertypes",
            "msdyn_name",
            name,
            {"msdyn_incidentrequired": True, "msdyn_taxable": False},
        )

    # Validate
    console.print("\n  Validating Phase 3...")
    ok = validate_count(
        client,
        "msdyn_workordertypes",
        "msdyn_name",
        WORK_ORDER_TYPES,
        "Work Order Types",
    )
    if not ok:
        raise RuntimeError("Work Order Types validation failed")

    return wot_ids


def phase4_service_tasks(client: DataverseClient) -> dict[str, str]:
    """Phase 4: Create 20 Service Task Types."""
    console.print("\n[bold magenta]═══ Phase 4: Service Task Types ═══[/bold magenta]")
    task_ids: dict[str, str] = {}

    for name, duration, description in SERVICE_TASKS:
        task_ids[name] = find_or_create(
            client,
            "msdyn_servicetasktypes",
            "msdyn_name",
            name,
            {"msdyn_estimatedduration": duration, "msdyn_description": description},
        )

    # Validate
    console.print("\n  Validating Phase 4...")
    task_names = [t[0] for t in SERVICE_TASKS]
    ok = validate_count(
        client, "msdyn_servicetasktypes", "msdyn_name", task_names, "Service Task Types"
    )
    if not ok:
        raise RuntimeError("Service Task Types validation failed")

    return task_ids


def phase5_incident_types(
    client: DataverseClient,
    wot_ids: dict[str, str],
    task_ids: dict[str, str],
) -> dict[str, str]:
    """Phase 5: Create 4 Incident Types and link service tasks."""
    console.print("\n[bold magenta]═══ Phase 5: Incident Types ═══[/bold magenta]")
    incident_ids: dict[str, str] = {}

    for it in INCIDENT_TYPES:
        name = it["name"]
        wot_name = it["wot"]
        wot_id = wot_ids[wot_name]

        incident_ids[name] = find_or_create(
            client,
            "msdyn_incidenttypes",
            "msdyn_name",
            name,
            {
                "msdyn_estimatedduration": it["duration"],
                "msdyn_description": it["description"],
                "msdyn_defaultworkordertype@odata.bind": f"/msdyn_workordertypes({wot_id})",
            },
        )

    # Link service tasks
    console.print("\n  Linking Service Tasks to Incident Types...")
    for it in INCIDENT_TYPES:
        incident_id = incident_ids[it["name"]]
        for order, task_name in enumerate(it["tasks"], start=1):
            task_id = task_ids[task_name]
            link_name = f"{it['name']} - {task_name}"
            find_or_create(
                client,
                "msdyn_incidenttypeservicetasks",
                "msdyn_name",
                link_name,
                {
                    "msdyn_incidenttype@odata.bind": f"/msdyn_incidenttypes({incident_id})",
                    "msdyn_tasktype@odata.bind": f"/msdyn_servicetasktypes({task_id})",
                    "msdyn_lineorder": order,
                },
            )

    # Validate
    console.print("\n  Validating Phase 5...")
    for it in INCIDENT_TYPES:
        incident_id = incident_ids[it["name"]]
        result = client.get(
            "msdyn_incidenttypeservicetasks",
            {
                "$filter": f"_msdyn_incidenttype_value eq {incident_id}",
                "$select": "msdyn_name,msdyn_lineorder",
                "$orderby": "msdyn_lineorder asc",
            },
        )
        linked_count = len(result.get("value", []))
        expected = len(it["tasks"])
        if linked_count >= expected:
            console.print(
                f"  [green]✓ {it['name']}: {linked_count} tasks linked[/green]"
            )
        else:
            console.print(
                f"  [red]✗ {it['name']}: {linked_count} tasks, expected {expected}[/red]"
            )
            raise RuntimeError(f"Incident type {it['name']} has wrong task count")

    return incident_ids


def phase6_products(client: DataverseClient) -> dict[str, str]:
    """Phase 6: Create 8 products."""
    console.print("\n[bold magenta]═══ Phase 6: Products ═══[/bold magenta]")
    product_ids: dict[str, str] = {}

    # Get unit group and unit
    result = client.get(
        "uomschedules",
        {"$filter": "name eq 'Default Unit'", "$select": "uomscheduleid", "$top": "1"},
    )
    unit_groups = result.get("value", [])
    if unit_groups:
        ug_id = unit_groups[0]["uomscheduleid"]
    else:
        res = client.post("uomschedules", {"name": "Default Unit"})
        ug_id = extract_guid(res["@odata.id"])

    result = client.get(
        "uoms",
        {
            "$filter": f"name eq 'Primary Unit' and _uomscheduleid_value eq {ug_id}",
            "$select": "uomid",
            "$top": "1",
        },
    )
    units = result.get("value", [])
    if units:
        uom_id = units[0]["uomid"]
    else:
        # Try just "Each"
        result = client.get(
            "uoms", {"$filter": "name eq 'Each'", "$select": "uomid", "$top": "1"}
        )
        units = result.get("value", [])
        if units:
            uom_id = units[0]["uomid"]
        else:
            res = client.post(
                "uoms",
                {
                    "name": "Each",
                    "uomscheduleid@odata.bind": f"/uomschedules({ug_id})",
                    "quantity": 1,
                },
            )
            uom_id = extract_guid(res["@odata.id"])

    console.print(f"  [dim]Unit group: {ug_id}, UoM: {uom_id}[/dim]")

    for name, description in PRODUCTS:
        product_ids[name] = find_or_create(
            client,
            "products",
            "name",
            name,
            {
                "description": description,
                "productnumber": name.replace(" ", "-")
                .replace("(", "")
                .replace(")", "")[:30],
                "quantitydecimal": 0,
                "defaultuomscheduleid@odata.bind": f"/uomschedules({ug_id})",
                "defaultuomid@odata.bind": f"/uoms({uom_id})",
            },
        )

    # Validate
    console.print("\n  Validating Phase 6...")
    product_names = [p[0] for p in PRODUCTS]
    ok = validate_count(client, "products", "name", product_names, "Products")
    if not ok:
        console.print("  [yellow]⚠ Some products may need manual review[/yellow]")

    return product_ids


def phase7_lookup_existing(client: DataverseClient) -> dict[str, str]:
    """Phase 7: Look up existing CW Willowbrook Farm and Chris Walker."""
    console.print(
        "\n[bold magenta]═══ Phase 7: Lookup Existing Records ═══[/bold magenta]"
    )
    ids: dict[str, str] = {}

    # CW Willowbrook Farm
    console.print("  Looking up CW Willowbrook Farm...")
    account_id = find_record(client, "accounts", "name", "Willowbrook")
    if not account_id:
        console.print("  [red]✗ CW Willowbrook Farm NOT FOUND — halting[/red]")
        raise RuntimeError("CW Willowbrook Farm account not found in Dataverse")
    console.print(f"  [green]✓ Found CW Willowbrook Farm: {account_id}[/green]")
    ids["account"] = account_id

    # Chris Walker
    console.print("  Looking up Chris Walker...")
    contact_id = find_record(client, "contacts", "fullname", "Chris Walker")
    if not contact_id:
        console.print("  [red]✗ Chris Walker NOT FOUND — halting[/red]")
        raise RuntimeError("Chris Walker contact not found in Dataverse")
    console.print(f"  [green]✓ Found Chris Walker: {contact_id}[/green]")
    ids["contact"] = contact_id

    return ids


def phase8_work_orders(
    client: DataverseClient,
    wot_ids: dict[str, str],
    incident_ids: dict[str, str],
    existing_ids: dict[str, str],
    article_ids: dict[str, str],
) -> dict[str, str]:
    """Phase 8: Create 4 work orders and attach knowledge articles."""
    console.print("\n[bold magenta]═══ Phase 8: Work Orders ═══[/bold magenta]")
    wo_ids: dict[str, str] = {}

    account_id = existing_ids["account"]
    contact_id = existing_ids["contact"]

    for wo_def in WORK_ORDERS:
        wot_name = wo_def["wot"]
        wot_id = wot_ids[wot_name]
        incident_name = wo_def["incident"]
        incident_id = incident_ids[incident_name]

        # Build work order payload
        wo_data = {
            "msdyn_serviceaccount@odata.bind": f"/accounts({account_id})",
            "msdyn_reportedbycontact@odata.bind": f"/contacts({contact_id})",
            "msdyn_workordertype@odata.bind": f"/msdyn_workordertypes({wot_id})",
            "msdyn_primaryincidenttype@odata.bind": f"/msdyn_incidenttypes({incident_id})",
            "msdyn_primaryincidentdescription": wo_def["description"],
            "msdyn_workordersummary": wo_def["description"],
            "msdyn_systemstatus": 690970000,  # Unscheduled
            "prioritycode": wo_def["priority"],
        }

        # Check if similar WO already exists before creating
        wo_label = f"WO - {incident_name}"
        result = client.post("msdyn_workorders", wo_data)
        if result and "@odata.id" in result:
            wo_id = extract_guid(result["@odata.id"])
            console.print(f"  [green]Created WO:[/green] {incident_name} ({wo_id})")
            wo_ids[incident_name] = wo_id
        else:
            console.print(f"  [red]Failed to create WO for {incident_name}[/red]")
            continue

        # Attach knowledge articles
        for article_title in wo_def["articles"]:
            if article_title in article_ids:
                art_id = article_ids[article_title]
                ref_endpoint = f"knowledgearticles({art_id})/msdyn_msdyn_workorder_knowledgearticle/$ref"
                ref_target = f"msdyn_workorders({wo_id})"
                success = client.post_ref(ref_endpoint, ref_target)
                if success:
                    short = article_title.split(" - ")[0]
                    console.print(f"    [green]Linked:[/green] {short}")
                else:
                    console.print(
                        f"    [yellow]Link may have failed for: {article_title}[/yellow]"
                    )

    # Validate
    console.print("\n  Validating Phase 8...")
    for incident_name, wo_id in wo_ids.items():
        # Check service tasks populated
        result = client.get(
            "msdyn_workorderservicetasks",
            {
                "$filter": f"_msdyn_workorder_value eq {wo_id}",
                "$select": "msdyn_name",
            },
        )
        task_count = len(result.get("value", []))
        console.print(
            f"  [green]✓ {incident_name}:[/green] {task_count} service tasks on work order"
        )

    return wo_ids


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═════════════════════════════════════════════════════════════════════════════


def main():
    console.print(
        "\n[bold magenta]═══════════════════════════════════════════════════════════[/bold magenta]"
    )
    console.print(
        "[bold magenta]  Contoso Utilities — Water Field Service Demo Setup[/bold magenta]"
    )
    console.print(
        "[bold magenta]═══════════════════════════════════════════════════════════[/bold magenta]"
    )

    client = DataverseClient()
    console.print(f"\n  [dim]Connecting to: {client.base_url}[/dim]")

    try:
        client.get("WhoAmI")
        console.print("  [green]✓ Connected to Dataverse[/green]")
    except Exception as e:
        console.print(f"  [red]✗ Connection failed: {e}[/red]")
        sys.exit(1)

    # Execute all phases sequentially — each validates before the next
    article_ids = phase1_knowledge_articles(client)
    char_ids = phase2_characteristics(client)
    wot_ids = phase3_work_order_types(client)
    task_ids = phase4_service_tasks(client)
    incident_ids = phase5_incident_types(client, wot_ids, task_ids)
    product_ids = phase6_products(client)
    existing_ids = phase7_lookup_existing(client)
    wo_ids = phase8_work_orders(
        client, wot_ids, incident_ids, existing_ids, article_ids
    )

    # ─── Summary ──────────────────────────────────────────────────────────
    console.print(
        "\n[bold magenta]═══════════════════════════════════════════════════════════[/bold magenta]"
    )
    console.print("[bold green]  ✓ Demo Setup Complete![/bold green]")
    console.print(
        "[bold magenta]═══════════════════════════════════════════════════════════[/bold magenta]"
    )

    table = Table(title="Contoso Utilities Demo Summary")
    table.add_column("Entity", style="cyan")
    table.add_column("Count", justify="right")
    table.add_row("Knowledge Articles (Published)", str(len(article_ids)))
    table.add_row("Characteristics (Alan Steiner)", str(len(char_ids)))
    table.add_row("Work Order Types", str(len(wot_ids)))
    table.add_row("Service Task Types", str(len(task_ids)))
    table.add_row("Incident Types", str(len(incident_ids)))
    table.add_row("Products", str(len(product_ids)))
    table.add_row("Work Orders", str(len(wo_ids)))
    console.print(table)

    console.print("\n[bold]Demo Records:[/bold]")
    console.print("  Service Account: CW Willowbrook Farm (existing)")
    console.print("  Contact: Chris Walker (existing)")
    console.print("  Technician: Alan Steiner")
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  1. Open D365 Field Service → Schedule Board")
    console.print("  2. Find the 4 unscheduled work orders for CW Willowbrook Farm")
    console.print("  3. Schedule to Alan Steiner")
    console.print("  4. Open mobile app and walk through service tasks")
    console.print("  5. Knowledge articles are linked to each work order\n")


if __name__ == "__main__":
    main()
