#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "GitCode CLI - 基于OpenMind的模型文件上传下载工具"

# 读取依赖文件
def read_requirements():
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return [
            'click>=8.1.7',
            'requests>=2.31.0',
            'tqdm>=4.66.1',
            'pathlib>=1.0.1',
            'colorama>=0.4.6',
            'tabulate>=0.9.0'
        ]

setup(
    name='gitcode',
    version='1.2.0',
    author='GitCode CLI Team',
    author_email='sa@gitcode.com',
    description='GitCode模型文件上传下载CLI工具',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://gitcode.com/gitcode-ai/gitcode_cli',
    packages=['gitcode'],
    package_dir={'gitcode': '.'},
    py_modules=['gitcode_hub'],
    install_requires=read_requirements(),
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'gitcode=gitcode.cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Archiving',
        'Topic :: Utilities',
    ],
    keywords='openmind model dataset upload download cli',
    project_urls={
        'Bug Reports': 'https://gitcode.com/gitcode-ai/gitcode_cli/issues',
        'Source': 'https://gitcode.com/gitcode-ai/gitcode_cli',
    },
) 