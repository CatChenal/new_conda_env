from setuptools import setup, find_packages

with open("README.md") as rm_file:
    readme = rm_file.read()

# get the dependencies and installs
with open("requirements.txt") as f:
    all_reqs = f.read().splitlines()

install_requires = [x.strip() for x in all_reqs]

setup(
    name="new_conda_env",
    keywords="conda env tool",
    url="https://github.com/CatChenal/new_conda_env",
    version="0.1.0",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    description="A Python package for generating a 'lean' environment yaml file (see README).",
    long_description=readme,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    include_package_data=True,
    license="MIT license",
    packages=find_packages(include=["new_conda_env", "new_conda_env.*"]),
    test_suite="tests",
    tests_require=["pytest"],
    entry_points={"console_scripts": ["new-conda-env = new_conda_env.cli:main"]},
    author="Cat Chenal",
    author_email="catchenal@gmail.com",
)
