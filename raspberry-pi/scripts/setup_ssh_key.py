"""Copy SSH public key to Pi for passwordless login."""

from raspberry_pi.client import PiClient

# Read the public key
with open(r'C:\Users\marcjones\.ssh\id_rsa.pub', 'r') as f:
    pubkey = f.read().strip()

with PiClient() as pi:
    # Create .ssh directory if needed
    pi.run('mkdir -p ~/.ssh')
    pi.run('chmod 700 ~/.ssh')
    
    # Check if key already exists
    result = pi.run('grep -c "TABLET-ECJ41CC1" ~/.ssh/authorized_keys 2>/dev/null || echo 0')
    if result.stdout.strip() == '0':
        # Add the key
        pi.run(f'echo "{pubkey}" >> ~/.ssh/authorized_keys')
        pi.run('chmod 600 ~/.ssh/authorized_keys')
        print('✓ SSH key added to Pi!')
    else:
        print('SSH key already exists on Pi')
    
    # Verify
    result = pi.run('cat ~/.ssh/authorized_keys | wc -l')
    print(f'Total keys in authorized_keys: {result.stdout}')
