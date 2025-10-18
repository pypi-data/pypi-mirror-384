## Engine Flow Diagram
``` mermaid
flowchart TD
    init_download([Command: get solution]) -->
    fetch_available_solution_list[Fetch Solution List] -- solution list -->
    choose_solution[/Input: Choose Solution/] -- chosen solution -->
    fetch_available_solution_versions[Fetch Available Versions] -- version list -->
    choose_version[/Input: Choose Version/] -- selected version -->
    download_solution[Download solution] -->
    cd_dir[Move execution scope to solution directory]  --> 
    do_assemble[/Input: Assemble the solution now?/] -- yes -->
    assemble_solution

    do_assemble -- no --> terminate_assemble([end])

    init_update([Command: update]) -->
    check_for_updates[Check for updates] -->
    new_version{{Newer version available}} -- no --> 
    terminate_update([end])
    new_version -- yes -->
    choose_update_version[/Select Version/] -- version -->
    download_update[Download update] --> do_assemble

    init_assemble([Command: assemble]) --> 
    assemble_solution[Assemble the solution] -->
    check_configure_solution[Check configuration requirements] --required user inputs--> 
    get_user_input[/Prompt user for required inputs/] --inputs--> 
    configure_service_module[Configure Service Module] -->
    do_build[/Build now?/] -- yes -->
    build[Build solution software] -->
    solution_is_setup{{Solution has been setup}} -- no -->
    setup_solution[Set up solution] -->
    do_start[/Start now?/] --yes--> start

    do_start -- no --> terminate_start([end])
    do_build -- no --> terminate_start    
    solution_is_setup -- yes --> do_start
    init_reconfigure([Command: reconfigure]) --> check_configure_solution
    
    init_build([Command: build]) --> build
    init_setup([Command: setup]) --> setup_solution

    init_start([Command: start]) -->
    start[Start solution] --> terminate_start

```