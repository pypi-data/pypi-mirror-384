from setuptools import setup, find_packages

setup(
    name='argumentari',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[],
    author="David Ikeda",
    author_email="dev.literalgargoyle@gmail.com",
    description="An API and toolkit for structured argument data, argument schemes, and visualization",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/literal-gargoyle/argumentari",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
    ],
)