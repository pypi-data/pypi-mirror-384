from pathlib import Path
import sys

from shoestring_assembler.interface.events.audit import Audit
from shoestring_assembler.interface.events import Update,FatalError


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shoestring_assembler.model.solution import SolutionModel


class SolutionFilesystem:
    def __init__(self, root=Path.cwd(), *, alt_recipe_path=None):
        if not isinstance(root, Path):
            root = Path(root)

        self.root_valid = True
        if root.is_file():  # will be False if root doesn't exist
            root = root.parent
        elif not root.exists():
            if root.parent.exists() and (root.parent / ".git").exists(): # version predating assembler
                root = root.parent
            else:
                self.root_valid = False

        # variables
        self.__alt_recipe_path = alt_recipe_path

        # externally accessed variables
        ## directories
        self.root = root
        self.assembler_output_dir = root / "assembled"
        self.solution_data_dir = root / "data"
        self.compiled_user_config_dir = (
            self.assembler_output_dir / "compiled_user_config"
        )
        self.fetched_sources_dir = self.assembler_output_dir / "sources"
        self.source_config_dir = root / "solution_config/source_config"
        self.user_config_templates_dir = root / "solution_config/user_config_templates"

        ## files
        self.compose_file = self.assembler_output_dir / "compose.yml"
        self.assembler_log_file = self.assembler_output_dir / "console_log.html"
        self.env_file = root / "solution_config/.env"

    @property
    def recipe_file(self):
        if self.__alt_recipe_path:
            alt_recipe_path = Path(self.__alt_recipe_path)
            if alt_recipe_path.is_absolute():
                return alt_recipe_path
            else:
                return self.root / alt_recipe_path
        else:
            return self.root / "recipe.toml"

    def get_source_fs(self, source_name):
        return SourceFilesystem(
            self.fetched_sources_dir / source_name,
            self.source_config_dir / source_name,
            self.user_config_templates_dir / source_name,
        )

    def get_module_fs(self, module_name):
        return ModuleFilesystem(
            self.solution_data_dir / module_name,
            self.compiled_user_config_dir / module_name,
        )

    # utility functions

    async def clean(self):
        # delete console_log.html
        # delete compose.yml
        pass

    def prepare(self):
        pass

    async def verify(self):

        all_ok = True

        # check source config
        all_ok = await check_dir(self.source_config_dir) and all_ok

        all_ok = await check_or_create_dir(self.assembler_output_dir)

        # check fetched sources directories
        all_ok = await check_or_create_dir(self.fetched_sources_dir) and all_ok

        # check data directories
        all_ok = await check_or_create_dir(self.solution_data_dir) and all_ok

        # check user config directories
        all_ok = await check_or_create_dir(self.compiled_user_config_dir) and all_ok

        return all_ok


class SourceFilesystem:

    def __init__(
        self, fetch_root: Path, config_root: Path, user_config_template_root: Path
    ):
        # external
        self.fetch_dir = fetch_root
        self.meta_file = fetch_root / "meta.toml"
        self.config_dir = config_root
        self.user_config_template = UserConfigTemplateFilesystem(
            user_config_template_root
        )

    async def verify(self, check_source_download):
        all_ok = True

        all_ok = await check_or_create_dir(self.config_dir) and all_ok
        all_ok = await self.user_config_template.verify() and all_ok
        if check_source_download:
            all_ok = await check_or_create_dir(self.fetch_dir) and all_ok
            all_ok = await check_file(self.meta_file) and all_ok

        return all_ok

    async def clean(self, remove_downloaded_files):
        if remove_downloaded_files:
            await rmtree(self.fetch_dir)


class ModuleFilesystem:

    def __init__(self, data_root: Path, user_config_root: Path):
        self.data_dir = data_root
        self.user_config = CompiledUserConfigFilesystem(user_config_root)

    async def verify(self):
        all_ok = True

        all_ok = await check_or_create_dir(self.data_dir) and all_ok
        all_ok = await self.user_config.verify() and all_ok

        return all_ok


class UserConfigTemplateFilesystem:
    def __init__(self, root: Path):
        # internal
        self.__metadata_dir = root / "__templating"
        # external
        self.dir = root
        self.version_file = self.__metadata_dir / "__version__"
        self.defaults_file = self.__metadata_dir / "defaults.json"
        self.prompts_file = self.__metadata_dir / "prompts.toml"

    async def verify(self):
        if self.dir.exists():
            all_ok = True
            all_ok = await check_file(self.version_file) and all_ok
            # all_ok = await check_file(self.defaults_file) and all_ok    # optional - in future - check with schema if file is present
            # all_ok = await check_file(self.prompts_file) and all_ok     # optional - in future - check with schema if file is present
            return all_ok
        else:
            return True

    async def get_files(self):
        return await walk_dir(self.dir, [self.__metadata_dir])


