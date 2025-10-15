from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

package_info = {}
with open("src/usdm4_m11/__info__.py") as fp:
    exec(fp.read(), package_info)

setup(
    name="usdm4_m11",
    version=package_info["__package_version__"],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "usdm4>=0.11.0",
        "raw_docx>=0.10.0",
    ],
    package_data={
        "usdm4_m11": [
            "data/specification/sections.yaml",
            "data/specification/templates/title_page_template.html",
            "data/specification/elements/title_page_elements.yaml",
            "data/mapping/title_page_mapping.yaml",
        ]
    },
    author="D Iberson-Hurst",
    author_email="",
    description="A package for processing M11 protocol documents and converting them to USDM format",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    tests_require=[
        "anyio",
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "python-dotenv",
        "ruff",
    ],
    python_requires=">=3.12",
)
