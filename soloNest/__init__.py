# Compatibility patch for Django 4.2 running on Python 3.14+
try:
    from django.template.context import BaseContext
    def _basecontext_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate
    BaseContext.__copy__ = _basecontext_copy
except Exception:
    pass
