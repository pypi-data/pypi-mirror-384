# Third-party libraries
import yaml  # For parsing YAML partials in compose definitions

# Project-specific modules
from shoestring_assembler.utilities import (
    minimal_mustache,
)  # Minimal mustache template rendering
from shoestring_assembler.constants import Constants  # Project-wide constants
from shoestring_assembler.interface.events import (
    FatalError,
    Progress,
    Update,
    ProgressSection,
)
import asyncio

# Imports for type annotations
from shoestring_assembler.model import SolutionModel, ServiceModuleModel, BaseModule


class Assembler:
    """
    Orchestrates the process of gathering sources, building the service definitions for each service module,
    and generating the Docker Compose file.
    """

    def __init__(self, solution_model: SolutionModel):
        """
        Initialize the Assembler with a SolutionModel instance.
        :param solution_model: The solution model
        """
        self.solution_model = solution_model

    async def load_sources(self, do_gather):
        """
        Gather all service module sources required by the solution.
        If do_gather is False, skip fetching sources.
        :param do_gather: Whether to fetch sources or not.
        """
        await Update.StepHeading("Gathering Service Module Sources")

        if not do_gather:
            await Update.SuccessMsg(
                "Fetching service module sources disabled by command line arguements"
            )
        else:
            # Collect all unique sources from modules
            # this is a set, not a dict to prevent duplicates
            used_sources = {
                module.source for module in self.solution_model.module_iterator()
            }

            async with ProgressSection("fetch"):
                # Use a progress bar to show fetching status
                progress = await Progress.new_tracker(
                    "fetch_source",
                    "Gathering Service Module Sources",
                    total=len(used_sources),
                )

                for source in used_sources:
                    await Update.InfoMsg(
                        f"Fetching {source.name}",
                        detail_level=Update.LevelOfDetail.ALWAYS_CLI_ONLY,
                    )

                    result = await source.fetch()

                    if result:
                        await Update.SuccessMsg(f"Fetched '{source.name}' ")
                        await progress.update(
                            progress.current + 1
                        )  # updates progress bar
                    else:
                        await progress.update(progress.total)
                        raise FatalError(
                            f"An error occured while fetching '{source.name}'"
                        )

            await Update.SuccessMsg("All Service Module Sources Gathered")

    async def generate_compose_file(self):
        """
        Generate a Docker Compose file for the solution, including all service and infrastructure modules.
        """
        await Update.StepHeading("Generating Compose File")
        compose_definition = {
            "services": {},
            "networks": {
                Constants.DOCKER_NETWORK_NAME: {"name": "shoestring-internal"}
            },
        }

        async with ProgressSection("generate"):
            # Add all service modules to the compose definition
            for service_module in self.solution_model.service_modules:
                service_set = await self.generate_docker_services_for_module(
                    service_module
                )
                compose_definition["services"].update(service_set)
                await asyncio.sleep(0.2)

            # Add all infrastructure modules to the compose definition
            for infrastructure_module in self.solution_model.infrastructure:
                service_set = await self.generate_docker_services_for_module(
                    infrastructure_module
                )
                compose_definition["services"].update(service_set)
                await asyncio.sleep(0.2)

        # Add recipe metadata to the compose file
        compose_definition["x-shoestring"] = {
            "recipe": {
                "filename": str(self.solution_model.recipe_details.filepath_provided),
                "hash": self.solution_model.recipe_details.hash,
            }
        }

        # Save the generated compose specification
        self.solution_model.save_compose_spec(compose_definition)

        await Update.SuccessMsg(f"Compose file complete")

    async def generate_docker_services_for_module(self, module: BaseModule):
        """
        Generate Docker Compose service definitions for a given module.
        Handles build context, config, volumes, and ports for each container.
        :param module: The module model to generate services for.
        :return: Dictionary of service definitions for the module's containers.
        """
        module_tracker = await Progress.new_tracker(
            key=module.name.strip(), label=module.name, total=len(module.containers)
        )
        # await Update.InfoMsg(f"[cyan]*  {module.name}")
        module_services = {}

        for container in module.containers:
            container_tracker = None
            if len(module.containers) > 1:
                # await Update.InfoMsg(f"[cyan]**  {container.identifier}")
                container_tracker = await Progress.new_tracker(
                    key=container.identifier.strip(),
                    label=f"| {container.identifier}",
                    total=1,
                )

            # Determine build context and config paths relative to solution root
            ## root of fetched solution files relative to root of solution
            build_context_relative_path = module.source.fs.fetch_dir.relative_to(
                self.solution_model.fs.root
            )
            ## root of source config files relative to root of solution
            config_relative_path = module.source.fs.config_dir.relative_to(
                self.solution_model.fs.root
            )
            ## Dockerfile path relative to build context (i.e. fetched solution files)
            docker_file_relative_path = (
                f"./{container.meta.get('dockerfile','Dockerfile')}"  # TODO move to fs?
            )

            # Base service definition
            service_definition = {
                "build": {
                    "context": str(build_context_relative_path),
                    "dockerfile": str(docker_file_relative_path),
                    "additional_contexts": [f"solution_config={config_relative_path}"],
                },
                "networks": {
                    Constants.DOCKER_NETWORK_NAME: {
                        "aliases": [f"{container.alias}{Constants.DOCKER_ALIAS_SUFFIX}"]
                    }
                }, 
                "logging": {
                    "driver": "json-file",
                    "options": {"max-size": "10m", "max-file": "3"},
                },
                "labels": {
                    "net.digitalshoestring.solution": self.solution_model.solution_details.slug,
                    "net.digitalshoestring.function": module.type,
                },
                "restart": "unless-stopped",
            }

            # Merge in any partial compose snippets (source-provided overrides)
            raw_partials_string = container.partial_compose_snippet
            if raw_partials_string:
                template_applied_string = minimal_mustache.render(
                    raw_partials_string, module.spec.get("template", {})
                )
                partials = yaml.safe_load(template_applied_string)
            else:
                partials = {}

            # Merge partials with base service definition.
            # base service definition takes precedence to prevent partials from overwriting
            # service_definition keys
            service_definition = {
                **partials,
                **service_definition,
            }

            # Handle container volumes
            container.volumes.apply_container_spec(container.meta.get("volume", {}))

            compose_volumes = []
            for volume in container.volumes.values():
                if volume.ignored:  # container doesn't use this volume
                    continue
                volume.check_valid()  # throws errors if problems exist
                compose_volumes.append(volume.formatted())

            if len(compose_volumes) > 0:
                service_definition["volumes"] = compose_volumes

            # Map ports (container and host)
            ports = {}  # defaults

            # Map container ports
            container_ports = container.meta.get("ports", {})
            for name, port_number in container_ports.items():
                if name not in ports:
                    ports[name] = {}
                ports[name]["container"] = port_number
            # Map host ports
            for name, port_number in container.host_ports.items():
                if name not in ports:
                    ports[name] = {}
                ports[name]["host"] = port_number

            # Combine port mappings for Docker Compose
            compose_ports = []
            for name, mapping in ports.items():
                has_host = "host" in mapping
                has_cnt = "container" in mapping
                if has_host and has_cnt:  # everything as expected
                    entry = f'{mapping["host"]}:{mapping["container"]}'
                    compose_ports.append(entry)
                elif has_host:
                    # No container entry to map to
                    raise FatalError(
                        f"No corresponding container entry for port {name} of {container.identifier}."
                    )
                elif has_cnt:
                    # No host entry to map to
                    raise FatalError(
                        f"No corresponding host entry for port {name} of {container.identifier}."
                    )
            if len(compose_ports) > 0:
                service_definition["ports"] = compose_ports

            # Add the service definition for this container to the list of module services
            module_services[container.identifier] = service_definition

            if container_tracker:
                await container_tracker.update(1)
            await module_tracker.update(module_tracker.current + 1)
        return module_services


"""
TO DO List:
* work out what clean means
* handle volumes in snippets

Longer term
* solution config templates & bootstrapping
* host side volume specification
* named volumes - when only has container entry?
    * would need warning if repeated
* Environment variables
* coveying port and alias mappings to services
*   external resources
"""
