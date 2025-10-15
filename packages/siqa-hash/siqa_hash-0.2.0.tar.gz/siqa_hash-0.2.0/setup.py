from setuptools import setup, find_packages

with open("README.md","r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="siqa_hash",          # consistent with Python package name
    version="0.2.0",
    author="Mohana Priya Thinesh Kumar",
    author_email="manthramohana1@gmail.com",
    description="Quantum hash function built using Qiskit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MohanaPriyaThineshKumar/SIQA_Hash",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "qiskit>=1.0.0",
        "qiskit-aer",
        "numpy"
    ],
    license="MIT",
    entry_points={
        "console_scripts": [
            "siqa-hash=siqa_hash.siqa_hashcode:main"
        ]
    }
)

