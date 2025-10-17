import lazy_loader as lazy

__getattr__, __dir__, __all__ = lazy.attach(
    __name__,
    submod_attrs={
        "file": ["load_file"],
        "group": ["load_groups"],
    },
)
