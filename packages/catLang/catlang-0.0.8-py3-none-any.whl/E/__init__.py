from .E import exc, exec_file, transpile

# Backward compatibility: allow catLang.exec(...) to work
exec = exc

__all__ = ["exc", "exec_file", "transpile", "exec"]