from dektools.serializer.yaml import yaml as yaml_, Yaml, Resolver
from .tags import FuncTag, CallTag, ExtendTag, tmpl_data_final

yaml = Yaml(resolvers=Resolver.ordereddict)
yaml.reg_other(yaml_)

yaml.reg_batch(FuncTag, CallTag, ExtendTag)

data_final_list = [tmpl_data_final]
