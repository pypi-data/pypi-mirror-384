import setuptools
from pathlib import Path


#with open("README.md", "r",encoding="utf-8") as fh:
#    long_description = fh.read()

chemin = Path(__file__).parent
long_description = (chemin / "README.md").read_text()


setuptools.setup(
    name = 'cnaclib',
    version = '0.1.19',
    license='MIT',
    author= 'BENHAMADA Nadir',
    author_email='aistatendz@gmail.com',
    description='Simulateur RAC',
    packages=setuptools.find_packages(),
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=["certifi >=2023.5.7",
                    "charset-normalizer >=3.1.0",
                    "idna >=3.4",
                    "numpy >=1.24.3",
                    "pandas >=2.0.1",
                    "python-dateutil >=2.8.2",
                    "pytz >=2023.3",
                    "six >=1.16.0",
                    "tzdata >=2023.3",
                    "urllib3 >=2.0.2"],
    python_requires=">=3.12", 
    keywords=['cnac', 'tools'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)