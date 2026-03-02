"""Install neofetch and set as MOTD."""

from raspberry_pi.client import PiClient

with PiClient() as pi:
    # Check if neofetch is installed
    result = pi.run("which neofetch")
    if result.stdout:
        print("neofetch already installed:", result.stdout)
    else:
        print("Installing neofetch...")
        result = pi.run("sudo apt-get update && sudo apt-get install -y neofetch")
        print("Installed!" if result.success else result.stderr)
    
    # Create the new MOTD script with neofetch
    print("\nUpdating MOTD script...")
    script = """#!/bin/bash
neofetch
"""
    result = pi.run(f"echo '{script}' | sudo tee /etc/update-motd.d/99-pi-status")
    result = pi.run("sudo chmod +x /etc/update-motd.d/99-pi-status")
    print("Done!")
    
    # Test it
    print("\nTesting neofetch:")
    result = pi.run("neofetch --stdout")
    print(result.stdout)
