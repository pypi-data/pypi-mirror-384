from setuptools import setup, find_packages
import pathlib

this_dir = pathlib.Path(__file__).parent
long_description = (this_dir / "README.md").read_text(encoding="utf-8") if (this_dir / "README.md").exists() else ""

setup(
    name="python-htmlinfo",
    version="0.1.6",
    author="ATRCORE-UA",
    author_email="mail@atrcore.pp.ua",
    description="Beautiful HTML version of phpinfo(), but for Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/python-htmlinfo/",
    project_urls={
        "Source": "https://github.com/ATRCORE-UA/python-htmlinfo",
    },
    packages=find_packages(),
    include_package_data=True,
    install_requires=["setuptools"],
    python_requires=">=3.6",
    license="MIT",
    keywords=["python", "info", "phpinfo", "html", "system", "environment"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "pyinfo=python_htmlinfo:pyinfo",
        ],
    },
)
