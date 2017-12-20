"""Pytsite Content Plugin
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import plugman as _plugman

if _plugman.is_installed(__name__):
    # Public API
    from . import _model as model, _widget as widget
    from ._api import register_model, get_models, find, get_model, get_model_title, dispense, get_statuses, \
        is_model_registered, generate_rss, find_by_url, paginate


def plugin_load():
    from pytsite import events, lang
    from plugins import assetman, permissions
    from . import _eh

    # Lang resources
    lang.register_package(__name__)

    # Assetman resources
    assetman.register_package(__name__)
    assetman.t_js(__name__)

    # Permissions
    permissions.define_group('content', 'content@content')
    permissions.define_permission('content@manage_settings', 'content@manage_content_settings_permission', 'content')


    # Event handlers
    events.listen('auth@user.delete', _eh.auth_user_delete)


def plugin_load_console():
    from pytsite import console
    from . import _console_command

    console.register_command(_console_command.Generate())


def plugin_load_uwsgi():
    from pytsite import cron, events, router, tpl
    from plugins import admin, http_api, settings, robots_txt
    from . import _eh, _controllers, _http_api_controllers, _settings_form

    # Tpl resources
    tpl.register_package(__name__)

    # Events listeners
    cron.hourly(_eh.cron_hourly)
    cron.daily(_eh.cron_daily)
    events.listen('comments@create_comment', _eh.comments_create_comment)

    # Routes
    router.handle(_controllers.Index, 'content/index/<model>', 'content@index')
    router.handle(_controllers.View, 'content/view/<model>/<id>', 'content@view')
    router.handle(_controllers.Modify, 'content/modify/<model>/<id>', 'content@modify')

    # HTTP API endpoints
    http_api.handle('PATCH', 'content/view/<model>/<uid>', _http_api_controllers.PatchViewsCount,
                    'content@patch_view_count')
    http_api.handle('GET', 'content/widget_entity_select_search/<model>/<language>',
                    _http_api_controllers.GetWidgetEntitySelectSearch, 'content@get_widget_entity_select_search')
    http_api.handle('POST', 'content/abuse/<model>/<uid>', _http_api_controllers.PostAbuse, 'content@post_abuse')

    # Settings
    settings.define('content', _settings_form.Form, 'content@content', 'fa fa-glass', 'content@manage_settings')

    # Admin elements
    admin.sidebar.add_section('content', 'content@content', 100)

    # Sitemap location in robots.txt
    robots_txt.sitemap('/sitemap/index.xml')


def plugin_install():
    from plugins import assetman

    plugin_load()
    assetman.build(__name__)
    assetman.build_translations()
