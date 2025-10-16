import argparse
import sys

from . import cli

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Serverless',
        prog='shopcloud-serverless'
    )

    subparsers = parser.add_subparsers(help='commands', title='commands')
    parser.add_argument('--debug', '-d', help='Debug', action='store_true')
    parser.add_argument('--simulate', '-s', help='Simulate the process', action='store_true')
    parser.add_argument('--secrethub-token', help='Secrethub-Token', type=str)
    parser.add_argument('--config', help='The Config Filename', type=str)

    parser_init = subparsers.add_parser('init', help='init the eventbus')
    parser_init.add_argument('--base-dir', help='Base directory', type=str)
    parser_init.add_argument('--api-title', help='API title', type=str)
    parser_init.add_argument('--api-description', help='API description', type=str)
    parser_init.add_argument('--cloud', help='Cloud type', type=str, default='gcp')
    parser_init.add_argument('--project', help='Cloud project id', type=str)
    parser_init.add_argument('--region', help='Cloud region', type=str)
    parser_init.set_defaults(which='init')

    parser_endpoint = subparsers.add_parser('endpoints', help='endpoints')
    parser_endpoint.add_argument(
        'action',
        const='generate',
        nargs='?',
        choices=['init', 'list', 'create', 'describe', 'deploy', 'serve', 'test']
    )
    parser_endpoint.add_argument('endpoint', const='generate', nargs='?')
    parser_endpoint.set_defaults(which='endpoints')

    parser_gateway = subparsers.add_parser('gateway', help='api gateway')
    parser_gateway.add_argument(
        'action',
        const='generate',
        nargs='?',
        choices=['init', 'deploy']
    )
    parser_gateway.set_defaults(which='gateway')

    parser_jobs = subparsers.add_parser('jobs', help='jobs')
    parser_jobs.add_argument(
        'action',
        const='generate',
        nargs='?',
        choices=['init', 'list', 'create', 'describe', 'deploy', 'run', 'run-dev']
    )
    parser_jobs.add_argument('name', const='generate', nargs='?')
    parser_jobs.set_defaults(which='jobs')

    parser_memorystore = subparsers.add_parser('memorystore', help='generate a redis memorystor')
    parser_memorystore.add_argument(
        'action',
        const='generate',
        nargs='?',
        choices=['init']
    )
    parser_memorystore.set_defaults(which='memorystore')

    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    rc = cli.main(args)
    if rc != 0:
        sys.exit(rc)
