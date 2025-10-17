# kube-compose

An opinionated way of deploying docker-compose to kubernetes clusters by managing them with a helm chart.

The CLI is intended to be easy to use for those familiar with docker-compose and includes some additional features. Basically all features expect you to have a `docker-compose.yaml` file in the working directory.

- `kube-compose init` => specify the helm release name/namespace in your `docker-compose.yaml` file
- docker-compose-like features
  - `kube-compose up` => `helm install/upgrade` + volume create (pvc)
  - `kube-compose down` => `helm uninstall`
  - `kube-compose ps` => `helm status`
  - `kube-compose logs SERVICE` => `kubectl logs`
  - `kube-compose exec SERVICE` => `kubectl exec`
  - `kube-compose restart SERVICE` => `kubectl rollout restart`
  - `kube-compose top SERVICE` => `kubectl exec pod -- cat /proc/*/stats`
  - `kube-compose stats SERVICE` => `kubectl top pod`
  - `kube-compose events SERVICE` => `kubectl events`
  - `kube-compose start SERVICE` => `kubectl scale --replicas={compose_defined}`
  - `kube-compose scale SERVICE` => `kubectl scale --replicas={user_specified}`
  - `kube-compose stop SERVICE` => `kubectl scale --replicas=0`
- helm-like features
  - `kube-compose ls` => `helm list`
  - `kube-compose template` => `helm template`
  - `kube-compose history` => `helm history`
  - `kube-compose status` => `helm status`
  - `kube-compose get WHAT` => `helm get WHAT`
  - `kube-compose rollback REVISION` => `helm rollback REVISION`
- additional features
  - `kube-compose volume ...` => manage docker-compose defined volumes as persistent volume claims
    - `kube-compose volume create [VOLUME]` => create the claim(s)
    - `kube-compose volume rm [VOLUME]` => delete the claim(s)
  - `kube-compose diff` => `diff -Naur <(helm get values) <(docker-compose config)`
  - `kube-compose drift` => `helm template | kubectl diff -f -`
  - `kube-compose version SERVICE [<newversion> | major | minor | patch]` => like npm version but for services in the docker-compose.yaml
  - `kube-compose port-forward SERVICE local:remote`

## Pre-requisites
- kubernetes cluster
- kubectl
- helm
- docker-compose

## Installation
```bash
# install off of pypi
pip install kube-compose

# verify install was successful
kube-compose --help
```

## CLI Usage with Docker
```bash
# Assuming your kubeconfig is at the default location ~/.kube/config
alias kube-compose="docker run -v .:/work -v ~/.kube/config:/work/.kube/config -it u8sand/kube-compose"

# verify install was successful
kube-compose --help
```


## End-to-end Example with K3D
```bash
# launch a test kubernetes cluster
k3d cluster create -a1 -p "80:80@loadbalancer" -p "443:443@loadbalancer"

# one option for auto-creating Ingress resources from annotations on the deployment
helm repo add maayanlab https://maayanlab.github.io/helm-charts
helm install kubernetes-auto-ingress maayanlab/kubernetes-auto-ingress --set ingressClassName=traefik

# with one of the unit tests
cd tests/units/simple
# OR for testing the current source base
# alias kube-compose="python -m kube_compose -f tests/units/simple/docker-compose.yaml"

# start the docker-compose service(s) on the kubernetes cluster
kube-compose up
# check the status of the kubernetes resources
kube-compose ps
# check logs of a service
kube-compose logs test-web
# get into the service container
kube-compose exec -it test-web /bin/sh
# restart a service
kube-compose restart test-web
# see top processes running on the service
kube-compose top test-web
# see cpu/memory being used by the service
kube-compose stats test-web
# see any events that may have occurred for the service
kube-compose events test-web
# stop the service temporarily
kube-compose stop test-web
# start it back up
kube-compose start test-web
# scale the service up
kube-compose scale test-web=2

# we can see helm charts (like kube-compose deployed things) deployed to the cluster with
kube-compose ls --context k3d-k3s-default
# we can get the actual deployment kubernetes would use with
kube-compose template
# we can see what revision we're at/when it was updated with
kube-compose history
kube-compose status
# we can rollback (with optional version number) if a change we made was bad with
kube-compose rollback
# we can get information like the docker-compose.yaml that was deployed with
kube-compose get values
# we can access cluster services locally with port-forward hostport:containerport
kube-compose port-forward test-web 8080:80
# we can manage persistent volumes with the volume subcommand
kube-compose volume ls
# we can version image in the docker-compose
kube-compose version test-web 1.0.0
# we can diff our local docker-compose with the one that is deployed
kube-compose diff
# we can use drift to see if the deployment spec has been modified outside of kube-compose
kube-compose drift
# let's revert that change
kube-compose version test-web latest

# remove it from the cluster (with volumes, otherwise they stay)
kube-compose down -v

# remove test cluster
k3d cluster delete
```
