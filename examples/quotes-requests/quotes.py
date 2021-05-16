import greenletio

# import the application with blocking functions monkey patched
with greenletio.patch_blocking():
    from quotes_app import app
