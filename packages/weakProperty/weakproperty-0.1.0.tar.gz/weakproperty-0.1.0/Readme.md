# weakProperty

just a property, but it automatically got weakref

source code :
```python
def weakProperty(func):
    attr_name = f"_weak_{func.__name__}"
    @property
    def wrapper(self):
        ref = getattr(self, attr_name, None)
        return None if ref is None else ref()

    @wrapper.setter
    def wrapper(self, value):
        if value is None:
            setattr(self, attr_name, None)
        else:
            setattr(self, attr_name, weakref.ref(value))

    @wrapper.deleter
    def wrapper(self):
        setattr(self, attr_name, None)

    return wrapper
```
## usage
same as `@property`