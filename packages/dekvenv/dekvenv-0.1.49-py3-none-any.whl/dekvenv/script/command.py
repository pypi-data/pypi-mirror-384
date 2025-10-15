import os
import json
import sys
import time
import subprocess
import virtualenv
import typer
import typing_extensions
from packaging.requirements import Requirement
from dektools.shell import shell_wrapper
from dektools.sys import sys_paths_relative, paths_sys
from dektools.file import write_file, read_text, sure_dir, remove_path
from dektools.venvx.constants import venv_main
from dektools.cfg import ObjectCfg
from ..main.command import build, get_pkg_path, retry
from .core import get_pkg_entry_points_paths

workdir = ObjectCfg(__name__, module=True).path_dir

path_scripts = os.path.join(workdir, 'scripts')
path_scripts_info = os.path.join(workdir, '.scripts.json')

path_pyproject = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res', 'pyproject.toml-tpl')

app = typer.Typer(add_completion=False)

cmd_retry = f"{__name__.partition('.')[0]} {retry.__name__}"


@app.command()
def add(
        pkg: typing_extensions.Annotated[str, typer.Argument()] = '', name=None, path='.', args=''):
    from ..utils.common import get_py_pkg_name
    from ..pdm.core import is_pdm_project
    if name and not pkg:
        pkg = name
    if pkg:
        req = Requirement(pkg)
        if not name:
            name = req.name
    else:
        assert path
        path = os.path.normpath(os.path.abspath(path))
        if not name:
            name = get_py_pkg_name(path)
        if os.path.isdir(path):
            if not is_pdm_project(path):
                build(path)
    path_scripts_item = os.path.join(path_scripts, name)
    sure_dir(path_scripts_item)
    path_venv = os.path.join(path_scripts_item, venv_main)
    virtualenv.cli_run([path_venv])
    path_venv_scripts = sys_paths_relative(path_venv)['scripts']
    bin_exe_pre = set(os.listdir(path_venv_scripts))
    path_pyproject_item = os.path.join(path_scripts_item, 'pyproject.toml')
    if not os.path.exists(path_pyproject_item):
        write_file(path_pyproject_item, s=read_text(path_pyproject))
    os.system(f'{cmd_retry} pdm lock -p {path_scripts_item}')
    command_record = 'dekvenv add '
    if pkg:
        cmd = f'{cmd_retry} pdm add "{pkg}" {args} -v -p {path_scripts_item}'
        command_record += f'--pkg {pkg}'
    else:
        if os.path.isfile(path):
            file = path
        elif is_pdm_project(path):
            file = path
        else:
            file = get_pkg_path(path)
        cmd = f'{cmd_retry} pdm add file:///{file} {args} -v -p {path_scripts_item}'
        command_record += f'--path {file}'
    shell_wrapper(cmd)
    entry_points = get_pkg_entry_points_paths(name, path_venv).values()
    while True:
        for ep in entry_points:
            if not os.path.isfile(ep):
                time.sleep(0)
                continue
        break
    bin_exe_set = set(os.listdir(path_venv_scripts)) - bin_exe_pre
    path_sys_exe_scripts = paths_sys()['scripts']
    dict_path_cmd_proxy = {}
    for bin_exe in bin_exe_set:
        path_bin_exe_real = os.path.join(path_venv_scripts, bin_exe)
        path_exe_proxy = os.path.join(path_sys_exe_scripts, bin_exe)
        bin_write(name, path_bin_exe_real, path_exe_proxy)
        dict_path_cmd_proxy[bin_exe] = path_exe_proxy
    scripts_info = json.loads(read_text(path_scripts_info, '{}'))
    scripts_info.setdefault('path', {})[name] = path_scripts_item
    record_info = scripts_info.setdefault('record', {})
    record_info_list = record_info.setdefault(name, [])
    if command_record not in record_info_list:
        record_info_list.append(command_record)
    dict_info = scripts_info.setdefault('proxy', {})
    dict_info = dict_info.setdefault(name, {})
    dict_info.update(dict_path_cmd_proxy)
    write_file(path_scripts_info, json.dumps(scripts_info, indent=4, ensure_ascii=False))


