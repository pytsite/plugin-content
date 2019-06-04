"""PytSite Content Plugin Controllers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from datetime import datetime
from pytsite import router, metatag, lang, routing, tpl, events
from plugins import auth, odm, taxonomy, hreflang, widget
from plugins.odm_auth import PERM_MODIFY, PERM_DELETE
from . import _model
from ._constants import CONTENT_PERM_VIEW, CONTENT_PERM_VIEW_OWN, CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING


class Index(routing.Controller):
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
        breadcrumb = widget.select.Breadcrumb('content-index-breadcrumb')
        breadcrumb.append_item(lang.t('content@home_page'), router.base_url())

        # Filter by term
        term_field_name = self.arg('term_field')
        term_alias = self.arg('term_alias')
        term = None
        if term_field_name and f.mock.has_field(term_field_name):
            term_field = f.mock.get_field(term_field_name)  # type: odm.field.Ref
            if term_alias and term_field.model:
                for term_model in term_field.model:
                    term = taxonomy.find(term_model).eq('alias', term_alias).first()
                    if term:
                        self.args['term'] = term
                        if isinstance(f.mock.fields[term_field_name], odm.field.Ref):
                            f.eq(term_field_name, term)
                        elif isinstance(f.mock.fields[term_field_name], odm.field.RefsList):
                            f.inc(term_field_name, term)
                        metatag.t_set('title', term.title)
                        breadcrumb.append_item(term.title)
                    else:
                        raise self.not_found()
            else:
                raise self.not_found()

        # Filter by author
        author_nickname = self.arg('author')
        if author_nickname:
            try:
                author = auth.get_user(nickname=author_nickname)
                f.eq('author', author.uid)
                self.args['author'] = author
                metatag.t_set('title', lang.t('content@articles_of_author', {'name': author.first_last_name}))

                if term:
                    breadcrumb.pop_item()
                    breadcrumb.append_item(term.title, router.rule_url('content@index', {
                        'model': model,
                        'term_field': term_field_name,
                        'term_alias': term_alias,
                    }))

                breadcrumb.append_item(author.first_last_name)
            except auth.error.UserNotFound:
                raise self.not_found()

        self.args.update({
            'finder': f,
            'breadcrumb': breadcrumb,
        })

        try:
            # Call a controller provided by application
            return router.call('content_index', self.args)

        except routing.error.RuleNotFound:
            # Render a template provided by application
            return tpl.render('content/index', self.args)


class View(routing.Controller):
    """Content Entity View
    """

    def exec(self):
        from . import _api

        model = self.arg('model')
        entity = _api.find(model, status='*', check_publish_time=False) \
            .eq('_id', self.arg('eid')) \
            .first()  # type: _model.ContentWithURL

        # Check entity existence
        if not entity:
            raise self.not_found()

        # Check permissions
        if not entity.odm_auth_check_entity_permissions(CONTENT_PERM_VIEW):
            raise self.not_found()

        # Show non-published entities only to authors and users who can edit or delete them
        c_user = auth.get_current_user()
        if (entity.has_field('publish_time') and entity.publish_time > datetime.now()) or \
                (entity.has_field('status') and entity.status in (CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING)):
            if not (entity.author == c_user or entity.odm_auth_check_entity_permissions([PERM_MODIFY, PERM_DELETE])):
                raise self.not_found()

        # Show warnings about unpublished entities
        if entity.has_field('publish_time') and entity.publish_time > datetime.now():
            router.session().add_warning_message(lang.t('content@content_warning_future_publish_time'))
        if entity.has_field('status') and entity.status in (CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING):
            router.session().add_warning_message(lang.t('content@content_status_warning_{}'.format(entity.status)))

        # Breadcrumb
        breadcrumb = widget.select.Breadcrumb('content-index-breadcrumb')
        breadcrumb.append_item(lang.t('content@home_page'), router.base_url())
        entity.content_breadcrumb(breadcrumb)

        # Meta title
        if entity.has_field('title'):
            title = entity.title
            metatag.t_set('title', title)
            metatag.t_set('og:title', title)
            metatag.t_set('twitter:title', title)

        # Meta description
        if entity.has_field('description'):
            description = entity.f_get('description')
            metatag.t_set('description', description)
            metatag.t_set('og:description', description)
            metatag.t_set('twitter:description', description)

        # Meta keywords
        if entity.has_field('tags'):
            metatag.t_set('keywords', entity.f_get('tags', as_string=True))

        # Meta image
        if entity.has_field('images') and entity.images:
            metatag.t_set('twitter:card', 'summary_large_image')
            image_w = 900
            image_h = 500
            image_url = entity.images[0].get_url(width=image_w, height=image_h)
            metatag.t_set('og:image', image_url)
            metatag.t_set('og:image:width', str(image_w))
            metatag.t_set('og:image:height', str(image_h))
            metatag.t_set('twitter:image', image_url)
        else:
            metatag.t_set('twitter:card', 'summary')

        # Various metatags
        metatag.t_set('og:type', 'article')
        metatag.t_set('og:url', entity.url)
        metatag.t_set('article:publisher', entity.url)

        # 'Author' metatag
        if entity.has_field('author') and entity.author:
            metatag.t_set('author', entity.author.first_last_name)
            metatag.t_set('article:author', entity.author.first_last_name)

        # Alternate languages URLs
        for lng in lang.langs(False):
            f_name = 'localization_' + lng
            if entity.has_field(f_name) and entity.f_get(f_name):
                hreflang.put(lng, entity.f_get(f_name).url)
            else:
                hreflang.remove(lng)

        # Update args
        self.args.update({
            'entity': entity,
            'breadcrumb': breadcrumb,
        })

        # Notify listeners
        events.fire('content@view', entity=entity)

        try:
            # Call a controller provided by application
            return router.call('content_view', self.args)

        except routing.error.RuleNotFound:
            # Render a template provided by application
            return tpl.render('content/view', self.args)
