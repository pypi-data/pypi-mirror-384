# shoestring_assembler.interface.events package

## Submodules

## shoestring_assembler.interface.events.audit module

### *class* shoestring_assembler.interface.events.audit.Audit

Bases: `object`

#### *class* Context(context_label)

Bases: `object`

#### *class* Type(value)

Bases: `Enum`

An enumeration.

#### Expected *= 1*

#### Log *= 0*

#### Unexpected *= 2*

#### *classmethod* from_boolean(value)

#### *classmethod* get_instance()

#### pop_context(context_id)

#### push_context(context_label)

returns context_id for use in pop
expected to be used by
with Context(“<label>”):

> Audit.sumbit(…)

#### *async classmethod* submit(source, event_type: [Type](#shoestring_assembler.interface.events.audit.Audit.Type), \*\_, \*\*kwargs)

### *class* shoestring_assembler.interface.events.audit.AuditEvent(context: list[str], type: 'Audit.Type', extra: dict)

Bases: `object`

#### context *: list[str]*

#### extra *: dict*

#### type *: [Type](#shoestring_assembler.interface.events.audit.Audit.Type)*

## shoestring_assembler.interface.events.input module

### *class* shoestring_assembler.interface.events.input.Input

Bases: `object`

#### *class* Request(prompt: str, type: [Variant](#shoestring_assembler.interface.events.input.Input.Request.Variant), options: dict = {})

Bases: `object`

#### *class* Variant(value)

Bases: `Enum`

An enumeration.

#### CONFIRM *= 'confirm'*

#### CONTINUE *= 'continue'*

#### SELECT *= 'select'*

#### TEXT *= 'text'*

#### *async* get_response()

#### resolve(response)

#### *property* resolved

#### *async static* make_request(payload)

## shoestring_assembler.interface.events.progress module

### *class* shoestring_assembler.interface.events.progress.Progress

Bases: `object`

#### *classmethod* get_instance()

#### *async classmethod* new_tracker(key, label, total, initial_value=0, detail_level=LevelOfDetail.ALWAYS)

#### *async* on_bar_update_callback(key)

### *class* shoestring_assembler.interface.events.progress.ProgressBar(label, total, current, callback, detail_level)

Bases: `object`

#### *property* details

#### *async* update(value)

### *class* shoestring_assembler.interface.events.progress.ProgressEvent(key: str, label: str, value: int, total: int, detail_level: [shoestring_assembler.interface.events.updates.Update.LevelOfDetail](#shoestring_assembler.interface.events.updates.Update.LevelOfDetail))

Bases: `object`

#### detail_level *: [LevelOfDetail](#shoestring_assembler.interface.events.updates.Update.LevelOfDetail)*

#### key *: str*

#### label *: str*

#### total *: int*

#### value *: int*

### *class* shoestring_assembler.interface.events.progress.ProgressSection(key)

Bases: `object`

### *class* shoestring_assembler.interface.events.progress.SectionEvent(key: str, entered: bool)

Bases: `object`

#### entered *: bool*

#### key *: str*

## shoestring_assembler.interface.events.updates module

### *exception* shoestring_assembler.interface.events.updates.FatalError(message)

Bases: `Exception`

### *class* shoestring_assembler.interface.events.updates.Update

Bases: `object`

#### *async static* AttentionMsg(content)

#### *async static* DebugLog(content)

#### *async static* ErrorMsg(content)

#### *class* Event(type: 'Update.Type', lod: 'Update.LevelOfDetail', content: str)

Bases: `object`

#### content *: str*

#### lod *: [LevelOfDetail](#shoestring_assembler.interface.events.updates.Update.LevelOfDetail)*

#### type *: [Type](#shoestring_assembler.interface.events.updates.Update.Type)*

#### *async static* InfoMsg(content, detail_level=None)

#### *class* LevelOfDetail(value)

Bases: `IntEnum`

An enumeration.

#### ALWAYS *= 0*

#### ALWAYS_CLI_ONLY *= 1*

#### DEBUG *= 5*

#### FEEDBACK *= 2*

#### *async static* NotifyMsg(content)

#### *async static* StageHeading(stage)

#### *async static* StepHeading(section)

#### *async static* SuccessMsg(content)

#### *class* Type(value)

Bases: `Enum`

An enumeration.

#### ATTENTION *= 7*

#### DEBUG *= 6*

#### ERROR *= 4*

#### INFO *= 2*

#### NOTIFY *= 8*

#### STAGE *= 0*

#### STEP *= 1*

#### SUCCESS *= 5*

#### WARNING *= 3*

#### *async static* WarningMsg(content)

## Module contents
