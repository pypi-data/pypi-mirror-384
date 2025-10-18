from shoestring_assembler.model import SolutionModel
from shoestring_assembler.interface.events.audit import Audit
from shoestring_assembler.interface.events import FatalError, Update

class SolutionFilesystem:
    @classmethod
    async def clean(cls, solution_model:SolutionModel,remove_downloaded_files=True):
        await Update.StepHeading("Cleaning old files")
        
        await solution_model.fs.clean()
        for source in solution_model.sources:
            with Audit.Context(f"source::{source.name}"):
                await source.fs.clean(remove_downloaded_files)

        await Update.SuccessMsg("Old assembled files cleaned")

    @classmethod
    async def verify(cls, solution_model: SolutionModel, check_source_download=False):

        await Update.StepHeading("Verifying filesystem structure")

        all_ok = await solution_model.fs.verify()

        if not all_ok:
            raise FatalError(
                "Solution filesystem failed validation - unable to continue"
            )

        for source in solution_model.sources:
            with Audit.Context(f"source::{source.name}"):
                all_ok = await source.fs.verify(check_source_download) and all_ok

        for sm in solution_model.service_modules:
            with Audit.Context(f"service_module::{sm.name}"):
                all_ok = await sm.fs.verify() and all_ok

        for inf in solution_model.infrastructure:
            with Audit.Context(f"infrastructure::{inf.name}"):
                all_ok = await inf.fs.verify() and all_ok

        if not all_ok:
            raise FatalError(
                "Source filesystem failed validation - unable to continue"
            )

        await Update.SuccessMsg("Filesystem valid")
