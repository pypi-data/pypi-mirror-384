---
title: Integration Tests
hide:
    - footer
---

The main goal of integration tests is to run the `deploy` command against a test project, and verify that it makes appropriate changes to the project. This happens *without* any network calls, or use of external resources.

Integration tests include some other tests as well, such as making sure that invalid calls generate appropriate error messages.

The challenge
---

The challenge of writing integration tests is that `deploy` is a standalone management command. The project has no settings of its own. There are no apps, no *manage.py* file, or anything like that.

The current approach to integration testing is to copy the example project to a temp dir, and then run `manage.py deploy` against that temp project. Including the `--integration-testing` flag when running the `deploy` command prevents any network calls from being made.

It's also a challenge that the `deploy` command needs to be called repeatedly against the same temp project. The test suite issues Git commands to manage the state of the temp project during the test run.

Running integration tests
---

```sh
(.venv)django-simple-deploy$ pytest tests/integration_tests
```

Integration tests require that Poetry and Pipenv are installed. The tests call `manage.py deploy` against a version using each of these package managers, once for each supported platform. It should tell you gracefully if one of these requirements is not met.

### Testing and plugins

To fully test `django-simple-deploy`, you need to have a plugin installed in editable mode. That plugin needs to have an appropriate set of integration tests. When developing the core project, I use the `dsd-flyio` plugin. (Installing a plugin through PyPI does not include the plugin's tests.)

You can run tests without a plugin installed, but they are very minimal tests. You won't actually be testing the changes that simple deploy makes to a user's project, and you won't be testing the core-plugin interface.

It's probably worth developing a plugin that's purely used for integration testing. The test plugin would make generic changes to the user's project such as modifying settings and adding new files, without being specific to any one platform.

### Consider using the `-s` flag

```sh
(.venv)django-simple-deploy$ pytest tests/integration_tests -s
```

If you include the `-s` flag, you'll see a whole bunch of output that can be helpful for troubleshooting. For example you'll see output related to creating a copy of the project in a temp environment, you'll see all the variations of the `deploy` command that are being run, and you'll see the locations of the test projects that are being set up.

Running unit and integration tests together
---

Unit tests and integration tests can be run together:

```sh
(.venv)django-simple-deploy$ pytest
```

The bare `pytest` command will run all unit and integration tests. It will *not* run end-to-end tests; those tests need to be run explicitly.

Tests as a development tool
---

The integration tests are quite useful for ongoing development work. For example, consider the following test command:

```sh
(.venv)django-simple-deploy$ % pytest tests/integration_tests -k req_txt -s
```

This will create a temp project that uses requirements.txt to manage dependencies, and run a slight variation of `python manage.py deploy` against the project.

The `-s` flag will show you exactly where that temp project is. You can open a terminal, cd to that directory, activate the project's virtual environment, and poke around as much as you need to. You can modify `django-simple-deploy`, and run the `deploy` command again. You can run `git status` and `git log`, and reset the project to an earlier state, and run the `deploy` command as many times as you want.

This is often *much* easier than just working in a test project that you set up manually. And if tests are not passing, you can run `pytest tests/integration_tests -x` repeatedly with the same kind of workflow. This has been a really powerful workflow in developing the project so far.

If you run the `deploy` command in this way, use the `--unit-testing` flag as well. That will avoid any network calls, and use appropriate project names. In the output of the integration test, you can see exactly what the `deploy` command looks like in testing:

```txt
*** dsd_command: /private/.../pytest-48/blog_project1/b_env/bin/python manage.py deploy --unit-testing --deployed-project-name my_blog_project ***
```

### Look at the logs

If you're troubleshooting a failed test, run `pytest tests/integration_tests --lf -s` to rerun the last failed test. Go to the temp project directory, and look at the log that was generated in `dsd_logs/`. That log file will often tell you exactly where the command failed. Again, you can use Git to reset the test project, and run the `deploy` command again to recreate the issue manually.

### Experimental feature

On macOS, you can run the following command:

```sh
(.venv)django-simple-deploy$ pytest tests/integration_tests -x --open-test-project
```

This will stop at the first failed test, and open a new terminal tab at the test project's location. It runs `git status` and `git log --pretty=oneline` automatically, and invites you to poke around the project. This is a really helpful feature, that I'd like to refine.

Maintaining integration tests
---

### Updating reference files

Examining the test project is an efficient way to update reference files. Say you've just updated the code for generating a Dockerfile for a specific package management system, ie Poetry. You can run the test suite with `pytest -x`, and it will fail at the test that checks the Dockerfile for that platform when Poetry is in use. You can examine the test project, open the Dockerfile, and verify that it was generated correctly for the sample project. If it is, copy this file into the `reference_files/` directory, and the tests should pass.

### Updating packages in `vendor/`

The main purpose of the `vendor/` directory is to facilitate integration testing. To add a new package to the directory:

```sh
(.venv) $ pip download --dest vendor/ package_name
```

To upgrade all packages in `vendor/`:

```sh
$ rm -rf vendor/
$ pip download --dest vendor/ -r sample_project/blog_project/requirements.txt
```

This can be done automatically by running the update script from *developer_resources/*:

```sh
$ python developer_resources/update_sample_project_reqs.py
```

This will generate an updated *requirements.txt* file for the sample project, and download the appropriate packages to *vendor/*. This will break existing tests for plugins, so this should only be done on new Django point releases.