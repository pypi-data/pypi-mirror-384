from setuptools import setup, find_packages

setup(
    name="catLang",
    version="0.0.8",
    packages=find_packages(),
    install_requires=[
        "regex>=1.0.0"  # your library depends on regex
    ],
    author="catLang",
    description="catLang: Custom transpiller from catLang code into Python code.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown", 
    classifiers=[
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License"
    ],
)
