from setuptools import setup, find_packages

setup(
    name="metepy",  # 包名（PyPI上需唯一）
    version="0.1.3",    # 版本号
    packages=find_packages(), # 必须的
    package_data={
        'metepy': ['*.pyd', 'data/*.txt']  # 包含所有.pyd文件和data目录下的所有.txt文件
    },
    include_package_data=True,
    python_requires=">=3.9, <3.10",
    install_requires=[
        "numpy>=1.18.0",
        "pandas>=1.0.0",
        "meteva>=1.0.0"
    ]
)