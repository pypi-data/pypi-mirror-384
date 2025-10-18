from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="eizon-lib",  
    version="1.0.1",  
    author="Eizon",
    author_email="eizontool@gmail.com",  
    description="Python için gelişmiş matematik, string işlemleri ve veri analiz kütüphanesi. telegram: @besteizon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://t.me/eizonxTool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers", 
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6",
    keywords="mathematics, string operations, file operations, utilities, turkish",
)