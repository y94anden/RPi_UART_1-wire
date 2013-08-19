def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    reverse = dict((value, key) for key, value in enums.items())
    keys = [key for key, value in enums.items()]
    values = [enums[key] for key in keys]
    enums['__reverse_mapping__'] = reverse
    enums['__keys__'] = keys
    enums['__values__'] = values
    return type('Enum', (), enums)
