from setuptools import setup, find_packages

setup(
    name="som-abb",
    version="0.1.0",  # Adjust version as needed
    author="ABDOL",
    author_email="abdoldevtra@example.com",
    description="A Somali abbreviation replacement library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/abdoltd/somali_abbreviation",
    packages=find_packages(),
    package_data={
        'somali_abbreviation': ["data/abbreviation_dict.json"],  # Specify the dataset file
    },
    include_package_data=True,  # Ensure package data is included
    # classifiers=[
    #     "Programming Language :: Python :: 3",
    #     "License :: OSI Approved :: MIT License",
    #     "Operating System :: OS Independent",
    # ],
    # python_requires=">=3.6",
)
