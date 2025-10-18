import os

class Cache:
    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self.entries = []
        self.saved = True
        
        if self.cache_file and os.path.isfile(self.cache_file):
            with open(self.cache_file, 'r') as f:
                self.entries = f.read().split('\n')

    def add(self, entry: str):
        if not self.has(entry):
            self.saved = False
            self.entries.append(entry)

    def has(self, entry: str):
        return entry in self.entries

    def save(self):
        if self.saved:
            return
        if not self.cache_file:
            return
        with open(self.cache_file, 'w') as f:
            f.write('\n'.join(self.entries))
        self.saved = True

    def __del__(self):
        self.save()
