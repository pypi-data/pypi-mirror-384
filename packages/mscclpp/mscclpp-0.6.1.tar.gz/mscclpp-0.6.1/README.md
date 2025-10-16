# Webhook Package

This is a Python package that triggers a web request to a webhook when installed via pip.

## Installation

```bash
pip install webhook-package
```

Note: Installing this package will send a GET request to a predefined webhook URL.

## Usage

Once installed, you can import it:

```python
import webhook_package
```

But it's mainly for demonstration.

## Uploading to PyPI

1. Install twine: `pip install twine`
2. Build the package: `python setup.py sdist`
3. Upload: `twine upload dist/*`

Make sure to replace the webhook URL in `setup.py` with your actual webhook URL.

Also, update the author, email, and other details in `setup.py`.