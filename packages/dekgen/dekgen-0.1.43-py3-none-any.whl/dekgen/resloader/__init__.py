import os
from collections import OrderedDict
from dektools.zip import decompress_files
from dektools.file import FileHitChecker, normal_path
from ..utils.yaml import yaml, data_final_list
from ..tmpl.template import TemplateWide


class ResLoader:
    accept_ext_set = {'.yaml'}
    ignore_prefix = '_'
    ignore_res = '.resignore'

    template_cls = TemplateWide
    serializer = yaml
    data_final_list = data_final_list

    @classmethod
    def data_final(cls, data_list):
        for df in data_final_list:
            data_list = df(data_list)
        return data_list

    @classmethod
    def is_res_file(cls, filepath):
        return bool(cls.get_res_name(filepath))

    @classmethod
    def get_res_name(cls, filepath):
        filename = os.path.basename(filepath)
        fb, ext = os.path.splitext(filename)
        if ext in cls.accept_ext_set and not fb.startswith(cls.ignore_prefix):
            return fb
        return None

    @classmethod
    def glob_files(cls, filepath, judge, *ignores):
        result = []
        if os.path.isfile(filepath):
            result.append(filepath)
        elif os.path.isdir(filepath):
            for f in os.listdir(filepath):
                result.extend(cls.glob_files(os.path.join(filepath, f), None))
        if ignores:
            fhc = FileHitChecker(filepath, *ignores)
            return [x for x in result if not judge or judge(cls.is_res_file, fhc.new_match(), x)]
        else:
            return result

    @classmethod
    def glob_res_file(cls, filepath, ignore=ignore_res):
        return cls.glob_files(filepath, lambda is_res_file, is_hit, x: is_res_file(x) and not is_hit(x), ignore)

    @classmethod
    def glob_not_res_file(cls, filepath, ignore=ignore_res):
        return cls.glob_files(filepath, lambda is_res_file, is_hit, x: not is_res_file(x) or is_hit(x), ignore)

    @classmethod
    def data_from_file(cls, close_tpl, *args):
        data_list = []
        for arg in cls._extend_filepath_args(args):
            data = cls.serializer.loads(
                cls.template_cls(
                    arg.get('variables') or {}, **arg.get('kwargs') or {}
                ).render_string(arg['filepath'], close_tpl=close_tpl)
            ) or OrderedDict()
            if 'order' in arg:
                data['__order__'] = arg['order']
            data['__file__'] = arg['filepath']
            data['__context__'] = arg.get('context') or {}
            data_list.append(data)
        data_list = sorted(data_list, key=lambda x: x.get('__order__') or 0)
        return cls.data_final(data_list)

    @classmethod
    def data_from_template_file(cls, *args):
        return cls.data_from_file(False, *args)

    @classmethod
    def from_template_file(cls, *args):
        return cls(cls.data_from_template_file(*args))

    @classmethod
    def load_res(cls, path_res, close_tpl=False, path=None):
        if not os.path.exists(path_res):
            raise FileNotFoundError(path_res)
        if os.path.isfile(path_res):
            path_res = decompress_files(path_res)
        path_res = normal_path(path_res)
        if path:
            path_res = path(path_res)
        return cls(cls.data_from_file(close_tpl, *(dict(filepath=x) for x in cls.glob_res_file(path_res))))

    @classmethod
    def _extend_filepath_args(cls, args):
        def get_key_map(pa):
            r = {}
            for path, arg in pa.items():
                key = get_path_unique(path)
                if key not in r or r[key][1] > len(path):
                    r[key] = [arg, len(path)]
            return {key: v[0] for key, v in r.items()}

        def get_path_unique(path):
            file_base = os.path.basename(path).split('.', 1)[0]
            dir_path = os.path.dirname(path)
            return dir_path, file_base

        def extend_to_valid_paths(paths):
            path_children = {}
            path_extends = OrderedDict()
            for path in paths:
                key = get_path_unique(path)
                dir_path, file_base = key
                if dir_path not in path_children:
                    path_children[dir_path] = sorted(os.listdir(dir_path))
                if key not in path_extends:
                    path_list = path_extends[key] = []
                    for fn in path_children[dir_path]:
                        fp = os.path.join(dir_path, fn)
                        if cls.is_res_file(fp) and fn.startswith(f'{file_base}.'):
                            path_list.append(fp)
            return path_extends

        path_map = OrderedDict([(os.path.normpath(os.path.abspath(arg['filepath'])), arg) for arg in args])
        key_map = get_key_map(path_map)
        result = []
        for k, fl in extend_to_valid_paths(path_map.keys()).items():
            for f in fl:
                if f in path_map:
                    arg = path_map[f]
                else:
                    arg = {**key_map[k], **dict(filepath=f)}
                result.append(arg)
        return result

    def __init__(self, data_list):
        self.data_list = data_list
