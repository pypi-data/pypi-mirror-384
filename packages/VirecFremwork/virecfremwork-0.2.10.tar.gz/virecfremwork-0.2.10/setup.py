from setuptools import setup, find_packages

setup(
    name="VirecFremwork",
    version="0.2.10",
    description="Validate our data",
    long_description=open("README.md", encoding="utf-8").read(),
    author="Sumit Zala",
    author_email="sumit.zala@xbyte.io",
    license="MIT",
    packages=find_packages(include=["Virec_publish", "Virec_publish.*"]),
    install_requires=[
        "requests",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,  # include files from MANIFEST.in
    zip_safe=False,
)
