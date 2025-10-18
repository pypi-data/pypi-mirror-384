# shoestring_assembler.engine package

## Submodules

## shoestring_assembler.engine.engine module

### *class* shoestring_assembler.engine.engine.Engine(engine_pipe: Duplex, update_sender: Sender)

Bases: `object`

#### *property* installed_solutions

#### *async static* next(pipe: Duplex, outcome=None)

#### *async* run()

#### *property* solution_model

### *class* shoestring_assembler.engine.engine.EngineInternal(engine_pipe: Duplex, update_sender: Sender)

Bases: `object`

#### *async* add_installed_solution(path, base_name)

#### *async* assemble_solution()

#### *async* build()

#### *async* check_for_updates()

#### *async* check_setup()

#### *async* configure()

#### *async* download_solution(spec)

#### *async* download_update()

#### *async* fetch_available_solution_list()

#### *async* fetch_available_solution_versions(solution_details)

#### *async* remove_solution()

#### *async* rename_solution(new_name)

#### *async* restart()

#### *async* run()

#### *async* set_solution_context(solution)

#### *async* setup()

#### *property* solution_model *: [SolutionModel](shoestring_assembler.model.md#shoestring_assembler.model.solution.SolutionModel)*

#### *async* start()

#### *async* stop()

#### *async* update_ui(message)

## Module contents
