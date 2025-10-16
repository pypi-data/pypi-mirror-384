# MemberAudit Dashboard Addon module for AllianceAuth.<a name="aa-memberaudit-dashboard"></a>

![Release](https://img.shields.io/pypi/v/aa-memberaudit-dashboard?label=release)
![Licence](https://img.shields.io/github/license/geuthur/aa-memberaudit-dashboard)
![Python](https://img.shields.io/pypi/pyversions/aa-memberaudit-dashboard)
![Django](https://img.shields.io/pypi/frameworkversions/django/aa-memberaudit-dashboard.svg?label=django)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Geuthur/aa-memberaudit-dashboard/master.svg)](https://results.pre-commit.ci/latest/github/Geuthur/aa-memberaudit-dashboard/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checks](https://github.com/Geuthur/aa-memberaudit-dashboard/actions/workflows/autotester.yml/badge.svg)](https://github.com/Geuthur/aa-memberaudit-dashboard/actions/workflows/autotester.yml)
[![codecov](https://codecov.io/gh/Geuthur/aa-memberaudit-dashboard/graph/badge.svg?token=B3BSovXASa)](https://codecov.io/gh/Geuthur/aa-memberaudit-dashboard)
[![Translation status](https://weblate.voices-of-war.de/widget/allianceauth/aa-memberaudit-dashboard/svg-badge.svg)](https://weblate.voices-of-war.de/engage/allianceauth/)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W810Q5J4)

Simple Dashboard Memberaudit Addon to display not registred Chars

## -

- [AA MemberAudit Dashboard](#aa-memberaudit-dashboard)
  - [Features](#features)
  - [Upcoming](#upcoming)
  - [Installation](#features)
    - [Step 1 - Install the Package](#step1)
    - [Step 2 - Configure Alliance Auth](#step2)
    - [Step 3 - Migration to AA](#step3)
  - [Highlights](#highlights)
  - [Translations](#translations)

## Introduce

Everyone knows the issue that some people not register correctly now the members see on the Dashboard that something is wrong...

## Features<a name="features"></a>

- Show not registred Characters on Dashboard
- Member Audit Character Issue Checker

## Upcoming<a name="upcoming"></a>

- More Information in Dashboard

## Installation<a name="installation"></a>

> [!NOTE]
> AA MemberAudit Dashboard needs at least Alliance Auth v4.0.0
> Please make sure to update your Alliance Auth before you install this APP

### Step 1 - Install the Package<a name="step1"></a>

Make sure you're in your virtual environment (venv) of your Alliance Auth then install the pakage.

```shell
pip install aa-memberaudit-dashboard
```

### Step 2 - Configure Alliance Auth<a name="step2"></a>

Configure your Alliance Auth settings (`local.py`) as follows:

- Add `'memberaudit',` to `INSTALLED_APPS`
- Add `'madashboard',` to `INSTALLED_APPS`

### Step 3 - Migration to AA<a name="step3"></a>

```shell
python manage.py collectstatic
python manage.py migrate
```

## Highlights<a name="highlights"></a>

![Screenshot 2024-07-05 093013](https://github.com/Geuthur/aa-memberaudit-dashboard/assets/761682/4fe45fc5-c260-4c9e-bc7a-29a6c9e8cdd1)

## Translations<a name="translations"></a>

[![Translations](https://weblate.voices-of-war.de/widget/allianceauth/aa-memberaudit-dashboard/multi-auto.svg)](https://weblate.voices-of-war.de/engage/allianceauth/)

Help us translate this app into your language or improve existing translations. Join our team!"

## Contributing <a name="contributing"></a>

You want to improve the project?
Please ensure you read the [contribution guidelines](https://github.com/Geuthur/aa-memberaudit-dashboard/blob/master/CONTRIBUTING.md)
