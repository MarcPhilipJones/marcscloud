"""Phase 1: Create and publish 5 Knowledge Articles for Contoso Utilities.

Usage:
    cd field-service-wessex
    python scripts/phase1_knowledge_articles.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from helpers import (
    H1,
    H2,
    LI,
    UL,
    P,
    console,
    extract_guid,
    find_record,
    get_client,
    save_state,
)

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


def main():
    console.print("\n[bold magenta]═══ Phase 1: Knowledge Articles ═══[/bold magenta]")
    client = get_client()

    article_ids: dict[str, str] = {}

    # Create articles
    for article in ARTICLES:
        title = article["title"]
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
    all_ok = True
    for title, aid in article_ids.items():
        result = client.get(f"knowledgearticles({aid})", {"$select": "statecode,title"})
        state = result.get("statecode")
        if state != 3:
            console.print(f"  [red]✗ {title} — statecode={state}, expected 3[/red]")
            all_ok = False
        else:
            console.print(f"  [green]✓ {title} — Published[/green]")

    if not all_ok:
        console.print("  [red]✗ PHASE 1 VALIDATION FAILED[/red]")
        sys.exit(1)

    console.print(
        f"\n  [green]✓ Phase 1 complete: {len(article_ids)} articles published[/green]"
    )
    save_state("phase1_articles", article_ids)


if __name__ == "__main__":
    main()
