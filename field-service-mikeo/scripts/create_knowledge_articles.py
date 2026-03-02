"""Create Knowledge Articles for Prison Field Service Demo.

Creates two knowledge articles with inline-styled HTML (Dataverse-compatible):
1. Network Printer Installation in Secure Facilities
2. Surface-Mounted Cable Trunking Installation
"""

import sys
import os

os.chdir(r"c:\VSCODE_Developement\logicappsdevelopment\logicappsdevelopment\mcp-dataverse-server")
sys.path.insert(0, "src")

from dotenv import load_dotenv
load_dotenv(".env")

from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings
import httpx
from rich.console import Console

console = Console()

# Common styles (inline on each element - Dataverse strips <style> tags)
H1_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 18pt; color: #2c3e50; margin-bottom: 15px;"'
H2_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 14pt; color: #2c3e50; margin-top: 20px; margin-bottom: 10px;"'
P_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; line-height: 1.6; margin-bottom: 15px;"'
LI_STYLE = 'style="font-family: Segoe UI, sans-serif; font-size: 12pt; margin-bottom: 8px;"'
UL_STYLE = 'style="margin: 0 0 15px 20px; padding: 0;"'

# Article 1: Printer Installation
PRINTER_ARTICLE = {
    "title": "Network Printer Installation in Secure Facilities",
    "description": "Step-by-step guide for technicians installing network printers in prisons and secure environments",
    "keywords": "printer, installation, network, prison, secure facility, security clearance, driver, configuration, HP, Canon, Lexmark",
    "content": f"""
<p {H1_STYLE}><strong>Network Printer Installation in Secure Facilities: A Technician's Guide</strong></p>

<p {P_STYLE}>Installing network printers in secure facilities such as prisons requires additional planning and compliance with security protocols. This guide covers the complete process from pre-arrival preparation through to end-user handover.</p>

<p {H1_STYLE}><strong>Before You Arrive</strong></p>

<p {H2_STYLE}><strong>1. Security Clearance</strong></p>
<p {P_STYLE}>Ensure you have completed all required security vetting before attempting to enter the facility. Contact the facility security office at least 48 hours in advance to confirm your appointment and provide details of any equipment you'll be bringing.</p>

<p {H2_STYLE}><strong>2. Equipment Checklist</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}><strong>Printer unit:</strong> Verify model matches the work order specification</li>
<li {LI_STYLE}><strong>Power cable:</strong> UK 3-pin plug, appropriate length</li>
<li {LI_STYLE}><strong>Network cable:</strong> CAT6 Ethernet cable (length as specified)</li>
<li {LI_STYLE}><strong>Driver media:</strong> USB drive with latest drivers or network access credentials</li>
<li {LI_STYLE}><strong>Tools:</strong> Screwdrivers, cable ties, label printer</li>
<li {LI_STYLE}><strong>Documentation:</strong> Work order printout, IP configuration sheet, sign-off form</li>
</ul>

<p {H2_STYLE}><strong>3. PPE Requirements</strong></p>
<p {P_STYLE}>Wear appropriate personal protective equipment including safety boots and high-visibility vest if required by the facility. Remove any items that could be considered contraband according to facility policy.</p>

<p {H1_STYLE}><strong>On-Site Installation Process</strong></p>

<p {H2_STYLE}><strong>1. Security Check-In Procedure</strong></p>
<p {P_STYLE}>Report to the main reception with your identification and work order. You will need to:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Present valid photo ID and company credentials</li>
<li {LI_STYLE}>Sign the visitor log and obtain a visitor badge</li>
<li {LI_STYLE}>Declare all tools and equipment for inspection</li>
<li {LI_STYLE}>Wait for your facility escort before proceeding</li>
</ul>

<p {H2_STYLE}><strong>2. Site Assessment</strong></p>
<p {P_STYLE}>Before unpacking equipment, assess the installation location:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Verify power outlet availability and voltage (230V UK standard)</li>
<li {LI_STYLE}>Confirm network port is active and patched to the correct VLAN</li>
<li {LI_STYLE}>Check desk or mounting surface is suitable for printer weight</li>
<li {LI_STYLE}>Ensure adequate ventilation space around the printer</li>
</ul>

<p {H2_STYLE}><strong>3. Unpack and Inspect Equipment</strong></p>
<p {P_STYLE}>Carefully unpack the printer and inspect for any shipping damage. Remove all internal packaging materials including tape, foam inserts, and protective covers. Verify all accessories are present according to the packing list.</p>

<p {H2_STYLE}><strong>4. Network Connection</strong></p>
<p {P_STYLE}>Connect the printer to the network:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Connect the Ethernet cable to the printer's network port</li>
<li {LI_STYLE}>Connect to the wall outlet or patch panel port</li>
<li {LI_STYLE}>Power on the printer and wait for initialisation</li>
<li {LI_STYLE}>Configure static IP address or verify DHCP assignment</li>
<li {LI_STYLE}>Test network connectivity using the printer's built-in tools</li>
</ul>

<p {H2_STYLE}><strong>5. Driver Installation and Configuration</strong></p>
<p {P_STYLE}>Install the printer driver on the designated workstations:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Use the provided driver package or download from the manufacturer's website</li>
<li {LI_STYLE}>Configure the printer queue with the correct settings (duplex, default tray, etc.)</li>
<li {LI_STYLE}>Set up secure print if required by facility policy</li>
<li {LI_STYLE}>Configure department codes if cost tracking is required</li>
</ul>

<p {H2_STYLE}><strong>6. Test Print and Validation</strong></p>
<p {P_STYLE}>Perform comprehensive testing:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Print a test page from the printer's control panel</li>
<li {LI_STYLE}>Print a test document from each connected workstation</li>
<li {LI_STYLE}>Test all paper trays and print sizes</li>
<li {LI_STYLE}>Verify print quality meets standards</li>
<li {LI_STYLE}>Test any scanning or copying functions if applicable</li>
</ul>

<p {H2_STYLE}><strong>7. End User Handover</strong></p>
<p {P_STYLE}>Demonstrate the printer to the designated staff member:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Show how to load paper and clear jams</li>
<li {LI_STYLE}>Explain any secure print or department code features</li>
<li {LI_STYLE}>Provide contact details for future support</li>
<li {LI_STYLE}>Obtain signature on the completion form</li>
</ul>

<p {H1_STYLE}><strong>Troubleshooting Common Issues</strong></p>

<p {H2_STYLE}><strong>Printer Not Connecting to Network</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Verify the network cable is securely connected at both ends</li>
<li {LI_STYLE}>Check the network port is active (contact IT if needed)</li>
<li {LI_STYLE}>Confirm IP address configuration matches the network requirements</li>
<li {LI_STYLE}>Try a different network cable to rule out cable fault</li>
</ul>

<p {H2_STYLE}><strong>Print Quality Issues</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Run the printer's built-in cleaning cycle</li>
<li {LI_STYLE}>Check toner or ink levels</li>
<li {LI_STYLE}>Verify paper type settings match the loaded paper</li>
<li {LI_STYLE}>Print an alignment page and adjust if necessary</li>
</ul>

<p {H2_STYLE}><strong>When to Escalate</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}><strong>Hardware Damage:</strong> If the printer is damaged, do not proceed with installation. Report to your supervisor and arrange replacement.</li>
<li {LI_STYLE}><strong>Network Issues:</strong> If network connectivity cannot be established after basic troubleshooting, escalate to the facility IT department.</li>
<li {LI_STYLE}><strong>Security Concerns:</strong> Always follow facility staff instructions regarding security. If in doubt, ask.</li>
</ul>

<p {P_STYLE}>Completing printer installations in secure facilities requires patience and attention to security protocols. Always maintain professionalism and respect facility rules to ensure smooth future access for yourself and colleagues.</p>
"""
}

