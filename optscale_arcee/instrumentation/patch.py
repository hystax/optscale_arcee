import functools
import inspect
import logging
from collections import defaultdict
from typing import Callable

import gorilla

APPLIED_PATCHES = defaultdict(set)
LOG = logging.getLogger(__name__)


class PatcherSettings(gorilla.Settings):
    def __hash__(self):
        return hash(tuple(sorted(iter(self.__dict__.items()))))


class GorillaPatch(gorilla.Patch):
    def __hash__(self):
        # patches of same objects will be different because of wrappers
        # objects nature. Will have to exclude 'obj' attr from hash calculation
        # to get rid of this
        return hash(tuple(sorted(iter(self.__dict__.items()))))

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.__hash__() == other.__hash__()

        return NotImplemented


def update_wrapper(wrapper, wrapped):
    updated_wrapper = functools.update_wrapper(wrapper, wrapped)
    try:
        # TODO: check if required
        updated_wrapper.__signature__ = inspect.signature(wrapped)
    except Exception:
        LOG.error("Failed to set %s signature to wrapper", wrapper, wrapped)
    return updated_wrapper


def _create_patch(
        destination: object, name: str, patch_obj: object
) -> GorillaPatch:
    gorilla_patch = GorillaPatch(
        destination, name,
        patch_obj,
        settings=PatcherSettings(allow_hit=True, store_hit=True)
    )
    return gorilla_patch


def _apply_patch(component: str, gorilla_patch: GorillaPatch):
    gorilla.apply(gorilla_patch)
    APPLIED_PATCHES[component].add(gorilla_patch)


def patch(
        package: str, service: str, destination: object, name: str,
        patch_func: Callable, is_package_patch=False, is_service_patch=False):
    original_func = gorilla.get_attribute(destination, name)
    if is_package_patch:
        def wrapper(*args, **kwargs):
            return patch_func(package, original_func, *args, **kwargs)
    elif is_service_patch:
        def wrapper(*args, **kwargs):
            return patch_func(service, original_func, *args, **kwargs)
    else:
        def wrapper(*args, **kwargs):
            return patch_func(original_func, *args, **kwargs)

    wrapped_func = update_wrapper(wrapper, original_func)

    gorilla_patch = _create_patch(destination, name, wrapped_func)
    _apply_patch(service or package, gorilla_patch)


def revert_patches(component: str):
    for gorilla_patch in APPLIED_PATCHES.pop(component, []):
        gorilla.revert(gorilla_patch)
