import yaml


def get_config(path=None):
    if path is None:
        path = "./config.yaml"
    config = yaml.safe_load(open(path))
    return config