# Article 2: Cable Trunking Installation
CABLE_ARTICLE = {
    "title": "Surface-Mounted Cable Trunking Installation",
    "description": "Complete guide for installing cable trunking and running CAT6 network cables in secure facilities",
    "keywords": "cable, trunking, network, CAT6, installation, mounting, RJ45, termination, prison, secure facility, conduit",
    "content": f"""
<p {H1_STYLE}><strong>Surface-Mounted Cable Trunking Installation: A Technician's Guide</strong></p>

<p {P_STYLE}>Installing surface-mounted cable trunking in secure facilities requires careful planning and adherence to both electrical regulations and facility security protocols. This guide covers the complete process from survey through to testing and sign-off.</p>

<p {H1_STYLE}><strong>Before You Arrive</strong></p>

<p {H2_STYLE}><strong>1. Security Clearance</strong></p>
<p {P_STYLE}>Cable installation work often requires access to multiple areas of a secure facility. Ensure your security vetting is current and covers all required zones. Submit your tool list for pre-approval at least 72 hours before the scheduled work.</p>

<p {H2_STYLE}><strong>2. Materials Checklist</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}><strong>Trunking sections:</strong> Verify lengths and sizes match the survey specification</li>
<li {LI_STYLE}><strong>Accessories:</strong> Internal corners, external corners, flat angles, end caps, couplers</li>
<li {LI_STYLE}><strong>Mounting hardware:</strong> Screws, wall plugs, clips (appropriate for wall type)</li>
<li {LI_STYLE}><strong>CAT6 cable:</strong> Solid core for permanent runs, quantity as specified</li>
<li {LI_STYLE}><strong>Termination equipment:</strong> RJ45 connectors, crimping tool, cable tester</li>
<li {LI_STYLE}><strong>Patch panels and faceplates:</strong> As specified in work order</li>
</ul>

<p {H2_STYLE}><strong>3. Tool Requirements</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Cordless drill with masonry and wood bits</li>
<li {LI_STYLE}>Spirit level and laser level</li>
<li {LI_STYLE}>Measuring tape (minimum 5m)</li>
<li {LI_STYLE}>Hacksaw or trunking cutter</li>
<li {LI_STYLE}>Cable stripping and crimping tools</li>
<li {LI_STYLE}>Fluke or equivalent cable tester</li>
<li {LI_STYLE}>PPE: Safety glasses, dust mask, knee pads</li>
</ul>

<p {H1_STYLE}><strong>On-Site Installation Process</strong></p>

<p {H2_STYLE}><strong>1. Security Check-In Procedure</strong></p>
<p {P_STYLE}>Report to the main reception with your identification and work order. All tools must be declared and may be subject to inspection. Power tools may require specific approval. Wait for your facility escort before proceeding to the work area.</p>

<p {H2_STYLE}><strong>2. Survey Installation Route</strong></p>
<p {P_STYLE}>Before starting work, conduct a thorough route survey:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Verify the planned cable route against the original survey</li>
<li {LI_STYLE}>Identify any obstacles that may have changed since the survey</li>
<li {LI_STYLE}>Confirm mounting surface types (brick, block, plasterboard, etc.)</li>
<li {LI_STYLE}>Mark mounting points at regular intervals (typically 300mm)</li>
<li {LI_STYLE}>Plan corner and junction positions</li>
<li {LI_STYLE}>Check for any services behind walls before drilling</li>
</ul>

<p {H2_STYLE}><strong>3. Mount Trunking Brackets</strong></p>
<p {P_STYLE}>Install the trunking base sections:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Use a spirit level to ensure trunking runs horizontally or vertically</li>
<li {LI_STYLE}>Mark drill positions at each mounting point</li>
<li {LI_STYLE}>Drill holes and insert appropriate wall plugs</li>
<li {LI_STYLE}>Secure trunking base using screws (do not overtighten on plasterboard)</li>
<li {LI_STYLE}>Install corner pieces and joiners as you progress</li>
<li {LI_STYLE}>Ensure all joints are neat and aligned</li>
</ul>

<p {H2_STYLE}><strong>4. Run and Secure Cables</strong></p>
<p {P_STYLE}>Pull the network cables through the trunking:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Label cables at both ends before pulling</li>
<li {LI_STYLE}>Pull cables gently to avoid stretching or damaging the jacket</li>
<li {LI_STYLE}>Maintain minimum bend radius (4x cable diameter for CAT6)</li>
<li {LI_STYLE}>Do not exceed maximum pull tension (25 lbf for CAT6)</li>
<li {LI_STYLE}>Leave service loops at termination points</li>
<li {LI_STYLE}>Secure cables neatly within the trunking</li>
<li {LI_STYLE}>Fit trunking lids once cables are in place</li>
</ul>

<p {H2_STYLE}><strong>5. Terminate and Test Cables</strong></p>
<p {P_STYLE}>Terminate cables at both ends:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Strip outer jacket carefully (approximately 50mm)</li>
<li {LI_STYLE}>Untwist pairs only as much as necessary (maximum 13mm)</li>
<li {LI_STYLE}>Follow T568B wiring standard unless otherwise specified</li>
<li {LI_STYLE}>Crimp connectors securely using correct tool</li>
<li {LI_STYLE}>Test each cable run using a cable tester</li>
<li {LI_STYLE}>Verify wiremap, length, and crosstalk specifications</li>
<li {LI_STYLE}>Document test results for each cable run</li>
</ul>

<p {H2_STYLE}><strong>6. Clean Up and Sign Off</strong></p>
<p {P_STYLE}>Complete the installation professionally:</p>
<ul {UL_STYLE}>
<li {LI_STYLE}>Remove all packaging and debris from the work area</li>
<li {LI_STYLE}>Vacuum or sweep if dust has been created</li>
<li {LI_STYLE}>Label all outlets and patch panel ports clearly</li>
<li {LI_STYLE}>Update cable schedule documentation</li>
<li {LI_STYLE}>Obtain signature on the completion form</li>
<li {LI_STYLE}>Return all declared tools for inspection at security</li>
</ul>

<p {H1_STYLE}><strong>Troubleshooting Common Issues</strong></p>

<p {H2_STYLE}><strong>Cable Test Failures</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}><strong>Open/Short:</strong> Re-terminate the connector at the indicated end</li>
<li {LI_STYLE}><strong>Split Pair:</strong> Verify wiring sequence follows T568B standard</li>
<li {LI_STYLE}><strong>Length Fail:</strong> Check for kinks or excessive cable coils</li>
<li {LI_STYLE}><strong>Crosstalk:</strong> Ensure pairs are not untwisted more than 13mm</li>
</ul>

<p {H2_STYLE}><strong>Mounting Difficulties</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}><strong>Wall plugs not gripping:</strong> Use larger plugs or consider toggle fixings for hollow walls</li>
<li {LI_STYLE}><strong>Hitting services:</strong> Stop immediately and use a cable/pipe detector before continuing</li>
<li {LI_STYLE}><strong>Uneven surfaces:</strong> Use packer pieces behind the trunking</li>
</ul>

<p {H2_STYLE}><strong>When to Escalate</strong></p>
<ul {UL_STYLE}>
<li {LI_STYLE}><strong>Hidden Services:</strong> If you suspect hidden electrical or water services, stop and contact building management.</li>
<li {LI_STYLE}><strong>Structural Concerns:</strong> Do not drill into structural steelwork or load-bearing elements without approval.</li>
<li {LI_STYLE}><strong>Multiple Test Failures:</strong> If cables consistently fail testing, escalate to determine if there is a batch issue with materials.</li>
<li {LI_STYLE}><strong>Access Restrictions:</strong> If you cannot access required areas due to security or operational reasons, report to your supervisor.</li>
</ul>

<p {P_STYLE}>Professional cable installation requires attention to detail and compliance with both technical standards and facility requirements. Quality workmanship ensures reliable network infrastructure and reflects well on your organisation.</p>
"""
}


