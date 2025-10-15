Nextstrain Sphinx Theme
=======================

A `Sphinx theme`_ for Nextstrain's documentation, based on `Read The Docs`_'
default theme (sphinx_rtd_theme_).

Installation
------------

This theme is distributed on PyPI as nextstrain-sphinx-theme_ and can be
installed with ``pip``:

.. code:: console

    $ python3 -m pip install nextstrain-sphinx-theme

To use the theme in your Sphinx project, you will need to add the following to
your ``conf.py`` file:

.. code:: python

    html_theme = "nextstrain-sphinx-theme"

This theme is based on sphinx_rtd_theme_ and accepts most of the same
`configuration options`_ settable via ``html_theme_option`` and a few
additional options as well:

:logo: Boolean determining if the Nextstrain logo should be displayed.
       Defaults to true.

:logo_link: URL to use for the logo's link.  Defaults to
            <https://docs.nextstrain.org>.

:logo_only: Ignored.  Inherited from sphinx_rtd_theme_.  Instead, the project
            name and version info will not be displayed (thus showing only the
            logo) when ``subproject`` is true.

:subproject: Boolean determining if this is a subproject of the main Nextstrain
             documentation project on <https://docs.nextstrain.org>.  Defaults
             to true.

If your project wants to display its own logo, just set Sphinx's ``html_logo``
to point to the image file in your Sphinx project.

.. code:: python

    html_logo = "_static/your-logo.png"

This will automatically take precedence over the default Nextstrain logo
provided by the theme.

Development
-----------

.. code:: bash

    python3 -m pip install -e .
    make clean # not always needed, but better to be cautious
    make html
    open build/html/index.html

Releasing
---------

1. Make sure all your changes have been commited to the ``main`` branch.
2. Add a commit which describes the changes from the previous version to ``CHANGES.rst`` and updates the version number in ``lib/nextstrain/sphinx/theme/VERSION``.
3. Tag this commit with the version number, e.g. ``git tag -a 2020.4 -m "version 2020.4"``.
4. Push the commit and tag to GitHub, e.g. ``git push origin main 2020.4``.
5. Publish to PyPI by invoking a GitHub Actions workflow:

   1. Go to the workflow: `publish.yml <https://github.com/nextstrain/sphinx-theme/actions/workflows/publish.yml>`_.
   2. Select **Run workflow**. In the new menu:

      1. Select **Use workflow from** > **Tags** > new version number (e.g. 2020.4).
      2. Set **PyPI instance for publishing** as *PyPI* (default) or *TestPyPI*. `More info <https://packaging.python.org/en/latest/guides/using-testpypi/>`_
      3. Select **Run workflow**.

.. _Sphinx theme: https://www.sphinx-doc.org/en/master/theming.html
.. _Read The Docs: https://readthedocs.org
.. _sphinx_rtd_theme: https://github.com/readthedocs/sphinx_rtd_theme
.. _nextstrain-sphinx-theme: https://pypi.org/project/nextstrain-sphinx-theme/
.. _configuration options: https://sphinx-rtd-theme.readthedocs.io/en/latest/configuring.html

Testing
-------

PR test builds are available here: https://readthedocs.org/projects/nextstrain-sphinx-theme/builds/ and usually follow the following URL path convention: https://nextstrain--17.org.readthedocs.build/projects/sphinx-theme/en/17/ where 17 is the PR number
