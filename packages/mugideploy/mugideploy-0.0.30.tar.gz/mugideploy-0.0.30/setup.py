import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mugideploy",
    version="0.0.30",
    author="Doronin Stanislav",
    author_email="mugisbrows@gmail.com",
    url='https://github.com/mugiseyebrows/mugideploy',
    description="C++ deploy utility",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires = ['pefile', 'colorama', 'treelib'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        'console_scripts': [
            'mugideploy = mugideploy:main'
        ]
    },
    python_requires='>=3.5'
)
