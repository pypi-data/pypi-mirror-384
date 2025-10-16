# Serverless CLI

Serverless tool for the Google Cloud. You need the `gcloud` installed.

## Install

````sh
$ pip install shopcloud_serverless
$ serverless init
````

## Jobs

```sh
$ serverless jobs init
$ serverless jobs create <job-name>
$ serverless jobs deploy <job-name>
$ serverless jobs run <job-name>
```

__Secrets:__
Secrets can you write in the `.env.temp` file with the SecretHub syntax.

## Gateway

The main entrypoint for you serverless endpoint api is the gateway.

Init the gateway with the function and then deploy the endpoints and then you can deploy the api.yaml file with gateway deploy endpoint.

```sh
$ serverless gateway init
```

```sh
$ serverless gateway deploy
```


## Endpoints

Create a new endpoint for every path.

```sh
$ serverless endpoints init
$ serverless endpoints create health
```

Add the Endpoint in the `api.yaml` the `operation_id` must be unqie and is the identifier for the library.
You can change the `<endpoint-name>.yaml` with the parameters
- `memory`: memory in MB
- `runtime`: runtime of the function "python312"
- `trigger`: http or pubsub the value is the name of the `topic`
- `dependencies`: as string array

for development in the background we use [functions-framework](https://github.com/GoogleCloudPlatform/functions-framework-python)

```sh
$ serverless endpoints serve health
```

run the integration test suite

```sh
$ serverless endpoints test health
```

then deploy the function

```sh
$ serverless endpoints deploy health
```
