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
    from pytsite import admin, settings, console, assetman, events, tpl, lang, router, robots, browser, \
        http_api, permissions
    from . import _eh, _settings_form
    from ._console_command import Generate as GenerateConsoleCommand

    lang.register_package(__name__, alias='content')
    tpl.register_package(__name__, alias='content')

    http_api.register_handler('content', __name__ + '.http_api')

    # Permission groups
    permissions.define_group('content', 'content@content')
    permissions.define_permission('content.settings.manage', 'content@manage_content_settings_permission', 'content')

    # Assets
    assetman.register_package(__name__, alias='content')
    browser.include('responsive', True)

    # Common routes
    router.add_rule('/content/index/<model>', 'content@index', 'plugins.content@index')
    router.add_rule('/content/view/<model>/<id>', 'content@view', 'plugins.content@view')
    router.add_rule('/content/modify/<model>/<id>', 'content@modify', 'plugins.content@modify')
    router.add_rule('/content/search/<model>', 'content@search', 'content@index')
    router.add_rule('/content/ajax_search/<model>', 'content@ajax_search', 'plugins.content@ajax_search')

    # Propose route
    router.add_rule('/content/propose/<model>', 'content@propose', 'plugins.content@propose',
                    filters='pytsite.auth@f_authorize')
    router.add_rule('/content/propose/<model>/submit', 'content@propose_submit', 'plugins.content@propose_submit',
                    filters='pytsite.auth@f_authorize')

    # Admin elements
    admin.sidebar.add_section('content', 'content@content', 100)

    # Event handlers
    events.listen('pytsite.router.dispatch', _eh.router_dispatch)
    events.listen('pytsite.setup', _eh.setup)
    events.listen('pytsite.cron.hourly', _eh.cron_hourly)
    events.listen('pytsite.cron.daily', _eh.cron_daily)
    events.listen('pytsite.auth.user.delete', _eh.auth_user_delete)
    events.listen('comments.create_comment', _eh.comments_create_comment)

    # Settings
    settings.define('content', _settings_form.Form, 'content@content', 'fa fa-glass', 'content.settings.manage')

    # Console commands
    # console.register_command(GenerateConsoleCommand())

    # Sitemap location in robots.txt
    robots.sitemap('/sitemap/index.xml')


_init()
