# shoestring_assembler.model package

## Subpackages

* [shoestring_assembler.model.schemas package](shoestring_assembler.model.schemas.md)
  * [Submodules](shoestring_assembler.model.schemas.md#submodules)
  * [shoestring_assembler.model.schemas.schema_validators module](shoestring_assembler.model.schemas.md#module-shoestring_assembler.model.schemas.schema_validators)
    * [`MetaSchema`](shoestring_assembler.model.schemas.md#shoestring_assembler.model.schemas.schema_validators.MetaSchema)
      * [`MetaSchema.validate()`](shoestring_assembler.model.schemas.md#shoestring_assembler.model.schemas.schema_validators.MetaSchema.validate)
    * [`RecipeSchema`](shoestring_assembler.model.schemas.md#shoestring_assembler.model.schemas.schema_validators.RecipeSchema)
      * [`RecipeSchema.validate()`](shoestring_assembler.model.schemas.md#shoestring_assembler.model.schemas.schema_validators.RecipeSchema.validate)
    * [`load_schema()`](shoestring_assembler.model.schemas.md#shoestring_assembler.model.schemas.schema_validators.load_schema)
    * [`schema_validate()`](shoestring_assembler.model.schemas.md#shoestring_assembler.model.schemas.schema_validators.schema_validate)
  * [Module contents](shoestring_assembler.model.schemas.md#module-shoestring_assembler.model.schemas)

## Submodules

## shoestring_assembler.model.base_module module

### *class* shoestring_assembler.model.base_module.BaseModule(name: str, \*, spec, fs: [ModuleFilesystem](#shoestring_assembler.model.filesystem.ModuleFilesystem), source: [SourceModel](#shoestring_assembler.model.source.SourceModel))

Bases: `object`

#### *property* containers

#### *property* name *: str*

#### *property* source *: [SourceModel](#shoestring_assembler.model.source.SourceModel)*

#### *property* spec

#### *property* user_config *: [UserConfig](#shoestring_assembler.model.user_config.UserConfig)*

## shoestring_assembler.model.common module

### *class* shoestring_assembler.model.common.ModelMap

Bases: `object`

#### *classmethod* generate(ModelCls: Type[T], child_definitions) → List[T]

## shoestring_assembler.model.container module

### *class* shoestring_assembler.model.container.Container(name: str, \*, spec, module: [BaseModule](#shoestring_assembler.model.base_module.BaseModule))

Bases: `object`

#### *property* alias

#### *property* host_ports

#### *property* meta

#### *property* name

#### *property* partial_compose_snippet

### *class* shoestring_assembler.model.container.Volume(container_identifier, name, \*, host_path=None, container_path=None, mode=None)

Bases: `object`

#### apply_container_spec(spec)

#### check_valid()

#### formatted()

#### *classmethod* from_container_spec(container_id, name, spec)

### *class* shoestring_assembler.model.container.VolumeMap(container_id, host_volumes: dict, data_dir, uc_dir)

Bases: `MutableMapping`[`str`, [`Volume`](#shoestring_assembler.model.container.Volume)]

#### apply_container_spec(spec)

## shoestring_assembler.model.filesystem module

### *class* shoestring_assembler.model.filesystem.CompiledUserConfigFilesystem(root: Path)

Bases: `object`

#### ensure_directory(rel_path: Path)

#### get_file(rel_path: Path)

#### *async* verify()

### *class* shoestring_assembler.model.filesystem.ModuleFilesystem(data_root: Path, user_config_root: Path)

Bases: `object`

#### *async* verify()

### *class* shoestring_assembler.model.filesystem.SolutionFilesystem(root=PosixPath('/home/greg/projects/experiments/assembler/src/docs'), \*, alt_recipe_path=None)

Bases: `object`

#### *async* clean()

#### get_module_fs(module_name)

#### get_source_fs(source_name)

#### prepare()

#### *property* recipe_file

#### *async* verify()

### *class* shoestring_assembler.model.filesystem.SourceFilesystem(fetch_root: Path, config_root: Path, user_config_template_root: Path)

Bases: `object`

#### *async* clean(remove_downloaded_files)

#### *async* verify(check_source_download)

### *class* shoestring_assembler.model.filesystem.UserConfigTemplateFilesystem(root: Path)

Bases: `object`

#### *async* get_files()

#### *async* verify()

### *async* shoestring_assembler.model.filesystem.check_dir(abs_path: Path)

### *async* shoestring_assembler.model.filesystem.check_file(file: Path)

### *async* shoestring_assembler.model.filesystem.check_or_create_dir(abs_path)

### *async* shoestring_assembler.model.filesystem.rmtree(root: Path)

### *async* shoestring_assembler.model.filesystem.walk_dir(root: Path, ignored_dirs=[])

## shoestring_assembler.model.infrastructure_module module

### *class* shoestring_assembler.model.infrastructure_module.InfrastructureModule(name, \*\*kwargs)

Bases: [`BaseModule`](#shoestring_assembler.model.base_module.BaseModule)

## shoestring_assembler.model.installed module

### *class* shoestring_assembler.model.installed.InstalledSolutionsModel

Bases: `object`

#### *async* add_solution(path, base_name)

#### *async* check_running()

#### *async* remove_solution(solution: [SolutionModel](#shoestring_assembler.model.solution.SolutionModel))

#### *async* rename_solution(solution: [SolutionModel](#shoestring_assembler.model.solution.SolutionModel), new_name)

#### *async* saturate_solutions()

#### *property* solutions

## shoestring_assembler.model.prompts module

### *class* shoestring_assembler.model.prompts.Prompts

Bases: `object`

#### create(prompt_spec)

#### exists()

#### generate_outputs(context)

#### get(prefixed_id) → Base | None

#### *classmethod* load(file_path)

Load prompts from the prompts file (TOML).

#### next(context=None) → Base | None

#### start(prefix, context={})

## shoestring_assembler.model.recipe module

### *class* shoestring_assembler.model.recipe.FileSourceSpec(recipe_dict)

Bases: `object`

### *class* shoestring_assembler.model.recipe.GitSourceSpec(recipe_dict)

Bases: `object`

### *class* shoestring_assembler.model.recipe.ModuleSegment(recipe_dict: dict)

Bases: `object`

### *exception* shoestring_assembler.model.recipe.NoRecipeError(message, expected_location)

Bases: `Exception`

### *class* shoestring_assembler.model.recipe.Recipe(recipe_filepath, recipe, hash)

Bases: `object`

#### *property* infrastructure *: dict*

#### *async classmethod* load(recipe_filepath)

#### *property* service_modules *: dict*

#### *property* solution *: dict*

#### *property* sources *: dict[slice(<class 'str'>, 'SourceSpec', None)]*

#### *async* validate()

### *class* shoestring_assembler.model.recipe.SolutionSpec(recipe_dict: dict)

Bases: `object`

### *class* shoestring_assembler.model.recipe.SourceSpec(recipe_dict: dict)

Bases: `object`

### *class* shoestring_assembler.model.recipe.UnknownSourceSpec(recipe_dict: dict)

Bases: [`SourceSpec`](#shoestring_assembler.model.recipe.SourceSpec)

## shoestring_assembler.model.service_module module

### *class* shoestring_assembler.model.service_module.ServiceModuleModel(name, \*\*kwargs)

Bases: [`BaseModule`](#shoestring_assembler.model.base_module.BaseModule)

## shoestring_assembler.model.solution module

### *class* shoestring_assembler.model.solution.SolutionModel(name='', \*, root_dir=PosixPath('/home/greg/projects/experiments/assembler/src/docs'))

Bases: `object`

#### *class* Status(value)

Bases: `Enum`

An enumeration.

#### RUNNING *= 'running'*

#### STOPPED *= 'stopped'*

#### UNKNOWN *= 'unknown'*

#### *property* available_updates *: list*

#### *property* compose_spec

#### *property* current_version

#### *property* infrastructure

#### module_iterator()

#### *property* recipe_details *: [SolutionSpec](#shoestring_assembler.model.recipe.SolutionSpec)*

#### *async* saturate()

#### save_compose_spec(compose_definition)

#### *property* service_modules

#### *property* solution_details *: [SolutionSpec](#shoestring_assembler.model.recipe.SolutionSpec)*

#### *property* sources

#### *property* version_control *: [VersionControl](#shoestring_assembler.model.solution.VersionControl)*

### *class* shoestring_assembler.model.solution.VersionControl(solution)

Bases: `object`

#### *exception* NotLoadedException

Bases: `Exception`

#### *property* available_updates

#### can_update()

#### *property* current_version

#### *async* get_version_data()

#### *property* is_loaded

#### *property* target_version

#### *async* update()

## shoestring_assembler.model.source module

### *class* shoestring_assembler.model.source.SourceModel(name, \*, spec, fs: [SourceFilesystem](#shoestring_assembler.model.filesystem.SourceFilesystem), root)

Bases: `object`

#### *async* fetch()

#### *property* meta

#### *property* name

## shoestring_assembler.model.user_config module

### *class* shoestring_assembler.model.user_config.UserConfig(module_uc_filesystem: [CompiledUserConfigFilesystem](#shoestring_assembler.model.filesystem.CompiledUserConfigFilesystem), template_fs: [UserConfigTemplateFilesystem](#shoestring_assembler.model.filesystem.UserConfigTemplateFilesystem))

Bases: `object`

Manages the user’s configuration, including versioning, status, and previous answers.
Handles loading, saving, and status checking for user config files.

#### *class* Status(value)

Bases: `Enum`

Possible statuses for the user configuration.

#### MAJOR_UPDATE *= 'major_update'*

#### MINOR_UPDATE *= 'minor_update'*

#### NOT_INITIALISED *= 'first_setup'*

#### NO_TEMPLATE *= 'no_template'*

#### UP_TO_DATE *= 'up_to_date'*

#### WARN_FUTURE *= 'config_from_future'*

#### *property* context

#### *property* prev_answers

Lazily load and return previous answers from the file.

#### *property* prompt_defaults

Returns a merged dict of template defaults and previous answers.
Preference is given to previous answers

#### *property* status

Return the current status of the user config (lazy evaluation).

#### *property* template

Return the UserConfigTemplate instance.

#### *property* version

Lazily load and return the user config version.

### *class* shoestring_assembler.model.user_config.UserConfigTemplate(fs: [UserConfigTemplateFilesystem](#shoestring_assembler.model.filesystem.UserConfigTemplateFilesystem))

Bases: `object`

Handles loading and access to the user configuration template files.
Provides lazy loading for version, defaults, and prompts.

#### *property* defaults

Lazily load and return the default values from the template.

#### exists()

Check if the template directory exists.

#### *property* prompts

Lazily load and return the prompts from the template.

#### *property* version

Lazily load and return the template version.

### *class* shoestring_assembler.model.user_config.Version(version_string)

Bases: `tuple`

Validates version string.
Represents the version as a tuple (major, minor) so that it can be compared using <, ==, or >.
Returns original version string when treated as a string (i.e. printed)

#### *exception* Invalid

Bases: `Exception`

Raised when a version string is invalid.

#### valid_regex *= re.compile('^\\\\s\*(\\\\d+)\\\\.(\\\\d+)\\\\s\*$')*

## Module contents
