import ast
import inspect

from .helper_functions import Helper


class InterfaceMeta(type):
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)
        cls._is_interface_ = getattr(cls, "_is_interface_", None)
        cls._interface_contracts_ = {}
        
        annotations = namespace.get('__annotations__', {})
        for ann_attr, _ in annotations.items():
            if ann_attr not in namespace:
                cls._interface_contracts_[ann_attr] = "field"
        
        return cls

    def __call__(cls, *args, **kwargs):
        if getattr(cls, "_is_interface_", False):
            raise TypeError(f"Cannot instantiate interface class '{cls.__name__}'")
        return super().__call__(*args, **kwargs)
    

    def __validate__(cls):
        if cls._is_interface_ is None:
            raise TypeError("Class must be decorated with @interface or @concrete")

        MAGIC_INCLUDE = {
            "__init__", "__add__", "__sub__", "__mul__", "__truediv__", "__len__",
            "__getitem__", "__setitem__", "__iter__", "__next__", "__str__", "__repr__",
            "__contains__", "__eq__", "__lt__", "__le__", "__gt__", "__ge__", "__hash__"
        }

        if cls._is_interface_:
            # enforce interface contracts
            # TODO (PERFORMANCE): use itertools.chain to lazy load the iterable
            all_attrs = list(vars(cls).items()) + [(attr, None) for attr in cls.__annotations__ if attr not in cls.__dict__]
            for attr, value in all_attrs:
                if attr in ("__annotations__", "_is_interface_", "_interface_contracts_"):
                    continue
                if attr.startswith("__") and attr.endswith("__") and attr not in MAGIC_INCLUDE:
                    continue

                # ---- METHODS ----
                if inspect.isfunction(value):
                    if not Helper.is_empty_function(value):
                        raise TypeError(
                            f"Method '{attr}' in interface '{cls.__name__}' must have empty body."
                        )
                    sig = inspect.signature(value)
                    cls._interface_contracts_[attr] = ("method", sig, "function")
                    continue

                if isinstance(value, staticmethod):
                    fn = value.__func__
                    if not Helper.is_empty_function(fn):
                        raise TypeError(
                            f"Static method '{attr}' in interface '{cls.__name__}' must have empty body."
                        )
                    sig = inspect.signature(fn)
                    cls._interface_contracts_[attr] = ("method", sig, "staticmethod")
                    continue

                if isinstance(value, classmethod):
                    fn = value.__func__
                    if not Helper.is_empty_function(fn):
                        raise TypeError(
                            f"Class method '{attr}' in interface '{cls.__name__}' must have empty body."
                        )
                    sig = inspect.signature(fn)
                    cls._interface_contracts_[attr] = ("method", sig, "classmethod")
                    continue

                # ---- PROPERTY ----
                if isinstance(value, property):
                    prop_obj = cls.__dict__.get(attr, None)
                    if not isinstance(prop_obj, property):
                        raise TypeError(
                            f"In interface '{cls.__name__}', attribute '{attr}' must be declared as a property."
                        )

                    errors: list[str] = []

                    source_text = None
                    try:
                        source_text = inspect.getsource(cls)
                    except (OSError, TypeError):
                        source_text = None

                    getter_declared_explicitly = False
                    nonempty_property_getter = False

                    if source_text is not None:
                        try:
                            parsed = ast.parse(source_text)
                        except SyntaxError:
                            parsed = None

                        if parsed is not None:
                            for node in ast.walk(parsed):
                                if isinstance(node, ast.ClassDef) and node.name == cls.__name__:
                                    for sub in node.body:
                                        if isinstance(sub, ast.FunctionDef) and sub.name == attr:
                                            for dec in sub.decorator_list:
                                                if isinstance(dec, ast.Name) and dec.id == "property":
                                                    # property found — check body emptiness
                                                    if not Helper.is_ast_function_empty(sub):
                                                        nonempty_property_getter = True
                                                    break
                                                if isinstance(dec, ast.Attribute) and dec.attr == "getter":
                                                    val = dec.value
                                                    if isinstance(val, ast.Name) and val.id == attr:
                                                        getter_declared_explicitly = True
                                                        break
                                        if getter_declared_explicitly:
                                            break
                                    if getter_declared_explicitly or nonempty_property_getter:
                                        break

                    if getter_declared_explicitly or nonempty_property_getter:
                        errors.append(
                            f"In interface '{cls.__name__}', property '{attr}' must not define a getter."
                        )

                    if getattr(prop_obj, "fset", None) is not None:
                        errors.append(
                            f"In interface '{cls.__name__}', property '{attr}' must not define a setter."
                        )

                    if getattr(prop_obj, "fdel", None) is not None:
                        errors.append(
                            f"In interface '{cls.__name__}', property '{attr}' must not define a deleter."
                        )

                    if errors:
                        raise TypeError("\n".join(errors))

                    cls._interface_contracts_[attr] = ("property", None, None)
                    continue
                
                # ---- FIELD PLACEHOLDER ----
                ann = cls.__annotations__.get(attr) if hasattr(cls, "__annotations__") else None
                if ann is not None:
                    cls._interface_contracts_[attr] = ("field", None, None)
                    continue

                if value is Ellipsis:
                    cls._interface_contracts_[attr] = ("field", None, None)
                    continue

                if isinstance(value, type):
                    continue

                raise TypeError(
                    f"Attribute '{attr}' in interface '{cls.__name__}' should not have a concrete value."
                )

            # inherit contracts from parents
            for base in cls.__mro__[1:]:
                if hasattr(base, "_interface_contracts_"):
                    cls._interface_contracts_.update(base._interface_contracts_)

        else:
            # enforce concrete implementation
            contracts: dict[str, tuple] = {}
            for base in cls.__mro__[1:]:
                if hasattr(base, "_interface_contracts_"):
                    contracts.update(base._interface_contracts_)

            missing = []
            signature_mismatches = []

            # determine whether any interface in mro explicitly declared __init__
            explicit_init_in_interfaces = any(
                "__init__" in getattr(base, "_interface_contracts_", {})
                for base in cls.__mro__[1:]
                if getattr(base, "_is_interface_", False)
            )

            for name, info in contracts.items():
                kind = info[0]
                if kind == "method":
                    expected_sig = info[1]
                    expected_type = info[2]
                    
                    # first check in the concrete class itself
                    impl = cls.__dict__.get(name, None)

                    # if not in concrete class, search bases but IGNORE implementations that live on INTERFACE bases
                    source_cls_of_impl = None
                    if impl is None:
                        for base in cls.__mro__[1:]:
                            candidate = base.__dict__.get(name)
                            if candidate is None:
                                continue
                            # skip candidate if it comes from an interface — interface placeholders are NOT implementations
                            if getattr(base, "_is_interface_", False):
                                # keep searching; this indicates the name is declared on an interface, not implemented
                                continue
                            # candidate comes from a non-interface base => treat as an implementation
                            impl = candidate
                            source_cls_of_impl = base
                            break

                    # if still not found, it's missing
                    if impl is None:
                        missing.append(name)
                        continue
                    
                    # determine actual type and underlying function (if any)
                    actual_type = None
                    if isinstance(impl, staticmethod):
                        actual_type = "staticmethod"
                        func = impl.__func__
                    elif isinstance(impl, classmethod):
                        actual_type = "classmethod"
                        func = impl.__func__
                    elif isinstance(impl, property):
                        actual_type = "property"
                        func = None
                    elif inspect.isfunction(impl):
                        actual_type = "function"
                        func = impl
                    else:
                        # fallback: callable objects (decorated or descriptors stored at class level)
                        if callable(impl):
                            actual_type = "function"
                            func = impl
                        else:
                            actual_type = "field"
                            func = None

                    # enforce type equality if expected_type is provided
                    if expected_type is not None and actual_type != expected_type:
                        signature_mismatches.append((name, expected_type, actual_type))
                        continue

                    try:
                        impl_sig = inspect.signature(func) if func is not None else None
                    except (ValueError, TypeError):
                        # fallback for unusual or C-level callables without valid signature
                        impl_sig = None
                        
                    if expected_sig is not None:
                        if name == "__init__":
                            # if the concrete inherited a generic init (e.g., object.__init__ with *args/**kwargs)
                            # treat it as missing (not a signature mismatch)
                            if impl_sig is not None:
                                meaningful = [
                                    p for p in impl_sig.parameters.values()
                                    if p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
                                ]
                                # if only 'self' or no meaningful parameters => consider as not implemented
                                if len(meaningful) <= 1:
                                    missing.append(name)
                                    continue

                            # finally compare signatures
                            if impl_sig is None or impl_sig.parameters.keys() != expected_sig.parameters.keys():
                                signature_mismatches.append((name, expected_sig, impl_sig))
                        else:
                            # general methods
                            if impl_sig is None:
                                signature_mismatches.append((name, expected_sig, impl_sig))
                                continue
                            if impl_sig.parameters.keys() != expected_sig.parameters.keys():
                                signature_mismatches.append(
                                    (name, expected_sig, impl_sig)
                                )
                            
                elif kind == "field":
                    if not hasattr(cls, name):
                        missing.append(name)
                    else:
                        val = getattr(cls, name)
                        if val is Ellipsis:
                            missing.append(name)
                            continue
                        
                        impl = cls.__dict__.get(name, None)
                        if inspect.isfunction(impl) or isinstance(impl, (property, staticmethod, classmethod)):
                            raise TypeError(
                                f"Contract violation for '{name}' in '{cls.__name__}': expected a field, got {type(impl).__name__}."
                            )
                            
                elif kind == "property":
                    impl = cls.__dict__.get(name, None)
                    if impl is None:
                        missing.append(name)
                        continue
                    
                    if isinstance(impl, property):
                        continue  # ok
                    
                    # match static/class methods or normal funcs
                    if inspect.isfunction(impl):
                        raise TypeError(
                            f"Signature mismatch for '{name}' in concrete '{cls.__name__}': expected property, got function."
                        )
                    if isinstance(impl, staticmethod):
                        raise TypeError(
                            f"Signature mismatch for '{name}' in concrete '{cls.__name__}': expected property, got staticmethod."
                        )
                    if isinstance(impl, classmethod):
                        raise TypeError(
                            f"Signature mismatch for '{name}' in concrete '{cls.__name__}': expected property, got classmethod."
                        )

                    # everything else treated as field
                    raise TypeError(
                        f"Signature mismatch for '{name}' in concrete '{cls.__name__}': expected property, got field."
                    )

            if missing or signature_mismatches:
                parts: list[str] = []
                if missing:
                    parts.append(f"Concrete class '{cls.__name__}' must implement contracts: {', '.join(sorted(missing))}")
                if signature_mismatches:
                    for nm, exp, got in signature_mismatches:
                        parts.append(f"Signature mismatch for '{nm}' in concrete '{cls.__name__}': expected {exp}, got {got}.")
                
                raise TypeError("\n".join(parts))
