import setuptools

with open("README.md", "r",encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="QUBIT_Driver",
    version="1.0",
    author="He Guo Yang",
    author_email="2060817247@qq.com",
    description="Drive adapted for the quantum control system of the Beijing Quantum Institute",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    install_requires=[ 'numpy==1.14.4'],
    entry_points={
        'console_scripts': [
            'douyin_image=douyin_image:main'
        ],
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)