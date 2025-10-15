import os
import configparser
import toml
from dektools.file import read_text, write_file, remove_path


def get_py_pkg_info(path_dir):
    if os.path.isfile(path_dir) and os.path.splitext(path_dir)[-1] == '.whl':
        return os.path.basename(path_dir).split('-', 1)[0]
    path_cfg = os.path.join(path_dir, 'setup.cfg')
    path_toml = os.path.join(path_dir, 'pyproject.toml')
    result = {}
    if os.path.isfile(path_cfg):
        conf = configparser.ConfigParser()
        conf.read(path_cfg)
        result.update(
            name=conf.get('metadata', 'name', fallback=None),
            version=conf.get('metadata', 'version', fallback=None),
            ep=EntryPoints().from_conf(conf)
        )
    elif os.path.isfile(path_toml):
        conf = toml.loads(read_text(path_toml))
        result.update(
            name=conf['project']['name'] or None,
            version=conf['project']['version'] or None,
            ep=EntryPoints().from_json(conf)
        )
    return result


def get_py_pkg_name(path_dir):
    return get_py_pkg_info(path_dir)['name']


class EntryPoints:
    def __init__(self):
        self.data = []

    def save(self, fp):
        s = '\n'.join(self.data)
        remove_path(fp)
        if s.strip():
            write_file(fp, s=s)

    def from_conf(self, conf):
        section = 'options.entry_points'
        if conf.has_section(section):
            for option in conf.options(section):
                self.data.append(f'[{option}]')
                d = conf.get(section, option, fallback=None),
                self.data.extend(d)
        return self

    def from_json(self, data):
        scripts = (data.get('project') or {}).get('scripts')
        if scripts:
            self.data.append('[console_scripts]')
            for k, v in scripts.items():
                self.data.append(f'\n{k} = {v}')

        scripts = (data.get('project') or {}).get('gui-scripts')
        if scripts:
            self.data.append('[gui_scripts]')
            for k, v in scripts.items():
                self.data.append(f'\n{k} = {v}')

        eps = (data.get('project') or {}).get('entry-points')
        if eps:
            for name, d in eps.items():
                self.data.append(f'[{name}]')
                for k, v in d.items():
                    self.data.append(f'\n{k} = {v}')
        return self
