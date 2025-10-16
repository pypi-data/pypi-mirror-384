import os
import importlib

pkg = os.environ.get("BOT_NAME")
factory = os.environ.get("APP_FACTORY", "create_app")

if not pkg:
    raise RuntimeError("Set BOT_NAME to your child package name")

mod = importlib.import_module(pkg)
create_app = getattr(mod, factory, None)

if not callable(create_app):
    raise RuntimeError(f"{pkg}.{factory}() not found")

app = create_app()
