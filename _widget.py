"""PytSite Content Plugin Widgets
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang as _lang
from plugins import widget as _widget, odm_ui as _odm_ui, auth as _auth
from . import _api


class ModelSelect(_widget.select.Select):
    """Content Model Select
    """

    def __init__(self, uid: str, **kwargs):
        items = []
        for k, v in _api.get_models().items():
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
        model = kwargs.get('model')
        if not model:
            raise ValueError('Model is not specified')

        if not 'items' in kwargs:
            cls = _api.get_model_class(model)
            statuses = cls.content_statuses()
            if 'waiting' in statuses and not _auth.get_current_user().has_permission(
                    'content@bypass_moderation.' + model):
                statuses.remove('waiting')

            kwargs['items'] = [(s, cls.t('content_status_{}'.format(s))) for s in statuses]

        super().__init__(uid, **kwargs)


class EntitySelect(_odm_ui.widget.EntitySelect):
    def __init__(self, uid: str, **kwargs):
        kwargs.setdefault('model', list(_api.get_models().keys()))
        kwargs.setdefault('sort_by', 'title')

        super().__init__(uid, **kwargs)
