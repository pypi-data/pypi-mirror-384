from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="flextree",
    version="0.1.7",
    author="Zhenning Zhao",
    author_email="znzhaopersonal@gmail.com",
    description="FlexTree - A flexible and intuitive Python library for creating and manipulating tree data structures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/znzhao/flextree",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Data Structures",
    ],
    python_requires=">=3.6",
    keywords="tree, data-structure, node, hierarchy, graph",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/pytree/issues",
        "Source": "https://github.com/yourusername/pytree",
        "Documentation": "https://github.com/yourusername/pytree#readme",
    },
)