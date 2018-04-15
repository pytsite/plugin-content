"""PytSite Content Plugin Controllers
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from datetime import datetime as _datetime
from pytsite import router as _router, metatag as _metatag, lang as _lang, routing as _routing, tpl as _tpl
from plugins import assetman as _assetman, auth as _auth, odm as _odm, taxonomy as _taxonomy, comments as _comments, \
    odm_ui as _odm_ui, hreflang as _hreflang


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
        self.args['finder'] = f

        # Filter by term
        term_field_name = self.arg('term_field')
        if term_field_name and f.mock.has_field(term_field_name):
            term_field = f.mock.get_field(term_field_name)  # type: _odm.field.Ref
            term_model = term_field.model
            term_alias = self.arg('term_alias')
            if term_alias and term_model != '*':
                term = _taxonomy.find(term_model).eq('alias', term_alias).first()
                if term:
                    self.args['term'] = term
                    if isinstance(f.mock.fields[term_field_name], (_odm.field.Ref, _odm.field.ManualRef)):
                        f.eq(term_field_name, term)
                    elif isinstance(f.mock.fields[term_field_name], (_odm.field.RefsList, _odm.field.ManualRefsList)):
                        f.inc(term_field_name, term)
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

        model = self.arg('model')
        entity = _api.find(model, status='*', check_publish_time=False).eq('_id', self.arg('eid')).first()

        # Check entity existence
        if not entity:
            raise self.not_found()

        # Check permissions
        if not (entity.odm_auth_check_permission('view') or entity.odm_auth_check_permission('view_own')):
            raise self.forbidden()

        # Show non published entities only to users who can edit them
        if entity.has_field('publish_time') and entity.f_get('publish_time') > _datetime.now():
            if not (entity.odm_auth_check_permission('modify') or entity.odm_auth_check_permission('modify_own')):
                raise self.not_found()
            _router.session().add_warning_message(_lang.t('content@content_warning_future_publish_time'))

        if entity.has_field('status') and entity.status != 'published':
            if not (entity.odm_auth_check_permission('modify') or entity.odm_auth_check_permission('modify_own')):
                raise self.not_found()
            _router.session().add_warning_message(_lang.t('content@content_status_warning_{}'.format(entity.status)))

        # Update entity's comments count
        if entity.has_field('route_alias') and entity.has_field('comments_count') and entity.f_get('route_alias'):
            _auth.switch_user_to_system()
            entity.f_set('comments_count', _comments.get_all_comments_count(entity.route_alias.alias)).save()
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

        try:
            # Call a controller provided by application
            return _router.call('content_view', self.args)

        except _routing.error.RuleNotFound:
            # Render a template provided by application
            return _tpl.render('content/view', self.args)


class Browse(_routing.Controller):
    """Get entities browser
    """

    def exec(self) -> str:
        self.args['browser'] = _odm_ui.get_browser(self.arg('model'))

        try:
            # Call a controller provided by application
            return _router.call('content_browse', self.args)

        except _routing.error.RuleNotFound:
            # Render a template provided by application
            return _tpl.render('content/browse', self.args)


class Modify(_routing.Controller):
    """Get content entity create/modify form
    """

    def exec(self) -> str:
        try:
            self.args['form'] = _odm_ui.get_m_form(self.arg('model'), self.arg('eid'), hide_title=True)

            try:
                # Call a controller provided by application
                return _router.call('content_modify', self.args)

            except _routing.error.RuleNotFound:
                # Render a template provided by application
                return _tpl.render('content/modify', self.args)

        except _odm.error.EntityNotFound:
            raise self.not_found()


class Delete(_routing.Controller):
    """Get content entities delete form
    """

    def exec(self) -> str:
        self.args['form'] = _odm_ui.get_d_form(self.arg('model'), self.arg('eids', self.arg('ids', [])))

        try:
            # Call a controller provided by application
            return _router.call('content_delete', self.args)

        except _routing.error.RuleNotFound:
            # Render a template provided by application
            return _tpl.render('content/delete', self.args)
