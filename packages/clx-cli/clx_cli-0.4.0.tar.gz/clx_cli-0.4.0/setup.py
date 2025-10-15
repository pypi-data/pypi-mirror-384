from setuptools import setup, find_packages

setup(
    name="clx-cli",
    version="0.4.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "pyperclip",
        "openai",
        "python-dotenv"
    ],
    entry_points={
        "console_scripts": [
            "clx = clx.__main__:main",
        ],
    },
)
