from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="taypi-create",
    version="0.20.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "taypi-create=taypiproject.cli:main",
        ],
    },
    install_requires=[
        "inflection",
        "ruamel.yaml",
        "Jinja2",
    ],
    description="FastAPI and PostGreSQL.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Juan David Corrales Saldarriaga",
    author_email="sistemas@taypi.com",
    license="Proprietary",
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
