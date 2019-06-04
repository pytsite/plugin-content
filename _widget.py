"""PytSite Content Plugin Widgets
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang
from plugins import widget, odm_ui
from . import _api


class ModelSelect(widget.select.Select):
    """Content Model Select
    """

    def __init__(self, uid: str, **kwargs):
        items = []
        for k, v in _api.get_models().items():
            items.append((k, lang.t(v[1])))

        super().__init__(uid, items=sorted(items, key=lambda x: x[1]), **kwargs)


class ModelCheckboxes(widget.select.Checkboxes):
    """Content Model Checkboxes
    """

    def __init__(self, uid: str, **kwargs):
        self._check_perms = kwargs.get('check_perms', True)
        self._filter = kwargs.get('filter')

        items = []
        for model, info in _api.get_models().items():
            items.append((model, lang.t(info[1])))

        items = sorted(items, key=lambda x: x[1])

        if callable(self._filter):
            filtered_items = []
            for item in items:
                if self._filter(_api.dispense(item[0])):
                    filtered_items.append(item)
            items = filtered_items

        super().__init__(uid, items=items, **kwargs)


class StatusSelect(widget.select.Select):
    """Content Status Select
    """

    def __init__(self, uid: str, entity, **kwargs):
        """Init

        :type entity: plugins.content.model.Content
        """
        status_field = entity.get_field(kwargs.get('status_field_name', 'status'))
        statuses = entity.content_status_select_items()

        kwargs.setdefault('label', lang.t('content@status'))
        kwargs.setdefault('h_size', 'col-xs-12 col-12 col-sm-4 col-md-3')
        kwargs.setdefault('required', status_field.is_required)
        kwargs.setdefault('items', [(s, entity.t('content_status_{}_{}'.format(entity.model, s))) for s in statuses])
        kwargs.setdefault('hidden', len(kwargs.get('items')) <= 1)
        kwargs.setdefault('value', status_field.get_val())

        super().__init__(uid, **kwargs)


class EntitySelect(odm_ui.widget.EntitySelect):
    def __init__(self, uid: str, **kwargs):
        kwargs.setdefault('model', list(_api.get_models().keys()))
        kwargs.setdefault('sort_by', 'title')

        super().__init__(uid, **kwargs)
