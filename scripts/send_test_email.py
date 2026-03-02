"""
Send a test outbound email via Dataverse email activity.

Creates an email activity record with activity parties (From: support queue,
To: Chris Walker contact), sets regardingobjectid to the contact, then calls
the SendEmail bound action to deliver it via server-side sync.

The email will:
  1. Appear on Chris Walker's contact timeline immediately (as a draft)
  2. Be delivered to chriswalker@D365DemoTSCE63319057.onmicrosoft.com
  3. Transition from Draft -> Pending Send -> Sent on the timeline

Usage:
    python scripts/send_test_email.py
"""

import os
import sys
from datetime import datetime

# Add the MCP server source to the path so we can reuse its auth
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "mcp-dataverse-server", "src")
)

import httpx
from mcp_dataverse_server.auth import TokenProvider
from mcp_dataverse_server.config import load_settings

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Chris Walker contact
CONTACT_ID = "7fba73b9-2461-ef11-bfe2-002248a36d0e"
CONTACT_EMAIL = "chriswalker@D365DemoTSCE63319057.onmicrosoft.com"
CONTACT_NAME = "Chris Walker"

# Support queue (sender)
QUEUE_ID = "1891ce59-6560-ef11-bfe3-000d3a65cf07"
QUEUE_EMAIL = "support@D365DemoTSCE63319057.onmicrosoft.com"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    # Load settings and get token
    os.chdir(os.path.join(os.path.dirname(__file__), "..", "mcp-dataverse-server"))
    settings = load_settings()

    token_provider = TokenProvider(
        tenant_id=settings.dataverse_tenant_id,
        client_id=settings.dataverse_client_id,
        client_secret=settings.dataverse_client_secret,
        resource=settings.dataverse_base_url,
    )
    token = token_provider.get_access_token()

    base_url = settings.dataverse_base_url.rstrip("/")
    api_url = f"{base_url}/api/data/{settings.dataverse_api_version}"

    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Prefer": 'odata.include-annotations="*"',
    }

    now_str = datetime.now().strftime("%d %B %Y at %H:%M")

    # -----------------------------------------------------------------------
    # Step 1: Create the email activity with activity parties
    # -----------------------------------------------------------------------
    print("=" * 60)
    print("STEP 1: Creating outbound email activity...")
    print("=" * 60)

    email_payload = {
        "subject": f"Welcome to Support - {now_str}",
        "description": (
            f"<html><body>"
            f"<p style='font-family: Segoe UI, sans-serif; font-size: 11pt;'>"
            f"Dear {CONTACT_NAME},</p>"
            f"<p style='font-family: Segoe UI, sans-serif; font-size: 11pt;'>"
            f"Thank you for contacting our support team. This email confirms that "
            f"your details are on file and we are ready to assist you.</p>"
            f"<p style='font-family: Segoe UI, sans-serif; font-size: 11pt;'>"
            f"If you have any questions, please reply to this email or call us "
            f"on 0800 123 4567.</p>"
            f"<p style='font-family: Segoe UI, sans-serif; font-size: 11pt;'>"
            f"Kind regards,<br/>The Support Team</p>"
            f"</body></html>"
        ),
        "directioncode": True,  # Outgoing
        # Link to Chris Walker's contact record -> appears on his timeline
        "regardingobjectid_contact@odata.bind": f"/contacts({CONTACT_ID})",
        # Activity parties: From (queue) and To (contact)
        "email_activity_parties": [
            {
                # FROM: Support queue
                "partyid_queue@odata.bind": f"/queues({QUEUE_ID})",
                "participationtypemask": 1,  # 1 = From/Sender
            },
            {
                # TO: Chris Walker contact
                "partyid_contact@odata.bind": f"/contacts({CONTACT_ID})",
                "participationtypemask": 2,  # 2 = To Recipient
            },
        ],
    }

    print(f"  From:      {QUEUE_EMAIL}")
    print(f"  To:        {CONTACT_EMAIL}")
    print(f"  Subject:   {email_payload['subject']}")
    print(f"  Regarding: Contact - {CONTACT_NAME}")
    print()

    with httpx.Client(timeout=30.0) as client:
        # Create the email
        resp = client.post(
            f"{api_url}/emails",
            headers=headers,
            json=email_payload,
        )

        if resp.status_code not in (200, 201, 204):
            print(f"  FAILED to create email: {resp.status_code}")
            print(f"  Response: {resp.text}")
            sys.exit(1)

        # Get the activity ID from the OData-EntityId header or response body
        entity_id_header = resp.headers.get("OData-EntityId", "")
        if entity_id_header:
            # Extract GUID from URL like .../emails(guid)
            activity_id = entity_id_header.split("(")[-1].rstrip(")")
        else:
            body = resp.json()
            activity_id = body.get("activityid")

        print("  SUCCESS - Email activity created!")
        print(f"  Activity ID: {activity_id}")
        print("  Status: Draft (will appear on timeline immediately)")
        print()

        # -------------------------------------------------------------------
        # Step 2: Send the email via SendEmail bound action
        # -------------------------------------------------------------------
        print("=" * 60)
        print("STEP 2: Calling SendEmail bound action...")
        print("=" * 60)
        print(
            f"  POST {api_url}/emails({activity_id})/Microsoft.Dynamics.CRM.SendEmail"
        )
        print()

        send_resp = client.post(
            f"{api_url}/emails({activity_id})/Microsoft.Dynamics.CRM.SendEmail",
            headers=headers,
            json={"IssueSend": True},
        )

        if send_resp.status_code not in (200, 204):
            print(f"  FAILED to send email: {send_resp.status_code}")
            print(f"  Response: {send_resp.text}")
            print()
            print("  NOTE: If you see a mailbox/sync error, verify that the")
            print("  support queue mailbox has server-side sync enabled:")
            print("  D365 > Advanced Settings > Email Configuration > Mailboxes")
            sys.exit(1)

        print("  SUCCESS - SendEmail action completed!")
        print("  Email queued for delivery via server-side sync.")
        print()

        # -------------------------------------------------------------------
        # Step 3: Verify the email status
        # -------------------------------------------------------------------
        print("=" * 60)
        print("STEP 3: Verifying email status...")
        print("=" * 60)

        verify_resp = client.get(
            f"{api_url}/emails({activity_id})?$select=subject,statuscode,statecode,directioncode",
            headers=headers,
        )

        if verify_resp.status_code == 200:
            email_data = verify_resp.json()
            status_map = {
                1: "Draft",
                2: "Completed (Sent)",
                3: "Canceled",
                4: "Received",
                6: "Pending Send",
                7: "Sending",
                8: "Failed",
            }
            status = email_data.get("statuscode", "?")
            status_label = status_map.get(status, f"Unknown ({status})")

            print(f"  Subject:   {email_data.get('subject')}")
            print(
                f"  Direction: {'Outgoing' if email_data.get('directioncode') else 'Incoming'}"
            )
            print(f"  Status:    {status_label}")
            print()

        # -------------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------------
        print("=" * 60)
        print("DONE!")
        print("=" * 60)
        print()
        print("What to check:")
        print("  1. Open Chris Walker's contact record in D365:")
        print(
            f"     https://org6cb3e9fb.crm4.dynamics.com/main.aspx?etn=contact&id={CONTACT_ID}&pagetype=entityrecord"
        )
        print("     -> Timeline tab should show the outbound email")
        print()
        print("  2. Check Chris Walker's mailbox for the delivered email")
        print(f"     ({CONTACT_EMAIL})")
        print()
        print("  3. If status is 'Pending Send', wait 1-2 minutes for")
        print("     server-side sync to deliver. Check mailbox sync status")
        print("     if it stays pending.")


if __name__ == "__main__":
    main()
