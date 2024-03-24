from setuptools import find_packages, setup


setup(
    name="ksdb_parse",
    version="0.0.9",
    description="",
    package_dir={"": "app"},
    packages=find_packages(where="app"),
    long_description="KSDB Parse",
    long_description_content_type="text/markdown",
    url="",
    author="VISHAL AGHERA",
    author_email="",
    license="ACTOWIZ",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    install_requires=["scrapy >= 2.11.0", ],
    extras_require={
        "dev": ["twine>=4.0.2"],
    },
    python_requires=">=3.10",
)
