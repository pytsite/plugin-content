"""PytSite Content Plugin Widgets
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang as _lang
from plugins import widget as _widget, odm as _odm, odm_auth as _odm_auth, http_api as _http_api
from . import _model, _api


class ModelSelect(_widget.select.Select):
    """Content Model Select
    """

    def __init__(self, uid: str, **kwargs):
        self._check_perms = kwargs.get('check_perms', True)

        items = []
        for k, v in _api.get_models().items():
            if self._check_perms:
                if _odm_auth.check_permission('view', k) or _odm_auth.check_permission('view_own', k):
                    items.append((k, _lang.t(v[1])))
            else:
                items.append((k, _lang.t(v[1])))

        super().__init__(uid, items=sorted(items, key=lambda x: x[1]), **kwargs)


class ModelCheckboxes(_widget.select.Checkboxes):
    """Content Model Checkboxes
    """

    def __init__(self, uid: str, **kwargs):
        self._check_perms = kwargs.get('check_perms', True)

        items = []
        for k, v in _api.get_models().items():
            if self._check_perms:
                if _odm_auth.check_permission('view', k) or _odm_auth.check_permission('view_own', k):
                    items.append((k, _lang.t(v[1])))
            else:
                items.append((k, _lang.t(v[1])))

        super().__init__(uid, items=sorted(items, key=lambda x: x[1]), **kwargs)


class StatusSelect(_widget.select.Select):
    """Content Status Select
    """

    def __init__(self, uid: str, **kwargs):
        super().__init__(uid, items=_api.get_statuses(), **kwargs)


class EntitySelect(_widget.select.Select2):
    """Entity Select
    """

    def __init__(self, uid: str, **kwargs):
        kwargs['ajax_url'] = _http_api.url('content@get_widget_entity_select_search', {
            'model': kwargs.get('model'),
            'language': kwargs.get('language', _lang.get_current())
        })

        super().__init__(uid, **kwargs)

    def set_val(self, value):
        if isinstance(value, str) and not value:
            value = None
        elif isinstance(value, _model.Content):
            value = value.model + ':' + str(value.id)

        return super().set_val(value)

    def _get_element(self, **kwargs):
        # In AJAX-mode Select2 doesn't contain any items,
        # but if we have selected item, it is necessary to append it
        if self._ajax_url and self._value:
            self._items.append((self._value, _odm.get_by_ref(self._value).f_get('title')))

        return super()._get_element()
