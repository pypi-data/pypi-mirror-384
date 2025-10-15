from setuptools import setup, find_packages

setup(
    name="jasonite",
    version="0.1.2",
    description="Jasonite: a tiny JSON-backed document store for Python",
    author="Gianni Amato",
    author_email="guelfoweb@gmail.com",
    url="https://github.com/guelfoweb/jasonite",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

