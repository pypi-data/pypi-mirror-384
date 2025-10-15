from setuptools import setup, find_packages
import pathlib

# Довгий опис із README.md, якщо він є
this_dir = pathlib.Path(__file__).parent
long_description = (this_dir / "README.md").read_text(encoding="utf-8") if (this_dir / "README.md").exists() else ""

setup(
    name="python_htmlinfo",
    version="0.1.5",
    author="ATRCORE-UA",
    author_email="mail@atrcore.pp.ua",  # заміни на свою пошту
    description="HTML version of Python info, like phpinfo() but for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://pypi.org/project/python-htmlinfo/",
    project_urls={
        "Source": "https://github.com/ATRCORE-UA/python-htmlinfo",  # можеш додати GitHub посилання
    },
    packages=find_packages(),
    python_requires=">=3.6",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
