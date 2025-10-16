def api_endpoint(name: str, **kwargs) -> str:
  """
    Create an API endpoint.

    Parameters:
    - name (str): Name of the endpoint.
    - project (str): Project name.
    - region (str): Region name.

    Returns:
    - str: The content of the endpoint in Swagger OpenAPI 2.0 format
    """
  project = kwargs.get('project')
  region = kwargs.get('region')
  content = f"""
get:
  tags:
  - "Main"
  summary: {name} Endpoint
  operationId: {name}
  consumes:
  - "application/json"
  x-google-backend:
      address: https://{region}-{project}.cloudfunctions.net/{name}
  security:
  - api_key: []
  responses:
      "200":
      description: A successful response
    """
  return content

def api(**kwargs):
    """
    This function creates an Swagger API.

    Parameters:
    - api_title (str): Title of the API (default: 'My API')
    - api_description (str): Description of the API (default: 'My API Description')
    - project (str): Project name
    - region (str): Region name

    Returns:
    - str: The content of the endpoint in Swagger OpenAPI 2.0 format.
    """
    api_title = kwargs.get('api_title', 'My API')
    api_description = kwargs.get('api_description', 'My API Description')
    project = kwargs.get('project')
    region = kwargs.get('region')
    return f"""swagger: '2.0'
info:
  title: {api_title}
  description: {api_description}
  version: 0.0.0
schemes:
  - https
produces:
  - application/json
securityDefinitions:
  api_key:
    type: "apiKey"
    name: "X-API-KEY"
    in: "header"
paths:
  /health:
    get:
      tags:
      - "Main"
      summary: Health Endpoint
      operationId: health
      consumes:
      - "application/json"
      x-google-backend:
        address: https://{region}-{project}.cloudfunctions.net/health
      security:
      - api_key: []
      responses:
        "200":
          description: A successful response
          schema:
            $ref: "#/definitions/HealthResponse"
  /docs:
    get:
      tags:
      - "Documentation"
      summary: Documentation
      operationId: docs
      x-google-backend:
        address: https://{region}-{project}.cloudfunctions.net/docs
      parameters:
      - in: "query"
        type: "string"
        name: "content"
        description: "Specify the content"
        enum: ["docs", "openapi.json"]
        default: "docs"
      responses:
        "200":
          description: A successful response
definitions:
  HealthResponse:
    type: "object"
    required:
      - value
    properties:
      status:
        type: "string"

"""


def endpoint_main(name: str, **kwargs):
    if name == 'docs':
        return """import yaml
import os
import importlib
import functions_framework
from flask import jsonify

try:
    import src
except Exception:
    src = importlib.import_module('src')


@functions_framework.http
def main(request):
    if request.args.get('content') == 'openapi.json':
        file = "api.yaml"
        if os.environ.get('ENV') != 'production':
            file = "./../api.yaml"
        with open(file) as f:
            data = yaml.safe_load(f.read())
        return jsonify(data)

    return src.services.docs.template_docs()

"""

    return """import importlib
import functions_framework
from flask import jsonify

try:
    import src
except Exception:
    src = importlib.import_module('src')


@functions_framework.http
def main(request):
    return jsonify({'status': src.services.#SERVICE#.get_health()})

""".replace('#SERVICE#', name)


def endpoint_test(name: str, **kwargs):
    return """
import pytest
from shopcloud_serverless import endpoints_utils


class Test(endpoints_utils.TestEndpointAPIIntegration):
    FILE = __file__

    def test_main(self):
        response = self.client.get("/")
        assert response.status_code == 200


if __name__ == "__main__":
    exit_code = pytest.main([__file__])
    exit(exit_code)

""".replace('#SERVICE#', name)


def endpoint_config(name: str, **kwargs):
    return """trigger: http
"""


def endpoint_lib(name: str, **kwargs):
    if name == 'docs':
        return """def template_docs():
    return \"""<!DOCTYPE html>
<html>
<head>
<link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css">
<link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
<title>Swagger UI</title>
</head>
<body>
<div id="swagger-ui">
</div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js"></script>
<!-- `SwaggerUIBundle` is now available on the page -->
<script>
const ui = SwaggerUIBundle({
    url: '/docs?content=openapi.json',
"dom_id": "#swagger-ui",
"layout": "BaseLayout",
"deepLinking": true,
"showExtensions": true,
"showCommonExtensions": true,
oauth2RedirectUrl: window.location.origin + '/docs/oauth2-redirect',
presets: [
    SwaggerUIBundle.presets.apis,
    SwaggerUIBundle.SwaggerUIStandalonePreset
    ],
})
</script>
</body>
</html>
\"""

"""

    return """def get_health():
    return "ok"

    """


def requirements():
    return """functions-framework
pyyaml
"""


def job_main():
    return """from shopcloud_serverless import Environment

if __name__ == "__main__":
    env = Environment()
    print(env.get('ENV'))
    print("Hello World")

"""


def job_procfile():
    return """web: python3 main.py"""
