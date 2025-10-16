---
title: End-to-End Tests
hide:
    - footer
---

End-to-end tests recreate the exact steps we expect users to take on their own system, ending in a live deployment to the platform that's being tested.

Each test makes a copy of the sample project, runs the `deploy` command, and makes a full deployment. If you want to run these tests, you'll need an account on the platform you're testing against. The test will create an app under your account, and it should prompt you to destroy that app if the test runs successfully. If the test script fails, it may exit before destroying some deployed resources. **You should verify that the app and any related resources were actually destroyed, because these resources will almost certainly accrue charges on your account.** (If you have any questions or concerns about this, see the section [Testing on Your Own Account](../../contributing/own_account).)

E2e tests can take 3-10 minutes per deployment, and they almost always generate resources on a remote server that cost money if not destroyed properly. I have not set up an automated matrix of e2e tests like I have for integration tests. I don't want 3, 9, 27, etc full deployments accruing charges if something goes wrong! In practice, this has been fine. Integration tests cover things well enough for now that I haven't needed to test every full deployment path on every merge, or even every release.

Running e2e tests
---

Bare `pytest` calls only run unit and integration tests. If you want to run e2e tests, you have to do so explicitly.

For example, here's how you run an e2e test for deploying to Fly.io:

```sh
(.venv)django-simple-deploy$ pytest tests/e2e_tests --plugin dsd_flyio -s
```

E2e tests require the `-s` flag. There's too much information in an e2e test at this point to run silently. Also, some platforms take such a long time to finish a deployment that it's really helpful to know if the deployment is slow, or has hung in a way that won't finish.

The test creates a copy of the sample project, runs the `deploy` command, makes Git commits, and pushes the project. It does all these steps exactly as a user would. It also runs a small set of tests against the deployed project to make sure it actually works, and doesn't just show a correct home page. After that, it runs those same tests against a local version of the project. This makes sure the configuration changes for deployment haven't affected the ability to run the project locally.

If the test runs successfully, you'll see the deployed project in a new browser tab, and you'll be prompted to destroy the project. This lets you poke around at the deployed project if you need to.

### Specifying a package manager

By default, e2e tests use a requirements.txt file in the sample project. If you want to test a Poetry-based project, use this command:

```sh
(.venv)django-simple-deploy$ pytest tests/e2e_tests --plugin dsd_flyio --pkg-manager poetry -s
```

Options for `--pkg-manager` are `req_txt` (default), `poetry`, and `pipenv`.

### Testing the `--automate-all` flag

You can test a deployment with the `--automate-all` flag:

```sh
(.venv)django-simple-deploy$ pytest tests/e2e_tests --plugin dsd_flyio --automate-all -s
```

You won't notice a whole lot of difference compared to e2e tests without this flag, but it mimics the user's actions when using this flag. Instead of the e2e tests making commits on the test project, the `deploy` command makes those commits and runs the platform's push command just as it would on a user's system.

### Testing plugin-specific CLI args

You can test plugin-specific CLI args by passing the `--plugin-args-string` option:

```sh
$ pytest tests/e2e_tests --plugin dsd_flyio -s --plugin-args-string "--vm-size shared-cpu-2x"
```

Your test must pass the `cli_options.plugin_args_string` value to the function that actually calls `deploy`:

```python
def test_deployment(tmp_project, cli_options, request):
    """Test the full, live deployment process to Fly.io."""
    ...

    # Run simple_deploy against the test project.
    it_utils.run_simple_deploy(python_cmd, "fly_io", cli_options.automate_all, cli_options.plugin_args_string)
```

### Tests as a development tool

If you're investigating a bug that integration tests aren't helping with, a really efficient approach is to run the e2e test for the platform and workflow you're focusing on. Then open the test project in a new terminal window, activate its virtual environment, and do your development and debugging work there. You can reset the project to any state you want, modify `django-simple-deploy` and/or the relevant plugin, and rerun the `deploy` command as many times as you need. This is often much more efficient than making a sample project and doing a manual push using `django-simple-deploy`.

### Testing the PyPI release

After making a new release, it's reassuring to test the released version. You can do this with the `--pypi` flag. One benefit is that it can catch issues with the overall packaging of the project.

```sh
(.venv)django-simple-deploy$ pytest tests/e2e_tests --plugin dsd_flyio --pypi -s
```

After building the test project in a tmp dir, this will install `django-simple-deploy` and the relevant plugin from PyPI, instead of making editable installs of the local versions of these projects.

When you're testing right after a new release was made, make sure you're actually testing the new release. Caching issues, both locally and remote, can lead to a test of the previous release. You might need to [clear your pip cache](https://pip.pypa.io/en/stable/cli/pip_cache/) (`pip cache purge`) in order to test the new release.
