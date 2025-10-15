import os


def get_pkg_path(path):
    path_dist = os.path.join(path, 'dist')
    path_pkg = os.path.join(path_dist, next(x for x in os.listdir(path_dist) if x.endswith('.whl')))
    return path_pkg
