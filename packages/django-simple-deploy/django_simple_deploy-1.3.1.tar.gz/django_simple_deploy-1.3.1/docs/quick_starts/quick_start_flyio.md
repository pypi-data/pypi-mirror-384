---
title: "Quick Start: Deploying to Fly.io"
hide:
    - footer
---

# Quick Start: Deploying to Fly.io

## Overview

Deployment to Fly.io can be fully automated, but the configuration-only approach is recommended. This allows you to review the changes that are made to your project before committing them and making the initial push. The fully automated approach configures your project, commits these changes, and pushes the project to Fly.io's servers.

## Prerequisites

Deployment to Fly.io requires three things:

- You must be using Git to track your project.
- You need to be tracking your dependencies with a `requirements.txt` file, or be using Poetry or Pipenv.
- You must have an active Fly.io account, and the [Fly.io CLI](https://fly.io/docs/hands-on/install-flyctl/) must be installed on your system.

## Configuration-only deployment

First, install `django-simple-deploy` and add `django_simple_deploy` to `INSTALLED_APPS` in *settings.py*:

```sh
$ pip install django-simple-deploy[fly_io]
# Add "django_simple_deploy" to INSTALLED_APPS in settings.py.
$ git commit -am "Added django_simple_deploy to INSTALLED_APPS."
```

!!! note
    If you're using zsh, you need to put quotes around the package name when you install it: `$ pip install "django-simple-deploy[fly_io]"`. Otherwise zsh interprets the square brackets as glob patterns.

Now create a new Fly.io app using the CLI, and run the `deploy` command to configure your app:

```sh
$ fly apps create --generate-name
$ python manage.py deploy
```

You'll be asked if the correct Fly app was identified for deployment. A database will then be created, and linked to the app you just created. After that, your project will be configured for deployment.

At this point, you should review the changes that were made to your project. Running `git status` will show you which files were modified, and which files were created for a successful deployment. If you want to continue with the deployment process, commit these changes and run the `fly deploy` command; the initial migration is done automatically.

When deployment is complete, use the `fly apps open` command to see the deployed version of your project:

```sh
$ git add .
$ git commit -m "Configured for deployment to Fly.io."
$ fly deploy
$ fly apps open
```

You can find a record of the deployment process in `dsd_logs`. It contains most of the output you saw when running `deploy`.

## Automated deployment

If you want, you can automate this entire process. This involves just three steps:

```sh
$ pip install django-simple-deploy[fly_io]
# Add `django_simple_deploy` to INSTALLED_APPS in settings.py.
$ python manage.py deploy --automate-all
```

You should see a bunch of output as Fly.io resources are created for you, your project is configured for deployment, and `simple_deploy` pushes your project to Fly.io's servers. When everything's complete, your project should open in a new browser tab.

## Pushing further changes

After the initial deployment, you're almost certainly going to make further changes to your project. When you've updated your project and it works locally, you can commit these changes and push your project again, without using `django-simple-deploy`:

```sh
$ git status
$ git add .
$ git commit -m "Updated project."
$ fly deploy
```

## Running management commands

To run management commands such as `migrate` against the deployed project, use the `ssh` command to log into a console on the remote server:

```sh
$ fly ssh console
```

## Customizing the deployment

A deployment with no options configures smaller, cheaper resources. You can customize your deployment by passing extra CLI args. Currently there is one Fly-specific option, `--vm-size`:

```sh
$ python manage.py deploy --help
...
Options for dsd-flyio:
  --vm-size VM_SIZE     Name for a preset vm-size configuration on Fly.io, ie `shared-cpu-2x`.
```

To see the full set of options for `--vm-size`, see the [Started Fly Machines](https://fly.io/docs/about/pricing/#started-fly-machines) section on Fly's pricing page. You can also see a full list of options by running `fly platform vm-sizes`.

## Troubleshooting

If deployment doesn't work, feel free to open an [issue](https://github.com/django-simple-deploy/django-simple-deploy/issues). Please share the OS you're  using locally, and the specific error message or unexpected behavior you saw. If the project you're deploying is hosted in a public repository, please share that as well.

## A note about `fly` and `flyctl`

The `fly` and `flyctl` commands are used on the Fly.io docs interchangeably. They are standardizing on `fly`, so that's what we'll be using here.
