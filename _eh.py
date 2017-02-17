"""Event Handlers.
"""
from os import path as _path, makedirs as _makedirs
from shutil import rmtree as _rmtree
from datetime import datetime as _datetime
from pytsite import settings as _settings, sitemap as _sitemap, reg as _reg, logger as _logger, tpl as _tpl, \
    mail as _mail, lang as _lang, router as _router, metatag as _metatag, assetman as _assetman, auth as _auth, \
    errors as _errors, db as _db
from plugins import comments as _comments
from . import _api

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

_sitemap_generation_works = False


def setup():
    """`pytsite.setup` event handler.
    """
    user_role = _auth.get_role('user')
    anon_role = _auth.get_role('anonymous')

    # Allow ordinary users to create tags
    user_role.permissions = list(user_role.permissions) + ['pytsite.odm_auth.create.tag']

    # Allow all to view content
    for model in _api.get_models():
        user_role.permissions = list(user_role.permissions) + [
            'pytsite.odm_auth.view.{}'.format(model),
            'pytsite.odm_auth.view_own.{}'.format(model),
        ]
        anon_role.permissions = list(anon_role.permissions) + [
            'pytsite.odm_auth.view.{}'.format(model),
        ]

    _auth.switch_user_to_system()
    user_role.save()
    anon_role.save()
    _auth.restore_user()


def cron_hourly():
    """'pytsite.cron.hourly' event handler.
    """
    _generate_feeds()


def cron_daily():
    """'pytsite.cron.daily' event handler.
    """
    _generate_sitemap()


def router_dispatch():
    """'pytsite.router.dispatch' Event Handler.
    """
    settings = _settings.get('content')

    # Add inline JS code
    if 'add_js' in settings and settings['add_js']:
        _assetman.add_inline(settings['add_js'])

    # Add meta tags for home page
    if _router.is_base_url():
        lng = _lang.get_current()
        for s_key in ['title', 'description', 'keywords']:
            s_full_key = 'home_{}_{}'.format(s_key, lng)
            if s_full_key in settings:
                s_val = settings[s_full_key]
                if isinstance(s_val, list):
                    s_val = ','.join(s_val)
                _metatag.t_set(s_key, s_val)

                if s_key in ['title', 'description']:
                    _metatag.t_set('og:' + s_key, s_val)
                    _metatag.t_set('twitter:' + s_key, s_val)


def comments_create_comment(comment: _comments.model.AbstractComment):
    entity = _api.find_by_url(comment.thread_uid)
    if comment.is_reply or not entity or comment.author == entity.author:
        return

    tpl_name = 'content@mail/{}/comment'.format(_lang.get_current())
    subject = _lang.t('content@mail_subject_new_comment')
    body = _tpl.render(tpl_name, {'comment': comment, 'entity': entity})
    m_from = '{} <{}>'.format(comment.author.full_name, _mail.mail_from()[1])
    _mail.Message(entity.author.email, subject, body, m_from).send()


def auth_user_delete(user: _auth.model.AbstractUser):
    """'auth.user.delete' event handler.
    """
    for model in _api.get_models():
        f = _api.find(model, language=None)
        if f.mock.has_field('author'):
            entity = f.eq('author', user).first()
            if entity:
                raise _errors.ForbidDeletion(_lang.t('content@forbid_author_deletion', {
                    'author': user.full_name,
                    'content_model': model,
                    'content_title': entity.f_get('title'),
                }))


def _generate_sitemap():
    """Generate content sitemap.
    """
    global _sitemap_generation_works

    if _sitemap_generation_works:
        raise RuntimeError('Sitemap generation is still in progress')

    _sitemap_generation_works = True
    _logger.info('Sitemap generation start.')

    output_dir = _path.join(_reg.get('paths.static'), 'sitemap')
    if _path.exists(output_dir):
        _rmtree(output_dir)
    _makedirs(output_dir, 0o755, True)

    sitemap_index = _sitemap.Index()
    links_per_file = 50000
    loop_count = 1
    loop_links = 1
    sitemap = _sitemap.Sitemap()
    sitemap.add_url(_router.base_url(), _datetime.now(), 'always', 1)
    for lang in _lang.langs():
        for model in _settings.get('content.sitemap_models', ()):
            _logger.info("Sitemap generation started for model '{}', language '{}'.".
                         format(model, _lang.lang_title(lang)))

            for doc in _api.dispense(model).collection.find({'language': lang}):
                if not doc.get('route_alias') or not doc.get('publish_time'):
                    continue

                entity_url = _router.url(_db.get_database().dereference(doc['route_alias'])['alias'])
                entity_pub_time = doc['publish_time']

                sitemap.add_url(entity_url, entity_pub_time)
                loop_links += 1

                # Flush sitemap
                if loop_links >= links_per_file:
                    loop_count += 1
                    loop_links = 0
                    sitemap_path = sitemap.write(_path.join(output_dir, 'data-%02d.xml' % loop_count), True)
                    _logger.info("'{}' successfully written with {} links.".format(sitemap_path, loop_links))
                    sitemap_index.add_url(_router.url('/sitemap/{}'.format(_path.basename(sitemap_path))))
                    del sitemap
                    sitemap = _sitemap.Sitemap()

    # If non-flushed sitemap exist
    if len(sitemap):
        sitemap_path = sitemap.write(_path.join(output_dir, 'data-%02d.xml' % loop_count), True)
        _logger.info("'{}' successfully written with {} links.".format(sitemap_path, loop_links))
        sitemap_index.add_url(_router.url('/sitemap/{}'.format(_path.basename(sitemap_path))))

    if len(sitemap_index):
        sitemap_index_path = sitemap_index.write(_path.join(output_dir, 'index.xml'))
        _logger.info("'{}' successfully written.".format(sitemap_index_path))

    _logger.info('Sitemap generation stop.')
    _sitemap_generation_works = False


def _generate_feeds():
    # For each language we have separate feed
    for lng in _lang.langs():
        # Generate RSS feed for each model
        for model in _settings.get('content.rss_models', ()):
            filename = 'rss-{}'.format(model)
            _api.generate_rss(model, filename, lng, length=_reg.get('content.feed.length', 20))
