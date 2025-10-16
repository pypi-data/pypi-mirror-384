# Ensemble Tool

```
imsi ensemble --help
```

### High level config: The entry config

Calling the ensemble tool requires a high-level config be set in the `--config-path` argument. E.g.

```
imsi ensemble --config-path=config.yaml
```

The entry config consists of two main sub-levels, the `ensemble_level` and `member_level`.

### `ensemble_level` parameters
These are parameters that need only be logically defined *once per ensemble run*. For example:

```yaml
ensemble_level:
  user: ${oc.env:USER} # required, this recommended example sets omegaconf interpolation to $USER
  run_directory: /output/path/to/ensemble/setup_dirs/ # optional, defaults to cwd
  config_table: table.csv # optional
  share_repo: true # optional, defaults to false
```

| Parameter       | Description                                      | Default Value       |
|-----------------|--------------------------------------------------|---------------------|
| user            | The user running the ensemble                    | `$USER`, can be overriden by user               |
| run_directory   | Directory where ensemble setup directories are created | Current working directory |
| config_table    | Path to the configuration table. See more on configuration tables below                  | `None`           |
| share_repo      | If True, the first ensemble member's setup `src` repository is symlinked to each subsequent directory's setup directory.               | `False`               |
| aliases      | `alias: parameter` pairs to help keep table headers short.               | `None`               |

### `member_level` parameters
These are parameters that are defined *once per ensemble member* and can represent any imsi compatible parameter. Most importantly, *any* `member_level` variable can be either a value, or a list of values. If a list is specified, the ensemble tool will setup a new run for each unique value. The minimum set of required `member_level` parameters are the same as `imsi setup`, i.e.

| Parameter | Description                                      | Default Value |
|-----------|--------------------------------------------------|---------------|
| runid     | Unique identifier for each ensemble member run   | `None`        |
| model     | Model configuration for the ensemble member      | `None`        |

### Supported Configuration Formats for `ensemble_level: config_table`

Config tables are convenient configuration objects that store discrete ensemble member runs and their associated modified parameter space. IMSI's ensemble tool currently supports `.yaml` and `.csv` configuration formats. Note: The legacy `.txt` format is also supported, however users should note that white-space delimiting is inherently ambiguous. We are therefore transitioning to a `.csv` format for their ensemble tables instead. Future versions of IMSI will deprecate `.txt` support. A  `DeprecationWarning` is raised whenever a `.txt` table is used.

While `member_level` parameters can be modified directly to configure ensemble runs through configurations that specify a *list* of values at the end of a key-path (that is, the key and the hierarchy of parent keys of a given value), config tables are lists of configured *members*. For an illustrative example:

The following `member_level` configuration of two ensemble members:

```yaml
ensemble_level:
  user: ${oc.env:USER} # required, this recommended example sets omegaconf interpolation to $USER
  run_directory: /output/path/to/ensemble/setup_dirs/ # optional, defaults to cwd
  share_repo: true # optional, defaults to false

member_level:
  runid: [run-01, run-02]
  model: [canesm51_p1, canam51_p1]
  exp: [cmip6-piControl, cmip6-amip]
```
is equivalent to the following configuration:

```yaml
# entry config.yaml
ensemble_level:
  user: ${oc.env:USER} # required, this recommended example sets omegaconf interpolation to $USER
  run_directory: /output/path/to/ensemble/setup_dirs/ # optional, defaults to cwd
  config_table: config/example.csv # or config/example.yaml
  share_repo: true

member_level:
  runid: null # values are overidden in config table
```
CSV config table:
```text
# config/example.csv
runid,  model,       exp
run-01, canesm51_p1, cmip6-piControl
run-02, canam51_p1,  cmip6-amip
```
(equivalent to)
YAML config table:
```yaml
# config/example.yaml
- runid: run-01
  model: canesm51_p1
  exp: cmip6-piControl

- runid: run-02
  model: canam51_p1
  exp: cmip6-amip
```

Note that at this time, a minimum `member_level` config is required to initialize the ensemble runs even if all parameters are coming entirely from a config table. Users can simply set `member_level` as the following in this scenario:

```yaml
member_level:
  runid: null
```

For `.csv` and `.yaml` config tables, the ensemble tool now supports configurations where users can omit parameters from ensemble runs that are present in other members. For example, the following config tables are valid:

```text
runid,      model,       exp
run-01-csv, canesm51_p1,
run-02-csv, canam51_p1,  cmip6-amip
```

```yaml
- run-01-yaml-table:
  model: canesm51_p1

- run-02-yaml-table:
  model: canam51_p1
  exp: cmip6-amip
  experiment: ...
  components: ...
```

### Broadcasting Configuration Parameters from `member_level`
As mentioned above, keys that are present in a config table override identical keys at the `member_level`. However, if there are keys in a `member_level` config that *don't* exist in the config table, the ensemble tool wil attempt to *broadcast* these values so that each ensemble member is initialized with this value. Broadcasting simply means copying values to have the same length. In this case, single values are copied into each ensemble member's configuration. 

The logic of how configurations are resolved is the following:

1. If a key path exists in *both* the `member_level` and `config_table`, the `config_table` values are resolved and `member_level` values are overidden.
2. If a key path exists in *only* the `member_level` and *not* the `config_table` and the value is a single value it is *broadcasted* and populated into the ensemble configuration. 
3. If a key path value exists as a list in the `member_level`, the ensemble tool will try to inject this into the ensemble configuration. However, the length of the list must match the number of ensemble members specified in the config table.
