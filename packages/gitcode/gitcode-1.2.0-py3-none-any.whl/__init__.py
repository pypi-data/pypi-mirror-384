#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitCode CLI - 基于OpenMind的模型文件上传下载工具

这是一个命令行工具，用于与OpenMind平台交互，
支持模型和数据集的上传、下载等操作。
"""

__version__ = '1.1.3'
__author__ = 'GitCode CLI Team'
__description__ = 'GitCode模型文件上传下载CLI工具'

try:
    from .config import config
    from .api import api
    from .cli import cli
except ImportError:
    from config import config
    from api import api
    from cli import cli

__all__ = ['config', 'api', 'cli'] 