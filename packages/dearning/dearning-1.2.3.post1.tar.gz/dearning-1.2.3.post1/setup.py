from setuptools import setup, find_packages

setup(
    name="dearning",
    version="1.2.3.post1",
    description="Libraries untuk membuat AI yang ringan",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Oriza",
    project_urls={
        "Homepage": "https://github.com/maker-games",
        "Chatting": "https://github.com/maker-games/tempat-komentar",
    },
    license="Apache-2.0",
    python_requires=">=3.9",
    packages=find_packages(include=["dearning", "dearning.*"]),
    package_data={
        "dearning": ["*.txt", "*.json", "*.md", "*.pdf"],
        "Memory": ["*.json", "*.txt", "*.dat"]
    },
    include_package_data=True,
    install_requires=[],
    entry_points={
        "console_scripts": [
            "dearning = dearning.__main__:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent"
    ]
)