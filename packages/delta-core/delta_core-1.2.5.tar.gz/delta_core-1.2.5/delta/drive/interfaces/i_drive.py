import abc


class IDrive(abc.ABC):

    def __init__(self):
        pass

    def clone(self, url: str, path_to_save: str = '.'):
        raise NotImplementedError()

    def init(self, path_to_save: str):
        raise NotImplementedError()

    def status(self):
        raise NotImplementedError()

    def tag(self, **kwargs):
        raise NotImplementedError()

    def commit(self, message: str):
        raise NotImplementedError()

    def pull(self, origin_name: str):
        raise NotImplementedError()

    def push(self, **kwargs):
        raise NotImplementedError()

    def branch(self, **kwargs):
        raise NotImplementedError()

    def checkout(self, branch_name: str):
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()

    def add_dependency(self):
        raise NotImplementedError()

    def add_resource(self, **kwargs):
        raise NotImplementedError()

    def check(self):
        raise NotImplementedError()

    def fetch(self, origin_name: str):
        raise NotImplementedError()

    def sync(self):
        raise NotImplementedError()
