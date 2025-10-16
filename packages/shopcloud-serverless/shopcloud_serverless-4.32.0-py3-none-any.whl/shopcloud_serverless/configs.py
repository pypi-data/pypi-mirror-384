from pathlib import Path

import yaml

from . import helpers


class Config:
    VERSION = 'V4'

    def __init__(self, **kwargs):
        self.filename = kwargs.get('config_filename')
        if self.filename is None:
            self.filename = 'serverless.yaml'
        self.version = None
        self.base_dir = None
        self.cloud_type = None
        self.cloud_project = None
        self.region = None
        self.endpoint_api_title = None
        self.endpoint_api_description = None
        self.endpoint_deploy_version = 0

    def load(self) -> bool:
        if not Path(self.filename).exists():
            print(
                helpers.bcolors.FAIL
                + 'Config file not found. Please run `init` first.'
                + helpers.bcolors.ENDC
            )
            return False

        with open(self.filename) as f:
            data = yaml.safe_load(f)
            self.version = data.get('version', '')
            self.base_dir = data.get('base_dir', '.')
            self.cloud = data.get('cloud')
            self.project = data.get('project')
            self.region = data.get('region')
            self.endpoint_api_title = data.get('endpoints', {}).get('api_title')
            self.endpoint_api_description = data.get('endpoints', {}).get('api_description')
            self.endpoint_deploy_version = int(data.get('endpoints', {}).get('deploy_version', 0))

        if str(self.version).strip() != self.VERSION:
            print(
                helpers.bcolors.FAIL
                + 'Config file is not compatible with this version. Please run `init` again.'
                + helpers.bcolors.ENDC
            )
            return False

        return True

    def save(self):
        with open(self.filename, 'w') as f:
            yaml.dump(self.dict(), f)

    def dict(self):
        return {
            'version': self.VERSION,
            'base_dir': self.base_dir or '.',
            'cloud': self.cloud,
            'project': self.project,
            'region': self.region,
            'endpoints': {
                'api_title': self.endpoint_api_title,
                'api_description': self.endpoint_api_description,
                'deploy_version': self.endpoint_deploy_version,
            },
        }
