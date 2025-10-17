import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="poresim",
    version="0.3.0",
    author="Hamzeh Kraus",
    author_email="kraus@itt.uni-stuttgart.de",
    description="Pore system simulation generator.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PoreMS/PoreSim",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=['numpy','pyyaml', 'jinja2==3.0.3'],
    include_package_data=True,
)
