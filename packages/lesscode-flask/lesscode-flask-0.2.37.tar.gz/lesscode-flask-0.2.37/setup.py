# -*- coding: utf-8 -*-

from lesscode_flask import __version__

import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

with open("requirements.txt", "r") as requirements:
    install_requires = requirements.read()

setuptools.setup(
    name="lesscode-flask",
    version=__version__,
    author="Chao.yy",
    author_email="yuyc@ishangqi.com",
    description="lesscode-flask 是基于flask的web开发脚手架项目，该项目初衷为简化开发过程，让研发人员更加关注业务。",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://lesscode-flask",
    # packages=setuptools.find_packages(),
    package_dir={'lesscode_flask': 'lesscode_flask',
                 'redash': 'redash'},
    classifiers=[
            "Programming Language :: Python :: 3",
            # "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        python_requires='>=3.9',
        platforms='python',
        install_requires=install_requires.split("\n")

)
"""
        "aiopg>=1.3.3",
"""
"""
1、打包流程
打包过程中也可以多增加一些额外的操作，减少上传中的错误

# 先升级打包工具
pip install --upgrade setuptools wheel twine

# 打包
python setup.py sdist bdist_wheel

# 检查
twine check dist/*

# 上传pypi
twine upload dist/*
twine upload dist/* -u yuyc -p yu230225
twine upload dist/* --repository-url https://pypi.chanyeos.com/ -u admin -p shangqi
# 安装最新的版本测试
pip install -U lesscode-flask -i https://pypi.org/simple
pip install -U lesscode-flask -i https://pypi.chanyeos.com/simple
"""
