Utilities
*********

This section shows general objects and helper functions that are used with this package.

Driver
======

.. autoclass:: balderhub.webdriver.lib.utils.driver.BaseWebdriverDriverClass
    :members:

WebElement Bridges
==================

The bindings between the original web browser automation tool (like selenium) and the
`balderhub-guicontrol <https://hub.balder.dev/projects/guicontrol>`_ are provided within the bridge classes. This BalderHub
project provides abstract bridge classes that supports the WebDriver protocol.

.. autoclass:: balderhub.webdriver.lib.utils.web_element_bridges.BaseWebdriverElementBridge
    :members:

.. autoclass:: balderhub.webdriver.lib.utils.web_element_bridges.FullyReidentifiableElementBridge
    :members:

.. autoclass:: balderhub.webdriver.lib.utils.web_element_bridges.NotReidentifiableElementBridge
    :members:

.. autoclass:: balderhub.webdriver.lib.utils.web_element_bridges.PartlyReidentifiableElementBridge
    :members:
