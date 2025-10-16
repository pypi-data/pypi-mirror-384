# Welcome to SportsX SDK Documentation

# Overview

The STX SDK is a wrapper around the Sportsx Graphql APIs and Phoenix channels.
The SDK provides object-oriented APIs to connect with the available Sportsx APIs and socket channels.
The SDK is built on the following libraries:
 - GQL: https://github.com/graphql-python/gql
 - Websockets: https://github.com/aaugustin/websockets

## Compatibility

This library is compatible with the following versions of Python:

 - 3.7
 - 3.8
 - 3.9

# Developer Guide:

Detailed developer guide and demo scripts are available on this [link](https://github.com/stxapp/pysdk-demo)

There are two services available **StxClient** and **StxChannelClient**

 - **StxClient** provides sync operations, while
 - **StxChannelClient** provides connectivity with websocket channels.

## Steps to build python package and upload to PyPI

Some commands require a newer version of pip, so start by making sure you have the latest version installed:

 - For Linux/Mac:

    ```python3 -m pip install --upgrade pip```
 - For Windows:

    ```py -m pip install --upgrade pip```

 ### Setting up build package version

Open `pyproject.toml` file and update the `version` field with the new version name.

 ### Generating distribution archives (built package)

The next step is to generate distribution packages for the package.
These are archives that are uploaded to the Python Package Index and can be installed by pip.

Make sure you have the latest version of PyPA’s build installed:

 - For Linux/Mac:

    ```python3 -m pip install --upgrade build```
 - For Windows:

    ```py -m pip install --upgrade build```

Now run the following command from the root directory where pyproject.toml is located:

 - For Linux/Mac:

    ```python3 -m build```
 - For Windows:

    ```py -m build```

This command should output a lot of text listing all the packaged files and once completed
should generate two files in the dist directory:

    dist/
        ├── stx_pysdk-VERSION_NUMBER-py3-none-any.whl
        └── stx-pysdk-VERSION_NUMBER.tar.gz

The `tar.gz` file is a source distribution whereas the `.whl` file is a built distribution.
Newer pip versions preferentially install built distributions, but will fall back to source distributions if needed.

### Uploading the distribution archives (built package)

Finally, it’s time to upload your package to the Python Package Index!

You’ll need to install Twine if not already installed, reinstalling it makes sure you have the latest version
Twine is used to upload the distribution packages.

 - For Linux/Mac:

    ```python3 -m pip install --upgrade twine```
 - For Windows:

    ```py -m pip install --upgrade twine```

Once installed, run Twine to upload all the archives under dist:

 - For Linux/Mac:

    ```python3 -m twine upload --repository pypi dist/*```
 - For Windows:

    ```py -m twine upload --repository pypi dist/*```

You will be prompted for a username and password.

After the command completes, you should see output similar to this:

    Uploading distributions to https://pypi.org/legacy/
    Enter your username: <USERNAME>
    Enter your password: <PASSWORD>
    Uploading stx_pysdk-VERSION_NUMBER-py3-none-any.whl
    100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 8.2/8.2 kB • 00:01 • ?
    Uploading stx-pysdk-VERSION_NUMBER.tar.gz
    100% ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.8/6.8 kB • 00:00 • ?

Once uploaded, your package should be viewable on PyPI; https://pypi.org/project/stx-pysdk/
