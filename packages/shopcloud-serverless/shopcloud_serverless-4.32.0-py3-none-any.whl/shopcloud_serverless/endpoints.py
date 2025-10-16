import os
import shlex
from pathlib import Path
from typing import List, Optional, TypedDict

import pkg_resources
import yaml

from . import file_contents, helpers, steps
from .configs import Config


class Runtime:
    def __init__(self, config: Config, operation_id: str, **kwargs):
        self.config = config
        self.operation_id = operation_id
        self.entry_point = kwargs.get('entry_point', 'main')
        self.runtime = kwargs.get('runtime', 'python312')
        self.memory = kwargs.get('memory', '256MB')
        self.dependencies = kwargs.get('dependencies', [])
        self.trigger = kwargs.get('trigger', 'http')
        if self.trigger == 'http':
            self.trigger = '--trigger-http'
        else:
            self.trigger = f"--trigger-topic='{self.trigger}'"
        self.vpc_connector = kwargs.get('vpc_connector', None)

    @property
    def command(self) -> str:
        vpc_connector = ''
        if self.vpc_connector is not None:
            vpc_connector = f'--vpc-connector="{self.vpc_connector}"'
        return f'gcloud functions deploy --project="{self.config.project}" {self.operation_id} {self.trigger} --env-vars-file env.yaml --runtime {self.runtime} --entry-point="{self.entry_point}" --memory={self.memory} --region="{self.config.region}" --no-allow-unauthenticated {vpc_connector}'.strip()


class Endpoint:
    def __init__(self, operation_id: str, **kwargs):
        self.operation_id = operation_id
        self.summary = kwargs.get('summary', '')
        self.config = kwargs.get('config', None)
        self.runtime_config = None

    def _load_runtime_config(self, config: Config):
        if self.runtime_config is not None:
            return self.runtime_config
        with open(f'{config.base_dir}/endpoints/{self.operation_id}.yaml') as f:
            self.runtime_config = yaml.safe_load(f.read())
        return self.runtime_config

    def runtime(self, config: Config) -> Runtime:
        runtime_config = self._load_runtime_config(config)
        return Runtime(config, self.operation_id, **runtime_config)

    def _env_secrets(self, config: Config, **kwargs) -> List[dict]:
        runtime_config = self._load_runtime_config(config)
        secrets = {x.get('name'): "{{ "+x.get('value')+" }}" for x in runtime_config.get('secrets', [])}
        return secrets

    def env(self, config: Config, **kwargs) -> str:
        is_simulate = kwargs.get('is_simulate', False)
        env = {
            **self._env_secrets(config, is_simulate=is_simulate),
            **{
                'ENV': 'production',
            }
        }
        env = yaml.dump(env, explicit_start=True, sort_keys=False, indent=2, width=1000)
        env = env.replace("'{{", "{{").replace("}}'", '}}')
        return env


def endpoint_load(config: Config) -> dict:
    with open(f"{config.base_dir}/api.yaml") as f:
        data = yaml.safe_load(f)
    return data


def endpoint_list(config: Config) -> List[Endpoint]:
    data = endpoint_load(config)
    endpoints = list(data.get('paths', {}).values())
    endpoints = [
        [Endpoint(y.get('operationId'), summary=y.get('summary'), config=y) for y in x.values()]
        for x in endpoints
    ]
    return [item for sublist in endpoints for item in sublist]


def endpoint_append_api(config: Config, name: str):
    api_config = endpoint_load(config)
    api_config['paths'][f'/{name}'] = yaml.safe_load(
        file_contents.api_endpoint(
            name,
            project=config.project,
            region=config.region,
        )
    )
    with open(f"{config.base_dir}/api.yaml", "w") as file:
        file.write(yaml.dump(
            api_config,
            explicit_start=True,
            sort_keys=False,
            indent=2,
            width=1000
        ))


def endpoint_create(config: Config, name: str):
    endpoint_path = 'endpoints'
    if Path(config.base_dir, endpoint_path, 'src', 'services', '__init__.py').exists():
        with open(f"{config.base_dir}/{endpoint_path}/src/services/__init__.py", "a") as file:
            file.write(f"\nfrom . import {name}\n")
    if not Path(config.base_dir, 'src', 'services', f'{name}.py').exists():
        with open(f"{config.base_dir}/{endpoint_path}/src/services/{name}.py", "w") as file:
            file.write(file_contents.endpoint_lib(name))
    if not Path(config.base_dir, endpoint_path).exists():
        Path(config.base_dir, endpoint_path).mkdir()
    if not Path(config.base_dir, f'{endpoint_path}/{name}.py').exists():
        with open(f"{config.base_dir}/{endpoint_path}/{name}.py", "w") as file:
            file.write(file_contents.endpoint_main(name))
    if not Path(config.base_dir, f'{endpoint_path}/{name}_test.py').exists():
        with open(f"{config.base_dir}/{endpoint_path}/{name}_test.py", "w") as file:
            file.write(file_contents.endpoint_test(name))
    if not Path(config.base_dir, f'{endpoint_path}/{name}.yaml').exists():
        with open(f"{config.base_dir}/{endpoint_path}/{name}.yaml", "w") as file:
            file.write(file_contents.endpoint_config(name))

    if name not in ['docs', 'health']:
        endpoint_append_api(config, name)


