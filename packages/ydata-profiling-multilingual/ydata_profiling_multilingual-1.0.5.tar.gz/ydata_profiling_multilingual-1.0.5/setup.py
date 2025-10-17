from pathlib import Path
from setuptools import setup, find_packages

# Read the contents of README file
source_root = Path(".")
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

try:
    version = (source_root / "VERSION").read_text().rstrip("\n")
except FileNotFoundError:
    version = "1.0.1"

with open(source_root / "src/ydata_profiling/version.py", "w") as version_file:
    version_file.write(f"__version__ = '{version}'")

setup(
    name="ydata-profiling-multilingual",
    version=version,
    author="Landon Zeng",
    author_email="landonzeng@example.com",
    description="forked from ydataai/ydata-profiling and modify the code to support international multilingual functionality",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/landonzeng/ydata-profiling-multilingual",
    project_urls={
        "Original Repository": "https://github.com/ydataai/ydata-profiling",
        "Bug Reports": "https://github.com/landonzeng/ydata-profiling-multilingual/issues",
        "Source": "https://github.com/landonzeng/ydata-profiling-multilingual",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Internationalization",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "ydata-profiling-translate=ydata_profiling.i18n.tools:cli",
        ],
    },
    package_data={
        "ydata_profiling": [
            "assets/fonts/*.ttf",
            "assets/fonts/*.md",
            "i18n/locales/*.json",
            "report/presentation/flavours/html/templates/**/*.html",
            "report/presentation/flavours/html/templates/**/*.css",
            "report/presentation/flavours/html/templates/**/*.js",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "pandas", "profiling", "data-science", "data-analysis",
        "internationalization", "i18n", "multilingual", "localization", "ydata-profiling-multilingual", "ydata-profiling-fork"
    ],
)