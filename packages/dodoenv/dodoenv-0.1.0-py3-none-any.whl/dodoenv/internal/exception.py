class EnvNotFoundException(Exception):
    def __init__(self, env_name:str):
        self.env_name = env_name

    def __str__(self):
        return f"EnvNotFound Exception : {self.env_name} is not found."