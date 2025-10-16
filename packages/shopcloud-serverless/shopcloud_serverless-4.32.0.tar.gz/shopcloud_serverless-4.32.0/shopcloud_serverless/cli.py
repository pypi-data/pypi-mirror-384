from . import endpoints, gateways, helpers, jobs
from .configs import Config


def main(args) -> int:
    if not hasattr(args, 'which'):
        print(
            helpers.bcolors.FAIL
            + 'Can not parse action use --help'
            + helpers.bcolors.ENDC
        )
        return 1

    if hasattr(args, 'debug') and args.debug:
        print(args)

    config = Config(config_filename=args.config)

    if args.which == 'init':
        config.base_dir = args.base_dir or helpers.ask_for('Base directory', '.')

        # Cloud
        config.cloud = args.cloud or helpers.ask_for('Cloud', 'gcp')
        config.project = args.project or helpers.ask_for('Cloud project')
        config.region = args.region or helpers.ask_for('Cloud region', 'europe-west1')

        # Endpoints
        config.endpoint_api_title = args.api_title or helpers.ask_for('Endpoint API title', 'My API')
        config.endpoint_api_description = args.api_description or helpers.ask_for('Endpoint API description', 'My API description')

        config.save()
        print(helpers.bcolors.OKGREEN + 'Init config success' + helpers.bcolors.ENDC)
        return 0
    elif args.which == 'jobs':
        return jobs.cli_main(args, config)
    elif args.which == 'gateway':
        return gateways.cli_main(args, config)
    elif args.which == 'endpoints':
        return endpoints.cli_main(args, config)
    elif args.which == 'memorystore':
        if not config.load():
            return 1
        print('# Init Memory Store')
        print(f'- go to https://console.cloud.google.com/memorystore/&project={config.project} and create a redis instance')
        print('- set network as default')
        print('# Init Serverloser VPC-Zugriff')
        print(f'- go to https://console.cloud.google.com/networking/connectors/list?project={config.project}')
        print(f'- create a connector with name `serverless-vpc-connector` and region `{config.region}`')
        print('  - with network 10.8.0.0/28')
        print('')
        print('to use it in the gcloud functions use the --vpc-connector option')