def main():
    settings = load_settings()
    tp = TokenProvider(
        settings.dataverse_tenant_id,
        settings.dataverse_client_id,
        settings.dataverse_client_secret,
        settings.dataverse_base_url
    )
    token = tp.get_access_token()
    base = settings.dataverse_base_url
    ver = settings.dataverse_api_version
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }
    
    url = f"{base}/api/data/{ver}/knowledgearticles"
    
    articles = [PRINTER_ARTICLE, CABLE_ARTICLE]
    
    console.print("\n[bold cyan]Creating Knowledge Articles (Draft) with inline styles...[/bold cyan]\n")
    
    with httpx.Client(timeout=60.0) as client:
        for article in articles:
            payload = {
                "title": article["title"],
                "description": article["description"],
                "keywords": article["keywords"],
                "content": article["content"],
            }
            
            response = client.post(url, headers=headers, json=payload)
            
            if response.status_code in (200, 201, 204):
                entity_id = response.headers.get("OData-EntityId", "")
                if entity_id:
                    article_id = entity_id.split("(")[-1].rstrip(")")
                else:
                    article_id = "unknown"
                
                console.print(f"[green]✓ Created:[/green] {article['title']}")
                console.print(f"  [dim]ID: {article_id}[/dim]")
            else:
                console.print(f"[red]✗ Failed:[/red] {article['title']}")
                console.print(f"  [dim]Status: {response.status_code}[/dim]")
                console.print(f"  [dim]Error: {response.text[:500]}[/dim]")
    
    console.print("\n[bold green]Knowledge articles created as drafts.[/bold green]")
    console.print("[dim]Open Customer Service Hub to review and publish.[/dim]\n")


if __name__ == "__main__":
    main()
