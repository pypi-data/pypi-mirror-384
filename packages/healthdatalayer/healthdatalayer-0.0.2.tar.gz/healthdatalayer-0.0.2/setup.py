from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements=f.read().splitlines()

setup(
    name="healthdatalayer",
    version="0.0.2",
    include_package_data=True,
    python_requires='>=3.13',
    packages=find_packages(),
    setup_requires=['setuptools-git-versioning'],
    install_requires=requirements,
    author="Jesus Martinez",
    author_email="jesusmartinez@noosds.com",
    description="Health Datalayer to access data from different sources",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    version_config={
       "dirty_template": "{tag}",
    }
)
