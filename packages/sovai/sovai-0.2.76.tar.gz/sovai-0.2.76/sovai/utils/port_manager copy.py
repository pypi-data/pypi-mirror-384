import random
from functools import lru_cache

class PortManager:
    def __init__(self):
        self.app_ports = {}
        self.min_port = 8050
        self.max_port = 8099

    def get_unique_port(self, app_name):
        if app_name in self.app_ports:
            return self.app_ports[app_name]
        else:
            while True:
                port = random.randint(self.min_port, self.max_port)
                if port not in self.app_ports.values():
                    self.app_ports[app_name] = port
                    return port

@lru_cache(maxsize=None)
def get_port_manager():
    return PortManager()

def get_unique_port(app_name):
    return get_port_manager().get_unique_port(app_name)
