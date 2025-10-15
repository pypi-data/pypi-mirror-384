import os

from funutil.util.log import get_logger

logger = get_logger("funutil")


def info(msg):
    logger.info(msg)


"""
os.path重构
"""


def rename(src, dst):
    if os.path.exists(src):
        return os.rename(src, dst)
    else:
        logger.error("{} not exist!".format(src))
        return


"""
path
"""


def path_parse(path):
    if path is None:
        return path
    # ~处理
    path = os.path.expanduser(path)
    if not path.startswith("/"):
        return os.path.join(os.getcwd(), path)
    return path


def path_join(parent_path, child_path):
    parent_path = path_parse(parent_path)

    return os.path.join(parent_path, child_path)
    pass


def join_path(child_path, parent_path=None):
    return path_join(parent_path, child_path)


def delete_file(file_path):
    if exists_file(file_path):
        info("file exist and delete")
        os.remove(file_path)


def exists_dir(file_dir, mkdir=False):
    return exists(file_dir=file_dir, mkdir=mkdir, mode="path")


def exists_file(file_path, mkdir=False):
    return exists(file_path=file_path, mkdir=mkdir, mode="file")


def exists(file_path=None, file_dir=None, file_name=None, mode="file", mkdir=False):
    """
    文件或者目录是否存在，不存在是否需要新建
    :param file_path: 文件路径
    :param file_dir:  文件目录
    :param file_name: 文件名称
    :param mode:  file-文件，path-目录
    :param mkdir: 目录不存在是否需要新建
    :return: 是否存在
    """

    file_path = path_parse(file_path)
    file_dir = path_parse(file_dir)

    if mode == "file":
        if file_path is not None:
            file_dir, file_name = os.path.split(file_path)
        elif file_dir is not None and file_name is not None:
            file_path = os.path.join(file_dir, file_name)
        else:
            logger.warning("file_path or file_dir&file_name is needed")
            return False

        if os.path.exists(file_dir) and os.path.isdir(file_dir):
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return True
            else:
                return False
        elif not os.path.exists(file_dir) and mkdir:
            makedirs(file_dir)
        return False

    elif mode == "path":
        if file_path is not None:
            file_dir, file_name = os.path.split(file_path)
        elif file_dir is None:
            logger.warning("file_path or file_dir is needed")
            return False

        if os.path.exists(file_dir) and os.path.isdir(file_dir):
            return True
        elif mkdir:
            makedirs(file_dir)
        return False

    return False


def exist_and_create(file_dir):
    if os.path.exists(file_dir) and os.path.isdir(file_dir):
        return

    os.makedirs(file_dir)
    return


def _file_path(path):
    return os.path.dirname(path)


def _file_name(path):
    return os.path.basename(path)


def makedirs(name, mode=0o777, exist_ok=False):
    os.makedirs(name, mode=mode, exist_ok=exist_ok)


def meta(file_dir, file_name=None, deep=1):
    """
    返回文件的基本信息
    :param file_dir: 路径
    :param file_name: 文件名称
    :param deep: 深度
    :return:文件信息
    """
    return {
        "dir": file_dir,
        "name": file_name,
        "path": file_dir if file_name is None else os.path.join(file_dir, file_name),
        "isdir": True if file_name is None else False,
        "deep": deep,
    }


def list_file(file_dir, deep=1):
    """
    返回这个目录下所有的目录和文件，深度为deep
    :param file_dir: 路径
    :param deep:深度
    :return: 所有目录和文件
    """
    result = []
    if deep <= 0:
        return result
    for file_name in os.listdir(file_dir):
        tmp_path = os.path.join(file_dir, file_name)

        if os.path.isfile(tmp_path):
            result.append(meta(file_dir=file_dir, file_name=file_name, deep=deep))
        elif os.path.isdir(tmp_path):
            result.append(meta(file_dir=tmp_path, deep=deep))
            result.extend(list_file(tmp_path, deep=deep - 1))
    return result


def merge_file(source_file, target_file):
    flag = 0  # 计数器

    info("开始。。。。。")

    with open(target_file, "w+") as write_file:
        for file_path in source_file:
            with open(file_path, "r") as f_source:
                for line in f_source:
                    write_file.write(line)
            write_file.write("\n")

    info("done " + str(flag) + "\t" + target_file)
    info("完成。。。。。")


def split_file(source_file, target_dir, max_line=2000000):
    file_name = _file_name(source_file)
    flag = 0  # 计数器
    name = 1  # 文件名

    info("开始。。。。。")

    def get_filename():
        return str(target_dir) + file_name + "-split-" + str(name) + ".csv"

    write_file = open(get_filename(), "w+")

    with open(source_file, "r") as f_source:
        for line in f_source:
            flag += 1

            write_file.write(line)

            if flag == max_line:
                info("done " + str(flag) + "\t" + get_filename())
                name += 1
                flag = 0

                write_file.close()
                write_file = open(get_filename(), "w+")
    write_file.close()
    info("done " + str(flag) + "\t" + get_filename())
    info("完成。。。。。")


class LocalPath:
    """ """

    def __init__(self, file_dir=None, file_name=None, file_path=None):
        if file_path is not None:
            file_dir, file_name = os.path.split(file_path)

        if file_dir is not None and file_name is not None:
            file_path = os.path.join(file_dir, file_name)

        self.file_dir = file_dir
        self.file_name = file_name
        self.file_path = file_path

    def make_dirs(self):
        os.makedirs(self.file_dir)

    def exist(self):
        return os.path.exists(self.file_path)

    def list_file(self, deep=1):
        result = []
        if deep <= 0:
            return result
        for file in os.listdir(self.file_dir):
            tmp_path = os.path.join(self.file_dir, file)
            if os.path.isfile(tmp_path):
                result.append(self.to_json(file, deep=deep))
            elif os.path.isdir(tmp_path):
                result.append(self.to_json(deep=deep))
                result.extend(LocalPath(file_dir=tmp_path).list_file(deep=deep - 1))

        return result

    def meta(self):
        return self.to_json(self.file_name)

    def to_json(self, file_name=None, deep=1):
        return {
            "dir": self.file_dir,
            "name": file_name,
            "path": self.file_dir
            if file_name is None
            else os.path.join(self.file_dir, file_name),
            "isdir": True if file_name is None else False,
            "deep": deep,
        }
