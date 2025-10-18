from shoestring_assembler.interface.events.audit import AuditEvent, Audit

def audit_event_to_string(event: AuditEvent):
    match event.context:
        case [*_, "check_dir"]:
            dir = event.extra.get("dir")
            match event.extra.get("outcome"):
                case "ok":
                    return f"[green]\[ok][white]  {dir}"
                case "error_not_found":
                    return f"[red]\[error - not found] {dir}"
                case "error_not_dir":
                    return f"[red]\[error - not a directory]  {dir} (there may be a file with the same name)"

        case [*_, "check_or_create_dir"]:
            dir = event.extra.get("dir")
            match event.extra.get("outcome"):
                case "ok":
                    return f"[green]\[ok][white]  {dir}"
                case "created":
                    return f"[green]\[created][white]  {dir}"
                case "error_no_parent":
                    return f"[red]\[error - parent directory not present]  {dir}"
                case "error_cant_create":
                    return f"[red]\[error - can't create]  {dir} (there may be a file with the same name)"

        case [*_, "check_file"]:
            file = event.extra.get("file")
            match event.extra.get("outcome"):
                case "ok":
                    return f"[green]\[ok][white]  {file}"
                case "error_not_found":
                    return f"[red]\[error - not found]  {file}"
                case "error_not_file":
                    return f"[red]\[error - not a file]  {file} (there may be a directory with the same name)"

        case [*_, "rmtree"]:
            root = event.extra.get("root")
            match event.extra.get("method"):
                case "walked":
                    return f"[yellow]\[cleared][white]  {root} (deleted)"
                case "symlink":
                    return f"[yellow]\[cleared][white]  {root} (unlinked)"

        case [*_, "clone_git"]:
            match event.type:
                case Audit.Type.Expected:
                    return f"[green]\[downloaded][white] Downloaded to {event.extra.get('dest')}"
                case Audit.Type.Unexpected:
                    return f"[red]\[failed][white] Download failed with code: {event.extra.get('return_code')}"

        case [*_, "fetch_filesystem_link"]:
            match event.type:
                case Audit.Type.Expected:
                    return f"[green]\[linked][white] Linked {event.extra.get('src')} to {event.extra.get('dest')}"
                case Audit.Type.Unexpected:
                    return event    # TODO:

        case _:
            return event
