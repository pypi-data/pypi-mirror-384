from setuptools import setup, find_packages

def get_description():
    try:
        with open("README.md", encoding="utf-8") as readme_file:
            long_description = readme_file.read()
        return long_description
    except:
        return None


setup(
    name="random_header_generator_compat",
    version='4.0.40',
    description="random_header_generator_compat is a fork of the requests library with the playwright dependencies removed.",
    long_description_content_type="text/markdown",
    long_description=get_description(),
    author="Chetan",
    author_email="53407137+Chetan11-dev@users.noreply.github.com",
    maintainer="Chetan",
    maintainer_email="53407137+Chetan11-dev@users.noreply.github.com",
    license="MIT",
    python_requires=">=3.5",
    keywords=[
        "tls", "client", "http", "scraping", "requests", "humans"
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    install_requires=[
    ],
    url="https://github.com/omkarcloud/botasaurus-requests",
    project_urls={
        "Homepage": "https://github.com/omkarcloud/botasaurus-requests",
        "Bug Reports": "https://github.com/omkarcloud/botasaurus-requests/issues",
        "Source": "https://github.com/omkarcloud/botasaurus-requests"
    },
    packages=find_packages(include=["random_header_generator_compat"]),
    include_package_data=True,
)
