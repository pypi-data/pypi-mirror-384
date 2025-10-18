# Standard library imports
import json
import yaml
import re
from enum import Enum, unique
from typing import TYPE_CHECKING

# Project-specific imports
from shoestring_assembler.model.prompts import Prompts
from shoestring_assembler.model.filesystem import (
    UserConfigTemplateFilesystem,
    CompiledUserConfigFilesystem,
)
from shoestring_assembler.interface.events.updates import FatalError

# typing nonsense to prevent circular imports
if TYPE_CHECKING:
    from shoestring_assembler.model.base_module import BaseModule


class UserConfigTemplate:
    """
    Handles loading and access to the user configuration template files.
    Provides lazy loading for version, defaults, and prompts.
    """

    def __init__(self, fs: "UserConfigTemplateFilesystem"):
        self.fs = fs  # Filesystem abstraction for template files
        self.__version_loaded = False
        self.__version = None
        self.__defaults = None
        self.__prompts_loaded = False
        self.__prompts = None

    def exists(self):
        """Check if the template directory exists."""
        return self.fs.dir.exists()

    @property
    def version(self):
        """Lazily load and return the template version."""
        if not self.__version_loaded:
            self.__version = self.__load_version()
            self.__version_loaded = True
        return self.__version

    def __load_version(self):
        """Load the version from the template version file."""
        try:
            with self.fs.version_file.open("r") as f:
                return Version(f.read())
        except FileNotFoundError:
            raise FatalError(
                f"Couldn't find version file in template directory. File expected at {self.fs.version_file}."
            )
        except Version.Invalid:
            raise FatalError(f"The template version file contained an invalid version.")

    @property
    def defaults(self):
        """Lazily load and return the default values from the template."""
        if self.__defaults is None:
            self.__defaults = self.__load_defaults()
        return self.__defaults

    def __load_defaults(self):
        """Load default values from the defaults file (JSON)."""
        try:
            with self.fs.defaults_file.open("rb") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @property
    def prompts(self):
        """Lazily load and return the prompts from the template."""
        if not self.__prompts_loaded:
            self.__prompts = Prompts.load(self.fs.prompts_file)
            self.__prompts_loaded = True
        return self.__prompts


class UserConfig:
    """
    Manages the user's configuration, including versioning, status, and previous answers.
    Handles loading, saving, and status checking for user config files.
    """

    @unique
    class Status(Enum):
        """Possible statuses for the user configuration."""

        NO_TEMPLATE = "no_template"
        NOT_INITIALISED = "first_setup"
        MINOR_UPDATE = "minor_update"
        MAJOR_UPDATE = "major_update"
        WARN_FUTURE = "config_from_future"  # current version is higher than template
        UP_TO_DATE = "up_to_date"

    def __init__(
        self,
        module_uc_filesystem: "CompiledUserConfigFilesystem",
        template_fs: "UserConfigTemplateFilesystem",
    ):
        # Template for this user config
        self.__template = UserConfigTemplate(template_fs)

        # Filesystem abstraction for user config files
        self.fs = module_uc_filesystem
        self.__version_loaded = False
        self.__version = None
        self.__prev_answers = None
        self.__status = None

        # State for configuration process
        self.requires_configuration = False
        self.answers = {}

    @property
    def template(self):
        """Return the UserConfigTemplate instance."""
        return self.__template

    @property
    def version(self):
        """Lazily load and return the user config version."""
        if not self.__version_loaded:
            self.__version = self.__load_version()
            self.__version_loaded = True
        return self.__version

    @version.setter
    def version(self, new_value):
        """Set and save the user config version."""
        with self.fs.version_file.open("w") as f_out:
            f_out.write(str(new_value))

    def __load_version(self):
        """Load the version from the user config version file."""
        try:
            with self.fs.version_file.open("r") as f:
                return Version(f.read())
        except FileNotFoundError:
            return None
        except Version.Invalid:
            raise FatalError(
                f"The user config version file contained an invalid version."
            )

    @property
    def status(self):
        """Return the current status of the user config (lazy evaluation)."""
        if self.__status is None:
            self.__status = self.__get_status()
        return self.__status

    def __get_status(self):
        """Determine the status of the user config by comparing versions."""
        if not self.template.exists():  # there is no template
            return UserConfig.Status.NO_TEMPLATE

        # check template version - errors if format invalid or not found
        self.template.version

        # get user_config version from file - errors if format invalid
        # if not found then user config hasn't been set up - trigger setup
        if self.version == None:
            return UserConfig.Status.NOT_INITIALISED

        # compare versions and handle updates accordingly
        for index in range(2):
            if self.version[index] == self.template.version[index]:
                continue
            if self.version[index] < self.template.version[index]:
                match index:
                    case 0:  # major update
                        return UserConfig.Status.MAJOR_UPDATE
                    case 1:  # minor update
                        return UserConfig.Status.MINOR_UPDATE
            if self.version[index] > self.template.version[index]:
                return UserConfig.Status.WARN_FUTURE

        return UserConfig.Status.UP_TO_DATE

    @property
    def prev_answers(self):
        """Lazily load and return previous answers from the file."""
        if self.__prev_answers is None:
            self.__prev_answers = self.__load_prev_answers()
        return self.__prev_answers

    @prev_answers.setter
    def prev_answers(self, new_value):
        """Save new previous answers to the config file."""
        with self.fs.previous_answers.open("w") as f:
            json.dump(new_value, f)

    def __load_prev_answers(self):
        """Load previous answers from the config file (JSON)."""
        try:
            with self.fs.previous_answers.open("rb") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @property
    def prompt_defaults(self):
        """
        Returns a merged dict of template defaults and previous answers.
        Preference is given to previous answers
        """
        val = {**self.template.defaults, **self.prev_answers}
        print(f"DEF {val}")
        return {**self.template.defaults, **self.prev_answers}

    @property
    def answer_context(self):
        return {**self.prompt_defaults, **self.answers}

    @property
    def context(self):  # file gen context
        return self.template.prompts.generate_outputs(self.answer_context)


class Version(tuple):
    """
    Validates version string.
    Represents the version as a tuple (major, minor) so that it can be compared using <, ==, or >.
    Returns original version string when treated as a string (i.e. printed)
    """

    valid_regex = re.compile(r"^\s*(\d+)\.(\d+)\s*$")

    class Invalid(Exception):
        """Raised when a version string is invalid."""

        pass

    def __new__(cls, version_string):
        match = cls.valid_regex.match(version_string)
        if match is None:
            raise cls.Invalid(version_string)
        # Store as tuple of strings (major, minor)
        return super().__new__(cls, match.groups())

    def __init__(self, version_string):
        self.__version_string = version_string

    def __str__(self):
        return self.__version_string
