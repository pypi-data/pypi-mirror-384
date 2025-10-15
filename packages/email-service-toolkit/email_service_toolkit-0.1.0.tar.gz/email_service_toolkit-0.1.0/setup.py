from setuptools import setup, find_packages

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="email_service_toolkit",  # Package name
    version="0.1.0",               # Incremented version
    author="Vamsi Gudapati",
    author_email="vamsi7673916775@gmail.com",
    description="Reusable Python toolkit for sending emails and managing email templates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vamsichowdaryg/email_service_toolkit",
    packages=find_packages(),
    install_requires=[
        "aiohttp>=3.8.0",
        "fastapi>=0.102.0",
        "python-dotenv>=1.0.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
    ],
    license="MIT",
    include_package_data=True,
)
