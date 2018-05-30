"""Pytsite Content Plugin
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

# Public API
from . import _model as model, _widget as widget
from ._api import register_model, get_models, find, get_model, get_model_title, dispense, get_statuses, \
    is_model_registered, generate_rss, find_by_url, paginate
from ._model import Content, ContentWithURL


def plugin_load():
    from pytsite import lang, router
    from plugins import permissions, admin, assetman
    from . import _eh, _controllers

    # Resources
    lang.register_package(__name__)
    assetman.register_package(__name__)

    # Assetman tasks
    assetman.t_js(__name__)

    # Permissions group
    permissions.define_group('content', 'content@content')

    # Admin section should exist before any content's models registration
    admin.sidebar.add_section('content', 'content@content', 100)

    # Routes which must be registered in any environment
    router.handle(_controllers.View, 'content/view/<model>/<eid>', 'content@view')


def plugin_install():
    from plugins import assetman

    assetman.build(__name__)


def plugin_load_console():
    from pytsite import console
    from . import _console_command

    console.register_command(_console_command.Generate())


def plugin_load_wsgi():
    from pytsite import cron, events, router, tpl
    from plugins import http_api, settings, robots_txt, auth_ui
    from . import _eh, _controllers, _http_api_controllers, _settings_form

    # Tpl resources
    tpl.register_package(__name__)

    # Events listeners
    cron.hourly(_eh.cron_hourly)
    cron.daily(_eh.cron_daily)
    events.listen('comments@create_comment', _eh.comments_create_comment)

    # Routes
    router.handle(_controllers.Index, 'content/index/<model>', 'content@index')
    router.handle(_controllers.Browse, 'content/browse/<model>', 'content@browse',
                  filters=auth_ui.AuthFilterController)
    router.handle(_controllers.Modify, 'content/<model>/modify/<eid>', 'content@modify',
                  filters=auth_ui.AuthFilterController)
    router.handle(_controllers.Delete, 'content/<model>/delete', 'content@delete', methods=('GET', 'POST'),
                  filters=auth_ui.AuthFilterController)

    # HTTP API endpoints
    http_api.handle('PATCH', 'content/view/<model>/<uid>', _http_api_controllers.PatchViewsCount,
                    'content@patch_view_count')
    http_api.handle('POST', 'content/abuse/<model>/<uid>', _http_api_controllers.PostAbuse, 'content@post_abuse')

    # Settings
    settings.define('content', _settings_form.Form, 'content@content', 'fa fa-glass', 'dev')

    # Sitemap location in robots.txt
    robots_txt.sitemap('/sitemap/index.xml')
