def public(func):
    setattr(func, 'public', True)
    return func

def direct(func):
    setattr(func, 'direct', True)
    return func