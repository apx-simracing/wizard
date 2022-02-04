import subprocess
from os import listdir, path
from wizard.settings import (
    CHILDREN_DIR
)

print(f'Servers directory: {CHILDREN_DIR}')

servers = listdir(CHILDREN_DIR)

print(f'Found {len(servers)} server(s): {servers}')

for server in servers:
    python_path = path.join(CHILDREN_DIR, server, 'python.exe')
    print(f'Patching: {python_path}')
    process = subprocess.Popen([python_path, '-m', 'pip', 'install', '--upgrade', '--force-reinstall', 'git+https://github.com/enthought/comtypes.git'], stdout=subprocess.PIPE,  universal_newlines=True)

    while True:
        output = process.stdout.readline()
        if output:
            print(output.strip())
        return_code = process.poll()
        if return_code is not None:
            if return_code == 0:
                print('Done')
            else:
                print('Oops! Something ain\'t right!')
            break