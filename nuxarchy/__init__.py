"""
NUXARCHY: Linux-Native Gaming Hub
"""

__version__ = "2.0.0"

def main():
    from nuxarchy.main import main as _main
    return _main()

__all__ = ["main", "__version__"]
