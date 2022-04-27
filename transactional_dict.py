""" Make changes to dict in transaction with option to abort all of them or none

>>> test_values = {'1': 1, '2': 2, 'nested': {'1': 1}}
>>> d = TransactionalDict(test_values)

>>> d["1"] = "a"  # edit in transaction
>>> d["1"]
'a'

>>> d["3"] = 3  # new key in transaction
>>> d["3"]
3
>>> "3" in d
True

>>> del d["2"]  # delete key in transaction
>>> d["2"]
Traceback (most recent call last):
...
KeyError: 'Key 2 has been deleted in current transaction.'
>>> "2" in d
False

# items created and deleted in transaction are cleaned (not marked as a change)
>>> d["4"] = 4
>>> del d["4"]
>>> "4" in d._overlay
False

>>> d["nested"]["1"] = 2  # even nested dictionaries are transacted
>>> d["nested"]["1"]
2

# base mapping api works on TransactionalDict
>>> sorted(d.keys())
['1', '3', 'nested']
>>> sorted(d)
['1', '3', 'nested']

# changes introduced in transaction can be retrieved by diff
>>> d.diff() == {'1': (1, 'a'), '3': (Undefined, 3), '2': (2, Undefined), 'nested': {'1': (1, 2)}}
True

>>> test_values == {'1': 1, '2': 2, 'nested': {'1': 1}}  # changed still not reflected
True

>>> d.commit() == {'1': 'a', 'nested': {'1': 2}, '3': 3}  # returns the underlying changes dict
True
>>> test_values == {'1': 'a', 'nested': {'1': 2}, '3': 3}  # changes are reflected now
True


>>> test_values = {'1': 1, '2': 2, 'nested': {'1': 1}}
>>> d = TransactionalDict(test_values)

>>> d["1"] = "a"
>>> d["3"] = 3
>>> del d["2"]
>>> d["nested"]["1"] = 2

>>> d.abort() == {'1': 1, '2': 2, 'nested': {'1': 1}}
True
>>> test_values == {'1': 1, '2': 2, 'nested': {'1': 1}}
True
"""

from itertools import chain
from contextlib import contextmanager


class Undefined:
    "represent deleted value in overly"


class TransactionalDict:
    "Keep track of changes but do not change underlying dict before commit is inferred."

    def __init__(self, original: dict):
        self._original = original
        self._overlay = {}

    def commit(self) -> dict:
        "commit changes to underlying dict"
        for key, value in self._overlay.items():
            if isinstance(value, TransactionalDict):
                self._original[key] = value.commit()
            elif value is Undefined:
                del self._original[key]
            else:
                self._original[key] = value
        self._overlay = {}
        return self._original

    def abort(self) -> dict:
        "abort changes introduced so far"
        for key, value in self._overlay.items():
            if isinstance(value, TransactionalDict):
                value.abort()
        self._overlay = {}
        return self._original

    def diff(self):
        "return changes introduced so far"
        diff = {}
        for key, value in self._overlay.items():
            if isinstance(value, TransactionalDict):
                diff[key] = value.diff()
            else:
                diff[key] = (self._original.get(key, Undefined), self._overlay.get(key, Undefined))
        return diff

    def __len__(self):
        return len(self.__iter__())

    def __getitem__(self, key):
        if key in self._overlay:
            item = self._overlay[key]
            if item is Undefined:
                raise KeyError(f"Key {key} has been deleted in current transaction.")
        else:
            item = self._original[key]
            if isinstance(item, dict) and not isinstance(item, TransactionalDict):
                item = TransactionalDict(item)
            self._overlay[key] = item
        return item

    def __setitem__(self, key, value):
        self._overlay[key] = value

    def __delitem__(self, key):
        if key in self._original:
            self._overlay[key] = Undefined
        elif key in self._overlay:
            del self._overlay[key]
        else:
            raise KeyError("Key {key} not in original dict nor in transaction.")

    def __missing__(self, key):
        return key not in self

    def __iter__(self):
        return iter(self.__keys())

    def keys(self):
        return list(self.__keys())

    def __keys(self):
        return {
            key for key in chain(self._original.keys(), self._overlay.keys())
            if self._overlay.get(key, None) is not Undefined
        }

    def __reversed__(self):
        return super().__reversed__()

    def __contains__(self, key):
        return (key not in self._overlay or self._overlay[key] is not Undefined) \
                and (key in self._original or key in self._overlay)


@contextmanager
def transaction(original_dict):
    """ manage transaction as context
    >>> data = {1: 1}
    >>> with transaction(data) as rw:
    ...   rw[1] = "a"
    ...   rw[1]
    ...   data[1]
    'a'
    1

    >>> data[1]  # data are commited on context exit
    'a'

    >>> # exception aborts transaction leaving data unchanged
    >>> data = {1: 1}
    >>> with transaction(data) as rw:
    ...   rw[1] = "a"
    ...   raise Exception()
    Traceback (most recent call last):
    ...
    Exception
    >>> data
    {1: 1}


    """
    assert isinstance(original_dict, dict)
    try:
        transactional_dict = TransactionalDict(original_dict)
        yield transactional_dict
        transactional_dict.commit()
    except Exception:
        transactional_dict.abort()
        raise


if __name__ == "__main__":

    import doctest
    doctest.testmod()
