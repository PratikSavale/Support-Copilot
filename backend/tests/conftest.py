import httpx

# Monkeypatch httpx.Client.__init__ to fix incompatibility with older Starlette versions
original_init = httpx.Client.__init__

def custom_init(self, *args, **kwargs):
    kwargs.pop('app', None)
    kwargs.pop('backend', None)
    kwargs.pop('backend_options', None)
    original_init(self, *args, **kwargs)

httpx.Client.__init__ = custom_init
