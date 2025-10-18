"""
Implementation of a very minimal version of the mustache spec - 
namely only the {{variable}} part. "{{" can be escaped with a preceeding '\'. a "}}" can't be escaped within a variable name.

Added functionality to specify a default value with ':' after the variable name
"""


def render(template:str,data:dict,keep_if_no_match = True):
    out_list = []

    while template and len(template)>0:
        try:
            text, rest = template.split('{{',1)
            out_list.append(text)
        except ValueError:  # no more "{{" in template
            out_list.append(template)
            break

        if text[-1] == '\\':  # escaped
            out_list.append("{{")
            template = rest
            continue

        raw_variable, template = rest.split('}}')
        variable, *default = raw_variable.split(':',1)  #if no ':' present then default will be empty list
        if variable in data:
            out_list.append(data[variable])
        elif len(default) > 0:
            out_list.append(default[0])
        else:
            out_list.append(f"{{{{{variable}}}}}" if keep_if_no_match else "")

    return "".join(out_list)
