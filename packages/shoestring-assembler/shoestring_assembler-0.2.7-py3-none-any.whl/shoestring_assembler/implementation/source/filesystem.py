from pathlib import Path
import sys
import asyncio

# pathlib changed from NotImplementedError to UnsupportedError in a recent version update
try:
    from pathlib import UnsupportedOperation
except ImportError:
    UnsupportedOperation = NotImplementedError

from shoestring_assembler.implementation.source import SourceImplementation, SourceABC
from shoestring_assembler.model.recipe import FileSourceSpec
from shoestring_assembler.interface.events.audit import Audit


@SourceImplementation.register(FileSourceSpec)
class FilesystemSource:

    def __new__(cls, source_spec: FileSourceSpec,*args) -> SourceABC:
        match (source_spec.mode):
            case "copy":
                return FilesystemCopySource(source_spec,*args)
            case "link":
                return FilesystemLinkSource(source_spec,*args)
            case _:
                raise NotImplementedError(
                    f"No implementation available for sources with file.mode={source_spec.mode}"
                )


class BaseFilesystemSource(SourceABC):
    def __init__(self, source_spec: FileSourceSpec,*args):
        super().__init__(source_spec,*args)
        path = source_spec.filepath
        raw_src = Path(path)
        if not raw_src.is_absolute():
            raw_src = self.solution_root / raw_src
        self.src_path = Path.resolve(raw_src)


class FilesystemCopySource(BaseFilesystemSource):

    async def fetch(self, dest_path):
        do_copy(self.src_path, dest_path)

        # f"{self.src_path} [green]copied[/green] to {self.dest_path}",
        await Audit.submit(
            "fetch_filesystem_copy", Audit.Type.Expected, src=self.src_path, dest=dest_path
        )
        await asyncio.sleep(0.2 )
        return True


class FilesystemLinkSource(BaseFilesystemSource):

    async def fetch(self, dest_path):
        success = True
        try:
            dest_path.symlink_to(self.src_path, target_is_directory=True)
            outcome = "linked"
        except UnsupportedOperation:
            success = False
            outcome = "no_link_support"
        except FileExistsError:
            success = False
            outcome = "already_exists"

        # f"{self.src_path} [green]linked[/green] to {dest_path}",
        # f"Operating system does not support symlinks. Could not link [purple]{self.src_path}[/purple] to [purple]{dest_path}[/purple] for source. Consider changing [cyan]mode[/cyan] to [cyan]copy[/cyan] in the recipe.",
        # f"Files already present at destination - Could not link [purple]{self.src_path}[/purple] to [purple]{dest_path}[/purple] for source."
        await Audit.submit(
            "fetch_filesystem_link",
            Audit.Type.from_boolean(success),
            outcome,
            src=self.src_path,
            dest=dest_path,
        )
        await asyncio.sleep(0.2)
        return success


if sys.version_info[0] == 3 and sys.version_info[1] < 14:

    def do_copy(src_path, dest_path, create_dirs=False):
        import shutil

        shutil.copytree(src_path, dest_path, dirs_exist_ok=create_dirs)

else:

    def do_copy(src_path: Path, dest_path: Path, create_dirs=False):
        src_path.copy_into(dest_path)
