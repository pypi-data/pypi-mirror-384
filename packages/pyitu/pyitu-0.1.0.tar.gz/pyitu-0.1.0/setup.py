import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "pyitu",
    version = "0.1.0",
    author = "Richard Tjörnhammar",
    author_email = "richard.tjornhammar@gmail.com",
    description = "A collection of ITU based propagation models",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/richardtjornhammar/pyitu",
    packages = setuptools.find_packages('src'),
    package_dir = {'pyitu':'src/pyitu','tooling':'src/tooling','p838':'src/p838','p676':'src/p676'},
    classifiers = [
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
