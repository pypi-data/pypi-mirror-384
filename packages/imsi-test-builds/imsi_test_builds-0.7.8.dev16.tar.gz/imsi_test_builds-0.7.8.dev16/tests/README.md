Make sure you have installed imsi with tests. E.g. 

```
pip install -e .[tests]
```

To run tests, you can specify the target setup parameters in `tests/.env.test`. The defaults are defined in `tests/conftest.py`:

```bash
coverage run -m pytest tests/
```

Please view [coverage](https://coverage.readthedocs.io/en/7.9.2/) for more information on running and reading test results.