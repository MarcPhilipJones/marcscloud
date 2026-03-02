"""Remove duplicate MOTD call from .bashrc."""

from raspberry_pi.client import PiClient

with PiClient() as pi:
    # Remove the lines we added to bashrc
    result = pi.run("grep -v 99-pi-status ~/.bashrc | grep -v 'Show Pi status' > /tmp/bashrc.new")
    result = pi.run("mv /tmp/bashrc.new ~/.bashrc")
    print("Removed from .bashrc")
    
    # Verify
    print("\nLast 5 lines of .bashrc:")
    result = pi.run("tail -5 ~/.bashrc")
    print(result.stdout)
