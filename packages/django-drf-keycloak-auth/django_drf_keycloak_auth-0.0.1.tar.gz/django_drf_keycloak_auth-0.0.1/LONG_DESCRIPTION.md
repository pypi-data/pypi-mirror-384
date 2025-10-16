# django-drf-keycloak-auth

When using `Django`, `DRF`, and `Keycloak` for authentication and permission management, `django-drf-keycloak-auth` can make your work easier.

## Getting Started

```bash
pip install django-drf-keycloak-auth

OR

uv add django-drf-keycloak-auth
```

## Usage

## Examples

## Deploy project(memo for developer)

### setuptools version

The latest `setuptools`(version 80.9.0) produces `.whl` files with a `METADATA` version of `2.4`. You can check this by running:

```bash
unzip -p dist/*.whl '*/METADATA' | sed -n '1,160p'
```

Note that `TestPyPI` only supports `METADATA` versions `1.0–2.2`. Therefore, if you plan to publish your package to TestPyPI, you should not use the latest `setuptools`.

### Deploy to TestPyPI

> Depending on the network environment, you may need to use a proxy.

```bash
# https://test.pypi.org/
expect interactive_deploy_test.expect
```

> Install `django-drf-keycloak-auth` from TestPyPI.
>
> ```bash
> uv pip uninstall django-drf-keycloak-auth
> 
> uv pip install --no-cache-dir \
>   --index-url https://pypi.org/simple \
>   --extra-index-url https://test.pypi.org/simple \
>   --index-strategy unsafe-best-match \
>   django-drf-keycloak-auth==0.0.1
> ```
>
> OR
>
> `uv pip install --index-url https://test.pypi.org/simple django-drf-keycloak-auth==0.0.1`

### Deploy to PyPI

> Depending on the network environment, you may need to use a proxy.

```bash
# https://pypi.org/
expect interactive_deploy.expect
```

### How to mark a version as yanked

```bash
twine yank <package_name> --version <version> --reason "Reason this release was yanked: Yanked due to <reason>"
```


# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2025-10-15

-   First commit(Only for test)



