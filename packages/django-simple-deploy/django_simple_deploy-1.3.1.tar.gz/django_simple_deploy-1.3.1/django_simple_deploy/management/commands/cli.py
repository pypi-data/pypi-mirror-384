"""Defines the CLI for django-simple-deploy."""

import argparse


def get_usage():
    """Return a custom usage text."""
    return """manage.py deploy
        [--automate-all]
        [--no-logging]
        [--ignore-unclean-git]

        [--region REGION]
        [--deployed-project-name DEPLOYED_PROJECT_NAME]"""


class SimpleDeployCLI:
    def __init__(self, parser):
        """Defines the CLI for django-simple-deploy."""

        # Define groups of arguments. These groups help generate a clean
        #   output for `manage.py deploy --help`
        help_group = parser.add_argument_group("Get help")
        required_group = parser.add_argument_group("Required arguments")
        behavior_group = parser.add_argument_group(
            "Customize django-simple-deploy's behavior"
        )
        deployment_config_group = parser.add_argument_group(
            "Customize deployment configuration"
        )

        # Show our own help message.
        help_group.add_argument(
            "--help", "-h", action="help", help="Show this help message and exit."
        )

        # --- Arguments to customize django-simple-deploy behavior ---

        behavior_group.add_argument(
            "--automate-all",
            help="Automate all aspects of deployment. Create resources, make commits, and run `push` or `deploy` commands.",
            action="store_true",
        )

        # Allow users to skip logging.
        behavior_group.add_argument(
            "--no-logging",
            help="Do not create a log of the configuration and deployment process.",
            action="store_true",
        )

        # Allow users to use the deploy command even with an unclean git status.
        behavior_group.add_argument(
            "--ignore-unclean-git",
            help="Run the deploy command even with an unclean `git status` message.",
            action="store_true",
        )

        # --- Arguments to customize deployment configuration ---

        # Allow users to set the deployed project name. This is the name that will be
        # used by the platform, which may be different than the name used in the
        # `startproject` command. See the Platform.sh script for use of this flag.
        deployment_config_group.add_argument(
            "--deployed-project-name",
            type=str,
            help="Provide a name that the plugin will use for this project.",
            default="",
        )

        # Allow users to specify the region for a project when using --automate-all.
        deployment_config_group.add_argument(
            "--region",
            type=str,
            help="Specify the region that this project will be deployed to.",
            default="us-3.platform.sh",
        )

        # --- Testing arguments ---

        # Since these are never used by end users, they're not included in the help
        # text. Make sure these are appropriately documented in other ways.

        # If we're doing local unit testing, we need to avoid some network calls.
        parser.add_argument(
            "--unit-testing", action="store_true", help=argparse.SUPPRESS
        )

        # Used for e2e testing, to avoid confirmations.
        parser.add_argument(
            "--e2e-testing", action="store_true", help=argparse.SUPPRESS
        )
