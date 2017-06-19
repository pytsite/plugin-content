"""Pytsite Content Endpoints.
"""
from datetime import datetime as _datetime
from pytsite import odm_ui as _odm_ui, auth as _auth, router as _router, metatag as _metatag, \
    assetman as _assetman, odm as _odm, lang as _lang, tpl as _tpl, logger as _logger, hreflang as _hreflang, \
    routing as _routing
from plugins import taxonomy as _taxonomy, comments as _comments

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class Index(_routing.Controller):
    def exec(self):
        """Content Index.
        """
        # Delayed import to prevent circular dependency
        from . import _api

        # Checking if the model is registered
        model = self.arg('model')
        if not model or not _api.is_model_registered(model):
            _logger.warn("Content model '{}' is not found. Redirecting to home.".format(model))
            return self.redirect(_router.base_url())

        # Getting finder
        f = _api.find(model)
        self.args['finder'] = f

        # Filter by term
        term_field = self.arg('term_field')
        if term_field and f.mock.has_field(term_field):
            term_model = f.mock.get_field(term_field).model
            term_alias = self.arg('term_alias')
            if term_alias and term_model != '*':
                term = _taxonomy.find(term_model).eq('alias', term_alias).first()
                if term:
                    self.args['term'] = term
                    if isinstance(f.mock.fields[term_field], _odm.field.Ref):
                        f.eq(term_field, term)
                    elif isinstance(f.mock.fields[term_field], _odm.field.RefsList):
                        f.inc(term_field, term)
                    _metatag.t_set('title', term.title)
                else:
                    raise self.not_found()
            else:
                raise self.not_found()
        # Filter by author
        author_nickname = _router.request().inp.get('author') or self.arg('author')
        if author_nickname:
            author = _auth.get_user(nickname=author_nickname)

            if author:
                _metatag.t_set('title', _lang.t('content@articles_of_author', {'name': author.full_name}))
                f.eq('author', author.uid)
                self.args['author'] = author
            else:
                raise self.not_found()

        # Search
        query = _router.request().inp.get('query')
        if query:
            f.where_text(query)
            _metatag.t_set('title', _lang.t('content@search', {'query': query}))

        # Call final endpoint
        return _router.call('content_entity_index', self.args)


class View(_routing.Controller):
    """View Content Entity
    """

    def exec(self):
        from . import _api

        model = self.arg('model')
        entity = _api.find(model, status='*', check_publish_time=False).eq('_id', self.arg('id')).first()

        # Check entity existence
        if not entity:
            raise self.not_found()

        # Check permissions
        if not (entity.odm_auth_check_permission('view') or entity.odm_auth_check_permission('view_own')):
            raise self.not_found()

        # Show non published entities only to users who can edit them
        if entity.has_field('publish_time') and entity.f_get('publish_time') > _datetime.now():
            if not (entity.odm_auth_check_permission('modify') or entity.odm_auth_check_permission('modify_own')):
                raise self.not_found()
        if entity.has_field('status') and entity.status != 'published':
            if not (entity.odm_auth_check_permission('modify') or entity.odm_auth_check_permission('modify_own')):
                raise self.not_found()

        # Update entity's comments count
        if entity.has_field('route_alias') and entity.has_field('comments_count') and entity.f_get('route_alias'):
            _auth.switch_user_to_system()
            with entity:
                entity.f_set('comments_count',
                             _comments.get_all_comments_count(entity.f_get('route_alias').alias)).save()
            _auth.restore_user()

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
            _metatag.t_set('author', entity.author.full_name)
            _metatag.t_set('article:author', entity.author.full_name)

        # Alternate languages URLs
        for lng in _lang.langs(False):
            f_name = 'localization_' + lng
            if entity.has_field(f_name) and entity.f_get(f_name):
                _hreflang.add(lng, entity.f_get(f_name).url)

        # Necessary JS code
        _assetman.preload('content@js/content.js')

        # Push entity into args
        self.args.update({
            'entity': entity,
        })

        # Call final endpoint
        return _router.call('content_entity_view', self.args)


class Modify(_routing.Controller):
    """Get content entity create/modify form
    """

    def exec(self) -> str:
        model = self.arg('model')
        eid = self.arg('id')

        try:
            self.args['frm'] = _odm_ui.get_m_form(model, eid if eid != 0 else None)

            if _router.has_rule('content_entity_modify'):
                return _router.call('content_entity_modify', self.args)
            else:
                return _tpl.render('content@page/modify-form', self.args)

        except _odm.error.EntityNotFound:
            raise self.not_found()


class Propose(_routing.Controller):
    def exec(self):
        """Propose content endpoint.
        """
        model = self.arg('model')

        frm = _odm_ui.get_m_form(model, redirect=_router.base_url())
        frm.title = None

        _metatag.t_set('title', _lang.t('content@propose_content'))

        self.args['form'] = frm

        return _router.call('content_entity_propose', self.args)