def init_file_structure(config: Config):
    base_dir = config.base_dir
    if base_dir != '.':
        if not Path(base_dir).exists():
            Path(base_dir).mkdir()
    if not Path(base_dir, 'endpoints').exists():
        Path(base_dir, 'endpoints').mkdir()
    if not Path(base_dir, 'endpoints', 'src').exists():
        Path(base_dir, 'endpoints', 'src').mkdir()
        with open(f"{base_dir}/endpoints/src/__init__.py", "w") as file:
            file.write("""from . import services
""")
        Path(base_dir, 'endpoints', 'src', 'services').mkdir()
        with open(f"{base_dir}/endpoints/src/services/__init__.py", "w") as file:
            file.write("""from . import docs
from . import health
""")
        endpoint_create(config, 'health')
        endpoint_create(config, 'docs')

    if not Path(base_dir, 'api.yaml').exists():
        with open(f"{base_dir}/api.yaml", "w") as file:
            file.write(file_contents.api(
                api_title=config.endpoint_api_title,
                api_description=config.endpoint_api_description,
                project=config.project,
                region=config.region,
            ))
    if not Path(base_dir, 'requirements.txt').exists():
        with open(f"{base_dir}/requirements.txt", "w") as file:
            file.write(file_contents.requirements())
    if not Path(base_dir, 'requirements.in').exists():
        with open(f"{base_dir}/requirements.in", "w") as file:
            file.write(file_contents.requirements())


class Dependency(TypedDict):
    name: str
    is_installed: bool
    version: Optional[str]


def check_dependencies_exists(name: List[str]) -> List[Dependency]:
    def check(package_name: str):
        try:
            dist = pkg_resources.get_distribution(package_name)
            return {
                'name': package_name,
                'is_installed': True,
                'version': dist.version,
            }
        except pkg_resources.DistributionNotFound:
            return {
                'name': package_name,
                'is_installed': False,
                'version': None,
            }

    return [check(x) for x in name]


def check_dependencies() -> bool:
    dependency_data = check_dependencies_exists([
        'functions-framework',
        'pytest',
    ])
    dependencies_not_installed = [x for x in dependency_data if not x['is_installed']]
    if len(dependencies_not_installed) > 0:
        print(helpers.bcolors.FAIL + 'Missing python dependencies:' + helpers.bcolors.ENDC)
        for dependency in dependencies_not_installed:
            print(f"+ {dependency['name']}")
        return False
    return True


