# Development

`Geneva` requires Python 3.10+, KinD, and Kuberay

## Setting up KinD
To install KinD please see [this page](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)

TL;DR

for Linux
```bash
# For AMD64 / x86_64
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-linux-amd64
# For ARM64
[ $(uname -m) = aarch64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-linux-arm64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

for Mac
```bash
# For Intel Macs
[ $(uname -m) = x86_64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-darwin-amd64
# For M1 / ARM Macs
[ $(uname -m) = arm64 ] && curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.27.0/kind-darwin-arm64
chmod +x ./kind
mv ./kind /some-dir-in-your-PATH/kind
```

## Setting up Kuberay
To install Kuberay please see [this page](https://ray-project.github.io/kuberay/deploy/helm/)

TL;DR
```bash
helm repo add kuberay https://ray-project.github.io/kuberay-helm/

helm install kuberay-operator kuberay/kuberay-operator

# Check the KubeRay operator Pod in `default` namespace
kubectl get pods
# NAME                                READY   STATUS    RESTARTS   AGE
# ...
```

## Building and Testing
See the Makefile

## How to Release

We use github actions to release bits to our pypi repos.

Go to https://github.com/lancedb/geneva/actions/workflows/publish.yml and choose "Run workflow".  Choose your branch and then the bump type.

You can use this command to see how bump types will change the version for release.

```
$ uv run bump-my-version
0.2.4-beta1 ── bump ─┬─ major ─ 1.0.0-beta0
                     ├─ minor ─ 0.3.0-beta0
                     ├─ patch ─ 0.2.5-beta0
                     ├─ pre_l ─ 0.2.4
                     ╰─ pre_n ─ 0.2.4-beta2
```

You can see that the diferent options yield different release numbers.

Any release without "beta" in the version will be publshed to official pypi (https://pypi.org/project/geneva/) while any release with "beta" will be publisedh to the fury repo (https://pypi.fury.io/lancedb/geneva).
