from setuptools import setup, find_packages

setup(
    name="mkdocs-vwidref",
    version="1.0.15",
    description="MkDocs plugin to link by front-matter ID with status/progress/title flags ([[id:s|p|t:...]]).",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "mkdocs>=1.4",
        "PyYAML>=6.0",
    ],
    entry_points={
        "mkdocs.plugins": [
            "vwidref = mkdocs_vwidref.plugin:IdRefPlugin",
        ],
    },
    classifiers=[
        "Framework :: MkDocs",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="mkdocs plugin wiki interwiki frontmatter idref",
)
