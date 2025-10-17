from navdict.navdict import NavDict


class ChangeTracker:
    """Tracks whether any changes have been made"""

    def __init__(self):
        self._changed = False

    def mark_changed(self):
        self._changed = True

    def reset(self):
        self._changed = False

    @property
    def changed(self):
        return self._changed


class MutableProxy:
    """
    A proxy that wraps mutable objects (lists, dicts, sets, etc.) and
    tracks when any mutating operation is performed on them.
    """

    # Methods that mutate the object (not exhaustive, but covers common cases)
    MUTATING_METHODS = {
        "list": {
            "append",
            "extend",
            "insert",
            "remove",
            "pop",
            "clear",
            "sort",
            "reverse",
            "__setitem__",
            "__delitem__",
            "__iadd__",
        },
        "dict": {"__setitem__", "__delitem__", "pop", "popitem", "clear", "update", "setdefault"},
        "set": {
            "add",
            "remove",
            "discard",
            "pop",
            "clear",
            "update",
            "intersection_update",
            "difference_update",
            "symmetric_difference_update",
            "__ior__",
            "__iand__",
            "__ixor__",
            "__isub__",
        },
    }

    def __init__(self, obj, tracker):
        """
        Args:
            obj: The object to wrap (list, dict, set, etc.)
            tracker: A ChangeTracker instance to notify on changes
        """
        # Use object.__setattr__ to avoid triggering our own __setattr__
        object.__setattr__(self, "_obj", obj)
        object.__setattr__(self, "_tracker", tracker)
        object.__setattr__(self, "_obj_type", type(obj).__name__)

    def __getattr__(self, name):
        """Intercept attribute access"""
        # Get the actual attribute from the wrapped object
        attr = getattr(self._obj, name)

        # If it's a method, wrap it
        if callable(attr):
            return self._wrap_method(name, attr)

        # If it's a mutable object, wrap it too (for nested structures)
        if isinstance(attr, (list, dict, set)):
            return MutableProxy(attr, self._tracker)

        return attr

    def _wrap_method(self, method_name, method):
        """Wrap a method to track changes"""

        def wrapper(*args, **kwargs):
            # Call the actual method
            result = method(*args, **kwargs)

            # Check if this method mutates the object
            mutating_methods = self.MUTATING_METHODS.get(self._obj_type, set())
            if method_name in mutating_methods:
                self._tracker.mark_changed()

            # If the result is mutable, wrap it too
            if isinstance(result, (list, dict, set)):
                return MutableProxy(result, self._tracker)

            return result

        return wrapper

    def __setattr__(self, name, value):
        """Intercept attribute setting"""
        if name.startswith("_"):
            # Internal attributes
            object.__setattr__(self, name, value)
        else:
            setattr(self._obj, name, value)
            self._tracker.mark_changed()

    def __setitem__(self, key, value):
        """Handle obj[key] = value"""
        self._obj[key] = value
        self._tracker.mark_changed()

    def __delitem__(self, key):
        """Handle del obj[key]"""
        del self._obj[key]
        self._tracker.mark_changed()

    def __getitem__(self, key):
        """Handle obj[key]"""
        result = self._obj[key]
        # Wrap mutable results
        if isinstance(result, (list, dict, set)):
            return MutableProxy(result, self._tracker)
        return result

    def __repr__(self):
        return f"MutableProxy({self._obj!r})"

    def __str__(self):
        return str(self._obj)

    def __len__(self):
        return len(self._obj)

    def __iter__(self):
        return iter(self._obj)

    def unwrap(self):
        """Get the original object"""
        return self._obj


