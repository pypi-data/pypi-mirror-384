from pathlib import Path
from setuptools import setup, find_packages


def parse_requirements(filename):
    """Parse requirements file and return list of dependencies."""
    req_file = Path(filename)
    if not req_file.exists():
        print(f"Warning: {filename} not found")
        return []

    requirements = []
    for line in req_file.read_text().splitlines():
        line = line.strip()
        # Skip empty lines and comments
        if line and not line.startswith('#'):
            requirements.append(line)

    print(f"Found {len(requirements)} requirements in {filename}")
    return requirements


setup(
    name="pymdt2json",
    version="0.5.0",
    description="Convert markdown tables into JSON code blocks",
    author="Amadou Wolfgang Cisse",
    author_email="amadou.6e@googlemail.com",
    readme="README.md",
    url="https://github.com/amadou-6e/pymdt2json.git",  # change this
    packages=find_packages(),  # looks in current dir
    entry_points={
        "console_scripts": ["pymdt2json=pymdt2json:main",],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=parse_requirements("requirements.txt"),
    python_requires=">=3.7",
    include_package_data=True,
)
