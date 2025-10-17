from setuptools import setup, find_packages

setup(
    name="yoyogram",
    version="0.0.8",
    description="The framework to ease the work with huge projects with aiogram",
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    author="dhmmmhb",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "yoyo = _yoyo_cli.cli:main"
        ]
    },
    install_requires=[
        "aiogram",
        "redis",
        "environs",
        "aiosqlite",
        "APScheduler",
        "rich"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.7",
)