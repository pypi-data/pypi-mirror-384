from setuptools import setup, find_packages

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setup(
    name="tefasfon",
    version="0.3.0",
    packages=find_packages(),
    author="Uraz Akgül",
    author_email="urazdev@gmail.com",
    description="Fetches fund data from the TEFAS website.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/urazakgul/tefasfon",
    license="MIT",
    install_requires=[
        "requests",
        "pandas",
        "openpyxl",
        "selenium",
        "rich",
        "lxml",
        "webdriver-manager",
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires=">=3.8",
)