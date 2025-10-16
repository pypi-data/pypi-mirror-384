from ....tmpl.env import EnvExtend

env_extend = EnvExtend()


@env_extend.globals
def not_empty(x):
    if isinstance(x, str):
        return x.strip()
    else:
        return x
