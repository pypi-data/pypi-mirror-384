BalderHub-GUIControl
====================

.. note::
    This is a BalderHub package for the `Balder <https://docs.balder.dev/>`_ test framework. It is used in different
    other balderhub projects that interact with graphical user interfaces. If you are new to Balder check out the
    `official documentation <https://docs.balder.dev>`_ first.

The BalderHub GUIControl package provides basic feature implementation for controlling GUI components of a lot of
different kinds.

This package is used in projects like shown in the following table:

+-----------------------------------------------------------------+----------------------------------------------------+
| Project                                                         | Description                                        |
+=================================================================+====================================================+
| ``balderhub-webdriver`` (COMING SOON)                           | Base package for different guicontrol packages     |
|                                                                 | like ``balderhub-selenium``,                       |
|                                                                 | ``balderhub-appium`` or ``balderhub-playwright``   |
+-----------------------------------------------------------------+----------------------------------------------------+
| ``balderhub-selenium`` (COMING SOON)                            | package to control browsers with                   |
|                                                                 | `selenium <https://www.selenium.dev/>`_            |
|                                                                 |                                                    |
+-----------------------------------------------------------------+----------------------------------------------------+
| ``balderhub-playwright`` (COMING SOON)                          | package to control browsers with                   |
|                                                                 | `playwright <https://playwright.dev/>`_            |
|                                                                 |                                                    |
+-----------------------------------------------------------------+----------------------------------------------------+
| ``balderhub-appium`` (COMING SOON)                              | package to control browsers or android/ios apps    |
|                                                                 | with `Appium <https://appium.io/>`_                |
|                                                                 |                                                    |
+-----------------------------------------------------------------+----------------------------------------------------+
| ``balderhub-textual`` (COMING SOON)                             | package for testing textual applications           |
|                                                                 | (see Textual                                       |
|                                                                 | `Documentation <https://textual.textualize.io/>`_) |
+-----------------------------------------------------------------+----------------------------------------------------+

.. note::
   Please note, this package is still under development. If you would like to contribute, take a look into the
   `GitHub project <https://github.com/balder-dev/balderhub-guicontrol>`_.


.. toctree::
   :maxdepth: 2

   installation.rst
   topic_intro.rst
   scenarios.rst
   features.rst
   examples.rst
   utilities.rst
