from setuptools import setup, find_packages

# Lendo o README.md para o PyPI
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="calculator-lib-by-magalhaes",  # ⚡ Nome com hífen para o PyPI
    version="0.1.0",
    description="Biblioteca de operações matemáticas básicas em Python do Piani",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Israel Magalhães",
    author_email="israelmcarmo@gmail.com",
    url="",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)