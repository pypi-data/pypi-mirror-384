# Jama

Jama is a [Django](https://www.djangoproject.com/) application that exposes APIs and UIs that allow users to organize collections of resources.

Knowledge of the Django framework is expected and the Jama documentation is, to put it midly, a work in progress.

## Install

    pip install jama-CERTIC

## Usage

Jama behaves like a normal Django app except the management script is not called `manage.py` but `jama`.

List of commands:

    jama --help

Upon first run, Jama creates a `$HOME/.jama/` directory where it stores all its data.

Development server:

    jama runserver

Background tasks:

    jama run_huey

## Configuration

Configuration can be changed by adding environment variables the usual way or by adding them to your
`$HOME/.jama/env` configuration file

Available variables:

    JAMA_DEBUG="0"
    JAMA_APPS="ui"
    JAMA_IIIF_ENDPOINT="http://localhost/iip/IIIF="  # base URL for the IIIF server (use IIP server or Cantaloupe)
    JAMA_IIIF_UPSCALING_PREFIX="^"
    JAMA_SECRET="7d*_8c!d$vv963qpr45_x)@f2t-x6fu2&yi+m+d6s!p!lt+_j+"
    JAMA_SITE="http://localhost:8000/"
    JAMA_STATIC_ROOT="var/static"  # where to put files when using "jama collectstatic"
    JAMA_USE_MODSHIB="1"
    MODSHIB_SHOW_LOCAL_LOGIN="1"
    MODSHIB_SHOW_SSO_LOGIN="0"
