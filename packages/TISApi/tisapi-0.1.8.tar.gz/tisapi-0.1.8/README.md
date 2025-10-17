# TISApi

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version 0.1.8](https://img.shields.io/badge/version-0.1.8-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-orange)
![signed](https://img.shields.io/badge/signed-yes-green)

TISApi is a powerful Python package for controlling TIS devices. It provides a simple and intuitive API for interacting with TIS devices, making it easy to integrate TIS devices into your Python applications.

## Features

- ✅ Fully Supports Asynchronous Operations
- ✅ Flawless feedback mechanism to prevent data loss
- ✅ Debounce mechanism to prevent multiple commands from being sent for protection
- ✅ Easy to use API for controlling TIS devices
- ✅ Clean and simple codebase
- ✅ Ready to integrate with Home Assistant

## Installation

You can install TISApi by adding it to your Manifest file or by using pip. Here's how you can install it using pip:

```bash
pip install TISApi
```

## Verifying Package Signatures

This package is signed with GPG to ensure authenticity. Follow these steps to verify:

1. **Install GPG**: Ensure you have GPG installed (`gpg --version`).

2. **Get My Public Key**:
   - Import from a keyserver: `gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys E896735458D3FE00A6F593A712A4B1572AACB7CC`

3. **Download Files**: Get the `.tar.gz`, `.whl`, and `.asc` files from PyPI or GitHub Releases.

4. **Verify**:

   ```bash
   gpg --verify tisapi-0.1.0.tar.gz.asc tisapi-0.1.8.tar.gz
   gpg --verify tisapi-0.1.0-py3-none-any.whl.asc tisapi-0.1.8-py3-none-any.whl

## License

TISApi is licensed under the MIT license. See the [LICENSE](https://github.com/KarimTIS/TISApi/blob/main/LICENSE) file for details.