class CompiledUserConfigFilesystem:

    def __init__(self, root: Path):
        # internal
        self.dir = root
        self.__metadata_dir = root / "__templating"
        # external
        self.version_file = self.__metadata_dir / "__version__"
        self.previous_answers = self.__metadata_dir / "prev_answers.json"

    def ensure_directory(self, rel_path: Path):
        (self.dir / rel_path).mkdir(exist_ok=True)

    def get_file(self, rel_path: Path):
        return self.dir / rel_path

    async def verify(self):
        all_ok = True
        all_ok = await check_or_create_dir(self.dir) and all_ok
        if self.__metadata_dir.exists():
            all_ok = await check_file(self.version_file) and all_ok
            # all_ok = check_file(self.previous_answers) and all_ok  # optional - in future - check with schema if file is present
        return all_ok


# Utility function implementations


async def check_file(file: Path):
    success = True
    outcome = "ok"
    if not file.exists():
        success = False
        outcome = "error_not_found"
    elif not file.is_file():
        success = False
        outcome = "error_not_file"

    await Audit.submit(
        "check_file", Audit.Type.from_boolean(success), file=file, outcome=outcome
    )
    return success


async def check_dir(abs_path: Path):
    success = True
    outcome = "ok"
    if not abs_path.exists():
        success = False
        outcome = "error_not_found"
    elif not abs_path.is_dir():
        success = False
        outcome = "error_not_dir"

    await Audit.submit(
        "check_dir", Audit.Type.from_boolean(success), dir=abs_path, outcome=outcome
    )
    return success


async def check_or_create_dir(abs_path):
    success = True
    outcome = "created"
    try:
        abs_path.mkdir(exist_ok=False)
    except FileExistsError:
        try:
            abs_path.mkdir(exist_ok=True)
            outcome = "ok"
        except FileExistsError:
            success = False
            outcome = "error_cant_create"
    except FileNotFoundError:
        success = False
        outcome = "error_no_parent"

    await Audit.submit(
        "check_or_create_dir",
        Audit.Type.from_boolean(success),
        dir=abs_path,
        outcome=outcome,
    )
    return success


# if using python prior to 3.12 then pathlib doesn't have a walk function
if sys.version_info[0] == 3 and sys.version_info[1] < 12:
    import os

    async def rmtree(root: Path):
        if root.is_symlink():
            root.unlink()
            await Audit.submit(
                "rmtree", Audit.Type.Expected, root=root, method="symlink"
            )
        else:
            for walk_root, dirs, files in os.walk(root, topdown=False):
                walk_root = Path(walk_root)
                for name in files:
                    (walk_root / name).unlink()
                for name in dirs:
                    path = walk_root / name
                    if path.is_symlink():
                        path.unlink()
                    else:
                        path.rmdir()
            await Audit.submit(
                "rmtree", Audit.Type.Expected, root=root, method="walked"
            )

    async def walk_dir(root: Path, ignored_dirs=[]):

        dir_set = []
        file_set = []

        for raw_base, dirs, files in os.walk(root, topdown=True):
            base = Path(raw_base)

            if base in ignored_dirs:
                continue  # ignore all files in ignored_dirs

            rel_base = Path(raw_base).relative_to(root)
            for name in files:
                file_set.append(rel_base / name)
            for name in dirs:
                if (base / name).is_symlink():
                    # symlinks aren't exected, but accounting for it just in case
                    file_set.append(rel_base / name)
                else:
                    dir_set.append(rel_base / name)

        return dir_set, file_set

else:

    async def rmtree(root: Path):
        if root.is_symlink():
            root.unlink()
            await Audit.submit(
                "rmtree", Audit.Type.Expected, root=root, method="symlink"
            )
        else:
            for root, dirs, files in root.walk(top_down=False):
                for name in files:
                    (root / name).unlink()
                for name in dirs:
                    (root / name).rmdir()
            await Audit.submit(
                "rmtree", Audit.Type.Expected, root=root, method="walked"
            )

    async def walk_dir(root: Path, ignored_dirs=[]):
        dir_set = []
        file_set = []

        for base, dirs, files in root.walk(top_down=True):
            if base in ignored_dirs:
                continue  # ignore all files in ignored_dirs
            rel_base = base.relative_to(root)
            for name in files:
                file_set.append(rel_base / name)
            for name in dirs:
                dir_set.append(rel_base / name)

        return dir_set, file_set
