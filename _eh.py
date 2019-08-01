"""PytSite Content Plugin Event Handlers
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from os import path, makedirs
from shutil import rmtree
from datetime import datetime
from pytsite import reg, logger, tpl, mail, lang, router
from plugins import comments, sitemap, flag, auth
from . import _api
from ._model import Content, ContentWithURL

_sitemap_generation_works = False


def on_cron_hourly():
    """pytsite.cron.hourly
    """
    _generate_feeds()


def on_cron_daily():
    """pytsite.cron.daily
    """
    _generate_sitemap()


def on_content_view(entity: ContentWithURL):
    if entity.has_field('comments_count') and entity.has_field('route_alias') and entity.route_alias:
        # Update entity's comments count
        try:
            auth.switch_user_to_system()
            cnt = comments.get_all_comments_count(entity.route_alias.alias)
            entity.f_set('comments_count', cnt).save(fast=True)
            return cnt
        finally:
            auth.restore_user()


def on_comments_create_comment(comment: comments.model.AbstractComment):
    """comments.create_comment
    """
    entity = _api.find_by_url(comment.thread_uid)
    if comment.is_reply or not entity or comment.author == entity.author:
        return

    tpl_name = 'content@mail/{}/comment'.format(lang.get_current())
    subject = lang.t('content@mail_subject_new_comment')
    body = tpl.render(tpl_name, {'comment': comment, 'entity': entity})
    m_from = '{} <{}>'.format(comment.author.first_last_name, mail.mail_from()[1])
    mail.Message(entity.author.login, subject, body, m_from).send()


def on_flag_toggle(flg: flag.Flag):
    if not isinstance(flg.entity, Content):
        return

    f_name = '{}_count'.format(lang.english_plural(flg.variant))
    if flg.entity.has_field(f_name):
        try:
            auth.switch_user_to_system()
            flg.entity.f_set(f_name, flag.count(flg.entity, flg.variant)).save(fast=True)
        finally:
            auth.restore_user()


def _generate_sitemap():
    """Generate content sitemap
    """
    global _sitemap_generation_works

    if _sitemap_generation_works:
        raise RuntimeError('Sitemap generation is still in progress')

    _sitemap_generation_works = True
    logger.info('Sitemap generation start.')

    output_dir = path.join(reg.get('paths.static'), 'sitemap')
    if path.exists(output_dir):
        rmtree(output_dir)
    makedirs(output_dir, 0o755, True)

    sitemap_index = sitemap.Index()
    links_per_file = 50000
    loop_count = 1
    loop_links = 1
    sm = sitemap.Sitemap()
    sm.add_url(router.base_url(), datetime.now(), 'always', 1)
    for lng in lang.langs():
        for model in reg.get('content.sitemap_models', ()):
            logger.info("Sitemap generation started for model '{}', language '{}'".
                        format(model, lang.lang_title(lng)))

            for entity in _api.find(model, language=lng):  # type: ContentWithURL
                sm.add_url(entity.url, entity.publish_time)
                loop_links += 1

                # Flush sitemap
                if loop_links >= links_per_file:
                    loop_count += 1
                    loop_links = 0
                    sitemap_path = sm.write(path.join(output_dir, 'data-%02d.xml' % loop_count), True)
                    logger.info("'{}' successfully written with {} links".format(sitemap_path, loop_links))
                    sitemap_index.add_url(router.url('/sitemap/{}'.format(path.basename(sitemap_path))))
                    del sm
                    sm = sitemap.Sitemap()

    # If non-flushed sitemap exist
    if len(sm):
        sitemap_path = sm.write(path.join(output_dir, 'data-%02d.xml' % loop_count), True)
        logger.info("'{}' successfully written with {} links.".format(sitemap_path, loop_links))
        sitemap_index.add_url(router.url('/sitemap/{}'.format(path.basename(sitemap_path))))

    if len(sitemap_index):
        sitemap_index_path = sitemap_index.write(path.join(output_dir, 'index.xml'))
        logger.info("'{}' successfully written.".format(sitemap_index_path))

    logger.info('Sitemap generation stop.')
    _sitemap_generation_works = False


def _generate_feeds():
    # For each language we have separate feed
    for lng in lang.langs():
        # Generate RSS feed for each model
        for model in reg.get('content.rss_models', ()):
            filename = 'rss-{}'.format(model)
            _api.generate_rss(model, filename, lng, length=reg.get('content.feed_length', 20))
