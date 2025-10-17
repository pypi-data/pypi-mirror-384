# Delta Core

## prerequisites
### Initialize or update submodule dependency
```
git submodule update --init
```
### Install Ansible requirements
this action requires credentials to GitLab at https://git2.gael.fr 
```shell
cd ansibleworkplan
ansible-galaxy install --force
```

## Run the DeltaTwin-Run microservice
### command
```shell
python -m delta.run.api.api
```
### Environment variables
| name                        | default                                         | description                              |
|:----------------------------|:------------------------------------------------|:-----------------------------------------|
| DELTA_GSS_API_URL           |                                                 | DeltaTwin GSS API                        |
| DELTA_RUN_LIMIT             | 10                                              | Maximal active parallel runs per owner   |
| DELTA_EVICTION_ACTIVE       | false                                           | Active run eviction                      |
| DELTA_EVICTION_KEEP_PERIOD  | 48                                              | Run retention time in hour               |
| DELTA_DATABASE_URL          | sqlite:///.delta-run.db?check_same_thread=false | DeltaTwin Run database URL               |
| DELTA_DATABASE_SHOW_SQL     | false                                           | Log database SQL requests                |
| DELTA_PAGE_LIMIT            | 100                                             | Max element returned from a request      |
| DELTA_SOCKETIO_ADAPTER_URL  |                                                 | Redis server URL (redis://hostname:port) |
| DELTA_KEYCLOAK_JWKS_URL     |                                                 | OpenID certs endpoint                    |
| DELTA_IMAGE_REPO_HOSTNAME   |                                                 | image registry hostname for model images |
| DELTA_IMAGE_REPO_USERNAME   |                                                 | image registry username                  |
| DELTA_IMAGE_REPO_PASSWORD   |                                                 | image registry password                  |
| DELTA_S3_ENDPOINT           |                                                 | S3 object storage endpoint               |
| DELTA_S3_REGION             |                                                 | S3 object storage region                 |
| DELTA_S3_ACCESS_KEY         |                                                 | S3 object storage access key             |
| DELTA_S3_SECRET_ACCESS_KEY  |                                                 | S3 object storage secret access key      |
| DELTA_S3_BUCKET             |                                                 | S3 object storage bucket name            |
| DELTA_K8S_CONTEXT           |                                                 | K8s config context name                  |
| DELTA_K8S_NAMESPACE         |                                                 | K8s config namespace                     |
| DELTA_K8S_CLUSTER_NAME      |                                                 | K8s config cluster name                  |
| DELTA_K8S_CLUSTER_CERT_AUTH |                                                 | K8s config cluster cert                  |
| DELTA_K8S_CLUSTER_SERVER    |                                                 | K8s config cluster server                |
| DELTA_K8S_USER_NAME         |                                                 | K8s config user name                     |
| DELTA_K8S_USER_CLI_CERT     |                                                 | K8s config user client cert              |
| DELTA_K8S_USER_CLI_KEY      |                                                 | K8s config user client key               |

## Docker
### Build image
All prerequisites are managed in the Docker image.
```
docker build --build-arg "GIT_USERNAME=<git2.gael.fr username>" --build-arg "GIT_PASSWORD=<git2.gael.fr password>" -t registry.gael.fr/gael10/delta/software/delta-core/delta-run .
```
### Compose
#### Environment variables
| name                         | default                    | description                              |
|:-----------------------------|:---------------------------|:-----------------------------------------|
| DB_USERNAME                  |                            | database username                        |
| DB_PASSWORD                  |                            | database password                        |
| DB_DATABASE                  |                            | database name                            |
| DB_DRIVER                    |                            | database driver (psycopg)                |
| DELTA_GSS_API_URL            |                            | DeltaTwin GSS API URL                    |
| DELTA_RUN_LIMIT              |                            | Maximal active parallel runs per owner   |
| DELTA_EVICTION_ACTIVE        |                            | Active run eviction                      |
| DELTA_EVICTION_KEEP_PERIOD   |                            | Run retention time in hour               |
| DELTA_SOCKETIO_ADAPTER_URL   | redis://redis-adapter:6379 | Redis server URL                         |
| DELTA_KEYCLOAK_JWKS_URL      |                            | OpenID certs endpoint                    |
| DELTA_DATABASE_SHOW_SQL      |                            | Log database SQL requests                |
| DELTA_IMAGE_REPO_HOSTNAME    |                            | image registry hostname for model images |
| DELTA_IMAGE_REPO_USERNAME    |                            | image registry username                  |
| DELTA_IMAGE_REPO_PASSWORD    |                            | image registry password                  |
| DELTA_S3_ENDPOINT            |                            | S3 object storage endpoint               |
| DELTA_S3_REGION              |                            | S3 object storage region                 |
| DELTA_S3_ACCESS_KEY          |                            | S3 object storage access key             |
| DELTA_S3_SECRET_ACCESS_KEY   |                            | S3 object storage secret access key      |
| DELTA_S3_BUCKET              |                            | S3 object storage bucket name            |
| DELTA_K8S_CONTEXT            |                            | K8s config context name                  |
| DELTA_K8S_NAMESPACE          |                            | K8s config namespace                     |
| DELTA_K8S_CLUSTER_NAME       |                            | K8s config cluster name                  |
| DELTA_K8S_CLUSTER_CERT_AUTH  |                            | K8s config cluster cert                  |
| DELTA_K8S_CLUSTER_SERVER     |                            | K8s config cluster server                |
| DELTA_K8S_USER_NAME          |                            | K8s config user name                     |
| DELTA_K8S_USER_CLI_CERT      |                            | K8s config user client cert              |
| DELTA_K8S_USER_CLI_KEY       |                            | K8s config user client key               |
