"""PytSite Content Plugin Widgets
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang as _lang
from plugins import widget as _widget, odm_auth as _odm_auth
from . import _api


class ModelSelect(_widget.select.Select):
    """Content Model Select
    """

    def __init__(self, uid: str, **kwargs):
        self._check_perms = kwargs.get('check_perms', True)

        items = []
        for k, v in _api.get_models().items():
            if self._check_perms:
                if _odm_auth.check_permission('view', k):
                    items.append((k, _lang.t(v[1])))
            else:
                items.append((k, _lang.t(v[1])))

        super().__init__(uid, items=sorted(items, key=lambda x: x[1]), **kwargs)


class ModelCheckboxes(_widget.select.Checkboxes):
    """Content Model Checkboxes
    """

    def __init__(self, uid: str, **kwargs):
        self._check_perms = kwargs.get('check_perms', True)
        self._filter = kwargs.get('filter')

        items = []
        for model, info in _api.get_models().items():
            if self._check_perms:
                if _odm_auth.check_permission('view', model):
                    items.append((model, _lang.t(info[1])))
            else:
                items.append((model, _lang.t(info[1])))

        items = sorted(items, key=lambda x: x[1])

        if callable(self._filter):
            filtered_items = []
            for item in items:
                if self._filter(_api.dispense(item[0])):
                    filtered_items.append(item)
            items = filtered_items

        super().__init__(uid, items=items, **kwargs)


class StatusSelect(_widget.select.Select):
    """Content Status Select
    """

    def __init__(self, uid: str, **kwargs):
        super().__init__(uid, items=_api.get_statuses(), **kwargs)
