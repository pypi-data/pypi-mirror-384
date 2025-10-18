from setuptools import setup, find_packages

# Read the contents of your README file
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="django-smart-storages",
    version="0.1.0",
    description="Simplified S3 storage backends for Django projects with intelligent bucket and region selection.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/awais786/django-smart-storages",
    author="Awais Qureshi",
    author_email="awais786@hotmail.com",
    license="MIT",  # Assuming MIT License

    # Define the required Python version
    python_requires=">=3.8",

    # Use standard find_packages
    packages=find_packages(exclude=["tests", "tests.*"]),

    install_requires=[
        "Django>=4.2",  # Explicit minimum Django version
        "django-storages>=1.14.3",
        "boto3>=1.28.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",  # Suggesting 'Beta' as it's a new package
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.2",  # Explicitly name tested Django versions
        "Framework :: Django :: 5.2",  # Explicitly name tested Django versions
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)