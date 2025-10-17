import os
import os.path
from datetime import datetime


def clean_expired_files_and_dirs(current_dir, last_generate_time):
    """
    清理目录的方法，按照指定规则处理目录及其子目录

    参数:
    current_dir: 当前要处理的目录路径
    last_generate_time: 最后生成时间，datetime类型
    """
    # 1. 优先处理子目录（递归）
    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        if os.path.isdir(item_path) and not os.path.islink(item_path):
            clean_expired_files_and_dirs(item_path, last_generate_time)

    # 2. 处理当前目录下的py文件
    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        if os.path.isfile(item_path) and item.endswith('.py'):
            # 检查文件修改时间
            file_mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
            if file_mtime < last_generate_time:
                # 检查是否包含指定关键字
                try:
                    content = open(item_path, 'r', encoding='utf-8').read()
                    if '@author: fastcodedog' in content:
                        os.remove(item_path)
                        print(f"已删除文件: {item_path}")
                except Exception as e:
                    print(f"处理文件 {item_path} 时出错: {e}")

    # 3. 检查并处理空的__init__.py
    init_file = os.path.join(current_dir, '__init__.py')
    if os.path.exists(init_file) and os.path.isfile(init_file):
        # 检查目录是否还有其他文件或子目录
        has_other_items = False
        for item in os.listdir(current_dir):
            if item != '__init__.py' or not os.path.isfile(os.path.join(current_dir, item)):
                has_other_items = True
                break

        if not has_other_items:
            # 检查__init__.py是否为空
            try:
                if os.path.getsize(init_file) == 0:
                    os.remove(init_file)
                    print(f"已删除空的__init__.py: {init_file}")
            except Exception as e:
                print(f"处理__init__.py {init_file} 时出错: {e}")

    # 4. 如果目录为空则删除
    try:
        if not os.listdir(current_dir):  # 检查目录是否为空
            os.rmdir(current_dir)
            print(f"已删除空目录: {current_dir}")
    except Exception as e:
        print(f"删除目录 {current_dir} 时出错: {e}")
