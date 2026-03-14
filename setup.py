from setuptools import setup, find_packages

setup(
    name="leviathan-sandbox",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer",
        "rich",
        "pyyaml",
        "openai",
        "rembg",
        "opencv-python-headless",
        "pillow",
        "numpy",
        "requests",
        "pydantic"
    ],
    entry_points={
        "console_scripts": [
            "leviathan-sandbox=leviathan_sandbox.cli.main:app",
        ],
    },
    author="Leviathan Sandbox Contributors",
    description="An AI-Driven RTS Sandbox with Automated Asset Generation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="CC BY-NC 4.0",
)
