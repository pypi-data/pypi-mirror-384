# DBCA Django web template

This project consists of a basic Django application containing HTML
templates that provide a starting point for web applications used by the
[Department](http://www.dbca.wa.gov.au). The base template consists of a mobile-friendly
HTML5 template with a fixed top navbar, plus static assets.
The project also contains functional examples of **login** and
**logged out** templates.

The base templates are based upon [HTML5 Boilerplate](https://html5boilerplate.com).

## Development

The recommended way to set up this project for development is using
[uv](https://docs.astral.sh/uv/)
to install and manage a Python virtual environment.
With uv installed, install the required Python version (see `pyproject.toml`). Example:

    uv python install 3.12

Change into the project directory and run:

    uv python pin 3.12
    uv sync

Activate the virtualenv like so:

    source .venv/bin/activate

Run unit tests using `pytest` (or `tox`, to test against multiple Python versions):

    pytest -sv
    tox -v

## Releases

Tagged releases are built and pushed to PyPI automatically using a GitHub
workflow in the project. Update the project version in `pyproject.toml` and
tag the required commit with the same value to trigger a release. Packages
can also be built and uploaded manually, if desired.

Build the project locally using uv, [publish to the PyPI registry](https://docs.astral.sh/uv/guides/publish/#publishing-your-package)
using the same tool if you require:

    uv build
    uv publish

## Installation

1. Install via pip: `pip install webtemplate-dbca`.
1. Add `'webtemplate_dbca'` to `INSTALLED_APPS`.
1. Ensure that the `staticfiles` application is included and configured
   correctly.
1. (Optional) Ensure that you have defined the following named URLs: `login` and
   `logout` (this requirement can be overriden, see below).
1. Extend the included base template by placing the following at the head
   of your own templates, e.g. `{% extends "webtemplate_dbca/base_b4.html" %}`
1. Place page content within the required blocks (see below).

## Included CSS and JavaScript

The base_b4/base_b5 templates include the following CSS and JavaScript assets:

- Modernizr (HTML5 polyfills)
- Bootstrap 4 or 5 (CSS & JS)
- jQuery (base/base_b4 templates)

Additional styling can be included using the `extra_style` or `extra_js`
blocks, like so::

    {% load static from staticfiles %}

    {% block extra_style %}
    {{ block.super }}
    <link rel="stylesheet" href="{% static 'css/custom.css' %}">
    {% endblock %}

You can also overide the `base_style` and `base_js` blocks completely to
use different CSS or JS libraries. Note that you will also need to replace the
`top_navbar` block contents if you replace the base Bootstrap CSS & JS.

The version of jQuery which is loaded in the base is by default a slimmed-down
minimal version of the library. To include a different specific version, override
the `jquery_version` block. Example::

    {% block jquery_version %}
    <script src="https://code.jquery.com/jquery-3.4.1.js"></script>
    {% endblock %}

**NOTE**: There is no jQuery loaded with the base_b5 template, as it was dropped
as a requirement of Bootstrap.

## Template blocks

The base template contains a number of block tags that are used to render the
content of your project. The main template content blocks are as follows:

- `navbar_links` - used to define navigation links in the top navbar.
- `navbar_auth` - used to display either a **Login** or **Logout** link.
- `page_content` - used to contain the page's main content.
- `page_footer` - used to contain a page footer area.

Note that the `navbar_auth` block contains `{% url %}` templatetags with
named URLs called _login_ and _logout_. If this is not required or
inappropriate for your project, simply override the `navbar_auth` block
in a base template like so::

    {% block navbar_auth %}{% endblock %}

In addition, a number of context variables are defined:

- `page_title` - used to populate the page **<title>** tags.
- `site_title` - used to populate the projects's title in the top navbar.
- `site_acronym` - used to populate a shorter title in the navbar (B4 template).

Context variables should be passed to templates in every view.

## Bootstrap 4 & 5 examples

The following examples apply to the `base_b4.html` and `base_b5.html` templates.

To extend the base template with an optional row to display alert messages plus
a shaded footer div, try the following (further page content is then injected to
the `page_content_inner` block)::

    {% extends "webtemplate_dbca/base_b4.html" %}

    {% block extra_style %}
    <style>
        .footer {background-color: lightgrey}
    </style>
    {% endblock %}

    {% block page_content %}
        <div class="container-fluid">
            <!-- Messages  -->
            {% if messages %}
            <div class="row">
                <div class="col">
                    {% for message in messages %}
                    <div class="alert{% if message.tags %} alert-{{ message.tags }}{% endif %}">
                        {{ message|safe }}
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            <div class="row">
                <div class="col">
                    {% block page_content_inner %}{% endblock %}
                </div>
            </div>
        </div>
    {% endblock %}

    {% block page_footer %}
    <footer class="footer mt-auto py-3">
        <div class="container-fluid">
            <div class="row">
                <div class="col">
                    <small class="float-right">&copy; Department of Biodiversity, Conservation and Attractions</small>
                </div>
            </div>
        </div>
    </footer>
    {% endblock page_footer %}