path_bin_work = paths_sys()['scripts']
path_bin_proxy = os.path.join(path_bin_work, '.dekvenv', 'bin')


def bin_write(name, path_bin_exe_real, path_exe_proxy):
    write_file(
        os.path.join(
            path_bin_proxy, '.dekvenv', 'bin', os.path.basename(path_exe_proxy), name),
        c=path_bin_exe_real
    )
    ok = remove_path(path_exe_proxy, True)
    if ok:
        write_file(
            path_exe_proxy,
            c=path_bin_exe_real
        )
        if os.name != 'nt':
            os.system(f'chmod +x {path_exe_proxy}')


def bin_remove(name):
    bin_list = set()
    if os.path.isdir(path_bin_proxy):
        for bin_name in os.listdir(path_bin_proxy):
            bin_file = os.path.join(path_bin_proxy, bin_name, name)
            if os.path.exists(bin_file):
                remove_path(bin_file)
                bin_list.add(bin_name)
    for bin_name in bin_list:
        ok = remove_path(os.path.join(path_bin_proxy, bin_name), True)
        if ok:
            ret = os.listdir(os.path.join(path_bin_proxy, bin_name))
            if ret:
                write_file(
                    os.path.join(path_bin_work, bin_name),
                    c=os.path.join(path_bin_proxy, bin_name, ret[0])
                )
                if os.name != 'nt':
                    os.system(f'chmod +x {os.path.join(path_bin_work, bin_name)}')


def get_cmd_proxy_ref(scripts_info):
    dict_proxy = scripts_info.get('proxy') or {}
    result = {}
    for d_cmd in dict_proxy.values():
        for proxy in d_cmd:
            result[proxy] = result.get(proxy, 0) + 1
    return result


@app.command()
def remove(name):
    scripts_info = json.loads(read_text(path_scripts_info, '{}'))

    dict_path = scripts_info.get('path') or {}
    path_scripts_item = dict_path.get(name)
    if path_scripts_item:
        remove_path(path_scripts_item, True)

    cmd_proxy_ref = get_cmd_proxy_ref(scripts_info)
    record_info = scripts_info.get('record', {})
    dict_proxy = scripts_info.get('proxy') or {}
    dict_proxy_name = dict_proxy.get(name) or {}
    for cmd_proxy, path_cmd_proxy in dict_proxy_name.items():
        if cmd_proxy_ref.get(cmd_proxy, 0) <= 1:
            remove_path(path_cmd_proxy, True)

    record_info.pop(name, None)
    dict_path.pop(name, None)
    dict_proxy.pop(name, None)
    bin_remove(name)

    write_file(path_scripts_info, json.dumps(scripts_info, indent=4, ensure_ascii=False))

    remove_path(os.path.join(path_scripts, name))


@app.command()
def reset(pkg):
    remove(Requirement(pkg).name)
    add(pkg)


@app.command()
def pop(name: str = '', pkg: str = ''):
    assert pkg and name
    path_scripts_item = os.path.join(path_scripts, name)
    if os.path.exists(path_scripts_item):
        shell_wrapper(f'pdm remove "{pkg}" -v -p {path_scripts_item}')
    else:
        raise


@app.command()
def record():
    scripts_info = json.loads(read_text(path_scripts_info, '{}'))
    record_info = scripts_info.get('record', {})
    for name in sorted(record_info.keys()):
        array = record_info[name]
        for item in array:
            print(item)


@app.command()
def clean():
    scripts_info = json.loads(read_text(path_scripts_info, '{}'))
    dict_path = scripts_info.get('path') or {}
    for name in dict_path.keys():
        remove(name)
    remove_path(path_scripts_info)


@app.command()
def info():
    print(json.dumps(json.loads(read_text(path_scripts_info, '{}')), indent=4, ensure_ascii=False))


@app.command()
def shell(name):
    path_scripts_item = os.path.join(path_scripts, name)
    path_venv = os.path.join(path_scripts_item, venv_main)
    path_venv_bin = sys_paths_relative(path_venv)['scripts']
    path_exe = os.path.join(path_venv_bin, os.path.basename(sys.executable))
    subprocess.call([path_exe])
