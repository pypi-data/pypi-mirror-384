import os

import setuptools

version_id = os.getenv("BUILD_BUILDNUMBER", "0.0.1")

setuptools.setup(
    version=version_id,
    packages=setuptools.find_namespace_packages(),
    include_package_data=True,
    zip_safe=False,
)
