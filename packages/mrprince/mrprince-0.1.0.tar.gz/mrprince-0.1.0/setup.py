from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
if os.path.exists(readme_path):
    with open(readme_path, "r", encoding="utf-8") as fh:
        long_description = fh.read()
else:
    long_description = "A PySpark code snippets library"

setup(
    name="mrprince",
    version="0.1.0",
    author="Your Name",  # Replace with your name
    author_email="your.email@example.com",  # Replace with your email
    description="A PySpark code snippets library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mrprince",  # Replace with your repo URL
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pyspark>=3.0.0",
    ],
    entry_points={
        'console_scripts': [
            'mrprince=mrprince.main:main',
        ],
    },
)
