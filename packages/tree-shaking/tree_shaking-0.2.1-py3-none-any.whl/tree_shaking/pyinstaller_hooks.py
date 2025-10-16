import sys
import typing as t
from lk_utils import dedent
from lk_utils import fs
from lk_utils import run_cmd_args
from .config import graphs_root
from .config import parse_config
from .graph import T


def main(
    config_file: str,
    limited_search_root: t.Optional[str] = None,
):
    cfg: T.Config = parse_config(config_file)
    
    # ref: ./export.py:_mount_resources
    used_modules = set()
    for graph_id in cfg['entries'].values():
        graph_file = '{}/{}.yaml'.format(graphs_root, graph_id)
        graph: T.DumpedModuleGraph = fs.load(graph_file)
        
        limited_uid = None
        if limited_search_root:
            for uid, root in graph['source_roots'].items():
                if root == limited_search_root:
                    limited_uid = uid
                    break
        
        for module_name, relpath in graph['modules'].items():
            uid, relpath = relpath.split('/', 1)
            uid = uid[1:-1]
            if limited_uid and uid != limited_uid:
                continue
            used_modules.add(module_name.split('.', 1)[0])
    print(len(used_modules))
    frozen_modules = tuple(sorted(used_modules))
    
    writer = []
    writer.extend('import {}  # noqa'.format(x) for x in frozen_modules)
    writer.append('')
    writer.append(dedent(
        '''
        def main():
            print('hello world!')
        
        if __name__ == '__main__':
            main()
        '''
    ))
    
    curr_room = fs.xpath('_rooms/{}'.format('test'))  # TODO
    # fs.make_dir(curr_room)
    fs.dump(writer, '{}/fake_main.py'.format(curr_room))
    
    run_cmd_args(
        # sys.executable, '-m', 'pyinstaller',
        'poetry', 'run', 'pyinstaller',
        *(('-p', x) for x in cfg['search_paths']),
        'fake_main.py',
        verbose=True,
        cwd=curr_room
    )


def hook_imports():
    pass


def get_import_list():
    pass


if __name__ == '__main__':
    # pox -m tree_shaking.pyinstaller_hooks -h
    from argsense import cli
    cli.add_cmd(main)
    cli.run(main)
