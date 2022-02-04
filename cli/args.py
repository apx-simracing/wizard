import argparse

parser = argparse.ArgumentParser(description='Process some integers.')

required = parser.add_argument_group('required arguments')
required.add_argument('--server', metavar='server', type=str, nargs='+',
                      help='Server name', required=True)
required.add_argument('--config', metavar='config', type=str, nargs="?",
                      help='Config')
required.add_argument('--cmd', metavar='cmd', type=str, nargs="?",
                      help='Command', required=True)
required.add_argument('--args', metavar='args', type=str,  nargs='*',
                      help='Arguments')
