class InvalidAssocList(Exception):
    pass

def assoc(l, k):
    '''Looks up the given association list l for the given key k. Returns
    the associated value if found. Raises KeyError if not found or an
    InvalidAssocList if not a valid association list is given.

    '''

    if not isinstance(l, list):
        raise InvalidAssocList()

    if len(l) % 2 != 0:
        raise InvalidAssocList()

    for i in xrange(0, len(l), 2):
        if l[i] == k:
            return l[i+1]

    raise KeyError()
