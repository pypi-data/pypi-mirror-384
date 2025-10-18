from setuptools import setup, find_packages

setup(
    name="NitroExpose",
    version="1.3",
    author="@NacDevs",
    author_email="yuvrajmodz@gmail.com",
    description="Advanced CLI To Expose Port To Your Domain.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yuvrajmodz/NitroExpose",
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        "requests"
    ],
    entry_points={
        'console_scripts': [
            'NitroExpose=nitroexpose.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
)