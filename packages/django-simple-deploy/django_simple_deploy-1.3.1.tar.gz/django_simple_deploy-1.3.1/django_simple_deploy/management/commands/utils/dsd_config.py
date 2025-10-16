from .command_errors import DSDCommandError


class DSDConfig:
    """Class for managing attributes of `Command` that need to be shared with plugins.

    This is instantiated once at the module level in `plugin_utils`. That instance is
    imported into `deploy.py`, where `Command` defines all relevant attributes, and
    calls `validate()`.

    Plugins then import the `dsd_config` instance from `plugin_utils`. If mutability is an
    issue, or if multiple instances of `DSDConfig` are being created, consider making this
    a singleton class.

    No module other than `plugin_utils` should import this class directly, or otherwise
    make an instance of this class. All access should happen through the `dsd_config`
    variable in `plugin_utils`.
    """

    def __init__(self):
        """Define all attributes that will need to be shared."""
        # Version of the currently installed version of django-simple-deploy.
        self.version = None

        # Aspects of user's system.
        self.on_windows = None
        self.on_macos = None

        # Aspects of user's local project.
        self.local_project_name = ""
        self.pkg_manager = ""
        self.requirements = None
        self.nested_project = None
        self.nanodjango_project = None
        self.nanodjango_script = None
        self.wagtail_project = False

        # Paths in user's local project.
        self.project_root = None
        self.git_path = None
        self.settings_path = None
        self.pipfile_path = None
        self.pyprojecttoml_path = None
        self.req_txt_path = None

        # Aspects of user's deployment.
        self.deployed_project_name = ""
        self.log_output = None
        self.automate_all = None
        self.region = None

        # Attributes needed by plugin utility functions.
        self.use_shell = None
        self.e2e_testing = None
        self.unit_testing = None
        self.stdout = None

    def validate(self):
        """Make sure all required attributes have been defined."""
        if not self.version:
            msg = "Could not identify version of django-simple-deploy in use."
            raise DSDCommandError(msg)

        if not self.pkg_manager:
            msg = "Could not identify dependency management system in use."
            raise DSDCommandError(msg)

        if self.requirements is None:
            msg = "Could not identify project dependencies."
            raise DSDCommandError(msg)

        if self.project_root is None:
            msg = "Could not identify project's root directory."
            raise DSDCommandError(msg)

        if self.settings_path is None and not self.nanodjango_project:
            msg = "Could not identify path to settings.py."
            raise DSDCommandError(msg)

        if self.stdout is None:
            msg = "Failed to access stdout."
            raise DSDCommandError(msg)
