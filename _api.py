"""PytSite Content Plugin API Functions
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from typing import Callable as _Callable, List as _List, Union as _Union, Type as _Type, Tuple as _Tuple, Dict as _Dict
from datetime import datetime as _datetime
from urllib import parse as _urllib_parse
from os import path as _path, makedirs as _makedirs
from pytsite import util as _util, router as _router, lang as _lang, logger as _logger, reg as _reg
from plugins import odm as _odm, route_alias as _route_alias, feed as _feed, admin as _admin, widget as _widget
from . import _model

_models = {}  # type: _Dict[str, _Tuple[_Type[_model.Content], str]]


def register_model(model: str, cls: _Union[str, _Type[_model.Content]], title: str, menu_weight: int = 0,
                   menu_icon: str = 'fa fa-file-text-o', menu_sid: str = 'content', replace=False):
    """Register content model
    """
    # Resolve class
    if isinstance(cls, str):
        cls = _util.get_module_attr(cls)  # type: _Type[_model.Content]

    if not issubclass(cls, _model.Content):
        raise TypeError('Subclass of {} expected, got {}'.format(_model.Content, type(cls)))

    if not replace and is_model_registered(model):
        raise KeyError("Content model '{}' is already registered".format(model))

    # Register ODM model
    _odm.register_model(model, cls, replace)

    # Saving info about registered _content_ model
    _models[model] = (cls, title)

    if _reg.get('env.type') == 'wsgi':
        mock = dispense(model)
        perms = ['odm_auth@{}.{}'.format(p, model) for p in mock.odm_auth_permissions()],

        _admin.sidebar.add_menu(
            sid=menu_sid,
            mid=model,
            title=title,
            path=_router.rule_path('odm_ui@admin_browse', {'model': model}),
            icon=menu_icon,
            weight=menu_weight,
            permissions=perms,
            replace=replace,
        )


def is_model_registered(model: str) -> bool:
    """Check if the content model is registered
    """
    return model in _models


def get_models() -> _Dict[str, _Tuple[_Type[_model.Content], str]]:
    """Get registered content models
    """
    return _models.copy()


def get_model(model: str) -> tuple:
    """Get model information
    """
    if not is_model_registered(model):
        raise KeyError("Model '{}' is not registered as content model.".format(model))

    return _models[model]


def get_model_title(model: str) -> str:
    """Get human readable model title
    """
    return _lang.t(get_model(model)[1])


def dispense(model: str, eid: str = None) -> _model.Content:
    """Dispense content entity
    """
    e = _odm.dispense(model, eid)

    if not isinstance(e, _model.Content):
        raise TypeError("Model '{}' is not registered as a content model".format(model))

    return e


def find(model: str, **kwargs) -> _odm.Finder:
    """Instantiate content entities finder
    """
    check_publish_time = kwargs.get('check_publish_time', True)
    language = kwargs.get('language', _lang.get_current())
    status = kwargs.get('status', 'published')

    if not is_model_registered(model):
        raise KeyError("Model '{}' is not registered as content model.".format(model))
    f = _odm.find(model)

    # Publish time
    if f.mock.has_field('publish_time'):
        f.sort([('publish_time', _odm.I_DESC)])
        if check_publish_time:
            f.lte('publish_time', _datetime.now(), False)
    else:
        f.sort([('_modified', _odm.I_DESC)])

    # Language
    if language != '*' and f.mock.has_field('language'):
        f.eq('language', language)

    # Status
    if status != '*' and f.mock.has_field('status'):
        if status not in dict(get_statuses()):
            raise ValueError("'{}' is invalid content status".format(status))

        f.eq('status', status)

    return f


def find_by_url(url: str) -> _model.Content:
    """Find an entity by an URL
    """
    parsed_url = _urllib_parse.urlsplit(url, allow_fragments=False)

    try:
        r_alias = _route_alias.get_by_alias(parsed_url[2])

        # Path should have format `/content/view/{model}/{id}`
        parsed_path = r_alias.target.split('/')
        if len(parsed_path) == 5:
            return dispense(parsed_path[3], parsed_path[4])
    except _route_alias.error.RouteAliasNotFound:
        pass


def get_statuses() -> _List[_Tuple[str, str]]:
    """Get allowed content publication statuses
    """
    r = []
    for s in ('published', 'waiting', 'unpublished'):
        r.append((s, _lang.t('content@status_' + s)))

    return r


def generate_rss(model: str, filename: str, lng: str = '*', finder_setup: _Callable[[_odm.Finder], None] = None,
                 item_setup: _Callable[[_feed.xml.Serializable, _model.Content], None] = None, length: int = 20):
    """Generate RSS feeds
    """
    # Setup finder
    finder = find(model, language=lng)
    if finder_setup:
        finder_setup(finder)

    # Preparing output directory
    output_dir = _path.join(_reg.get('paths.static'), 'feed')
    if not _path.exists(output_dir):
        _makedirs(output_dir, 0o755, True)

    # Create generator
    content_settings = _reg.get('content')
    parser = _feed.rss.Parser()

    # Get <channel> element
    channel = parser.get_children('channel')[0]

    # Channel title
    channel.append_child(_feed.rss.em.Title(content_settings.get('home_title_' + lng) or 'UNTITLED'))

    # Channel description
    channel.append_child(_feed.rss.em.Description(content_settings.get('home_description_' + lng)))

    # Channel link
    channel.append_child(_feed.rss.em.Link(_router.base_url()))

    # Channel language
    channel.append_child(_feed.rss.em.Language(lng))

    # Channel logo
    logo_url = _router.url(_reg.get('content.rss_logo_url', 'assets/app/img/logo-rss.png'))
    channel.append_child(_feed.rss.yandex.Logo(logo_url))
    square_logo_url = _router.url(_reg.get('content.rss_square_logo_url', 'assets/app/img/logo-rss-square.png'))
    channel.append_child(_feed.rss.yandex.Logo(square_logo_url, square=True))

    # Append channel's items
    for entity in finder.get(length):
        item = _feed.rss.em.Item()
        try:
            item.append_child(_feed.rss.em.Title(entity.title))
            item.append_child(_feed.rss.em.Link(entity.url))
            item.append_child(_feed.rss.em.PdaLink(entity.url))
            item.append_child(_feed.rss.em.Description(entity.description if entity.description else entity.title))
            item.append_child(_feed.rss.em.PubDate(entity.publish_time))
            item.append_child(_feed.rss.em.Author('{} ({})'.format(entity.author.login, entity.author.first_last_name)))
        except _odm.error.FieldNotDefined:
            pass

        # Section
        if entity.has_field('section'):
            item.append_child(_feed.rss.em.Category(entity.section.title))

        # Tags
        if entity.has_field('tags'):
            for tag in entity.tags:
                item.append_child(_feed.rss.pytsite.Tag(tag.title))

        # Images
        if entity.has_field('images') and entity.images:
            # Attaching all the images as enclosures
            for img in entity.images:
                item.append_child(_feed.rss.em.Enclosure(url=img.get_url(), length=img.length, type=img.mime))

        # Video links
        if entity.has_field('video_links') and entity.video_links:
            m_group = item.append_child(_feed.rss.media.Group())
            for link_url in entity.video_links:
                m_group.add_widget(_feed.rss.media.Player(url=link_url))

        # Comments count
        if entity.has_field('comments_count'):
            item.append_child(_feed.rss.slash.Comments(entity.comments_count))

        # Body
        if entity.has_field('body'):
            item.append_child(_feed.rss.yandex.FullText(entity.f_get('body', process_tags=False, remove_tags=True)))
            item.append_child(_feed.rss.content.Encoded(entity.f_get('body', process_tags=False, remove_tags=True)))
            item.append_child(_feed.rss.pytsite.FullText(entity.f_get('body', process_tags=False)))

        if item_setup:
            item_setup(item, entity)

        channel.append_child(item)

    # Write feed content
    out_path = _path.join(output_dir, '{}-{}.xml'.format(filename, lng))
    with open(out_path, 'wt', encoding='utf-8') as f:
        f.write(parser.generate())

    _logger.info("RSS feed successfully written to '{}'.".format(out_path))


def paginate(finder: _odm.Finder, per_page: int = 10, css: str = '') -> dict:
    """Get paginated content finder query results
    """
    pager = _widget.select.Pager('content-pager', total_items=finder.count(), per_page=per_page, css=css)

    entities = []
    for entity in finder.skip(pager.skip).get(pager.limit):
        entities.append(entity)

    return {
        'entities': entities,
        'pager': pager,
    }
