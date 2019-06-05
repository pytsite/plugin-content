"""PytSite Content Plugin API Functions
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Callable, Union, Tuple, Dict, Type
from datetime import datetime
from urllib import parse as _urllib_parse
from os import path, makedirs
from pytsite import util, router, lang, logger, reg, events
from plugins import odm, route_alias, feed, admin, widget
from . import _model
from ._constants import CONTENT_STATUS_PUBLISHED

ContentModelClass = Type[_model.Content]

_models = {}  # type: Dict[str, Tuple[ContentModelClass, str]]


def register_model(model: str, cls: Union[str, ContentModelClass], title: str, menu_weight: int = 0,
                   menu_icon: str = 'fa fa-file-text-o', menu_sid: str = 'content', replace: bool = False):
    """Register content model
    """
    # Resolve class
    if isinstance(cls, str):
        cls = util.get_module_attr(cls)  # type: ContentModelClass

    if not issubclass(cls, _model.Content):
        raise TypeError('Subclass of {} expected, got {}'.format(_model.Content, type(cls)))

    if not replace and is_model_registered(model):
        raise KeyError("Content model '{}' is already registered".format(model))

    # Register ODM model
    odm.register_model(model, cls, replace)

    # Saving info about registered _content_ model
    _models[model] = (cls, title)

    if reg.get('env.type') == 'wsgi':
        mock = dispense(model)
        perms = ['odm_auth@{}.{}'.format(p, model) for p in mock.odm_auth_permissions()],

        admin.sidebar.add_menu(
            sid=menu_sid,
            mid=model,
            title=title,
            path=router.rule_path('odm_ui@admin_browse', {'model': model}),
            icon=menu_icon,
            weight=menu_weight,
            permissions=perms,
            replace=replace,
        )


def is_model_registered(model: str) -> bool:
    """Check if the content model is registered
    """
    return model in _models


def get_models() -> Dict[str, Tuple[ContentModelClass, str]]:
    """Get registered content models
    """
    return _models.copy()


def get_model(model: str) -> Tuple[ContentModelClass, str]:
    """Get model information
    """
    if not is_model_registered(model):
        raise KeyError("Model '{}' is not registered as content model.".format(model))

    return _models[model]


def get_model_class(model: str) -> ContentModelClass:
    """Get class of the content model
    """
    return get_model(model)[0]


def get_model_title(model: str) -> str:
    """Get human readable model title
    """
    return lang.t(get_model(model)[1])


def dispense(model: str, eid: str = None) -> _model.Content:
    """Dispense content entity
    """
    e = odm.dispense(model, eid)

    if not isinstance(e, _model.Content):
        raise TypeError("Model '{}' is not registered as a content model".format(model))

    return e


def find(model: str, **kwargs) -> odm.SingleModelFinder:
    """Instantiate content entities finder
    """
    check_publish_time = kwargs.get('check_publish_time', True)
    language = kwargs.get('language', lang.get_current())
    status = kwargs.get('status', [CONTENT_STATUS_PUBLISHED])

    if not is_model_registered(model):
        raise KeyError(f"Model '{model}' is not registered as content model")

    f = odm.find(model)
    mock = f.mock  # type: _model.Content

    # Publish time
    if mock.has_field('publish_time'):
        f.sort([('publish_time', odm.I_DESC)])
        if check_publish_time:
            f.lte('publish_time', datetime.now()).no_cache('publish_time')
    else:
        f.sort([('_modified', odm.I_DESC)])

    # Language
    if language != '*' and mock.has_field('language'):
        f.eq('language', language)

    # Status
    if status != '*' and mock.has_field('status'):
        if isinstance(status, str):
            status = [status]
        elif not isinstance(status, (list, tuple)):
            raise TypeError(f"'status' must be a string, list or tuple, not {type(status)}")

        f.inc('status', status)

    return f


def find_by_url(url: str) -> _model.Content:
    """Find an entity by an URL
    """
    parsed_url = _urllib_parse.urlsplit(url, allow_fragments=False)

    try:
        r_alias = route_alias.get_by_alias(parsed_url[2])

        # Path should have format `/content/view/{model}/{id}`
        parsed_path = r_alias.target.split('/')
        if len(parsed_path) == 5:
            return dispense(parsed_path[3], parsed_path[4])
    except route_alias.error.RouteAliasNotFound:
        pass


def generate_rss(model: str, filename: str, lng: str = '*',
                 finder_setup: Callable[[odm.SingleModelFinder], None] = None,
                 item_setup: Callable[[feed.xml.Serializable, _model.Content], None] = None, length: int = 20):
    """Generate RSS feeds
    """
    # Setup finder
    finder = find(model, language=lng)
    if finder_setup:
        finder_setup(finder)

    # Preparing output directory
    output_dir = path.join(reg.get('paths.static'), 'feed')
    if not path.exists(output_dir):
        makedirs(output_dir, 0o755, True)

    # Create generator
    content_settings = reg.get('content')
    parser = feed.rss.Parser()

    # Get <channel> element
    channel = parser.get_children('channel')[0]

    # Channel title
    channel.append_child(feed.rss.em.Title(content_settings.get('home_title_' + lng) or 'UNTITLED'))

    # Channel description
    channel.append_child(feed.rss.em.Description(content_settings.get('home_description_' + lng)))

    # Channel link
    channel.append_child(feed.rss.em.Link(router.base_url()))

    # Channel language
    channel.append_child(feed.rss.em.Language(lng))

    # Channel logo
    logo_url = router.url(reg.get('content.rss_logo_url', 'assets/app/img/logo-rss.png'))
    channel.append_child(feed.rss.yandex.Logo(logo_url))
    square_logo_url = router.url(reg.get('content.rss_square_logo_url', 'assets/app/img/logo-rss-square.png'))
    channel.append_child(feed.rss.yandex.Logo(square_logo_url, square=True))

    # Append channel's items
    for entity in finder.get(length):
        item = feed.rss.em.Item()
        try:
            item.append_child(feed.rss.em.Title(entity.title))
            item.append_child(feed.rss.em.Link(entity.url))
            item.append_child(feed.rss.em.PdaLink(entity.url))
            item.append_child(feed.rss.em.Description(entity.description if entity.description else entity.title))
            item.append_child(feed.rss.em.PubDate(entity.publish_time))
            item.append_child(feed.rss.em.Author('{} ({})'.format(entity.author.login, entity.author.first_last_name)))
        except odm.error.FieldNotDefined:
            pass

        # Section
        if entity.has_field('section'):
            item.append_child(feed.rss.em.Category(entity.section.title))

        # Tags
        if entity.has_field('tags'):
            for tag in entity.tags:
                item.append_child(feed.rss.pytsite.Tag(tag.title))

        # Images
        if entity.has_field('images') and entity.images:
            # Attaching all the images as enclosures
            for img in entity.images:
                item.append_child(feed.rss.em.Enclosure(url=img.get_url(), length=img.length, type=img.mime))

        # Video links
        if entity.has_field('video_links') and entity.video_links:
            m_group = item.append_child(feed.rss.media.Group())
            for link_url in entity.video_links:
                m_group.add_widget(feed.rss.media.Player(url=link_url))

        # Body
        if entity.has_field('body'):
            item.append_child(feed.rss.yandex.FullText(entity.f_get('body', process_tags=False, remove_tags=True)))
            item.append_child(feed.rss.content.Encoded(entity.f_get('body', process_tags=False, remove_tags=True)))
            item.append_child(feed.rss.pytsite.FullText(entity.f_get('body', process_tags=False)))

        if item_setup:
            item_setup(item, entity)

        channel.append_child(item)

    # Write feed content
    out_path = path.join(output_dir, '{}-{}.xml'.format(filename, lng))
    with open(out_path, 'wt', encoding='utf-8') as f:
        f.write(parser.generate())

    logger.info("RSS feed successfully written to '{}'.".format(out_path))


def paginate(finder: odm.SingleModelFinder, per_page: int = 10, css: str = '') -> dict:
    """Get paginated content finder query results
    """
    pager = widget.select.Pager('content-pager', total_items=finder.count(), per_page=per_page, css=css)

    entities = []
    for entity in finder.skip(pager.skip).get(pager.limit):
        entities.append(entity)

    return {
        'entities': entities,
        'pager': pager,
    }


def on_content_view(handler: Callable[[_model.ContentWithURL], None], priority: int = 0):
    """Shortcut
    """
    events.listen('content@view', handler, priority)
