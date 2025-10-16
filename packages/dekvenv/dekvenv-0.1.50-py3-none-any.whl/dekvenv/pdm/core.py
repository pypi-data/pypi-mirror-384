import json
import os
import subprocess
from pathlib import Path
from dektools.zip import decompress_files
from dektools.file import remove_path, sure_dir, read_text, write_file
from dektools.str import Fragment
from unearth import collector
from ..pypirc.core import PyPiRC


def get_pdm_cache_dir():
    return subprocess.getoutput('pdm config cache_dir').strip().split('\n', 1)[0].strip()


def get_pdm_cache_dir_hash():
    path = Path(get_pdm_cache_dir()) / 'hashes'
    assert str(path).startswith(os.path.expanduser('~'))
    return path


def get_pdm_cache_dir_pkg():
    path = Path(get_pdm_cache_dir()) / 'packages'
    assert str(path).startswith(os.path.expanduser('~'))
    return path


def get_pdm_cache_dir_metadata():
    path = Path(get_pdm_cache_dir()) / 'metadata'
    assert str(path).startswith(os.path.expanduser('~'))
    return path


def pdm_clear_cache_hash_pkg(server, pkg):
    from pdm.models.caches import HashCache
    path_cache = get_pdm_cache_dir_hash()
    hc = HashCache(path_cache)
    ppr = PyPiRC()
    repository = ppr.servers.get(server, {}).get('repository')
    if repository:
        url = f"{repository}/packages/{pkg}"
        path = hc._get_path_for_key(url)
        if str(path).startswith(str(path_cache)):
            remove_path(path_cache)


def pdm_clear_cache_hash():
    remove_path(get_pdm_cache_dir_hash())


def is_pdm_project(path):
    return os.path.isfile(os.path.join(path, 'pyproject.toml'))


def pdm_update_cache_pkg(path_dir, info):
    def handle_entry_points(fp):
        if os.path.isdir(fp):
            ep.save(os.path.join(fp, 'entry_points.txt'))

    name, version, ep = info['name'], info['version'], info['ep']
    prefix = f'{name}-{version}'
    path_pkgs = get_pdm_cache_dir_pkg()
    for fn in os.listdir(path_pkgs):
        if fn.startswith(prefix):
            path_pkg = os.path.join(path_pkgs, fn)
            path_lib = os.path.join(path_pkg, 'lib')
            fs = set(os.listdir(path_lib)) & set(os.listdir(path_dir))
            for f in fs:
                remove_path(os.path.join(path_lib, f), True)
                write_file(os.path.join(path_lib, f), ci=os.path.join(path_dir, f))

            for f in os.listdir(path_lib):
                if f.endswith('.dist-info'):
                    handle_entry_points(os.path.join(path_lib, f))
            for line in read_text(os.path.join(path_pkg, 'referrers')).splitlines():
                line = line.strip()
                if line:
                    handle_entry_points(line)


def pdm_clear_cache_pkg(pkg, dist=None):
    path_pkgs = get_pdm_cache_dir_pkg()
    for fn in os.listdir(path_pkgs):
        if dist:
            a = os.path.basename(dist).split('-')
            prefix = f'{a[0]}-{a[1]}'
            once = True
        else:
            prefix = f'{pkg}-'
            once = False
        if fn.startswith(prefix):
            path_pkg = os.path.join(path_pkgs, fn)
            if dist:
                path_lib = os.path.join(path_pkg, 'lib')
                remove_path(path_lib)
                sure_dir(path_lib)
                decompress_files(dist, path_lib)
            else:
                remove_path(path_pkg, True)
            if once:
                break


def pdm_clear_cache_metadata(dist):
    path_metadata = get_pdm_cache_dir_metadata()
    a = os.path.basename(dist).split('-')
    pkg, version = a[:2]
    for fn in os.listdir(path_metadata):
        path_meta = os.path.join(path_metadata, fn)
        data = json.loads(read_text(path_meta))
        for key in list(data.keys()):
            p, v = key.rsplit('-', 1)
            if (p.startswith(f'{pkg}[') or p == pkg) and v == version:
                data.pop(key, None)
        write_file(path_meta, s=json.dumps(data))


def fix_pdm(reverse=False):
    # disable mirror redirect
    path_target = collector.__file__
    content = read_text(path_target)
    replace = [[
        "        headers={",
        "        follow_redirects=False, headers={"
    ]]
    content = Fragment.replace_safe_again(content, replace, reverse)
    if content is not None:
        write_file(path_target, s=content)
