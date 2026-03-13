import os
import sys
import subprocess

REQUIRED_KEYS = [
    'MG_SIG_MASTER_KEY',
    'MG_SIG_HASH_KEY',
    'MG_KBIT_MASTER_KEY',
    'MG_KBIT_IV',
    'MG_KC_MASTER_KEY',
    'MG_KC_IV',
    'MG_ROOTSIG_MASTER_KEY',
    'MG_ROOTSIG_HASH_KEY',
    'MG_CONTENT_TABLE_IV',
    'MG_CONTENT_IV',
]

# Load keys from PS2KEYS.dat, filling in any keys not already in the environment
keys_file = os.path.join(os.path.dirname(__file__), 'PS2KEYS.dat')
if os.path.exists(keys_file):
    with open(keys_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                key = key.strip()
                value = value.strip()
                if key and key not in os.environ:
                    os.environ[key] = value

for key in REQUIRED_KEYS:
    if key not in os.environ:
        print(f'Failed to encrypt: {key} is not set (set via environment or utils/scripts/PS2KEYS.dat)')
        sys.exit(1)

if len(sys.argv) != 4:
    print('Failed to encrypt: invalid number of arguments')
    print('Usage: python3 kelfsign.py <header_id> <input_file> <output_file>')
    sys.exit(1)

header_id = sys.argv[1]
input_file = sys.argv[2]
output_file = sys.argv[3]

kelftool = os.environ.get('KELFTOOL', 'kelftool')

result = subprocess.run(
    [kelftool, 'encrypt', header_id, input_file, output_file],
    env=os.environ,
)

if result.returncode != 0:
    print(f'Failed to encrypt: kelftool exited with {result.returncode}')
    sys.exit(1)

print('File encrypted successfully')
