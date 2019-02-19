"""PytSite Content Plugin Event Handlers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from os import path as _path, makedirs as _makedirs
from shutil import rmtree as _rmtree
from datetime import datetime as _datetime
from pytsite import reg as _reg, logger as _logger, tpl as _tpl, mail as _mail, lang as _lang, router as _router
from plugins import comments as _comments, sitemap as _sitemap, flag as _flag, auth as _auth
from . import _api, _model

_sitemap_generation_works = False


def on_cron_hourly():
    """pytsite.cron.hourly
    """
    _generate_feeds()


def on_cron_daily():
    """pytsite.cron.daily
    """
    _generate_sitemap()


def on_comments_create_comment(comment: _comments.model.AbstractComment):
    """comments.create_comment
    """
    entity = _api.find_by_url(comment.thread_uid)
    if comment.is_reply or not entity or comment.author == entity.author:
        return

    tpl_name = 'content@mail/{}/comment'.format(_lang.get_current())
    subject = _lang.t('content@mail_subject_new_comment')
    body = _tpl.render(tpl_name, {'comment': comment, 'entity': entity})
    m_from = '{} <{}>'.format(comment.author.first_last_name, _mail.mail_from()[1])
    _mail.Message(entity.author.login, subject, body, m_from).send()


def on_flag_toggle(flag: _flag.Flag):
    if not isinstance(flag.entity, _model.Content):
        return

    f_name = '{}_count'.format(_lang.english_plural(flag.variant))
    if flag.entity.has_field(f_name):
        try:
            _auth.switch_user_to_system()
            flag.entity.f_set(f_name, _flag.count(flag.entity, flag.variant)).save()
        finally:
            _auth.restore_user()


def _generate_sitemap():
    """Generate content sitemap
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
        for model in _reg.get('content.sitemap_models', ()):
            _logger.info("Sitemap generation started for model '{}', language '{}'".
                         format(model, _lang.lang_title(lang)))

            for entity in _api.find(model, language=lang):  # type: _model.ContentWithURL
                sitemap.add_url(entity.url, entity.publish_time)
                loop_links += 1

                # Flush sitemap
                if loop_links >= links_per_file:
                    loop_count += 1
                    loop_links = 0
                    sitemap_path = sitemap.write(_path.join(output_dir, 'data-%02d.xml' % loop_count), True)
                    _logger.info("'{}' successfully written with {} links".format(sitemap_path, loop_links))
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
        for model in _reg.get('content.rss_models', ()):
            filename = 'rss-{}'.format(model)
            _api.generate_rss(model, filename, lng, length=_reg.get('content.feed_length', 20))
