import yaml
import os

AUTH_FILE_PATH = '~/.keta/config.yaml'


def list_clusters():
    config_dir = os.path.expanduser('~/.keta')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
        return conf


def set_default_cluster(name):
    config_dir = os.path.expanduser('~/.keta')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'config.yaml')
    with open(config_path, 'r+', encoding='utf-8') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
        for item in conf:
            if name == item['name']:
                item['default'] = True
            else:
                item['default'] = False
        f.seek(0)
        f.truncate()
        f.write(yaml.dump(conf, default_flow_style=False))
        return conf


def delete_cluster(name):
    config_dir = os.path.expanduser('~/.keta')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'config.yaml')
    with open(config_path, 'r+', encoding='utf-8') as f:
        conf = yaml.safe_load(f)
        need_delete_index = None
        for i in range(len(conf)):
            if name == conf[i]['name']:
                need_delete_index = i
        if need_delete_index is not None:
            del conf[need_delete_index]
        f.seek(0)
        f.truncate()
        f.write(yaml.dump(conf, default_flow_style=False))
        return conf


def get_current_cluster():
    config_dir = os.path.expanduser('~/.keta')
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
        for item in conf:
            if item['default']:
                return item
    return {}
