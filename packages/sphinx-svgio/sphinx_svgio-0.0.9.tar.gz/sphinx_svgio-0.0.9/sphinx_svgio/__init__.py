def setup(app) -> dict:
    from .list.setup import setup_svgio_list
    from .refs.setup import setup_refs
    from .svgio.setup import setup_svgio

    setup_svgio(app)
    setup_svgio_list(app)
    setup_refs(app)

    return {
        "version": "0.0.9",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
