import subprocess
import time


class RedisRunnerContext(object):

    def __init__(self, port=6379):
        self.port = port  # NOT implemented yet

    def __enter__(self):
        self.process = subprocess.Popen(["redis-server", "--save", "\"\"", "--appendonly", "no"])
        time.sleep(0.5)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.process.terminate()
        time.sleep(0.5)
