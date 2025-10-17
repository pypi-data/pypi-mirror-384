from setuptools import setup, find_packages

setup(
    name="scs-kc",
    version="0.1.2",
    packages=find_packages(),
    include_package_data=True,  # include files specified in MANIFEST.in
    description="Package for Kerr-cat optimization with supercoefficients",
    python_requires=">=3.10",
    install_requires = [
    "numpy>=1.25",
    "sympy>=1.12",
    "scipy>=1.11",
    "swg",  # installed from Cloudsmith
    ]
)
