# flake8: noqa: E721
from typing import Optional


def is_set(v) -> bool:
    return v is not None


def add(keys, left, right):
    if type(left) != type(right):
        raise TypeError(f'unsupported operand type(s) for +: '
                        f'{type(left)} and {type(right)}')
    kwargs = {}
    for key in keys:
        # add dicts and stats objects
        if isinstance(left, dict):
            left_value = left.get(key)
            right_value = right.get(key)
        else:
            left_value = getattr(left, key, None)
            right_value = getattr(right, key, None)
        if is_set(left_value) ^ is_set(right_value):
            kwargs[key] = left_value or right_value
        elif is_set(left_value) and is_set(right_value):
            if type(left_value) != type(right_value):
                raise TypeError(
                    f'unsupported operand type(s) for +: '
                    f'{type(left_value)} and {type(right_value)}')
            if hasattr(type(left_value), '__add__'):
                kwargs[key] = left_value + right_value
            elif isinstance(left_value, dict):
                kwargs[key] = add({*left_value, *right_value},
                                  left_value, right_value)
            elif isinstance(left_value, set):
                kwargs[key] = left_value | right_value
    return type(left)(**kwargs)


class StatsMeta(type):
    def __new__(cls, name, bases, namespace, **kwds):
        # forcing to use slots on Stats classes
        if '__slots__' not in namespace:
            namespace['__slots__'] = ()
        for base in bases:
            if hasattr(base, '__slots__'):
                namespace['__slots__'] += base.__slots__
        return type.__new__(cls, name, bases, namespace, **kwds)


class Stats(metaclass=StatsMeta):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def package(self) -> str:
        raise NotImplementedError

    @property
    def service(self) -> Optional[str]:
        return None

    def __add__(self, other: 'Stats'):
        return add(self.__slots__, self, other)

    def __radd__(self, other: 'Stats'):
        return self.__add__(other)

    def to_dict(self) -> dict:
        result = {}
        for k in self.__slots__:
            v = getattr(self, k, None)
            if v is None:
                # there is no use to dump unset or empty attrs. Omitting
                continue
            result[k] = v
        return result
