#! /usr/bin/env python3
# -*- coding:utf-8 -*-
# @Time : 2023/11/14 14:03
# @Author : JY
"""
文件操作相关
有些文件中文会报错，可以尝试encoding=‘gbk’
"""

import os
import shutil
import hashlib
import inspect
import datetime


class fileHelper:
    ENCODING_UTF8 = 'utf-8'
    ENCODING_GBK = 'gbk'

    def __init__(self):
        pass

    @staticmethod
    def read(file_path, encoding=ENCODING_UTF8):
        """一次性读取txt文件的全部内容"""
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        return content

    @staticmethod
    def read_by_line(file_path, encoding=ENCODING_UTF8):
        """按行读取txt的内容,返回一个生成器对象，如果想要数组结果，可以使用list把结果转一下：list(file.readTxtFileByLine('x.txt'))"""
        with open(file_path, 'r', encoding=encoding) as f:
            # 按行读取内容
            line = f.readline()
            while line:
                # 去除换行符并处理每行内容
                line = line.strip()
                # 打印每行内容或进行其他操作
                yield line
                line = f.readline()

    @staticmethod
    def write_append(file_path, content, encoding=ENCODING_UTF8, newline="\n"):
        """以追加的形式写文件 文件不存在会自动创建"""
        with open(file_path, 'a', encoding=encoding, newline=newline) as f:
            f.write(content)

    @staticmethod
    def write_new(file_path, content, encoding=ENCODING_UTF8, newline="\n"):
        """清空文件后写入 文件不存在会自动创建"""
        with open(file_path, 'w', encoding=encoding, newline=newline) as f:
            f.write(content)

    @staticmethod
    def count_lines(file_path, encoding=ENCODING_UTF8):
        """得到文件的行数"""
        with open(file_path, 'r', encoding=encoding) as f:
            line_count = sum(1 for line in f)
        return line_count

    @staticmethod
    def rename(old_file, new_file, cover=True):
        """
            重命名文件
            shutil.move(old_file, new_file) # 会覆盖已有的文件
            os.rename(old_file,new_file) # 不会覆盖，并且会报异常
        """
        try:
            if cover:
                shutil.move(old_file, new_file)
            else:
                os.rename(old_file, new_file)
            return True
        except Exception as e:
            print(str(e))
            return False

    @staticmethod
    def del_file(file_name):
        """"删除文件或者文件夹"""
        try:
            if os.path.isdir(file_name):
                shutil.rmtree(file_name)
                return True
            elif os.path.isfile(file_name):
                os.remove(file_name)
                return True
            else:
                return False
        except Exception as e:
            print(str(e))
            return False

    @staticmethod
    def isdir(file_name):
        """是否是目录"""
        return os.path.isdir(file_name)

    @staticmethod
    def isfile(file_name):
        """是否是文件"""
        return os.path.isfile(file_name)

    @staticmethod
    def mkdir(directory):
        """创建目录"""
        try:
            # 创建目录
            os.makedirs(directory)
            return True
        except FileExistsError:
            return True
        except OSError as e:
            print(f"mkdir '{directory}' error：{e}")
            return False

    @staticmethod
    def get_file_md5(file_path,algorithm='md5'):
        """计算单个文件的 MD5/sha256/sha512 值"""
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512()
        else:
            raise Exception('algorithm error')
        with open(file_path, 'rb') as f:
            # 逐块读取文件内容进行加密计算
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    @staticmethod
    def get_folder_md5(folder_path,algorithm='md5'):
        """计算文件夹的 MD5/sha256/sha512 值"""
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512()
        else:
            raise Exception('algorithm error')

        # 递归遍历文件夹中的所有文件
        for root, dirs, files in os.walk(folder_path):
            dirs.sort()
            files.sort()
            for file_name in files:  # 按文件名排序，确保一致性
                file_path = os.path.join(root, file_name)
                # 计算文件的 MD5 值并更新到文件夹 MD5 值中
                file_hash = fileHelper.get_file_md5(file_path,algorithm=algorithm)
                hash_obj.update(file_hash.encode(fileHelper.ENCODING_UTF8))  # 合并文件 MD5
        return hash_obj.hexdigest()

    @staticmethod
    def list_folder_files(folder_path,sort_file=True, only_list_this_dir=False, return_file=None,return_dir=None,return_file_and_dir=None,follow_links=False,on_error=None,ignore_dirs=None):
        """
        列出文件夹中的内容\n
        默认递归列出文件夹和子文件夹中的全部文件\n
        :param folder_path: 文件夹路径
        :param sort_file: 是否排序文件, 排序文件可以使每次调用的结果一致 默认排序
        :param only_list_this_dir: 是否只遍历当前目录不遍历子目录
        :param return_file: 返回文件 默认
        :param return_dir: 返回目录
        :param return_file_and_dir: 返回文件和目录
        :param follow_links: 是否会跟随符号链接（symlink）遍历指向的目录；默认不跟随，避免循环遍历
        :param on_error: 函数类型，用于处理遍历过程中出现的错误（如权限不足），默认 None（直接抛出异常）
        :param ignore_dirs: 忽略目录 如 ['.svn','.git']
        :return: 生成器（generator）
        """
        if not os.path.exists(path=folder_path):
            raise Exception('Folder Path Not Exists')
        if return_file is None and return_dir is None and return_file_and_dir is None:
            return_file = True
        if sum([bool(return_file), bool(return_dir), bool(return_file_and_dir)]) != 1:
            raise Exception('return_file, return_dir, return_file_and_dir 只能设置其中一个参数为True')
        if return_file_and_dir:
            return_file = True
            return_dir = True
        for root, dirs, files in os.walk(folder_path,onerror=on_error,followlinks=follow_links):
            if ignore_dirs is not None:
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
            if sort_file:
                dirs.sort()
                files.sort()
            if return_dir:
                for dir_name in dirs:
                    yield os.path.join(root, dir_name)
            if return_file:
                for file_name in files:  # 按文件名排序，确保一致性
                    yield os.path.join(root, file_name)
            if only_list_this_dir:
                break

    @staticmethod
    def get_current_path(include_file_name=False, dir_level=0):
        """
        :param include_file_name:是否返回包含文件名的路径
        :param dir_level:路径定位 0表示当前文件夹 1表示上一层 2表示上上层
        :return: file_path|dir_path
        """
        try:
            # 获取调用栈：栈帧列表，每个帧包含调用信息
            # stack()[0]：当前方法（getFilePath）的帧
            # stack()[1]：调用当前方法的帧（即调用者的位置）
            caller_frame = inspect.stack()[1]
            # 从调用帧中提取文件名
            caller_file = caller_frame.filename
            # 包含文件名的绝对路径
            caller_abs_file = os.path.abspath(caller_file)
            if include_file_name:
                return caller_abs_file
            else:
                # 提取目录路径（去掉文件名）
                caller_dir = os.path.dirname(caller_abs_file)
                caller_dir = caller_dir.split(os.sep)
                dir_level = abs(dir_level)
                caller_dir = caller_dir[0:caller_dir.__len__() - dir_level]
                # 预处理：修复Windows盘符（添加缺失的分隔符）
                if os.name == 'nt':  # 仅在Windows系统下处理
                    if len(caller_dir) > 0 and caller_dir[0].endswith(':'):
                        caller_dir[0] += os.sep  # 给盘符添加系统分隔符（\）
                else:
                    # linux下 ['','data','a'] 会解析为 data/a而非/data/a 处理这种情况
                    if len(caller_dir) > 0 and caller_dir[0] == '':
                        caller_dir[0] = os.sep
                return os.path.join(*caller_dir)
        except IndexError:
            # 处理调用栈不足的异常（极少发生）
            return None

    @staticmethod
    def get_size(file_path, size_name='B', precision=2):
        """得到文件/目录的大小"""
        total_size = 0
        allow_size_name = ("B", "KB", "MB", "GB", "TB")
        if size_name not in allow_size_name:
            raise Exception('getFileSize.size_name need in %s' % str(allow_size_name))
        if not os.path.exists(file_path):
            raise Exception(f"File or path not exists: {file_path}")
        """获取单个文件的大小（字节）"""
        if os.path.isfile(file_path):
            total_size = os.path.getsize(file_path)
        """递归计算目录的总大小（字节）"""
        if os.path.isdir(file_path):
            for root, dirs, files in os.walk(file_path):
                for one_file in files:
                    sub_file_path = os.path.join(root, one_file)
                    try:
                        total_size += os.path.getsize(sub_file_path)
                    except PermissionError:
                        print(f"No Permission: {sub_file_path}，passed")
        if size_name == 'B':
            pass
        elif size_name == 'KB':
            total_size = round(total_size / 1024, precision)
        elif size_name == 'MB':
            total_size = round(total_size / 1024 / 1024, precision)
        elif size_name == 'GB':
            total_size = round(total_size / 1024 / 1024 / 1024, precision)
        elif size_name == 'TB':
            total_size = round(total_size / 1024 / 1024 / 1024 / 1024, precision)
        return total_size

    @staticmethod
    def get_modify_time(file_path,get_timestamp=False):
        """
        获取文件/文件夹的最后修改时间
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        stat_info = os.stat(file_path)
        return int(stat_info.st_mtime) if get_timestamp else datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    # fileHelper.write_append('a.log',content="sdfsdf\nsdfsd好的f\na\n")
    # for row in fileHelper.list_folder_files('D:\code\myPythonPackages',only_list_this_dir=False,return_file_and_dir=True,ignore_dirs=['.svn','.idea']):
    #     print(row)
    #     pass

    print(fileHelper.get_folder_md5('D:\code\\test'))