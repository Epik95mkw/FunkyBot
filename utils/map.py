class Map:

    def __init__(self, keys: list, values: list[list]):
        self.mapping = []
        for t in values:
            d = dict(zip(keys, t))
            self.mapping.append(d)

    def __getitem__(self, i) -> dict:
        return self.mapping[i]

    def get(self, target) -> dict:
        for d in self.mapping:
            if target in d.values():
                return d
        raise KeyError('Target is not present in map.')

    def list(self, key) -> list:
        return [d[key] for d in self.mapping]