class ChangeTrackingDict(NavDict):
    """
    A dictionary that tracks changes to itself and any mutable values
    stored within it (including nested structures).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, "_tracker", ChangeTracker())

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._tracker.mark_changed()

    def __delitem__(self, key):
        super().__delitem__(key)
        self._tracker.mark_changed()

    def __getitem__(self, key):
        value = super().__getitem__(key)

        # Wrap mutable values in a proxy
        if isinstance(value, (list, dict, set)):
            return MutableProxy(value, self._tracker)

        return value

    def get(self, key, default=None):
        """Override get() to also wrap mutable values"""
        if key in self:
            return self[key]
        return default

    @property
    def changed(self):
        """Check if the dictionary or any of its values have changed"""
        return self._tracker.changed

    def reset_tracking(self):
        """Reset the change tracking flag"""
        self._tracker.reset()

    # Override other mutating methods
    def pop(self, *args, **kwargs):
        result = super().pop(*args, **kwargs)
        self._tracker.mark_changed()
        return result

    def popitem(self):
        result = super().popitem()
        self._tracker.mark_changed()
        return result

    def clear(self):
        super().clear()
        self._tracker.mark_changed()

    def update(self, *args, **kwargs):
        super().update(*args, **kwargs)
        self._tracker.mark_changed()

    def setdefault(self, key, default=None):
        result = super().setdefault(key, default)
        self._tracker.mark_changed()
        return result


# ============================================================================
# EXAMPLES AND TESTS
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Change Tracking Dictionary with Proxy Pattern")
    print("=" * 60)

    # Example 1: Basic usage
    print("\n1. Basic dictionary operations:")
    d = ChangeTrackingDict()
    print(f"   Initial changed status: {d.changed}")

    d["name"] = "Alice"
    print(f"   After d['name'] = 'Alice': {d.changed}")

    d.reset_tracking()
    print(f"   After reset: {d.changed}")

    # Example 2: List mutations
    print("\n2. Tracking list mutations:")
    d = ChangeTrackingDict()
    d["items"] = [1, 2, 3]
    d.reset_tracking()

    print(f"   Initial: {d['items']}, changed: {d.changed}")

    d["items"].append(4)
    print(f"   After append(4): {d['items']}, changed: {d.changed}")

    d.reset_tracking()
    d["items"].extend([5, 6])
    print(f"   After extend([5,6]): {d['items']}, changed: {d.changed}")

    d.reset_tracking()
    d["items"][0] = 999
    print(f"   After [0] = 999: {d['items']}, changed: {d.changed}")

    # Example 3: Nested structures
    print("\n3. Tracking nested structures:")
    d = ChangeTrackingDict()
    d["data"] = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
    d.reset_tracking()

    print(f"   Initial changed: {d.changed}")

    d["data"]["users"].append({"name": "Charlie"})
    print(f"   After appending to nested list: {d.changed}")

    d.reset_tracking()
    d["data"]["count"] = 3
    print(f"   After adding to nested dict: {d.changed}")

    d.reset_tracking()
    d["data"]["users"][1]["name"] = "Bill"
    print(f"   After changing name in 'users' list: {d.changed}")

    # Example 4: Set operations
    print("\n4. Tracking set mutations:")
    d = ChangeTrackingDict()
    d["tags"] = {"python", "programming"}
    d.reset_tracking()

    print(f"   Initial: {d['tags']}, changed: {d.changed}")

    d["tags"].add("coding")
    print(f"   After add('coding'): {d['tags']}, changed: {d.changed}")

    d.reset_tracking()
    d["tags"].remove("coding")
    print(f"   After remove('coding'): {d['tags']}, changed: {d.changed}")

    # Example 5: Non-mutating operations don't trigger changes
    print("\n5. Non-mutating operations:")
    d = ChangeTrackingDict()
    d["items"] = [1, 2, 3, 4, 5]
    d.reset_tracking()

    print(f"   Initial changed: {d.changed}")

    length = len(d["items"])
    print(f"   After len(): changed = {d.changed}")

    for item in d["items"]:
        pass
    print(f"   After iteration: changed = {d.changed}")

    contains = 3 in d["items"]
    print(f"   After 'in' check: changed = {d.changed}")

    # Example 6: Complex nested manipulation
    print("\n6. Complex nested example:")
    d = ChangeTrackingDict()
    d["config"] = {"settings": {"theme": "dark", "plugins": ["linter", "formatter"]}}
    d.reset_tracking()

    print(f"   Initial changed: {d.changed}")
    d["config"]["settings"]["plugins"].append("debugger")
    print(f"   After deeply nested append: {d.changed}")
    print(f"   Final plugins: {d['config']['settings']['plugins']}")
