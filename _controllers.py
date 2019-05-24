"""PytSite Content Plugin Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from datetime import datetime as _datetime
from pytsite import router as _router, metatag as _metatag, lang as _lang, routing as _routing, tpl as _tpl, \
    events as _events
from plugins import auth as _auth, odm as _odm, taxonomy as _taxonomy, hreflang as _hreflang, widget as _widget
from . import _model
from ._constants import CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING


class Index(_routing.Controller):
    """Content Entities Index
    """

    def exec(self):
        # Delayed import to prevent circular dependency
        from . import _api

        # Checking if the model is registered
        model = self.arg('model')
        if not _api.is_model_registered(model):
            raise self.not_found()

        # Getting finder
        f = _api.find(model)

        # Breadcrumb
        breadcrumb = _widget.select.Breadcrumb('content-index-breadcrumb')
        breadcrumb.append_item(_lang.t('content@home_page'), _router.base_url())

        # Filter by term
        term_field_name = self.arg('term_field')
        term_alias = self.arg('term_alias')
        term = None
        if term_field_name and f.mock.has_field(term_field_name):
            term_field = f.mock.get_field(term_field_name)  # type: _odm.field.Ref
            if term_alias and term_field.model:
                for term_model in term_field.model:
                    term = _taxonomy.find(term_model).eq('alias', term_alias).first()
                    if term:
                        self.args['term'] = term
                        if isinstance(f.mock.fields[term_field_name], _odm.field.Ref):
                            f.eq(term_field_name, term)
                        elif isinstance(f.mock.fields[term_field_name], _odm.field.RefsList):
                            f.inc(term_field_name, term)
                        _metatag.t_set('title', term.title)
                        breadcrumb.append_item(term.title)
                    else:
                        raise self.not_found()
            else:
                raise self.not_found()

        # Filter by author
        author_nickname = self.arg('author')
        if author_nickname:
            try:
                author = _auth.get_user(nickname=author_nickname)
                f.eq('author', author.uid)
                self.args['author'] = author
                _metatag.t_set('title', _lang.t('content@articles_of_author', {'name': author.first_last_name}))

                if term:
                    breadcrumb.pop_item()
                    breadcrumb.append_item(term.title, _router.rule_url('content@index', {
                        'model': model,
                        'term_field': term_field_name,
                        'term_alias': term_alias,
                    }))

                breadcrumb.append_item(author.first_last_name)
            except _auth.error.UserNotFound:
                raise self.not_found()

        self.args.update({
            'finder': f,
            'breadcrumb': breadcrumb,
        })

        try:
            # Call a controller provided by application
            return _router.call('content_index', self.args)

        except _routing.error.RuleNotFound:
            # Render a template provided by application
            return _tpl.render('content/index', self.args)


class View(_routing.Controller):
    """Content Entity View
    """

    def exec(self):
        from . import _api

        c_user = _auth.get_current_user()

        model = self.arg('model')
        entity = _api.find(model, status='*', check_publish_time=False) \
            .eq('_id', self.arg('eid')) \
            .first()  # type: _model.ContentWithURL

        # Check entity existence
        if not entity:
            raise self.not_found()

        # Check permissions
        if not entity.odm_auth_check_entity_permissions(['view', 'modify']):
            raise self.not_found()

        # Show non-published entities only to users who can edit or delete them
        if (entity.has_field('publish_time') and entity.publish_time > _datetime.now()) or \
                (entity.has_field('status') and entity.status in (CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING)):
            if not entity.odm_auth_check_entity_permissions(['modify', 'delete']):
                raise self.not_found()

        # Show warnings about unpublished entities
        if entity.has_field('publish_time') and entity.publish_time > _datetime.now():
            _router.session().add_warning_message(_lang.t('content@content_warning_future_publish_time'))
        if entity.has_field('status') and entity.status in (CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING):
            _router.session().add_warning_message(_lang.t('content@content_status_warning_{}'.format(entity.status)))

        # Breadcrumb
        breadcrumb = _widget.select.Breadcrumb('content-index-breadcrumb')
        breadcrumb.append_item(_lang.t('content@home_page'), _router.base_url())
        entity.content_breadcrumb(breadcrumb)

        # Meta title
        if entity.has_field('title'):
            title = entity.title
            _metatag.t_set('title', title)
            _metatag.t_set('og:title', title)
            _metatag.t_set('twitter:title', title)

        # Meta description
        if entity.has_field('description'):
            description = entity.f_get('description')
            _metatag.t_set('description', description)
            _metatag.t_set('og:description', description)
            _metatag.t_set('twitter:description', description)

        # Meta keywords
        if entity.has_field('tags'):
            _metatag.t_set('keywords', entity.f_get('tags', as_string=True))

        # Meta image
        if entity.has_field('images') and entity.images:
            _metatag.t_set('twitter:card', 'summary_large_image')
            image_w = 900
            image_h = 500
            image_url = entity.images[0].get_url(width=image_w, height=image_h)
            _metatag.t_set('og:image', image_url)
            _metatag.t_set('og:image:width', str(image_w))
            _metatag.t_set('og:image:height', str(image_h))
            _metatag.t_set('twitter:image', image_url)
        else:
            _metatag.t_set('twitter:card', 'summary')

        # Various metatags
        _metatag.t_set('og:type', 'article')
        _metatag.t_set('og:url', entity.url)
        _metatag.t_set('article:publisher', entity.url)

        # 'Author' metatag
        if entity.has_field('author') and entity.author:
            _metatag.t_set('author', entity.author.first_last_name)
            _metatag.t_set('article:author', entity.author.first_last_name)

        # Alternate languages URLs
        for lng in _lang.langs(False):
            f_name = 'localization_' + lng
            if entity.has_field(f_name) and entity.f_get(f_name):
                _hreflang.put(lng, entity.f_get(f_name).url)
            else:
                _hreflang.remove(lng)

        # Update args
        self.args.update({
            'entity': entity,
            'breadcrumb': breadcrumb,
        })

        # Notify listeners
        _events.fire('content@view', entity=entity)

        try:
            # Call a controller provided by application
            return _router.call('content_view', self.args)

        except _routing.error.RuleNotFound:
            # Render a template provided by application
            return _tpl.render('content/view', self.args)
