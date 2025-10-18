# Container Setup
A container can be configured with a setup command using the `x-shoestring-setup-command` variable in the containers `compose_partial` file - for example `x-shoestring-setup-command: ["python","setup.py"]` will call `python setup.py` in the setup phase for the container.

This is the place to execute setup that needs to execute in the container environment or requires user input. Examples of this type of setup include:
* Setting up initial passwords
* Configuring / testing attached hardware
* Generating cryptographic keys

## User interaction
### Output
The subprocess executing the setup command is wrapped in such a way that `stdout` and `stderr` are merged and their contents relayed to the user.
* All output must be terminated by a newline `\n`
* Output can be formatted by sending a json formatted string over `stdout` or `stderr` with the following format:
```json
{
    "type":"output",
    "message":"<text to display to user>",
    "variant":"heading" | "error" | "success" | "info"
}
```

### Input
The subprocess executing the setup command also wraps `stdin` so that user input can be relayed back to the process.

* To prompt for user input, send a json formatted string over `stdout` with the following format:
```json
{
    "type":"input",
    "prompt": "<prompt text to show the user>",
    "variant": "<see variant table below>",

    // only present when variant is "select"
    "options": {"<value>":"<label>"}   
}
```
* ***A script should only block for user input after prompting the user in the manner described above - not doing so will result in the setup process hanging***


|variant| |
|---|---|
|"text"| Presents the user with a free text input |
|"continue"| Presents the user with a continue trigger  - either a continue button to press or a prompt to press *Enter* |
|"confirm"| Presents the user with a Yes/No input |
|"select" | Presents the user with the ability to select one of the supplied `options` |

> When implementing in *Python* - inputs should be handled as follows: 
> ```python
>   import json
>   
>   ...
>
>   print(json.dumps({
>       "type":"input",
>       "prompt":"<prompt here>",
>       "variant":"<variant>"
>   }))
>   answer = input()
>```
> Using `answer = input(json.dumps(...))` will fail because `input()` doesn't terminate the json string with a newline.