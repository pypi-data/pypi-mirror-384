hqapi_client
============

Python client for HQAPI.com that allows you to interact with the HQAPI
service easily.  Get your API tokens at https://hqapi.com/


Features
--------
- Simple and intuitive Python interface
- Send screenshots and capture data
- Works with Python 3.8+

Installation
------------
You can install `hqapi-client` via pip:

.. code-block:: bash

    pip install hqapi-client

Usage
-----
Here is a basic example of how to use the client:

.. code-block:: python

    from hqapi_client import HQAPIClient

    client = HQAPIClient(api_key="YOUR_API_KEY")
    screenshot = client.capture_screenshot(url="https://example.com")
    print(screenshot)

Dependencies
------------
- `requests>=2.30.0`

License
-------
This project is licensed under the MIT License.

Contact
-------
Author: HQAPI

