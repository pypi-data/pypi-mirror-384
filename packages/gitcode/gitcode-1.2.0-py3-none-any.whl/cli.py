#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import click
import sys
from pathlib import Path
from getpass import getpass

# 设置OpenMind Hub的API端点为GitCode
os.environ["OPENMIND_HUB_ENDPOINT"] = "https://hub.gitcode.com"
# 设置缓存目录
cache_dir = os.path.expanduser("~/.cache/gitcode")
os.makedirs(cache_dir, exist_ok=True)
os.environ["HF_HOME"] = cache_dir

try:
    from .config import config
    from .api import api
    from .utils import (
        print_success, print_error, print_warning, print_info,
        validate_repo_name, validate_repo_type, get_directory_size,
        format_file_size, count_files_in_directory, confirm_action,
        is_valid_path, ensure_directory, setup_git_credentials, 
        clear_git_credentials, check_git_available
    )
except ImportError:
    from config import config
    from api import api
    from utils import (
        print_success, print_error, print_warning, print_info,
        validate_repo_name, validate_repo_type, get_directory_size,
        format_file_size, count_files_in_directory, confirm_action,
        is_valid_path, ensure_directory, setup_git_credentials,
        clear_git_credentials, check_git_available
    )


@click.group()
@click.version_option(version='1.1.1')
def cli():
    """GitCode CLI - 基于OpenMind SDK的GitCode平台模型文件上传下载工具"""
    pass


@cli.command()
@click.option('--token', '-t', help='OpenMind访问令牌')
def login(token):
    """登录到GitCode平台"""
    if not token:
        token = getpass('请输入访问令牌: ')
    
    if not token:
        print_error("令牌不能为空")
        sys.exit(1)
    
    print_info("正在验证登录信息...")
    
    if api.login(token):
        print_success(f"登录成功！")
        
        # 配置Git凭证助手
        if check_git_available():
            if setup_git_credentials(token):
                print_info("✨ Git凭证已配置，现在可以直接使用git命令访问GitCode仓库")
            else:
                print_warning("Git凭证配置失败，请手动配置或使用完整URL")
        else:
            print_warning("未检测到Git，跳过Git凭证配置")
    else:
        print_error("登录失败，请检查令牌是否正确")
        sys.exit(1)


@cli.command()
def logout():
    """退出登录"""
    if config.is_logged_in():
        config.clear_credentials()
        
        # 清除Git凭证配置
        if check_git_available():
            clear_git_credentials()
        
        print_success("已退出登录")
    else:
        print_info("当前未登录")


# @cli.command()
# def whoami():
#     """显示当前登录状态"""
#     if config.is_logged_in():
#         print_info("当前已登录")
#     else:
#         print_warning("当前未登录，请先运行 'gitcode login'")


@cli.group()
def repo():
    """仓库管理命令"""
    pass


# @repo.command()
# @click.argument('repo_name')
# @click.option('--type', 'repo_type', type=click.Choice(['model', 'dataset']), 
#               required=True, help='仓库类型 (model/dataset)')
# @click.option('--description', '-d', default='', help='仓库描述')
# @click.option('--private', is_flag=True, help='创建私有仓库')
# def create(repo_name, repo_type, description, private):
#     """创建新仓库"""
#     if not config.is_logged_in():
#         print_error("请先登录：gitcode_cli login")
#         sys.exit(1)
    
#     if not validate_repo_name(repo_name):
#         print_error("仓库名称格式不正确，应为: username/repo-name")
#         sys.exit(1)
    
#     print_info(f"正在创建{repo_type}仓库: {repo_name}")
    
#     if api.create_repo(repo_name, repo_type, description, private):
#         print_success(f"仓库 {repo_name} 创建成功")
#     else:
#         print_error(f"仓库 {repo_name} 创建失败")
#         sys.exit(1)


# @repo.command()
# @click.argument('repo_id')
# def info(repo_id):
#     """显示仓库信息"""
#     if not config.is_logged_in():
#         print_error("请先登录：gitcode_cli login")
#         sys.exit(1)
    
#     if not validate_repo_name(repo_id):
#         print_error("仓库ID格式不正确，应为: username/repo-name")
#         sys.exit(1)
    
#     repo_info = api.get_repo_info(repo_id)
#     if repo_info:
#         print_info(f"仓库名称: {repo_info.get('name', '未知')}")
#         print_info(f"仓库类型: {repo_info.get('type', '未知')}")
#         print_info(f"描述: {repo_info.get('description', '无')}")
#         print_info(f"是否私有: {'是' if repo_info.get('private', False) else '否'}")
#         print_info(f"创建时间: {repo_info.get('created_at', '未知')}")
#     else:
#         print_error(f"无法获取仓库 {repo_id} 的信息")
#         sys.exit(1)


