import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# DO NOT EDIT THIS NUMBER!
# IT IS AUTOMATICALLY CHANGED BY python-semantic-release
__version__ = "1.27.0"

setuptools.setup(
    name="angmom_suite",
    version=__version__,
    author="Chilton Group",
    author_email="nicholas.chilton@manchester.ac.uk",
    description="A package for working with phenomenological spin and angular momentum operators", # noqa
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/chilton-group/angmom_suite",
    project_urls={
        "Bug Tracker": "https://gitlab.com/chilton-group/angmom_suite/issues",
        "Documentation": "https://chilton-group.gitlab.io/angmom_suite"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    package_dir={"":"."},
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'angmom_suite = angmom_suite.cli:main'
            ]
        },
    python_requires=">=3.6",
    install_requires=["numpy", "scipy", "sympy<=1.12", "matplotlib", "h5py",
                      "hpc_suite>=1.8.0", "jax>=0.4.25", "jaxlib>=0.4.25",
                      "optax", "molcas_suite>=1.34.2", "pandas"]
)
