from setuptools import setup, find_packages

setup(
    name="bus_202",
    version="1.18",
    packages=find_packages(),
    package_data={
        'bus_202': ['data/*.xlsx']},
    install_requires=[
        'pandas>=1.0.0',
        'openpyxl>=3.0.0',
        'numpy>=1.20.0',
        'matplotlib>=3.0.0',
        'scipy>=1.6.0',
        'seaborn>=0.12.0',
        'statsmodels>=0.14.0'],
    python_requires='>=3.7',
    author="Justin G. Davis",
    author_email="",
    description="BUS 202, Fundamentals of Business Analytics",
    keywords="business, data, analysis, education")
