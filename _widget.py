"""Content Widgets
"""
from pytsite import widget as _widget, html as _html, lang as _lang, router as _router, tpl as _tpl, odm as _odm, \
    http_api as _http_api, odm_auth as _odm_auth
from . import _model, _api

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class ModelSelect(_widget.select.Select):
    """Content Model Select.
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
    """Content Model Checkboxes.
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
    """Content Status Select.
    """

    def __init__(self, uid: str, **kwargs):
        super().__init__(uid, items=_api.get_statuses(), **kwargs)


class EntitySelect(_widget.select.Select2):
    """Entity Select.
    """

    def __init__(self, uid: str, **kwargs):
        kwargs['ajax_url'] = _http_api.url('content@get_widget_entity_select_search', {
            'model': kwargs.get('model'),
            'language': kwargs.get('language', _lang.get_current())
        })

        super().__init__(uid, **kwargs)

    def set_val(self, value, **kwargs):
        if isinstance(value, str) and not value:
            value = None
        elif isinstance(value, _model.Content):
            value = value.model + ':' + str(value.id)

        return super().set_val(value, **kwargs)

    def _get_element(self, **kwargs):
        # In AJAX-mode Select2 doesn't contain any items,
        # but if we have selected item, it is necessary to append it
        if self._ajax_url and self._value:
            self._items.append((self._value, _odm.get_by_ref(self._value).f_get('title')))

        return super()._get_element()


class Search(_widget.Abstract):
    """Content Search Input.
    """

    def __init__(self, uid: str, **kwargs):
        """Init.
        """
        super().__init__(uid, **kwargs)

        self._model = kwargs.get('model')
        if not self._model:
            raise ValueError('Model is not specified.')

        self._value = _router.request().inp.get('search', '') if _router.request() else ''
        self._title_tag = kwargs.get('title_tag', 'h3')
        self._title_css = kwargs.get('title_css', 'title')

        self._form = _html.Form(css='wrapper form-inline', method='GET')
        placeholder = _lang.t('content@search_input_placeholder', language=self._language)
        self._form.append(_html.Input(type='text', css='form-control', name='search', required=True, value=self.value,
                                      placeholder=placeholder))
        self._form.set_attr('action', _router.rule_url('plugins.content@search', {'model': self._model}))

        btn = _html.Button(type='submit', css='btn btn-default')
        self._form.append(btn.append(_html.I(css='fa fa-search')))

        self._css += ' widget-content-search search-{}'.format(self._model)

    @property
    def title_tag(self) -> str:
        return self._title_tag

    @property
    def title_css(self) -> str:
        return self._title_css

    @property
    def model(self) -> str:
        return self._model

    @property
    def form(self) -> _html.Element:
        return self._form

    def _get_element(self, **kwargs) -> _html.Element:
        """Render the widget.
        :param **kwargs:
        """
        return _html.TagLessElement(_tpl.render('content@widget/search', {'widget': self}))
