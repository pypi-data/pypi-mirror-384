# Solution Recipe

The assembler builds solutions from a recipe. This document will describe how to write a recipe section by section.

## Solution Header

```toml
recipe_vsn = "1.0.0"

[solution]
    name = "Power Monitoring"
    slug = "power_monitoring"
    version = "1.3.0"
    description = "Shoestring Power Monitoring Starter Solution"
```

| Key           | Description                                                                                                                                         |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
| `recipe_vsn`  | Recipe format version - currently only 1.0.0 used.                                                                                                  |
| `name`        | Single phrase name of the solution                                                                                                                  |
| `slug`        | Underscore separated slug for the solution                                                                                                          |
| `version`     | Version string - Major . Minor . Patch                                                                                                              |
| `description` | Text describing the solution - not currently used for anything but seems like a good thing to have, even if purely as context when reading a recipe |

## Sources

### Format:

```toml
[source.<source_name>]
    # FILE SOURCE
    file.path = "<file path - usually relative>"
    file.mode = "<copy | link>"

    # or

    # GIT SOURCE 
    git.path = "<see below>"
    git.tag = "<tag value>"
    # or
    git.branch = "<branch name>"
```

* `file` source takes precedence over `git` if both are present.
* `file.mode` is either `"copy"` or `"link"`. If **copy**, the contents at `file.path` are copied, if **link** a symlink is used.
* if `file.mode` not present - defaults to `"copy"`
* `git.path` can take the following forms:
  * `<repo_name>` - DigitalShoestringSolutions org on GitHub assumed (`https://github.com/DigitalShoestringSolutions/` added as a prefix)
  * `<user or org>/<repo_name>` - GitHub is assumed (`https://github.com/` added as a prefix)
  * `<full url>` (including more than two `/`) - no assumptions are made
* if `git.tag` and `git.branch` both present, `git.tag` takes precedence

> `source_name` must be unique within the recipe and must be a valid for use as a directory name (You can check your recipe with the assembler and it will warn you if this is not the case)

### Example:

```toml
[source.current_sensing]
    git.path = "sm_SensingDC"
    git.branch = "rc/1.0.0"
[source.data_storage]
    git.path = "DigitalShoestringSolutions/sm_timeseries_db"
    git.branch = "rc/2.0.0"
[source.grafana]
    git.path = "sm_grafana_ui"
    git.branch = "rc/2.0.0"
[source.analysis]
    git.path = "sm_analysis"
    git.branch = "main"
[source.graph_src]
    file.path = "./custom_service_modules/graph"
    file.mode = "link"
[source.mqtt_broker]
    git.path = "sm_mqtt_broker"
    git.branch = "rc/2.0.0"
```

## Service Modules

### Format:

```toml
[service_module.<service_module_name>]
    source = "<source_name>"
    containers = ["<list of one or more container names>"]
    ports.<container_name>.<port_name> = <host port number>
    ... # more ports entries
    alias.<container_name> = "<alias in docker network>"   # .docker.local suffix added on the end
    ...  # more alias entries (max 1 per container)
    volume.<container_name>.<volume_name> = "<host_path>"
    ... # more volume entries
    template.<variable_name> = "<value>"
    ...  # more template entries
```

#### `<service_module_name>`

`service_module_name` must be unique within the recipe and must be a valid for use as a directory name (just like `source_name` above).

#### `source = "<source_name>"`

`source_name` value must be one of the source names defined as `[source.<source_name>]` in the previous section.

### `containers = ["<list of one or more container names>"]`

The list of container names will typically only have a single entry, but may have more than one in certain scenarios. The container names come from the service module source’s meta.toml file. In the example below the two container names are `influx` and `telegraf` which would lead to `containers = ["influx","telegraf"]` if both were used.

```toml
[influx]
    dockerfile = "influx.Dockerfile"
    compose_partial = "influx.snippet.yml"
    volume.data.path = "/var/lib/influxdb2"
    volume.data.mode = "rw"
    volume.user_config.ignore = true
    
    ports.ui = 8086

[telegraf]
    dockerfile = "telegraf.Dockerfile"
    compose_partial = "telegraf.snippet.yml"
    volume.user_config.ignore = true 
    volume.data.ignore = true
```

> Example meta.toml file from timeseries_db

### `ports.<container_name>.<port_name> = <host port number>`

The `ports` entry describes a mapping between a container port and a host port.

`container_name` is as described in the prior section. The `port_name` corresponds to the port name in the `meta.toml` (in the form `ports.<port_name>` - `ports.ui` for a `port_name` of `ui` in the example above).

> The `port_name` in the recipe and in the meta file must match

For example, if the recipe had `ports.app.api = 8001` and the corresponding `meta.toml` had:

```toml
[app]
    ports.api = 80
```

Then this would make port 80 within the container available at port 8001 on the host device (meaning other devices could access the api at port 8001).

### `volume.<container_name>.<volume_name> = "<host_path>"`

The host portion of a volume mapping, similar to a port mapping above.

An example of this is the barcode scanning service module which includes a mapping for `/run/udev` to detect and access barcode scanners

```toml
[service_module.scanner-1]
    ...
    volume.sensing.udev = "/run/udev"
    ...
```

> recipe.toml
```toml
[sensing]
    ...
    volume.udev.path = "/run/udev"
    volume.udev.mode = "ro"
```

> meta.toml

### `template.<variable_name> = "<value>"`

`template` entries are used to define variable names and values that are applied using mustache style template replacement (`{{variable_name}}`) to the provided snippets file.

> The snippets file is combined with the content generated by the assembler to form the compose entry for each container in a service module.

A common application of this is setting the log level:

```toml
[service_module.scanner-1]
    ...
    template.log_level = "info"
    ...

```

> recipe.toml
```yaml
...
command: ["python", "main.py", "--log", "{{log_level}}"]
...
```

> snippet.yaml

## Infrastructure

Same as Service Modules, just with `[infrastructure.<name>]` instead of `[service_module.<name>]` at the top level.
