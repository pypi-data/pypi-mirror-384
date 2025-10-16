import os
import setuptools

requirement_file = "requirements.txt"
reqs = [open(requirement_file).read().strip().split("\n")] if os.path.exists(requirement_file) else []

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setuptools.setup(
    name="fsspec-dnanexus",
    version="0.2.7",
    license="MIT",
    maintainer="DNAnexus-xVantage",
    maintainer_email="tphan@dnanexus.com",
    description="fsspec backend for the DNAnexus platform",
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=reqs,
    include_package_data=True,
    packages=setuptools.find_packages(),
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires='>=3.7',
    entry_points={
        'fsspec.specs': [
            'dnanexus=fsspec_dnanexus.DXFileSystem',
        ],
    },
)
