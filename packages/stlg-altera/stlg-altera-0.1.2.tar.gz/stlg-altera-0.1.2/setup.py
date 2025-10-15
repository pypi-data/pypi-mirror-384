from setuptools import setup, find_packages

setup(
    name="stlg-altera",
    version="0.1.2",
    author="Sai Kiran Gundeti",
    author_email="sai.kiran.gundeti@altera.com",
    description="Sample Test List Generator for SPeTCDB",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        # List your dependencies here
        "requests","pandas"
    ],
    license="MIT",  # Or your chosen license
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
