import shlex

from . import helpers, steps
from .configs import Config


def cli_main(args, config: Config) -> int:
    if not config.load():
        return 1
    if args.action == 'init':
        manager = steps.Manager(config, [
            steps.StepCommand(
                shlex.split(
                    f'gcloud services enable apigateway.googleapis.com --project="{config.project}"'
                ),
                is_async=False,
            ),
            steps.StepCommand(
                shlex.split(
                    f'gcloud services enable servicemanagement.googleapis.com --project="{config.project}"'
                ),
                is_async=False,
            ),
            steps.StepCommand(
                shlex.split(
                    f'gcloud services enable servicecontrol.googleapis.com --project="{config.project}"'
                ),
                is_async=False,
            ),
            steps.StepCommand(
                shlex.split(
                    f'gcloud services enable cloudbuild.googleapis.com --project="{config.project}"'
                ),
                is_async=False,
            ),
            steps.StepCommand(
                shlex.split(
                    f'gcloud services enable cloudfunctions.googleapis.com --project="{config.project}"'
                ),
                is_async=False,
            ),
        ], simulate=args.simulate)
        rc = manager.run()
        if rc != 0:
            return rc
        print(helpers.bcolors.OKGREEN + 'Init API-Gateway success' + helpers.bcolors.ENDC)
        return 0
    elif args.action == 'deploy':
        config.endpoint_deploy_version = config.endpoint_deploy_version + 1
        api_id = config.endpoint_api_title.lower().replace(' ', '-').replace('_', '-')
        api_config_id = f"v{config.endpoint_deploy_version}"

        if config.endpoint_deploy_version == 1:
            if args.debug:
                print(f'Creating API Gateway {api_id}')
            commands = [
                steps.StepCommand(
                    shlex.split(
                        f'gcloud api-gateway api-configs create {api_config_id} --api={api_id} --openapi-spec=api.yaml --project="{config.project}" --backend-auth-service-account="{config.project}@appspot.gserviceaccount.com"'
                    ),
                    work_dir=f'{config.base_dir}',
                    is_async=False,
                ),
                steps.StepCommand(
                    shlex.split(
                        f'gcloud api-gateway gateways create {api_id} --api={api_id} --api-config={api_config_id} --location={config.region} --project="{config.project}"'
                    ),
                    work_dir=f'{config.base_dir}',
                    is_async=False,
                )
            ]
        else:
            if args.debug:
                print(f'Updating API Gateway {api_id}')
            commands = [
                steps.StepCommand(
                    shlex.split(
                        f'gcloud api-gateway api-configs create {api_config_id} --api={api_id} --openapi-spec=api.yaml --project="{config.project}" --backend-auth-service-account="{config.project}@appspot.gserviceaccount.com"'
                    ),
                    work_dir=f'{config.base_dir}',
                    is_async=False,
                ),
                steps.StepCommand(
                    shlex.split(
                        f'gcloud api-gateway gateways update {api_id} --api={api_id} --api-config={api_config_id} --location={config.region} --project="{config.project}"'
                    ),
                    work_dir=f'{config.base_dir}',
                    is_async=False,
                )
            ]

        manager = steps.Manager(config, commands, simulate=args.simulate)
        rc = manager.run()
        if rc != 0:
            return rc
        print(helpers.bcolors.OKGREEN + 'Deploy API-Gatewway success' + helpers.bcolors.ENDC)
        config.save()
        return 0
