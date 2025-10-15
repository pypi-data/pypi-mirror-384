# CONTRIBUTING

## Unit Test

```
$ tox -e py39
```

## Lint, MyPY

```
$ tox -e lint
$ tox -e mypy
```

## CLI Development

Run the latest CLI code
```
$ uv run python -m strats.cmd.cmd
```

## Run E2E Test Applications

```
# e.g.,
$ PYTHONPATH=. strats runserver --target tests.e2e.e02_stream_monitor_negative.main:create_app --factory
```
