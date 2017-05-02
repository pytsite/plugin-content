"""Pytsite Content Module.
"""
# Public API
from . import _model as model, _widget as widget
from ._api import register_model, get_models, find, get_model, get_model_title, dispense, get_statuses, \
    is_model_registered, generate_rss, find_by_url, paginate

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


def _init():
    """Module Init Wrapper.
    """
    from pytsite import admin, settings, assetman, events, tpl, lang, router, robots, http_api, permissions, console
    from . import _eh, _settings_form, _http_api
    from ._console_command import Generate as GenerateConsoleCommand

    lang.register_package(__name__, alias='content')
    tpl.register_package(__name__, alias='content')

    # HTTP API
    http_api.handle('PATCH', 'content/view/<model>/<uid>', _http_api.patch_view_count, 'content@patch_view_count')
    http_api.handle('GET', 'content/widget_entity_select_search/<model>/<language>',
                    _http_api.get_widget_entity_select_search, 'content@get_widget_entity_select_search')

    # Permission groups
    permissions.define_group('content', 'content@content')
    permissions.define_permission('content.settings.manage', 'content@manage_content_settings_permission', 'content')

    # Assets
    assetman.register_package(__name__, alias='content')
    assetman.t_js(__name__ + '@**', 'js')

    # Common routes
    router.handle('content/index/<model>', 'plugins.content@index', 'content@index')
    router.handle('content/view/<model>/<id>', 'plugins.content@view', 'content@view')
    router.handle('content/modify/<model>/<id>', 'plugins.content@modify', 'content@modify')
    router.handle('content/search/<model>', 'plugins.content@search', 'content@search')
    router.handle('content/ajax_search/<model>', 'plugins.content@ajax_search', 'content@ajax_search')

    # Admin elements
    admin.sidebar.add_section('content', 'content@content', 100)

    # Event handlers
    router.on_dispatch(_eh.router_dispatch)
    events.listen('pytsite.setup', _eh.setup)
    events.listen('pytsite.cron.hourly', _eh.cron_hourly)
    events.listen('pytsite.cron.daily', _eh.cron_daily)
    events.listen('pytsite.auth.user.delete', _eh.auth_user_delete)
    events.listen('comments.create_comment', _eh.comments_create_comment)

    # Settings
    settings.define('content', _settings_form.Form, 'content@content', 'fa fa-glass', 'content.settings.manage')

    # Console commands
    console.register_command(GenerateConsoleCommand())

    # Sitemap location in robots.txt
    robots.sitemap('/sitemap/index.xml')


_init()
