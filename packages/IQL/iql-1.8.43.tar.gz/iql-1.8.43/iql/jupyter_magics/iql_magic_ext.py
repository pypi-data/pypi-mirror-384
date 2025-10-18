def load_ipython_extension(ip, enable_autocomplete: bool = True):
    """Defer imports for non-ipython environments"""
    from IPython.core.getipython import get_ipython

    from .autocompletion_v2 import init_completer
    from .iql_magic import IqlMagic

    ip = get_ipython()

    if enable_autocomplete:
        init_completer(ip)

    ip.register_magics(IqlMagic)  # type: ignore
