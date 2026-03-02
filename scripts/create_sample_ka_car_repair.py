"""
Create 5 sample Knowledge Articles about car repair in Dataverse.
All titles prefixed with "SAMPLE ".
Uses inline HTML styles (Dataverse strips <style> blocks).
Publishes only the latest version of each article.
"""

import sys
import os

os.chdir(r'c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\mcp-dataverse-server')
sys.path.insert(0, 'src')

import httpx
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings

# Style constants - inline styles required (Dataverse strips <style> blocks)
H1 = 'style="font-family: Segoe UI, sans-serif; font-size: 18pt; color: #2c3e50; margin-bottom: 15px;"'
H2 = 'style="font-family: Segoe UI, sans-serif; font-size: 14pt; color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"'
P = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"'
LI = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; margin-bottom: 8px;"'
UL = 'style="margin: 0 0 15px 20px; padding: 0;"'
STRONG = 'style="color: #c0392b;"'
NOTE = 'style="font-family: Segoe UI, sans-serif; font-size: 11pt; background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 10px 15px; margin: 15px 0;"'
TIP = 'style="font-family: Segoe UI, sans-serif; font-size: 11pt; background-color: #d4edda; border-left: 4px solid #28a745; padding: 10px 15px; margin: 15px 0;"'

ARTICLES = [
    {
        "title": "SAMPLE Diagnosing and Replacing Brake Pads",
        "description": "Step-by-step guide for inspecting worn brake pads and replacing them safely",
        "keywords": "brakes, brake pads, disc brakes, squealing, grinding, brake replacement, safety",
        "content": f"""
<h1 {H1}>Diagnosing and Replacing Brake Pads</h1>
<p {P}>Brake pads are a critical safety component that wear down over time. This guide covers how to identify worn pads and replace them correctly.</p>

<h2 {H2}>Symptoms of Worn Brake Pads</h2>
<ul {UL}>
    <li {LI}><strong {STRONG}>Squealing or screeching</strong> noise when braking - indicates the wear indicator is contacting the rotor</li>
    <li {LI}><strong {STRONG}>Grinding sound</strong> - pad material is completely worn; rotor damage is likely</li>
    <li {LI}><strong {STRONG}>Longer stopping distances</strong> - reduced friction material means less braking force</li>
    <li {LI}><strong {STRONG}>Brake pedal vibration</strong> - may indicate uneven pad wear or warped rotors</li>
    <li {LI}><strong {STRONG}>Warning light</strong> - vehicles with brake pad sensors will illuminate the dashboard light</li>
</ul>

<h2 {H2}>Tools Required</h2>
<ul {UL}>
    <li {LI}>Jack and axle stands</li>
    <li {LI}>Wheel brace / lug wrench</li>
    <li {LI}>Socket set (typically 14mm-17mm for caliper bolts)</li>
    <li {LI}>C-clamp or brake piston wind-back tool</li>
    <li {LI}>Brake cleaner spray</li>
    <li {LI}>Copper grease / anti-seize compound</li>
</ul>

<h2 {H2}>Replacement Procedure</h2>
<ol {UL}>
    <li {LI}>Safely raise the vehicle and secure on axle stands. Remove the wheel.</li>
    <li {LI}>Remove the caliper mounting bolts (usually 2 bolts on the rear of the caliper).</li>
    <li {LI}>Slide the caliper off the rotor and support it with wire - never let it hang by the brake hose.</li>
    <li {LI}>Remove the old pads from the caliper bracket.</li>
    <li {LI}>Use a C-clamp to push the piston back into the caliper body. Open the brake fluid reservoir cap first to prevent pressure build-up.</li>
    <li {LI}>Apply copper grease to the back of the new pads and the contact points on the bracket.</li>
    <li {LI}>Install new pads into the bracket. Ensure any wear indicator is positioned correctly (usually on the inner pad).</li>
    <li {LI}>Refit the caliper and torque bolts to manufacturer specification.</li>
    <li {LI}>Refit the wheel, lower the vehicle, and pump the brake pedal several times before driving.</li>
</ol>

<div {NOTE}><strong>Warning:</strong> Always replace brake pads in axle pairs (both front or both rear). Never replace just one side.</div>

<div {TIP}><strong>Tip:</strong> New pads require a bedding-in period. Avoid heavy braking for the first 100 miles.</div>
"""
    },
    {
        "title": "SAMPLE Engine Oil Change - Complete Guide",
        "description": "How to perform a full engine oil and filter change for most passenger vehicles",
        "keywords": "oil change, engine oil, oil filter, maintenance, service, drain plug, dipstick",
        "content": f"""
<h1 {H1}>Engine Oil Change - Complete Guide</h1>
<p {P}>Regular oil changes are the single most important maintenance task for engine longevity. Most vehicles require an oil change every 10,000-15,000 miles or annually, whichever comes first.</p>

<h2 {H2}>Before You Start</h2>
<ul {UL}>
    <li {LI}>Check your owner's manual for the correct oil specification (e.g., 5W-30, 0W-20) and capacity</li>
    <li {LI}>Purchase the correct oil filter for your vehicle (cross-reference part numbers)</li>
    <li {LI}>Warm the engine for 5 minutes - warm oil drains more completely</li>
</ul>

<h2 {H2}>Tools and Materials</h2>
<ul {UL}>
    <li {LI}>Correct grade and quantity of engine oil</li>
    <li {LI}>New oil filter</li>
    <li {LI}>New sump plug washer (copper or aluminium)</li>
    <li {LI}>Drain pan (minimum 6 litre capacity)</li>
    <li {LI}>Socket or spanner for drain plug</li>
    <li {LI}>Oil filter wrench</li>
    <li {LI}>Funnel</li>
    <li {LI}>Disposable gloves and rags</li>
</ul>

<h2 {H2}>Step-by-Step Procedure</h2>
<ol {UL}>
    <li {LI}>Position the drain pan under the sump plug. Remove the plug and allow oil to drain fully (10-15 minutes).</li>
    <li {LI}>While draining, remove the old oil filter. Apply a thin film of new oil to the rubber gasket of the new filter.</li>
    <li {LI}>Install the new filter hand-tight, then tighten an additional 3/4 turn.</li>
    <li {LI}>Fit a new sump plug washer and reinstall the drain plug. Torque to specification (typically 25-35 Nm).</li>
    <li {LI}>Fill with new oil through the filler cap. Add approximately 80% of the total capacity first.</li>
    <li {LI}>Start the engine and let it idle for 2 minutes. Check for leaks around the filter and drain plug.</li>
    <li {LI}>Switch off, wait 5 minutes, then check the dipstick. Top up to the maximum mark.</li>
    <li {LI}>Reset the service indicator if applicable (refer to owner's manual).</li>
</ol>

<div {NOTE}><strong>Important:</strong> Dispose of used oil responsibly. Most local recycling centres and motor factors accept used engine oil free of charge.</div>
"""
    },
    {
        "title": "SAMPLE Troubleshooting a Car That Won't Start",
        "description": "Diagnostic flowchart for identifying why a vehicle fails to start, covering battery, starter, fuel and ignition issues",
        "keywords": "won't start, no start, battery, starter motor, ignition, fuel pump, cranking, dead battery",
        "content": f"""
<h1 {H1}>Troubleshooting a Car That Won't Start</h1>
<p {P}>A no-start condition can have many causes. This guide walks through a systematic diagnostic process to identify the fault.</p>

<h2 {H2}>Step 1: What Happens When You Turn the Key?</h2>

<h2 {H2}>Scenario A: Nothing at All (No Lights, No Sound)</h2>
<ul {UL}>
    <li {LI}><strong>Cause:</strong> Dead battery or poor battery connections</li>
    <li {LI}>Check battery terminals for corrosion (white/green deposits). Clean with a wire brush.</li>
    <li {LI}>Test battery voltage with a multimeter - should read 12.4V or above</li>
    <li {LI}>Try a jump start. If the vehicle starts, the battery needs charging or replacing.</li>
</ul>

<h2 {H2}>Scenario B: Lights Work but Engine Won't Crank</h2>
<ul {UL}>
    <li {LI}><strong>Cause:</strong> Starter motor failure or ignition switch fault</li>
    <li {LI}>Listen for a single click when turning the key - this suggests a failed starter solenoid</li>
    <li {LI}>Try tapping the starter motor with a hammer while someone turns the key (temporary fix for a stuck motor)</li>
    <li {LI}>Check the starter relay and fuse</li>
</ul>

<h2 {H2}>Scenario C: Engine Cranks but Won't Fire</h2>
<ul {UL}>
    <li {LI}><strong>Check for spark:</strong> Remove a spark plug lead, hold near a ground point, crank the engine. A blue spark confirms ignition is working.</li>
    <li {LI}><strong>Check for fuel:</strong> Listen for the fuel pump priming when you turn the ignition to position II (a brief humming sound from the rear). No sound may indicate a failed fuel pump or blown fuse.</li>
    <li {LI}><strong>Check for compression:</strong> If spark and fuel are present, a compression test may reveal worn piston rings or a blown head gasket.</li>
</ul>

<h2 {H2}>Scenario D: Engine Starts Then Immediately Stalls</h2>
<ul {UL}>
    <li {LI}>Possible immobiliser fault - check the key fob battery</li>
    <li {LI}>Idle control valve may be stuck or dirty</li>
    <li {LI}>Vacuum leak causing lean running condition</li>
</ul>

<div {TIP}><strong>Tip:</strong> An OBD-II scanner can read fault codes from the engine ECU and significantly speed up diagnosis. Basic scanners cost under £20.</div>
"""
    },
    {
        "title": "SAMPLE Replacing a Flat Tyre - Roadside Guide",
        "description": "Safe procedure for changing a flat tyre at the roadside using the vehicle's spare wheel kit",
        "keywords": "flat tyre, puncture, spare wheel, jack, lug nuts, roadside, emergency, tyre change",
        "content": f"""
<h1 {H1}>Replacing a Flat Tyre - Roadside Guide</h1>
<p {P}>A flat tyre can happen at any time. Knowing how to safely change a wheel at the roadside is an essential skill for every driver.</p>

<h2 {H2}>Safety First</h2>
<ul {UL}>
    <li {LI}>Pull over to a firm, flat surface as far from traffic as possible</li>
    <li {LI}>Turn on hazard warning lights immediately</li>
    <li {LI}>Apply the handbrake and engage first gear (manual) or Park (automatic)</li>
    <li {LI}>Place the warning triangle 45 metres behind the vehicle</li>
    <li {LI}>Ensure all passengers are out of the vehicle and away from the roadside</li>
    <li {LI}><strong {STRONG}>Never</strong> change a tyre on a motorway hard shoulder - call for roadside assistance</li>
</ul>

<h2 {H2}>Equipment Check</h2>
<p {P}>Locate the following in your boot (usually under the floor panel):</p>
<ul {UL}>
    <li {LI}>Spare wheel (check it's inflated - a flat spare is useless)</li>
    <li {LI}>Scissor jack or bottle jack</li>
    <li {LI}>Wheel brace / lug wrench</li>
    <li {LI}>Locking wheel nut key (if fitted)</li>
</ul>

<h2 {H2}>Wheel Change Procedure</h2>
<ol {UL}>
    <li {LI}>With the vehicle on the ground, loosen each wheel nut by half a turn (anti-clockwise). Use your body weight on the brace if they're tight.</li>
    <li {LI}>Position the jack under the vehicle's designated jacking point (check the owner's manual - using the wrong point can damage the sills).</li>
    <li {LI}>Raise the vehicle until the flat tyre is approximately 2-3cm off the ground.</li>
    <li {LI}>Remove the wheel nuts completely and pull the flat wheel off.</li>
    <li {LI}>Mount the spare wheel, aligning the bolt holes. Hand-tighten all nuts in a star pattern.</li>
    <li {LI}>Lower the vehicle until the tyre just touches the ground (not fully lowered).</li>
    <li {LI}>Tighten the nuts fully in a star pattern to the correct torque (typically 110-120 Nm for most cars).</li>
    <li {LI}>Lower fully, remove the jack, and check the tyre pressure.</li>
</ol>

<div {NOTE}><strong>Important:</strong> If fitted with a space-saver spare, do not exceed 50mph and drive directly to a tyre fitting centre for a permanent repair or replacement.</div>

<div {TIP}><strong>Tip:</strong> After driving 50 miles, re-check the nut torques to ensure they haven't loosened.</div>
"""
    },
    {
        "title": "SAMPLE Diagnosing Coolant Leaks and Overheating",
        "description": "How to identify and resolve engine cooling system faults including leaks, thermostat failure and head gasket issues",
        "keywords": "overheating, coolant leak, radiator, thermostat, head gasket, water pump, temperature, cooling system",
        "content": f"""
<h1 {H1}>Diagnosing Coolant Leaks and Overheating</h1>
<p {P}>An overheating engine can cause catastrophic damage including warped cylinder heads and blown head gaskets. Early diagnosis of cooling system faults is essential.</p>

<h2 {H2}>Warning Signs</h2>
<ul {UL}>
    <li {LI}>Temperature gauge reading higher than normal or entering the red zone</li>
    <li {LI}>Steam or sweet-smelling vapour from under the bonnet</li>
    <li {LI}>Coolant warning light illuminated</li>
    <li {LI}>Heater blowing cold air (may indicate low coolant level or airlock)</li>
    <li {LI}>Visible coolant puddle under the vehicle (typically green, orange, or pink fluid)</li>
</ul>

<div {NOTE}><strong>Warning:</strong> Never remove the radiator cap or expansion tank cap when the engine is hot. The system is pressurised and boiling coolant will cause serious burns.</div>

<h2 {H2}>Common Causes and Diagnosis</h2>

<h2 {H2}>1. External Coolant Leak</h2>
<ul {UL}>
    <li {LI}><strong>Radiator:</strong> Look for wet patches, white residue, or damaged fins. Common with age and stone damage.</li>
    <li {LI}><strong>Hoses:</strong> Squeeze hoses when cold - they should be firm but flexible. Replace if cracked, swollen, or soft.</li>
    <li {LI}><strong>Water pump:</strong> Check for coolant weeping from the pump weep hole (located on the pump body). A failing bearing may also produce a whining noise.</li>
    <li {LI}><strong>Expansion tank:</strong> Plastic tanks become brittle with age and can crack, especially around the seams.</li>
</ul>

<h2 {H2}>2. Thermostat Failure</h2>
<ul {UL}>
    <li {LI}><strong>Stuck closed:</strong> Engine overheats rapidly, upper radiator hose stays cold (coolant not circulating)</li>
    <li {LI}><strong>Stuck open:</strong> Engine takes a very long time to warm up, heater is lukewarm, fuel economy drops</li>
    <li {LI}>Replacement is straightforward - the thermostat is usually housed where the upper hose meets the engine</li>
</ul>

<h2 {H2}>3. Head Gasket Failure</h2>
<p {P}>The most serious cooling system fault. Signs include:</p>
<ul {UL}>
    <li {LI}>Milky/frothy residue under the oil filler cap (coolant mixing with oil)</li>
    <li {LI}>White smoke from the exhaust that smells sweet (coolant burning in cylinders)</li>
    <li {LI}>Bubbles in the expansion tank when the engine is running (combustion gases entering the cooling system)</li>
    <li {LI}>Rapid coolant loss with no visible external leak</li>
</ul>

<div {TIP}><strong>Tip:</strong> A combustion leak test kit (sniff test) uses chemical fluid that changes colour in the presence of exhaust gases in the coolant. This is the quickest way to confirm a head gasket leak and costs under £15.</div>
"""
    }
]


