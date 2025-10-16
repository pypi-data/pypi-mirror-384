from mfire.composite.base import BaseModel


class Factory(BaseModel):
    factories: dict = {}

    def __init__(self, **kwargs):
        factories, no_factories = kwargs.pop("factories", {}), {}
        for key, val in kwargs.items():
            if key.endswith("_factory"):
                factories[key] = val
            else:
                no_factories[key] = val
        super().__init__(factories=factories, **no_factories)

    def __getattribute__(self, item):
        if not item.startswith("__"):
            factories = object.__getattribute__(self, "factories")
            if (key := f"{item}_factory") in factories:
                return factories[key]
        return super().__getattribute__(item)

    def __setattr__(self, key, value):
        if not key.endswith("_factory"):
            super().__setattr__(key, value)
        else:
            factories = object.__getattribute__(self, "factories")
            factories[key] = value
