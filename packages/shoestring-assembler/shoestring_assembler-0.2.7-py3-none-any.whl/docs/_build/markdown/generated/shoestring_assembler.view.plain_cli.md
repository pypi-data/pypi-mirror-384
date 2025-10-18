# shoestring_assembler.view.plain_cli package

## Submodules

## shoestring_assembler.view.plain_cli.audit_events module

### shoestring_assembler.view.plain_cli.audit_events.audit_event_to_string(event: [AuditEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.AuditEvent))

## Module contents

### *class* shoestring_assembler.view.plain_cli.PlainCLI(action)

Bases: `object`

#### create_progress_section(msg: [SectionEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.SectionEvent))

#### diplay_audit_msg(audit_event: [AuditEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.AuditEvent))

#### diplay_progress_update(progress_event: [ProgressEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent))

#### handle(step)

#### handle_input_request(request: [Request](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.input.Input.Request))

#### *async* listen_for_updates()

#### notify_fn(msg: [Event](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.Event))

#### *async* run()

### shoestring_assembler.view.plain_cli.task_callback(task: Task)
