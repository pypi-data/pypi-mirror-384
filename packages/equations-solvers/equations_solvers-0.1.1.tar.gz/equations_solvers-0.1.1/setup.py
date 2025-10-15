from setuptools import setup, find_packages

setup(
    name="Equations_Solvers",
    version="1.0.0",
    author="Hammail Riaz",
    author_email="hammailriaz.dev@gmail.com",
    description="A Python package for solving linear equations and performing 2x2 and 3x3 matrix operations including addition, subtraction, multiplication, determinant, adjoint, and inverse.",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hammailriaz/Equations_Solvers",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Mathematics",
    ],
    python_requires=">=3.7",
)
