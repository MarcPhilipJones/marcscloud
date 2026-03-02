"""Install local Pi status script with rich output."""

from raspberry_pi.client import PiClient

SCRIPT_PATH = "scripts/pi_status_local.py"
REMOTE_SCRIPT = "/usr/local/bin/pi-status"
MOTD_PATH = "/etc/update-motd.d/99-pi-status"

with PiClient() as pi:
    # Install rich
    print("Installing rich library...")
    result = pi.run("pip3 install rich --break-system-packages")
    print("rich installed!" if result.success else f"Warning: {result.stderr}")
    
    # Upload the script
    print("\nUploading pi-status script...")
    pi.upload_file(SCRIPT_PATH, "/tmp/pi-status")
    
    # Fix line endings and install
    pi.run("tr -d '\\r' < /tmp/pi-status > /tmp/pi-status.fixed")
    pi.run(f"sudo mv /tmp/pi-status.fixed {REMOTE_SCRIPT}")
    pi.run(f"sudo chmod +x {REMOTE_SCRIPT}")
    pi.run("rm /tmp/pi-status")
    print(f"Installed to {REMOTE_SCRIPT}")
    
    # Update MOTD to call the Python script
    print("\nUpdating MOTD...")
    motd_script = f"""#!/bin/bash
{REMOTE_SCRIPT}
"""
    pi.run(f"echo '{motd_script}' | sudo tee {MOTD_PATH}")
    pi.run(f"sudo chmod +x {MOTD_PATH}")
    
    # Fix line endings on MOTD too
    pi.run(f"sudo tr -d '\\r' < {MOTD_PATH} > /tmp/motd-fixed")
    pi.run(f"sudo mv /tmp/motd-fixed {MOTD_PATH}")
    pi.run(f"sudo chmod +x {MOTD_PATH}")
    print("MOTD updated!")
    
    # Test it
    print("\n--- Testing ---")
    result = pi.run(REMOTE_SCRIPT)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    print("\n✓ Done! SSH in to see the new status display.")
