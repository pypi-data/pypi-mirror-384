import os


def read_inc(file_path):
    _cur_dir = os.path.dirname(os.path.abspath(__file__))
    inc_file = os.path.join(_cur_dir, '..', file_path)
    with open(inc_file, 'r', encoding='utf-8') as f:
        content = f.read()
        return content