def main():
    settings = load_settings()
    token_provider = TokenProvider(
        tenant_id=settings.dataverse_tenant_id,
        client_id=settings.dataverse_client_id,
        client_secret=settings.dataverse_client_secret,
        resource=settings.dataverse_base_url
    )
    token = token_provider.get_access_token()
    base_url = settings.dataverse_base_url
    api_version = settings.dataverse_api_version
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'OData-MaxVersion': '4.0',
        'OData-Version': '4.0',
        'Accept': 'application/json'
    }

    state_map = {0: 'Draft', 1: 'Approved', 2: 'Scheduled', 3: 'Published', 4: 'Expired', 5: 'Archived', 6: 'Discarded'}
    created_ids = []

    with httpx.Client(timeout=30.0) as client:
        # Step 1: Create all 5 articles as Draft
        print("=" * 60)
        print("CREATING 5 SAMPLE KNOWLEDGE ARTICLES")
        print("=" * 60)

        for i, article in enumerate(ARTICLES, 1):
            payload = {
                "title": article["title"],
                "description": article["description"],
                "keywords": article["keywords"],
                "content": article["content"]
            }

            url = f"{base_url}/api/data/{api_version}/knowledgearticles"
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()

            # Extract article ID from response headers
            entity_url = resp.headers.get("OData-EntityId", "")
            article_id = entity_url.split("(")[-1].rstrip(")") if entity_url else None

            if not article_id:
                # Fallback: query for it
                params = {
                    "$filter": f"title eq '{article['title']}'",
                    "$select": "knowledgearticleid",
                    "$orderby": "createdon desc",
                    "$top": "1"
                }
                resp2 = client.get(url, headers=headers, params=params)
                resp2.raise_for_status()
                records = resp2.json().get("value", [])
                if records:
                    article_id = records[0]["knowledgearticleid"]

            created_ids.append(article_id)
            print(f"  [{i}/5] Created: {article['title']}")
            print(f"         ID: {article_id}")

        # Step 2: Publish each article (latest version only)
        print()
        print("=" * 60)
        print("PUBLISHING ARTICLES (latest version only)")
        print("=" * 60)

        for i, article_id in enumerate(created_ids, 1):
            # Find the latest version for this article
            params = {
                "$filter": f"knowledgearticleid eq {article_id} or _rootarticleid_value eq {article_id}",
                "$select": "knowledgearticleid,title,statecode,statuscode,islatestversion,majorversionnumber,minorversionnumber,articlepublicnumber",
                "$orderby": "majorversionnumber desc,minorversionnumber desc",
                "$top": "1"
            }
            url = f"{base_url}/api/data/{api_version}/knowledgearticles"
            resp = client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            records = resp.json().get("value", [])

            if not records:
                print(f"  [{i}/5] ERROR: Could not find article {article_id}")
                continue

            latest = records[0]
            latest_id = latest["knowledgearticleid"]

            # Publish via direct status update
            update_url = f"{base_url}/api/data/{api_version}/knowledgearticles({latest_id})"
            resp = client.patch(update_url, headers=headers, json={"statecode": 3, "statuscode": 7})
            resp.raise_for_status()

            # Verify
            resp = client.get(update_url, headers=headers, params={
                "$select": "title,statecode,statuscode,articlepublicnumber,majorversionnumber,minorversionnumber"
            })
            resp.raise_for_status()
            verified = resp.json()
            state = state_map.get(verified["statecode"], "Unknown")

            print(f"  [{i}/5] {verified['title']}")
            print(f"         Article#: {verified.get('articlepublicnumber')} | Version: {verified.get('majorversionnumber')}.{verified.get('minorversionnumber')} | State: {state}")
            print(f"         URL: {base_url}/main.aspx?etn=knowledgearticle&id={latest_id}&pagetype=entityrecord")
            print()

        print("=" * 60)
        print("COMPLETE: 5 articles created and published")
        print("=" * 60)


if __name__ == "__main__":
    main()
