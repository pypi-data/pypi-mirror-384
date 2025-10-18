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

    from hqapi.screenshot import ScreenshotClient

    # Set your token, get yours at https://hqapi.com/
    SCREENSHOT_API_TOKEN="--put--your--token--here--"

    client = ScreenshotClient(token=SCREENSHOT_API_TOKEN)
    image_data = client.create(url="https://hqapi.com/")

    # Save to disk
    with open("screenshot.png", "wb") as f:
        f.write(image_data)
    

Dependencies
------------
- `requests>=2.30.0`

License
-------
This project is licensed under the MIT License.

Contact
-------
Author: HQAPI

