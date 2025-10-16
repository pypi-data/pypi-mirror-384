from setuptools import setup, find_packages

setup(
    name="metepy",  # 包名（PyPI上需唯一）
    version="0.1.1",    # 版本号
    # description="A Collection of Objective Forecasting Algorithms in the Meteorological Field",
    packages=find_packages(),
    python_requires='==3.9',
    install_requires=[
        "numpy>=1.18.0",
        "pandas>=1.0.0",
        "meteva>=1.0.0"
    ]
)