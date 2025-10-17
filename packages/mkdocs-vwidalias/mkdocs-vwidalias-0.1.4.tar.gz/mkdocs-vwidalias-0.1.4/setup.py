from setuptools import setup, find_packages
import io, os

HERE = os.path.abspath(os.path.dirname(__file__))

def readme():
    with io.open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
        return f.read()

setup(
    name="mkdocs-vwidalias",
    version="0.1.4",  # bump
    description="MkDocs plugin to create /<ID>/ redirects from front-matter IDs",
    long_description=readme(),
    long_description_content_type="text/markdown",
    author="Gobidesert",
    author_email="gobidesert.mf@gmail.com",
    url="https://github.com/yourname/mkdocs-vwidalias",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["mkdocs>=1.4"],
    python_requires=">=3.8",
    entry_points={
        "mkdocs.plugins": [
            # Users will enable as `vwidalias` in mkdocs.yml
            "vwidalias = mkdocs_vwidalias.plugin:VwidAliasPlugin",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: MkDocs",
        "Topic :: Documentation",
        "Operating System :: OS Independent",
    ],
)