@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--repo-id', required=True, help='目标仓库ID (username/repo-name)')
@click.option('--message', '-m', default='', help='上传说明')
def upload(path, repo_id, message):
    """上传文件或目录到仓库"""
    if not config.is_logged_in():
        print_error("请先登录：gitcode login")
        sys.exit(1)
    
    if not validate_repo_name(repo_id):
        print_error("仓库ID格式不正确，应为: username/repo-name")
        sys.exit(1)
    
    path = Path(path)
    if not path.exists():
        print_error(f"路径不存在: {path}")
        sys.exit(1)
    
    if path.is_file():
        print_info(f"正在上传文件: {path}")
        file_size = format_file_size(path.stat().st_size)
        print_info(f"文件大小: {file_size}")
        
        if api.upload_file(path, repo_id, message=message):
            print_success(f"文件上传成功: {path.name}")
        else:
            print_error(f"文件上传失败: {path.name}")
            sys.exit(1)
    
    elif path.is_dir():
        file_count = count_files_in_directory(path)
        dir_size = format_file_size(get_directory_size(path))
        
        print_info(f"正在上传目录: {path}")
        print_info(f"文件数量: {file_count}")
        print_info(f"目录大小: {dir_size}")
        
        # if file_count > 10:
        #     if not confirm_action(f"即将上传 {file_count} 个文件，是否继续？"):
        #         print_info("取消上传")
        #         return
        
        if api.upload_directory(path, repo_id, message=message):
            print_success(f"目录上传成功: {path}")
        else:
            print_error(f"目录上传失败: {path}")
            sys.exit(1)
    
    else:
        print_error(f"不支持的路径类型: {path}")
        sys.exit(1)


@cli.command()
@click.argument('repo_id')
@click.option('--directory', '-d', type=click.Path(), 
              help='下载到指定目录')
@click.option('--force', is_flag=True, help='强制覆盖已存在的文件')
def download(repo_id, directory, force):
    """下载仓库到本地（公开仓库无需登录）"""
    if not validate_repo_name(repo_id):
        print_error("仓库ID格式不正确，应为: username/repo-name")
        sys.exit(1)
    
    # 确定下载目录
    if directory:
        local_path = Path(directory)
        if not is_valid_path(directory):
            print_error(f"无效的目录路径: {directory}")
            sys.exit(1)
    else:
        local_path = Path.cwd() / repo_id.split('/')[-1]
    
    # 检查目录是否存在
    if local_path.exists():
        if local_path.is_file():
            print_error(f"目标路径是文件，不是目录: {local_path}")
            sys.exit(1)
        elif local_path.is_dir() and any(local_path.iterdir()):
            if force:
                print_info("强制覆盖模式，将重新下载所有文件")
            else:
                print_info("目录已存在，启用断点续传模式")
    
    # 确保目录存在
    if not ensure_directory(local_path):
        print_error(f"无法创建目录: {local_path}")
        sys.exit(1)
    
    print_info(f"正在下载仓库: {repo_id}")
    print_info(f"下载到: {local_path}")
    
    # 如果未登录，提示用户这是公开仓库下载模式
    if not config.is_logged_in():
        print_info("当前未登录，尝试下载公开仓库...")
    
    if api.download_repo(repo_id, local_path, force_download=force):
        print_success(f"仓库下载成功: {local_path}")
    else:
        print_error(f"仓库下载失败: {repo_id}")
        if not config.is_logged_in():
            print_info("提示：如果这是私有仓库，请先使用 'gitcode login' 登录")
        sys.exit(1)


@cli.command()
def config_show():
    """显示配置信息"""
    if config.is_logged_in():
        credentials = config.get_credentials()
        print_info(f"登录状态: 已登录")
        print_info(f"配置文件: {config.config_file}")
        
        # 简单检查Git集成状态
        if check_git_available():
            try:
                import subprocess
                # 检查任一域名的凭证助手配置
                result1 = subprocess.run(['git', 'config', '--global', '--get', 'credential.https://gitcode.com.helper'], 
                                       capture_output=True, text=True)
                result2 = subprocess.run(['git', 'config', '--global', '--get', 'credential.https://hub.gitcode.com.helper'], 
                                       capture_output=True, text=True)
                
                if ((result1.returncode == 0 and 'git-credential-gitcode' in result1.stdout) or 
                    (result2.returncode == 0 and 'git-credential-gitcode' in result2.stdout)):
                    print_info("Git集成: 已启用")
                else:
                    print_info("Git集成: 未启用")
            except Exception:
                print_info("Git集成: 检查失败")
    else:
        print_warning("当前未登录")
        print_info(f"配置文件: {config.config_file}")



if __name__ == '__main__':
    cli() 