def cli_main(args, config: Config) -> int:
    if not config.load():
        return 1

    if not check_dependencies():
        return 1

    if args.action == 'init':
        manager = steps.Manager(config, [
            steps.StepFunction(
                'init-file-structure',
                lambda x: init_file_structure(config)
            ),
            steps.StepCommand(
                shlex.split(
                    f'gcloud services enable cloudfunctions.googleapis.com --project="{config.project}"'
                )
            ),
            steps.StepCommand(
                shlex.split(
                    f'gcloud services enable cloudbuild.googleapis.com --project="{config.project}"'
                )
            ),
        ], simulate=args.simulate)
        rc = manager.run()
        if rc != 0:
            return rc
        print(helpers.bcolors.OKGREEN + 'Init API-Endpoint success' + helpers.bcolors.ENDC)
        return 0
    elif args.action == 'list':
        endpoints = endpoint_list(config)
        for endpoint in endpoints:
            print(endpoint.operation_id, '-', endpoint.summary)
        return 0
    elif args.action == 'create':
        endpoints = [x for x in endpoint_list(config) if x.operation_id == args.endpoint]
        if len(endpoints) > 0:
            print(
                helpers.bcolors.FAIL
                + f'Endpoint {args.endpoint} already exists'
                + helpers.bcolors.ENDC
            )
            return 1
        endpoint_create(config, args.endpoint)
        print(helpers.bcolors.OKGREEN + 'Endpoint created' + helpers.bcolors.ENDC)
    elif args.action == 'describe':
        endpoints = [x for x in endpoint_list(config) if x.operation_id == args.endpoint]
        if len(endpoints) == 0:
            print(
                helpers.bcolors.FAIL
                + f'Endpoint {args.endpoint} not found'
                + helpers.bcolors.ENDC
            )
            return 1
        print('Operation ID:', endpoints[0].operation_id)
        print('Summary:', endpoints[0].summary)
        return 0
    elif args.action == 'deploy':
        endpoints = [x for x in endpoint_list(config) if x.operation_id == args.endpoint]
        if len(endpoints) == 0:
            print(
                helpers.bcolors.FAIL
                + f'Endpoint {args.endpoint} not found'
                + helpers.bcolors.ENDC
            )
            return 1

        print('# Deploy')
        endpoint = endpoints[0]
        runtime = endpoint.runtime(config)
        manager = steps.Manager(config, [
            steps.StepDeleteDir(f'{config.base_dir}/build/endpoints/{endpoint.operation_id}'),
            steps.StepCreatDir(f'{config.base_dir}/build/endpoints/{endpoint.operation_id}'),
            steps.StepCopyFileContent(
                f'{config.base_dir}/requirements.txt',
                f'{config.base_dir}/build/endpoints/{args.endpoint}/requirements.txt'
            ),
            steps.StepAppendFileContent(
                f'{config.base_dir}/build/endpoints/{args.endpoint}/requirements.txt',
                runtime.dependencies
            ),
            steps.StepCopyFileContent(
                f'{config.base_dir}/endpoints/{endpoint.operation_id}.py',
                f'{config.base_dir}/build/endpoints/{endpoint.operation_id}/main.py'
            ),
            steps.StepCopyFileContent(
                f'{config.base_dir}/api.yaml',
                f'{config.base_dir}/build/endpoints/{endpoint.operation_id}/api.yaml'
            ),
            steps.StepCopyDir(
                f'{config.base_dir}/endpoints/src',
                f'{config.base_dir}/build/endpoints/{endpoint.operation_id}/src'
            ),
            steps.StepCreateFile(
                f'{config.base_dir}/build/endpoints/{endpoint.operation_id}/env.temp.yaml',
                endpoint.env(config, is_simulate=args.simulate)
            ),
            steps.StepCommand(
                shlex.split("secrethub inject -i env.temp.yaml -o env.yaml"),
                work_dir=f'{config.base_dir}/build/endpoints/{endpoint.operation_id}',
                is_async=False,
            ),
            steps.StepCommand(
                shlex.split(runtime.command),
                work_dir=f'{config.base_dir}/build/endpoints/{endpoint.operation_id}',
                is_async=False,
            ),
        ], simulate=args.simulate)
        rc = manager.run()
        if rc != 0:
            return rc
        print(helpers.bcolors.OKGREEN + f'Deployed endpoint {endpoint.operation_id} success' + helpers.bcolors.ENDC)
        return 0
    elif args.action == 'serve':
        endpoints = [x for x in endpoint_list(config) if x.operation_id == args.endpoint]
        if len(endpoints) == 0:
            print(
                helpers.bcolors.FAIL
                + f'Endpoint {args.endpoint} not found'
                + helpers.bcolors.ENDC
            )
            return 1
        endpoint = endpoints[0]

        print('# Serve')
        manager = steps.Manager(config, [
            steps.StepCommand(
                shlex.split(f"functions-framework --source='{endpoint.operation_id}.py' --target main --debug --port=8004"),
                work_dir=f'{config.base_dir}/endpoints',
            ),
        ], simulate=args.simulate)
        rc = manager.run()
        if rc != 0:
            return rc
    elif args.action == 'test':
        endpoints = [x for x in endpoint_list(config) if x.operation_id == args.endpoint]
        if len(endpoints) == 0:
            print(
                helpers.bcolors.FAIL
                + f'Endpoint {args.endpoint} not found'
                + helpers.bcolors.ENDC
            )
            return 1
        endpoint = endpoints[0]

        path = f'{config.base_dir}/endpoints/{endpoint.operation_id}_test.py'
        if not os.path.exists(f'{config.base_dir}/endpoints/{endpoint.operation_id}_test.py'):
            print(
                helpers.bcolors.FAIL
                + f'Endpoint test {path} not exists'
                + helpers.bcolors.ENDC
            )
            return 1

        print('# Test')
        interpreter = 'python'

        venv_bin = 'venv/bin/python'
        if os.path.exists(venv_bin):
            interpreter = os.path.abspath('venv/bin/python')
        else:
            print(
                helpers.bcolors.WARNING
                + f'Venv {venv_bin} not found use default python interpreter'
                + helpers.bcolors.ENDC
            )

        manager = steps.Manager(config, [
            steps.StepCommand(
                shlex.split(f"{interpreter} {endpoint.operation_id}_test.py"),
                work_dir=f'{config.base_dir}/endpoints',
                verbose=True,
                is_async=False,
            ),
        ], simulate=args.simulate)
        rc = manager.run()
        if rc != 0:
            return rc
