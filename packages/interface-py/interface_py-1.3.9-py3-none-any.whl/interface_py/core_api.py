from .core import InterfaceMeta as _InterfaceMeta


class _InterfaceBase(metaclass=_InterfaceMeta):
    """Hidden base class for all interfaces (not exposed to the user)."""
    pass


def interface(cls):
    if _InterfaceBase not in cls.__mro__:
        cls = type(cls.__name__, (_InterfaceBase,) + cls.__bases__, dict(cls.__dict__))

    for base in cls.__bases__:
        if base is object or base is _InterfaceBase:
            continue
        if not getattr(base, "_is_interface_", False):
            raise TypeError(
                f"In interface '{cls.__name__}', all parents must be interfaces. Found non-interface parent '{base.__name__}'."
            )
    
    cls._is_interface_ = True
    cls.__validate__()
    return cls


def concrete(cls):
    has_interface_parent = any(getattr(base, "_is_interface_", False) for base in cls.__bases__)
    
    if not has_interface_parent:
        raise TypeError(
            f"Concrete class '{cls.__name__}' must inherit from at least one interface."
        )
    
    cls._is_interface_ = False
    cls.__validate__()
    return cls
