from setuptools import setup, find_packages

setup(
    name = "saas_common_lib_473815",
    version = "0.6",
    author = "Srinidhi Nagarajan",
    author_email = "Srinidhinsn@gmail.com",
    description = ("Packaging all common functionalities"),
    license = "BSD",
    keywords = "Saas application",
    url = "",
    packages=['database', 'models', 'utils', 'config', 'entity'],
    #packages = find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
    ],
)