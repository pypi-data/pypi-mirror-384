# shoestring_assembler.interface package

## Subpackages

* [shoestring_assembler.interface.events package](shoestring_assembler.interface.events.md)
  * [Submodules](shoestring_assembler.interface.events.md#submodules)
  * [shoestring_assembler.interface.events.audit module](shoestring_assembler.interface.events.md#module-shoestring_assembler.interface.events.audit)
    * [`Audit`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.Audit)
      * [`Audit.Context`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.Audit.Context)
      * [`Audit.Type`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.Audit.Type)
      * [`Audit.get_instance()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.Audit.get_instance)
      * [`Audit.pop_context()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.Audit.pop_context)
      * [`Audit.push_context()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.Audit.push_context)
      * [`Audit.submit()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.Audit.submit)
    * [`AuditEvent`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.AuditEvent)
      * [`AuditEvent.context`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.AuditEvent.context)
      * [`AuditEvent.extra`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.AuditEvent.extra)
      * [`AuditEvent.type`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.AuditEvent.type)
  * [shoestring_assembler.interface.events.input module](shoestring_assembler.interface.events.md#module-shoestring_assembler.interface.events.input)
    * [`Input`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.input.Input)
      * [`Input.Request`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.input.Input.Request)
      * [`Input.make_request()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.input.Input.make_request)
  * [shoestring_assembler.interface.events.progress module](shoestring_assembler.interface.events.md#module-shoestring_assembler.interface.events.progress)
    * [`Progress`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.Progress)
      * [`Progress.get_instance()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.Progress.get_instance)
      * [`Progress.new_tracker()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.Progress.new_tracker)
      * [`Progress.on_bar_update_callback()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.Progress.on_bar_update_callback)
    * [`ProgressBar`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressBar)
      * [`ProgressBar.details`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressBar.details)
      * [`ProgressBar.update()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressBar.update)
    * [`ProgressEvent`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent)
      * [`ProgressEvent.detail_level`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent.detail_level)
      * [`ProgressEvent.key`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent.key)
      * [`ProgressEvent.label`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent.label)
      * [`ProgressEvent.total`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent.total)
      * [`ProgressEvent.value`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent.value)
    * [`ProgressSection`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressSection)
    * [`SectionEvent`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.SectionEvent)
      * [`SectionEvent.entered`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.SectionEvent.entered)
      * [`SectionEvent.key`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.SectionEvent.key)
  * [shoestring_assembler.interface.events.updates module](shoestring_assembler.interface.events.md#module-shoestring_assembler.interface.events.updates)
    * [`FatalError`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.FatalError)
    * [`Update`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update)
      * [`Update.AttentionMsg()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.AttentionMsg)
      * [`Update.DebugLog()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.DebugLog)
      * [`Update.ErrorMsg()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.ErrorMsg)
      * [`Update.Event`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.Event)
      * [`Update.InfoMsg()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.InfoMsg)
      * [`Update.LevelOfDetail`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.LevelOfDetail)
      * [`Update.NotifyMsg()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.NotifyMsg)
      * [`Update.StageHeading()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.StageHeading)
      * [`Update.StepHeading()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.StepHeading)
      * [`Update.SuccessMsg()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.SuccessMsg)
      * [`Update.Type`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.Type)
      * [`Update.WarningMsg()`](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.WarningMsg)
  * [Module contents](shoestring_assembler.interface.events.md#module-shoestring_assembler.interface.events)

## Submodules

## shoestring_assembler.interface.signals module

### *class* shoestring_assembler.interface.signals.Action(value)

Bases: `Enum`

An enumeration.

#### ASSEMBLE *= 'assemble'*

#### BUILD *= 'build'*

#### DOWNLOAD *= 'download'*

#### EDIT *= 'edit'*

#### FIND *= 'find'*

#### RECONFIGURE *= 'reconfigure'*

#### REMOVE *= 'remove'*

#### RESTART *= 'restart'*

#### SETUP *= 'setup'*

#### START *= 'start'*

#### STOP *= 'stop'*

#### UPDATE *= 'update'*

### *class* shoestring_assembler.interface.signals.ActionSignal(action: [Action](#shoestring_assembler.interface.signals.Action), solution=None)

Bases: [`Signal`](#shoestring_assembler.interface.signals.Signal)

### *class* shoestring_assembler.interface.signals.BackSignal

Bases: [`Signal`](#shoestring_assembler.interface.signals.Signal)

### *class* shoestring_assembler.interface.signals.Signal

Bases: `object`

## Module contents
