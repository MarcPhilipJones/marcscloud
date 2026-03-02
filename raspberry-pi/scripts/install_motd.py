"""Install MOTD script on Raspberry Pi."""

from raspberry_pi.client import PiClient

SCRIPT_PATH = "scripts/99-pi-status"
REMOTE_PATH = "/tmp/99-pi-status"
MOTD_PATH = "/etc/update-motd.d/99-pi-status"

with PiClient() as pi:
    print("Uploading MOTD script...")
    pi.upload_file(SCRIPT_PATH, REMOTE_PATH)
    
    print("Fixing line endings (CRLF -> LF)...")
    pi.run(f"tr -d '\\r' < {REMOTE_PATH} > {REMOTE_PATH}.fixed")
    pi.run(f"mv {REMOTE_PATH}.fixed {REMOTE_PATH}")
    
    print("Installing to /etc/update-motd.d/...")
    result = pi.run(f"sudo cp {REMOTE_PATH} {MOTD_PATH}")
    if not result.success:
        print(f"Failed to copy: {result.stderr}")
    else:
        print("Copied successfully")
    
    result = pi.run(f"sudo chmod +x {MOTD_PATH}")
    if not result.success:
        print(f"Failed to chmod: {result.stderr}")
    else:
        print("Made executable")
    
    # Clean up temp file
    pi.run(f"rm {REMOTE_PATH}")
    
    # Test the script
    print("\n--- Testing MOTD output ---")
    result = pi.run(MOTD_PATH)
    print(result.stdout)
    
    print("\n✓ Done! You'll see this info next time you SSH into your Pi.")
