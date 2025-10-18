# shoestring_assembler.view.cli_app.screens package

## Submodules

## shoestring_assembler.view.cli_app.screens.config_inputs module

### *class* shoestring_assembler.view.cli_app.screens.config_inputs.ConfigInputs(solution_model: [SolutionModel](shoestring_assembler.model.md#shoestring_assembler.model.solution.SolutionModel))

Bases: `Screen`

#### AUTO_FOCUS *: ClassVar[str | None]* *= ''*

A selector to determine what to focus automatically when the screen is activated.

The widget focused is the first that matches the given [CSS selector](/guide/queries/#query-selectors).
Set to None to inherit the value from the screen’s app.
Set to “” to disable auto focus.

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'config.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### SUB_TITLE *: ClassVar[str | None]* *= 'Configure Solution'*

A class variable to set the *default* sub-title for the screen.

This overrides the app sub-title.
To update the sub-title while the screen is running,
you can set the [sub_title][textual.screen.Screen.sub_title] attribute.

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### select_download()

#### select_find()

### *class* shoestring_assembler.view.cli_app.screens.config_inputs.SelectQuestion(\*children, question_prompt='', choices=[], selected=None, question_id=None, name=None, id=None, classes=None, disabled=False, markup=True)

Bases: `VerticalGroup`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### refresh_flag

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

### *class* shoestring_assembler.view.cli_app.screens.config_inputs.ServiceModuleEntry(service_module: [BaseModule](shoestring_assembler.model.md#shoestring_assembler.model.base_module.BaseModule), \*args, \*\*kwargs)

Bases: `VerticalScroll`

#### can_focus *: bool* *= True*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### fix_focus()

#### handle_option_select(message: Changed)

#### handle_text_input(message: Blurred)

#### refresh_flag

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

#### select_download(message)

### *class* shoestring_assembler.view.cli_app.screens.config_inputs.SolutionAction(signal: [ActionSignal](shoestring_assembler.interface.md#shoestring_assembler.interface.signals.ActionSignal))

Bases: `Message`

Action selected message.

#### bubble *: ClassVar[bool]* *= True*

#### handler_name *: ClassVar[str]* *= 'on_solution_action'*

Name of the default message handler.

#### no_dispatch *: ClassVar[bool]* *= False*

#### time

#### verbose *: ClassVar[bool]* *= False*

### *class* shoestring_assembler.view.cli_app.screens.config_inputs.TextQuestion(\*children, question_prompt='', value=None, question_id=None, name=None, id=None, classes=None, disabled=False, markup=True)

Bases: `VerticalGroup`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

## shoestring_assembler.view.cli_app.screens.download module

### *class* shoestring_assembler.view.cli_app.screens.download.DownloadLocation

Bases: `Screen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'download.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### SUB_TITLE *: ClassVar[str | None]* *= 'Choose Download Location'*

A class variable to set the *default* sub-title for the screen.

This overrides the app sub-title.
To update the sub-title while the screen is running,
you can set the [sub_title][textual.screen.Screen.sub_title] attribute.

#### action_back()

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### default_selected

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

#### handle_input(event: Blurred)

#### handle_radio(event: Changed)

#### path

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

#### select_add()

#### show_file_picker(\_event)

### *class* shoestring_assembler.view.cli_app.screens.download.FilePickerModal(\*args, error_message='FATAL Error', \*\*kwargs)

Bases: `ModalScreen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'modals.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### handle_exit() → None

#### handle_file_selected(event: DirectorySelected)

### *class* shoestring_assembler.view.cli_app.screens.download.FilteredDirectoryTree(path: str | Path, \*, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False)

Bases: `DirectoryTree`

#### can_focus *: bool* *= True*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### filter_paths(paths: Iterable[Path]) → Iterable[Path]

Filter the paths before adding them to the tree.

Args:
: paths: The paths to be filtered.

Returns:
: The filtered paths.

By default this method returns all of the paths provided. To create
a filtered DirectoryTree inherit from it and implement your own
version of this method.

### *class* shoestring_assembler.view.cli_app.screens.download.RefreshableSelectedBar(\*children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False, markup: bool = True)

Bases: `HorizontalGroup`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### path

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

#### set_path(value)

## shoestring_assembler.view.cli_app.screens.engine module

### *class* shoestring_assembler.view.cli_app.screens.engine.BuildPrompt(future: Future)

Bases: [`PromptBase`](#shoestring_assembler.view.cli_app.screens.engine.PromptBase)

#### bubble *: ClassVar[bool]* *= True*

#### handler_name *: ClassVar[str]* *= 'on_build_prompt'*

Name of the default message handler.

#### no_dispatch *: ClassVar[bool]* *= False*

#### time

#### verbose *: ClassVar[bool]* *= False*

### *class* shoestring_assembler.view.cli_app.screens.engine.ContinuePrompt(future: Future)

Bases: [`PromptBase`](#shoestring_assembler.view.cli_app.screens.engine.PromptBase)

#### bubble *: ClassVar[bool]* *= True*

#### handler_name *: ClassVar[str]* *= 'on_continue_prompt'*

Name of the default message handler.

#### no_dispatch *: ClassVar[bool]* *= False*

#### time

#### verbose *: ClassVar[bool]* *= False*

### *class* shoestring_assembler.view.cli_app.screens.engine.EngineScreen(update_receiver, name=None, id=None, classes=None)

Bases: `Screen`

#### BINDINGS *: ClassVar[list[BindingType]]* *= {Binding(key='l', action='toggle_show_log', description='Show/Hide detailed logs', show=True, key_display='l', priority=False, tooltip='', id=None, system=False)}*

A list of key bindings.

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'engine.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### action_toggle_show_log()

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose() → Iterable[Widget]

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### create_progress_section(msg: [SectionEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.SectionEvent))

#### diplay_progress_update(progress_event: [ProgressEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent))

#### handle_can_contiue(prompt: [PromptBase](#shoestring_assembler.view.cli_app.screens.engine.PromptBase))

#### handle_input_request(msg: [Request](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.input.Input.Request))

#### notify_fn(msg: [Event](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.updates.Update.Event))

#### trigger_audit_msg(audit_event: [AuditEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.audit.AuditEvent))

#### *async* update_listener()

#### write_audit_msg(audit_event)

### *class* shoestring_assembler.view.cli_app.screens.engine.LogSection(\*children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False, markup: bool = True)

Bases: `VerticalGroup`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### shown

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

#### toggle_show()

### *class* shoestring_assembler.view.cli_app.screens.engine.PromptBase(future: Future)

Bases: `Message`

#### bubble *: ClassVar[bool]* *= True*

#### handler_name *: ClassVar[str]* *= 'on_prompt_base'*

Name of the default message handler.

#### no()

#### no_dispatch *: ClassVar[bool]* *= False*

#### time

#### verbose *: ClassVar[bool]* *= False*

#### yes()

### *class* shoestring_assembler.view.cli_app.screens.engine.PromptWrapper(\*children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False, markup: bool = True)

Bases: `HorizontalGroup`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### current_prompt *: [PromptBase](#shoestring_assembler.view.cli_app.screens.engine.PromptBase)*

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

#### handle_continue(event: Pressed)

### *class* shoestring_assembler.view.cli_app.screens.engine.RichLogConsoleWrapper(rich_log)

Bases: `object`

#### print(msg)

#### rule(\*args, \*\*kwargs)

### *class* shoestring_assembler.view.cli_app.screens.engine.StageLog(\*args, \*\*kwargs)

Bases: `VerticalScroll`

#### add_update(event)

#### can_focus *: bool* *= True*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### clear()

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### contents

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

#### handle_continue_pressed(event: Pressed)

#### handle_input_result(key, output)

#### handle_input_submitted(event: Submitted)

#### handle_no_pressed(event: Pressed)

#### handle_progress_section(msg: [SectionEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.SectionEvent))

#### handle_progress_update(event: [ProgressEvent](shoestring_assembler.interface.events.md#shoestring_assembler.interface.events.progress.ProgressEvent))

#### handle_select_changed(event: Changed)

#### handle_select_pressed(event: Pressed)

#### handle_yes_pressed(event: Pressed)

#### set_progress()

### *class* shoestring_assembler.view.cli_app.screens.engine.StartPrompt(future: Future)

Bases: [`PromptBase`](#shoestring_assembler.view.cli_app.screens.engine.PromptBase)

#### bubble *: ClassVar[bool]* *= True*

#### handler_name *: ClassVar[str]* *= 'on_start_prompt'*

Name of the default message handler.

#### no_dispatch *: ClassVar[bool]* *= False*

#### time

#### verbose *: ClassVar[bool]* *= False*

## shoestring_assembler.view.cli_app.screens.find_solution module

### *class* shoestring_assembler.view.cli_app.screens.find_solution.FilteredDirectoryTree(path: str | Path, \*, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False)

Bases: `DirectoryTree`

#### can_focus *: bool* *= True*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### filter_paths(paths: Iterable[Path]) → Iterable[Path]

Filter the paths before adding them to the tree.

Args:
: paths: The paths to be filtered.

Returns:
: The filtered paths.

By default this method returns all of the paths provided. To create
a filtered DirectoryTree inherit from it and implement your own
version of this method.

### *class* shoestring_assembler.view.cli_app.screens.find_solution.Find

Bases: `Screen`

#### SUB_TITLE *: ClassVar[str | None]* *= 'Find an installed solution'*

A class variable to set the *default* sub-title for the screen.

This overrides the app sub-title.
To update the sub-title while the screen is running,
you can set the [sub_title][textual.screen.Screen.sub_title] attribute.

#### action_back()

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### handle_file_selected(event: FileSelected)

#### select_add()

### *class* shoestring_assembler.view.cli_app.screens.find_solution.SelectBar(\*children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False, markup: bool = True)

Bases: `Container`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### selected

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

## shoestring_assembler.view.cli_app.screens.home module

### *class* shoestring_assembler.view.cli_app.screens.home.Home(installed_solutions: [InstalledSolutionsModel](shoestring_assembler.model.md#shoestring_assembler.model.installed.InstalledSolutionsModel))

Bases: `Screen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'home.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### SUB_TITLE *: ClassVar[str | None]* *= 'Select an Action'*

A class variable to set the *default* sub-title for the screen.

This overrides the app sub-title.
To update the sub-title while the screen is running,
you can set the [sub_title][textual.screen.Screen.sub_title] attribute.

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### *async* fetch_solution_status()

#### handle_solution_action(action: [SolutionAction](#shoestring_assembler.view.cli_app.screens.home.SolutionAction))

#### refresh_flag

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

#### select_download()

#### select_find()

### *class* shoestring_assembler.view.cli_app.screens.home.SolutionAction(signal: [ActionSignal](shoestring_assembler.interface.md#shoestring_assembler.interface.signals.ActionSignal))

Bases: `Message`

Action selected message.

#### bubble *: ClassVar[bool]* *= True*

#### handler_name *: ClassVar[str]* *= 'on_solution_action'*

Name of the default message handler.

#### no_dispatch *: ClassVar[bool]* *= False*

#### time

#### verbose *: ClassVar[bool]* *= False*

### *class* shoestring_assembler.view.cli_app.screens.home.SolutionEntry(solution: [SolutionModel](shoestring_assembler.model.md#shoestring_assembler.model.solution.SolutionModel), \*args, \*\*kwargs)

Bases: `Container`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### handle_button_press(message: Pressed)

#### *async* load_version_control()

#### refresh_flag

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

## shoestring_assembler.view.cli_app.screens.modals module

### *class* shoestring_assembler.view.cli_app.screens.modals.ConfirmModal(\*args, prompt='Continue?', \*\*kwargs)

Bases: `ModalScreen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'modals.tcss'*

Screen to confirm something

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose() → Iterable[Widget]

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### on_button_pressed(event: Pressed) → None

### *class* shoestring_assembler.view.cli_app.screens.modals.FatalErrorModal(\*args, error_message='FATAL Error', exit=True, \*\*kwargs)

Bases: `ModalScreen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'modals.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose() → Iterable[Widget]

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### handle_exit() → None

### *class* shoestring_assembler.view.cli_app.screens.modals.NewName(solution, \*args, \*\*kwargs)

Bases: `ModalScreen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'modals.tcss'*

Screen to confirm something

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose() → Iterable[Widget]

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

#### handle_text_input(message: Blurred)

#### on_button_pressed(event: Pressed) → None

## shoestring_assembler.view.cli_app.screens.select_update module

### *class* shoestring_assembler.view.cli_app.screens.select_update.UpdateVersionPicker(solution_model, \*\*kwargs)

Bases: `Screen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'solution_picker.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### SUB_TITLE *: ClassVar[str | None]* *= 'Select the Version to Update to'*

A class variable to set the *default* sub-title for the screen.

This overrides the app sub-title.
To update the sub-title while the screen is running,
you can set the [sub_title][textual.screen.Screen.sub_title] attribute.

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose() → Iterable[Widget]

Create child widgets for the app.

#### handle_option_select(message: Changed)

#### handle_selected(\_event)

#### refresh_flag

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

### *class* shoestring_assembler.view.cli_app.screens.select_update.VersionList(\*content, version_list=[], selected=None, \*\*kwargs)

Bases: `VerticalGroup`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

## shoestring_assembler.view.cli_app.screens.solution_picker module

### *class* shoestring_assembler.view.cli_app.screens.solution_picker.SolutionList(\*content, provider=None, solution_list={}, do_focus=False, \*\*kwargs)

Bases: `OptionList`

#### can_focus *: bool* *= True*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### on_mount()

### *class* shoestring_assembler.view.cli_app.screens.solution_picker.SolutionPicker(provider_list, \*\*kwargs)

Bases: `Screen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'solution_picker.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### SUB_TITLE *: ClassVar[str | None]* *= 'Select the Solution to Download'*

A class variable to set the *default* sub-title for the screen.

This overrides the app sub-title.
To update the sub-title while the screen is running,
you can set the [sub_title][textual.screen.Screen.sub_title] attribute.

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose() → Iterable[Widget]

Create child widgets for the app.

#### handle_selected(event)

### *class* shoestring_assembler.view.cli_app.screens.solution_picker.SolutionVersionPicker(available_versions, \*\*kwargs)

Bases: `Screen`

#### CSS_PATH *: ClassVar[CSSPathType | None]* *= 'solution_picker.tcss'*

File paths to load CSS from.

Note:
: This CSS applies to the whole app.

#### SUB_TITLE *: ClassVar[str | None]* *= 'Select the Version to Download'*

A class variable to set the *default* sub-title for the screen.

This overrides the app sub-title.
To update the sub-title while the screen is running,
you can set the [sub_title][textual.screen.Screen.sub_title] attribute.

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose() → Iterable[Widget]

Create child widgets for the app.

#### handle_option_select(message: Changed)

#### handle_selected(\_event)

#### refresh_flag

Create a reactive attribute.

Args:
: default: A default value or callable that returns a default.
  layout: Perform a layout on change.
  repaint: Perform a repaint on change.
  init: Call watchers on initialize (post mount).
  always_update: Call watchers even when the new value equals the old value.
  recompose: Compose the widget again when the attribute changes.
  bindings: Refresh bindings when the reactive changes.
  toggle_class: An optional TCSS classname(s) to toggle based on the truthiness of the value.

### *class* shoestring_assembler.view.cli_app.screens.solution_picker.VersionList(\*content, version_list=[], selected=None, \*\*kwargs)

Bases: `VerticalGroup`

#### can_focus *: bool* *= False*

Widget may receive focus.

#### can_focus_children *: bool* *= True*

Widget’s children may receive focus.

#### compose()

Called by Textual to create child widgets.

This method is called when a widget is mounted or by setting recompose=True when
calling [refresh()][textual.widget.Widget.refresh].

Note that you don’t typically need to explicitly call this method.

Example:
: ```
  ``
  ```
  <br/>
  ```
  `
  ```
  <br/>
  python
  def compose(self) -> ComposeResult:
  <br/>
  > yield Header()
  > yield Label(“Press the button below:”)
  > yield Button()
  > yield Footer()
  <br/>
  ```
  ``
  ```
  <br/>
  ```
  `
  ```

## Module contents
