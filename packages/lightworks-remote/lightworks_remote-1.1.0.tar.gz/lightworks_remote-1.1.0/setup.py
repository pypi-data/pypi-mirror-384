from setuptools import setup, find_packages

setup(
    name = "lightworks_remote",
    author = "Aegiq Ltd.",
    use_scm_version = True,
    description = "Remote job submission extension to lightworks.",
    license="Apache 2.0",
    packages = find_packages(where=".", exclude = ["tests"]),
    package_data={"lightworks_remote": ["py.typed"]},
    python_requires = ">=3.10",
    install_requires = [
        "lightworks>=2.3.0", 
        "requests>=2.32.3", 
        "pandas", 
        "multimethod>=1.11.2"
    ],
    entry_points={
        'console_scripts': [
            'lightworks_remote = lightworks_remote.__main__:main',
        ],
    },
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
    ]
)
