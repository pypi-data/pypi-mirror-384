import os
import configparser
from urllib.parse import urlparse


class PipConf(object):
    CONF_FILE = os.path.join(os.path.expanduser('~'),
                             *(['pip', 'pip.ini'] if os.name == 'nt' else ['.pip', 'pip.conf']))
    CONF_KEYS = ['index-url', 'extra-index-url', 'trusted-host']

    def __init__(self, conf_file=None):
        if conf_file is None:
            self.conf_file = self.CONF_FILE
        else:
            self.conf_file = conf_file

        self.conf = configparser.ConfigParser()

        if os.path.exists(self.conf_file):
            self.conf.read(self.conf_file)

        self._create_global()

        self.data = self._conf2dict()

    def set_index_url(self, url, username=None, password=None):
        url = self._attach_auth(url, username, password)
        self.data[self.CONF_KEYS[0]] = [url]
        self._reset_trusted_host()
        self.save()

    def add_extra_url(self, url, username=None, password=None):
        url = self._attach_auth(url, username, password)
        self.data[self.CONF_KEYS[1]] = list({url, *self.data.get(self.CONF_KEYS[1], [])})
        self._reset_trusted_host()
        self.save()

    def remove_extra_url(self, url):
        new_lst = []
        new_lst_trusted = []
        old_lst = self.data.get(self.CONF_KEYS[1], [])
        pr = urlparse(url)
        for x in old_lst:
            pr_ = urlparse(x)
            if pr_.hostname != pr.hostname or pr_.path != pr.path:
                new_lst.append(x)
                new_lst_trusted.append(pr_.hostname)
        if new_lst:
            self.data[self.CONF_KEYS[1]] = new_lst
        else:
            self.data.pop(self.CONF_KEYS[1], None)
        self._reset_trusted_host()
        self.save()
        return len(new_lst) != len(old_lst)

    def clear_extra_url(self):
        self.data.pop(self.CONF_KEYS[1], None)
        self._reset_trusted_host()
        self.save()

    def _reset_trusted_host(self):
        self.data[self.CONF_KEYS[-1]] = list({urlparse(url).hostname for url in
                                              self.data.get(self.CONF_KEYS[0], []) + self.data.get(self.CONF_KEYS[1],
                                                                                                   [])})

    def _create_global(self):
        if not self.conf.has_section('global'):
            self.conf.add_section('global')

    def _reset_conf(self):
        if self.conf.has_section('global'):
            self.conf.remove_section('global')
        self._create_global()

    def _attach_auth(self, url, username, password):
        if username and password:
            pr = urlparse(url)
            return f'{pr.scheme}://{username}:{password}@{pr.hostname}:{pr.port}{pr.path}'
        return url

    def _conf2dict(self):
        data = {}
        for key in self.CONF_KEYS:
            value = self.conf.get('global', key, fallback=None)
            if value is not None:
                data[key] = [x.strip() for x in value.split('\n') if x.strip()]
        return data

    def _dict2conf(self, data):
        self._reset_conf()
        for key in self.CONF_KEYS:
            if key in data:
                self.conf.set('global', key, '\n\t'.join(data[key]))

    def save(self):
        self._dict2conf(self.data)
        dir_name = os.path.dirname(self.conf_file)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        with open(self.conf_file, 'w') as configfile:
            self.conf.write(configfile)
