.. BalderHub SNMPAgent documentation master file, created by
   sphinx-quickstart on Wed Feb 22 19:24:39 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

BalderHub-WebDriver
===================

The BalderHub WebDriver package for the `Balder <https://docs.balder.dev/>`_ test framework. It allows you to interact with
web browsers. This package is like a interface package for using different kinds of browser automation tools. If you are new to Balder check out the
`official documentation <https://docs.balder.dev>`_ first.

This BalderHub package implements the `balderhub-guicontrol <https://hub.balder.dev/projects/guicontrol>`_ interface and
provides are more detailed interface for all further guicontrol packages that supports the
`WebDriver2 protocol <https://www.w3.org/TR/webdriver2/>`_.

.. note::
    This package can be used for implementing a own guicontrol package. In most of the cases it is more recommend to use
    the final guicontrol implementation packages `balderhub-selenium <https://hub.balder.dev/projects/selenium>`_.

.. note::
   Please note, this package is still under development. If you would
   like to contribute, take a look into the `GitHub project <https://github.com/balder-dev/balderhub-webdriver>`_.


.. toctree::
   :maxdepth: 2

   installation.rst
   topic_intro.rst
   scenarios.rst
   features.rst
   examples.rst
   utilities.rst
