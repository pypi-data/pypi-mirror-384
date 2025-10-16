if __name__ == '__main__':
    __package__ = 'tree_shaking'

import typing as t
from collections import defaultdict

from lk_utils import fs
from pyecharts.charts import Graph

from .config import parse_config
from .finder import Finder


def main(config_file: str, target_entry: str) -> None:
    cfg = parse_config(config_file)
    finder = Finder(cfg['ignores'])
    
    entrance_module_name = None
    for module, _ in finder.get_all_imports(
        script=target_entry, include_self=True
    ):
        if entrance_module_name is None:
            entrance_module_name = module
    
    _refs = finder.references
    
    def recurse(
        module_name: str, _dict: dict = None, _recorded: t.Set[str] = None
    ) -> t.Dict[str, t.Union[dict, str, None]]:
        if _dict is None:
            _dict = {}
        if _recorded is None:
            _recorded = set()
        for x in _refs[module_name]:
            if x in _recorded:
                _dict[x] = '...'
            else:
                _recorded.add(x)
                if _refs[x]:
                    _dict[x] = {}
                    recurse(x, _dict[x], _recorded)
                else:
                    _dict[x] = None
        return _dict
    
    tree = recurse(entrance_module_name)
    fs.dump(tree, 'test/tree_result.json')
    
    # -------------------------------------------------------------------------
    
    # weights = defaultdict(int)
    # for path0 in cfg['entries'].keys():
    #     sources = []
    #     target = None
    #     for module, path1 in finder.get_direct_imports(
    #         path0, include_self=True
    #     ):
    #         if target is None:
    #             target = module.full_name
    #             weights[module.full_name] += 10
    #         else:
    #             sources.append(module.full_name)
    #             weights[module.full_name] += 2
    #
    # # DELETE
    # refs = finder.references
    #
    # all_names = defaultdict(int)
    # for k, v in refs.items():
    #     all_names[k] += 10
    #     for w in v:
    #         all_names[w] += 2
    # nodes = [{'name': k, 'symbolSize': v} for k, v in all_names.items()]
    #
    # links = []
    # for k, v in refs.items():
    #     for w in v:
    #         links.append({'source': w, 'target': k})
    # print(len(nodes), len(links), ':v2')
    #
    # (
    #     Graph()
    #     .add('Dependency Network', nodes, links, repulsion=100)
    #     .render()
    # )


if __name__ == '__main__':
    from argsense import cli
    cli.add_cmd(main)
    cli.run(main)
