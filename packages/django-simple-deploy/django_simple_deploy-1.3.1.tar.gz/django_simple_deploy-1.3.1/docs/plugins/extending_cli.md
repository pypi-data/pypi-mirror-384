---
title: "Extending the CLI"
hide:
    - footer
---

# Extending the CLI

The core `django-simple-deploy` CLI has a fairly small set of options. You can see current output by running `python manage.py deploy --help`, and you can see a snapshot of that output [here](../general_documentation/cli_reference.md#help-output).

The [dsd-plugin-generator](https://github.com/django-simple-deploy/dsd-plugin-generator) will include support for extending the CLI shortly.

To see an example of a plugin that extends the core CLI, look at the [dsd-flyio](https://github.com/django-simple-deploy/dsd-flyio) plugin. In particular, note the following:

- The [two functions](https://github.com/django-simple-deploy/dsd-flyio/blob/main/dsd_flyio/deploy.py#L23-L32) `dsd_get_plugin_cli()` and `dsd_validate_cli()` in the plugin's `deploy.py` script.
- The `cli.py` [file](https://github.com/django-simple-deploy/dsd-flyio/blob/main/dsd_flyio/cli.py), which implements the plugin's options within the larger CLI.
- The [integration tests](https://github.com/django-simple-deploy/dsd-flyio/tree/main/tests/integration_tests). For example, see [test_vm_size_arg.py](https://github.com/django-simple-deploy/dsd-flyio/blob/main/tests/integration_tests/test_vm_size_arg.py) which verifies that passing a plugin-specific argument has the intended effect. This test tells core not to run `manage.py deploy`, so you can construct your own set of arguments for the call you want to test. This is specified by the mark `pytestmark = pytest.mark.skip_auto_dsd_call`.

The core library manages the overall CLI (core and plugin) until the final handoff to the plugin happens. Core validates the current command against its own CLI, and then runs the plugin's validation. This allows us to catch any potential issues before core makes any changes to the user's project.