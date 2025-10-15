# ============================================
# setup.py
# ============================================
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dsf-aml-sdk",
    version="1.0.69",
    author="api-dsfuptech",
    author_email="contacto@softwarefinanzas.com.co",
    description="SDK for DSF Adaptive ML with Knowledge Distillation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jaimeajl/dsf-aml-sdk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=["requests>=2.25.0"],
    keywords="dsf aml ml machine-learning distillation adaptive sdk",
)