# User Config Templates

## Versioning

A user config template has a version specified in the `solution_files/user_config_templates/<source_name>/__templating/__version__` file. The version string is in the format `<major>.<minor>`. A major version change indicates that there has been a breaking change and the user config files need to be regenerated with input from a user. A minor version change is a non-breaking change, the user config files do not need to be regenerated, and will work as is. However regenerating may be beneficial (e.g. enabling additional features).

## Prompts

The user config prompts are stored in the `prompts.yaml` file at `solution_files/user_config_templates/<source_name>/__templating/`. Each prompt has a `key` which us the variable name that the answer is asigned to for generation. It may also have an `answer_key` entry which is the name that the answer is assigned to when saving the answers to `prev_answers.json`. The contents of `prev_answers.json` are used to set the default value to the previous answer when doing re-generation of user config from templates.

### Prompt types

The prompts system supports the following prompt types:

#### Constant value prompts

Prompts that only contain a `key` and a `value`. Nothing is shown to the user, contents of `value` is assigned to variable specified by `key`. (Only really useful for options prompts- see below)

#### String prompts

If the prompt entry only contains a `key` and `text` then the user will be prompted with the contents of `text` and their typed answer will be assigned to the variable specified by `key` as a string.

#### Option prompts

If the prompt entry contains an `option` field, then the prompt is presented as multiple choice. The `option` field contains an array of entries. Each entry contains a `prompt` and either a `value` or a `target`. The `prompt` is the text that is shown next to that option in the multiple choice. If an entry has a `value` then that value is assigned to the option prompts key.

In the example below: `var_name = option_1` if the first option is selected.

If the entry has a `target` field, then that `target` field contains an array of one or more subsequent prompts that are displayed to the user.

In the example below, if the second option is chosen, then `different_var_name = option_2` from the constant value prompt and a subsequent prompt to select a sub option is shown.

Example:

```yaml
---
- key: var_name
  text: Choose an option
  option:
    - prompt: Option 1
      value: option_1
    - prompt: Option 2
      target: 
        - key: different_var_name
          value: option_2
        - key: next_tier
          text: Choose sub option
          option:
            ... etc.
```

> Note: the top level `---` indicates a top level array in yaml

## Template replacement

The assembler uses jinja2 as a template engine - refer [here](https://jinja.palletsprojects.com/en/stable/templates/) for documentation.

## Full example

A deeply nested prompt to choose which variant is deployed for power monitoring:

```yaml
---
- key: machine_name
  text: Choose a name for this machine
- answer_key: __variant
  text: Which power monitoring variant are you deploying
  option:
    - prompt: basic
      target:
        - answer_key: __adc_basic
          text: Which ADC are you using
          option:
            - prompt: Grove ADC v1.0
              target:
                - answer_key: __basic_grove_1_0
                  key: module_config_file
                  text: Which sensing configuration are you using
                  option:
                    - prompt: Single phase
                      value: pm_b_1p_grove_v1.0
                    - prompt: Three phase balanced (single clamp)
                      value: pm_b_3pb_grove_v1.0
                    - prompt: Three phase unbalanced
                      value: pm_b_3pu_grove_v1.0
                    - prompt: Gravity DC current sensor
                      value: pm_dc_gravity_grove_v1.0
            - prompt: Grove ADC v1.1
              target:
                - answer_key: __basic_grove_1_1
                  key: module_config_file
                  text: Which sensing configuration are you using
                  option:
                    - prompt: Single phase
                      value: pm_b_1p_grove_v1.1
                    - prompt: Three phase balanced (single clamp)
                      value: pm_b_3pb_grove_v1.1
                    - prompt: Three phase unbalanced
                      value: pm_b_3pu_grove_v1.1
                    - prompt: Gravity DC current sensor
                      value: pm_dc_gravity_grove_v1.1
            - prompt: ADS1115
              target:
                - answer_key: __basic_ads1115
                  key: module_config_file
                  text: Which sensing configuration are you using
                  option:
                    - prompt: Single phase
                      value: pm_b_1p_ads1115
                    - prompt: Three phase balanced (single clamp)
                      value: pm_b_3pb_ads1115
                    - prompt: Three phase unbalanced
                      value: pm_b_3pu_ads1115
                    - prompt: Gravity DC current sensor
                      value: pm_dc_gravity_ads1115
            - prompt: BC Robotics
              target:
                - answer_key: __basic_bc
                  key: module_config_file
                  text: Which sensing configuration are you using
                  option:
                    - prompt: Single phase
                      value: pm_b_1p_bc_robotics
                    - prompt: Three phase balanced (single clamp)
                      value: pm_b_3pb_bc_robotics
                    - prompt: Three phase unbalanced
                      value: pm_b_3pu_bc_robotics
                    - prompt: Gravity DC current sensor
                      value: pm_dc_gravity_bc_robotics
            - prompt: Sequent 16 channel Universal Inputs ADC
              target:
                - answer_key: __basic_sequent
                  key: module_config_file
                  text: Which sensing configuration are you using
                  option:
                    - prompt: Single phase
                      value: pm_b_1p_sequent
                    - prompt: Three phase balanced (single clamp)
                      value: pm_b_3pb_sequent
                    - prompt: Three phase unbalanced
                      value: pm_b_3pu_sequent
    - prompt: intermediate
      target:
        - answer_key: __num_phases_int
          key: module_config_file
          text: How many phases are you monitoring
          option:
            - prompt: single phase
              value: pm_i_1p
            - prompt: three phase
              value: pm_i_3p
    - prompt: advanced
      target:
        - answer_key: __num_phases_adv
          key: module_config_file
          text: How many phases are you monitoring
          option:
            - prompt: single
              value: pm_a_1p
            - prompt: three
              value: pm_a_3p
    - prompt: simulator
      target:
        - key: module_config_file
          value: pm_b_3pu_mock
```

As presented to a user:

```default
Choose a name for this machine: Machine A
> 1 - basic
> 2 - intermediate
> 3 - advanced
> 4 - simulator
Which power monitoring variant are you deploying [1/2/3/4]: 1
> 1 - Grove ADC v1.0
> 2 - Grove ADC v1.1
> 3 - ADS1115
> 4 - BC Robotics
> 5 - Sequent 16 channel Universal Inputs ADC
Which ADC are you using [1/2/3/4/5]: 2
> 1 - Single phase
> 2 - Three phase balanced (single clamp)
> 3 - Three phase unbalanced
> 4 - Gravity DC current sensor
Which sensing configuration are you using [1/2/3/4]: 3
```

Resulting template variables:

```python
{"machine_name": "Machine A","module_config_file":"pm_b_3pu_grove_v1.1"}
```

As stored in prev_answers.json

```json
{"machine_name": "Machine A", "__variant": 1, "__adc_basic": 2, "__basic_grove_1_1": 3}
```

Applied to template:

```default
...
module_config_file = "./module_config/{{module_config_file}}.toml"

calculation.machine_name.config.machine = "{{machine_name}}"
...
```

Resulting in:

```default
...
module_config_file = "./module_config/pm_b_3pu_grove_v1.1.toml"

calculation.machine_name.config.machine = "Machine A"
...
```
