import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "temp_wapi",
    version = "0.0.2",
    author = "Alireza Alizadeh",
    author_email = "alirezaalizadeh3690@gmail.com",
    description = "Fetches current temperature for given latitude and longitude",
    long_description = "A simple client API module to get current temperature from service providers",
    long_description_content_type = "text/markdown",
    url = "https://github.com/Alireza123480/temp_wapi",
    project_urls = {
        "Author": "https://jobinja.ir/user/HW-3398111",
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires = [
        "requests"
    ],
    package_dir = {"": "src"},
    packages = setuptools.find_packages(where="src"),
    python_requires = ">=3.6"
)