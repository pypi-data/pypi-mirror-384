import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pypx800v5",
    version="1.4.3",
    author="Aohzan",
    author_email="aohzan@gmail.com",
    description="Control the IPX800V5 and its extensions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aohzan/pypx800v5",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
