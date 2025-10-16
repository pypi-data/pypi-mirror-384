---
title: Choosing a platform
hide:
    - footer
---

# Choosing a Platform

Choosing a platform to deploy to might seem difficult, because there are many to choose from these days. It's hard to say that any one platform is better than any other, because they all take different approaches to a complex problem - pushing your project to a remote server in a way that lets it run reliably, at a reasonable cost.

`django-simple-deploy` aims to make it easier to choose a platform by simplifying your first deployments to a variety of hosts. You don't have to do a deep dive into each platform's documentation in order to get a deployment up and running. Typically, you can make an account with the platform you're interested in, install that platform's CLI, install the plugin for that platform, and then push your project. You get a working deployment with very little effort, which makes further exploration of each platform much easier and much less frustrating.

This page summarizes the strengths and potential drawbacks of each platform.

*Note: Best efforts are made to keep this page up to date. If you see something that's no longer accurate, please [open an issue](https://github.com/django-simple-deploy/django-simple-deploy/issues) and include a link to the updated information.*

## Quick comparison

|                       | Fly.io             | Platform.sh             | Heroku                                                      |
| --------------------- | ------------------ | ----------------------- | ----------------------------------------------------------- |
| Credit Cards required for trial | N/A                | N/A                      | N/A |
| Free trial length     | No free trial | No free trial ^1^ | No free trial |
| Cheapest paid plan    | $1.94/mo ^2^              | $12/mo                  | $10/mo ^3^                     |
| Company founded       | 2017               | 2012                    | 2007                                                        |

1. The new PAAS service [UpSun](https://upsun.com) from Platform.sh offers a free trial, but django-simple-deploy does not support deployment to UpSun at this point.
2. This is for the machine that runs the Django project. With a database and some traffic, the actual amount will likely be higher.
3. Using a $5/month [Eco dyno](https://www.heroku.com/pricing/) and a $5/month [Essential 0 Postgres](https://elements.heroku.com/addons/heroku-postgresql) database.

## Detailed notes

=== "Fly.io"

    **Known for**

    * Fly.io automatically deploys your project to physical servers spread around the world. The goal is that your app will be equally responsive to users around the world.

    **Strengths**

    * Offers a [public forum](https://community.fly.io) for support, and allows you to search for issues (and resolutions) that others have had.
    * The cheapest plan is currently about $2/month, but that machine only has 256MB of RAM. A 1GB is currently less than $6/month.
    * If your total invoice on a personal account is less than $5 for any given month, you won't be billed for that month. It's not a credit though; if your invoice is over $5 you're responsible for the full amount owed.

    **Issues**

    * The distributed server model may not be suitable for all projects.
    * Fly has been growing for a while, and has had some outages along the way that have frustrated some users.
    * The documentation [states](https://fly.io/docs/about/billing/#if-you-dont-have-a-credit-card) that you can use a prepaid card to buy credits if you don't have a credit card. However, you need a credit card on file in order to open an account, and if you run out of credits your credit card will be charged.

    **Links**

    * [Fly.io home page](https://fly.io/)
    * [Pricing](https://fly.io/docs/about/pricing/) | [Pricing calculator](https://fly.io/calculator)
    * [Docs home page](https://fly.io/docs/)
    * [CLI installation](https://fly.io/docs/hands-on/install-flyctl/)
    * [CLI reference](https://fly.io/docs/flyctl/)
    * [Fly.io Status page](https://status.flyio.net)

    **Using `django-simple-deploy` with Fly.io**

    - [Quick start: Deploying to Fly.io](../quick_starts/quick_start_flyio.md)

=== "Platform.sh"

    **Known for**

    * Platform.sh is a managed hosting platform that focuses on making continuous deployment easy and safe. They even tell you it's okay to deploy on Fridays. :)

    **Strengths**

    * Once you have an environment set up with the Platform.sh tools, pushing a project and maintaining it is as straightforward as it is on any other comparable platform.


    **Issues**

    * Error messages about resource usage are unclear. For example, new users are limited to two new apps per day until they have been billed successfully three times. Since billing occurs once a month, this limit applies for several months, even though you're willing to pay for usage. Also, if you try to create a new project and it fails because of this issue, you don't get a specific error message. You have to contact support to find out if this is the reason for failure, or if something else went wrong.
    * The CLI requires a bash shell for deployment. This isn't particularly difficult on macOS or Linux, but installation is not straightforward on Windows if you don't already have Windows Subsystem for Linux (WSL) installed, or a comparable bash-compatible environment.

    **Links**

    * [Platform.sh home page](https://platform.sh)
    * [Pricing](https://platform.sh/pricing/)
    * [Docs home page](https://docs.platform.sh)
    * [CLI installation](https://docs.platform.sh/administration/cli.html)
    * [Platform.sh Status page](https://status.platform.sh)

    **Using `django-simple-deploy` with Platform.sh**

    - [Quick start: Deploying to Platform.sh](../quick_starts/quick_start_platformsh.md)

=== "Heroku"

    **Known for**

    * Heroku was the original "Platform as a Service:" (PaaS) provider. Heroku pioneered the simple `git push heroku main` deployment process that most other platforms are trying to build on today.
    * Heroku is known for being more expensive than options such as VPS providers, and AWS. However, they quite reasonably argue that using Heroku requires less developer focus than unmanaged solutions like a VPS or AWS. You get to spend more of your time building your project, and less time acting as a sysadmin.

    **Strengths**

    * Heroku has been managing automated deployments longer than any of the other platforms supported by `django-simple-deploy`.

    **Issues**

    * Heroku was a great platform in the late 2000s through the mid 2010s, but then it began to stagnate. Packages that were recommended for deployment were archived and unmaintained, even though they were officially still recommended. Heroku "just worked" for a long time, but recently that neglect has caught up to them. They've been restructuring their platform for a long time now, and people are reasonably concerned about Heroku's long-term stability.
    * Heroku has had major incidents and outages in recent years, which they took a long time to resolve and communicated poorly about. This is the more significant reason many people have moved away from them in recent years.
    * Heroku was famous for a very generous free tier, where you could deploy up to 5 apps at a time including a small Heroku Postgres database. This kind of offering sounds nice, but it also draws abuse. Heroku was constantly fighting things like auto-deployed crypto miners. They no longer offer a free tier. Their cheapest plans are still reasonably priced, though, so the end of the free tier should not rule them out as a hosting option.

    **Links**

    * [Heroku home page](https://www.heroku.com)
    * [Pricing](https://www.heroku.com/pricing)
    * [Docs home page](https://devcenter.heroku.com)
    * [CLI installation](https://devcenter.heroku.com/articles/heroku-cli)
    * [CLI reference](https://devcenter.heroku.com/categories/command-line)
    * [Python on Heroku](https://devcenter.heroku.com/categories/python-support)
    * [Getting Started on Heroku with Python](https://devcenter.heroku.com/articles/getting-started-with-python?singlepage=true)
    * [Working with Django (on Heroku)](https://devcenter.heroku.com/categories/working-with-django)
    * [Heroku Status page](https://status.heroku.com)

    **Using `django-simple-deploy` with Heroku**

    - [Quick start: Deploying to Heroku](../quick_starts/quick_start_heroku.md)

---
