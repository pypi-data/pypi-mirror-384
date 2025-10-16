class JsonObject:
    """Convert a dict['element'] for access like object.property."""

    def __init__(self, json: dict):
        for k, v in json.items():
            setattr(self, k, v)
