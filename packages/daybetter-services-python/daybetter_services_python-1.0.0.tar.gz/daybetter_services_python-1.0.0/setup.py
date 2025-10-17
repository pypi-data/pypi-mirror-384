from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="daybetter-services-python",
    version="1.0.0",
    author="THDayBetter",
    author_email="chenp2368@163.com",
    description="Python client for DayBetter devices and services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/THDayBetter/daybetter-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=["aiohttp>=3.8.0"],
    keywords="daybetter, iot, home automation, mqtt",
    project_urls={
        "Bug Reports": "https://github.com/THDayBetter/daybetter-python/issues",
        "Source": "https://github.com/THDayBetter/daybetter-python",
    },
)
