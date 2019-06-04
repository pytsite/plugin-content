"""Pytsite Content Plugin
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

# Public API
from . import _model as model, _widget as widget
from ._constants import CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING, CONTENT_STATUS_PUBLISHED
from ._api import register_model, get_models, find, get_model, get_model_title, dispense, is_model_registered, \
    generate_rss, find_by_url, paginate, on_content_view
from ._model import Content, ContentWithURL


def plugin_load():
    from pytsite import router
    from plugins import permissions, admin
    from . import _eh, _controllers

    # Permissions group
    permissions.define_group('content', 'content@content')

    # Admin section should exist before any content's models registration
    admin.sidebar.add_section('content', 'content@content', 100)

    # Routes which must be registered in any environment
    router.handle(_controllers.View, 'content/view/<model>/<eid>', 'content@view')


def plugin_load_console():
    from pytsite import console
    from . import _console_command

    console.register_command(_console_command.Generate())


def plugin_load_wsgi():
    from pytsite import cron, events, router
    from plugins import http_api, settings, robots_txt, flag
    from . import _eh, _controllers, _http_api_controllers, _settings_form

    # Events listeners
    cron.hourly(_eh.on_cron_hourly)
    cron.daily(_eh.on_cron_daily)
    events.listen('comments@create_comment', _eh.on_comments_create_comment)
    flag.on_flag_create(_eh.on_flag_toggle)
    flag.on_flag_delete(_eh.on_flag_toggle)

    # Routes
    router.handle(_controllers.Index, 'content/index/<model>', 'content@index')

    # HTTP API endpoints
    http_api.handle('PATCH', 'content/view/<model>/<uid>', _http_api_controllers.PatchViewsCount,
                    'content@patch_view_count')
    http_api.handle('POST', 'content/abuse/<model>/<uid>', _http_api_controllers.PostAbuse, 'content@post_abuse')

    # Settings
    settings.define('content', _settings_form.Form, 'content@content', 'fa fa-glass', 'dev')

    # Sitemap location in robots.txt
    robots_txt.sitemap('/sitemap/index.xml')


from pytsite import semver


def plugin_update(v_from: semver.Version):
    if v_from < '4.20':
        from pytsite import mongodb

        mongodb.get_collection('content_model_entities').drop()
