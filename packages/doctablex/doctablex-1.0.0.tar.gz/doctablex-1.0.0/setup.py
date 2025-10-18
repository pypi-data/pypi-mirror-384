from setuptools import setup, find_packages

setup(
    name="doctablex",
    version="1.0.0",
    author="Faruq Afolabi",
    author_email="faruqafolabi@example.com",
    description="Extract and clean tables from Word (.docx) files with regex-based type detection.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/faruqAI/doctablex",
    packages=find_packages(),
    install_requires=[
        "python-docx>=0.8.11",
        "pandas>=2.0.0",
        "python-dateutil>=2.8.2",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Office/Business :: Financial :: Spreadsheet",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.8",
)