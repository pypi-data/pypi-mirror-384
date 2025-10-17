# Django-ESI

Django app for easy access to the EVE Swagger Interface (ESI)

[![Version](https://img.shields.io/pypi/v/django-esi)](https://pypi.org/project/django-esi/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-esi)](https://pypi.org/project/django-esi/)
[![Django Versions](https://img.shields.io/pypi/djversions/django-esi)](https://pypi.org/project/django-esi/)
[![License](https://img.shields.io/badge/license-GPLv3-green)](https://pypi.org/project/django-esi/)
[![Pipeline Status](https://gitlab.com/allianceauth/django-esi/badges/master/pipeline.svg)](https://gitlab.com/allianceauth/django-esi/pipelines)
[![Coverage](https://gitlab.com/allianceauth/django-esi/badges/master/coverage.svg)](https://gitlab.com/allianceauth/django-esi/pipelines)
[![Documentation Status](https://readthedocs.org/projects/django-esi/badge/?version=latest)](https://django-esi.readthedocs.io/en/latest/?badge=latest)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Chat on Discord](https://img.shields.io/discord/399006117012832262.svg)](https://discord.gg/fjnHAmk)

## Overview

Django-ESI is a Django app that provides an interface for easy access to the EVE Swagger Interface (ESI), the official API for the game [EVE Online](https://www.eveonline.com/).

It is built upon [Bravado](https://github.com/Yelp/bravado) - a python client library for Swagger 2.0 services.

Django-ESI adds the following main functionalities to a Django site:

- Dynamically generated client for interacting with public and private ESI endpoints
- Support for adding EVE SSO to authenticate characters and retrieve tokens
- Control over which ESI endpoint versions are used

## Python Support

Django-ESI follows the Django Python support schedule, The supported version of Python will differ based on the version of Django used.
<https://docs.djangoproject.com/en/5.2/faq/install/#what-python-version-can-i-use-with-django>

## History of this app

This app is a fork from [adarnauth-esi](https://gitlab.com/Adarnof/adarnauth-esi). Since this app is an important component of the [Alliance Auth](https://gitlab.com/allianceauth/allianceauth) system and Adarnof - the original author - was no longer able to maintain it the AA dev team has decided in December 2019 to take over maintenance and further developing for this app within the Alliance Auth project.

## Documentation

For all details on how to install and use Django-ESI please see the [Documentation](https://django-esi.readthedocs.io/en/latest/).
