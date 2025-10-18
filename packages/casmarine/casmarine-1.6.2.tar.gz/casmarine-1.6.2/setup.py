import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="casmarine",
    version="1.6.2",
    author="Furkan Kırlangıç, Begüm İpek, Oğuzhan Furkan Ocak, Ahmet Enes Şimşek",
    author_email="enes.simsek@std.yildiz.edu.tr",
    description="Extendable communication library with support for various protocols for the use of CASMarine ROV team",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CASMarine/Communication",
    project_urls={
        "Bug Tracker": "https://github.com/CASMarine/Communication/issues",
        },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(exclude=['tests', 'test']),
    install_requires=["pyserial", "crccheck", "stm32loader", "requests", "packaging"],
    python_requires=">=3.8"
)
