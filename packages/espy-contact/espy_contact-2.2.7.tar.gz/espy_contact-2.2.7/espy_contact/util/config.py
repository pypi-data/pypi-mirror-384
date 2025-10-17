from threading import local

class Config(local):
    def __init__(self):
        self.schema = "campus"

config = Config()

def get_current_schema():
    return config.schema

def set_current_schema(schema):
    config.schema = schema