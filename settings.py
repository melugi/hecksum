import os

DEBUG = bool(os.environ.get('DEBUG', False))
IGNORED_EXCEPTIONS = () if DEBUG else (Exception,)
