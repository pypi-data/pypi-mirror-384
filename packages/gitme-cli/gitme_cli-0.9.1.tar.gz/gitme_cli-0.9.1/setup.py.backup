from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gitme-cli",
    version="0.4.3",
    author="Jing Wang",
    author_email="jingwang.physics@gmail.com",
    description="Git commit message generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wangjing0/gitme",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "anthropic>=0.57.1",
    ],
    entry_points={
        "console_scripts": [
            "gitme=gitme.cli:main",
        ],
    },
)