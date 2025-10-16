from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="chef-bomber",
    version="1.0.0",
    author="Chef Bomber",
    author_email="your-email@example.com",
    description="A professional cooking-themed number utility tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["cook"],
    install_requires=[
        "requests>=2.25.1",
    ],
    entry_points={
        'console_scripts': [
            'cook=cook:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
