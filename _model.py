"""PytSite Content Plugin Content Models
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

import re as _re
from typing import Tuple as _Tuple, List as _List, Union as _Union, Iterable as _Iterable
from frozendict import frozendict as _frozendict
from datetime import datetime as _datetime
from pytsite import validation as _validation, html as _html, lang as _lang, events as _events, util as _util, \
    mail as _mail, tpl as _tpl, reg as _reg, router as _router, errors as _errors, routing as _routing
from plugins import auth as _auth, ckeditor as _ckeditor, route_alias as _route_alias, auth_ui as _auth_ui, \
    auth_storage_odm as _auth_storage_odm, file_storage_odm as _file_storage_odm, permissions as _permissions, \
    odm_ui as _odm_ui, odm as _odm, file as _file, form as _form, widget as _widget, file_ui as _file_ui, \
    admin as _admin
from ._constants import CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING, CONTENT_STATUS_PUBLISHED

_body_img_tag_re = _re.compile('\[img:(\d+)([^\]]*)\]')
_body_vid_tag_re = _re.compile('\[vid:(\d+)\]')
_html_img_tag_re = _re.compile('<img.*?src\s*=["\']([^"\']+)["\'][^>]*>')
_html_video_youtube_re = _re.compile(
    '<iframe.*?src=["\']?(?:https?:)?//www\.youtube\.com/embed/([a-zA-Z0-9_-]{11})[^"\']*["\']?.+?</iframe>'
)
_html_video_facebook_re = _re.compile(
    '<iframe.*?src=["\']?(?:https?:)?//www\.facebook\.com/plugins/video\.php\?href=([^"\']+)["\']?.+?</iframe>'
)


def _process_tags(entity, inp: str, responsive_images: bool = True, images_width: int = None) -> str:
    """Converts body tags like [img] into HTML tags

    :type entity: Content
    """
    enlarge_images_setting = _reg.get('content.enlarge_images', True)
    entity_images = entity.images if entity.has_field('images') else ()
    entity_images_count = len(entity_images)

    def process_img_tag(match):
        """Converts single body [img] tag into HTML <img> tag
        """
        nonlocal responsive_images, images_width

        # Image index
        img_index = int(match.group(1))

        # Does image exist?
        if entity_images_count < img_index:
            return ''

        img = entity_images[img_index - 1]

        # Additional parameters defaults
        link_orig = False
        link_target = '_blank'
        link_class = ''
        img_css = ''
        enlarge = enlarge_images_setting
        alt = entity.title if entity.has_field('title') else ''
        width = 0
        height = 0
        responsive = responsive_images

        for arg in match.group(2).split(':'):  # type: str
            arg = arg.strip()
            if arg in ('link_orig', 'link'):
                link_orig = True
            elif arg.startswith('link_target='):
                link_target = arg.split('=')[1]
            elif arg.startswith('link_class='):
                link_class = arg.split('=')[1]
            elif arg in ('skip_enlarge', 'no_enlarge'):
                enlarge = False
            elif arg.startswith('class='):
                img_css = arg.split('=')[1]
            elif arg.startswith('alt='):
                alt = arg.split('=')[1]
            elif arg.startswith('width='):
                responsive = False
                try:
                    width = int(arg.split('=')[1])
                except ValueError:
                    width = 0
            elif arg.startswith('height='):
                responsive = False
                try:
                    height = int(arg.split('=')[1])
                except ValueError:
                    height = 0

        if images_width:
            responsive = False
            width = images_width

        # HTML code
        if responsive:
            r = img.get_responsive_html(alt, enlarge=enlarge, css=_util.escape_html(img_css))
        else:
            r = img.get_html(alt, width=width, height=height, enlarge=enlarge, css=_util.escape_html(img_css))

        # Link to original file
        if link_orig:
            link = _html.A(r, href=img.url, target=link_target, title=_util.escape_html(alt))
            if link_class:
                link.set_attr('css', _util.escape_html(link_class))

            r = str(link)

        return r

    def process_vid_tag(match):
        """Converts single body [vid] tag into video player HTML code
        """
        vid_index = int(match.group(1))
        if len(entity.video_links) < vid_index:
            return ''

        return str(_widget.misc.VideoPlayer('content-video-' + str(vid_index), value=entity.video_links[vid_index - 1]))

    inp = _body_img_tag_re.sub(process_img_tag, inp)
    inp = _body_vid_tag_re.sub(process_vid_tag, inp)

    return inp


def _extract_images(entity) -> tuple:
    """Transforms inline HTML <img> tags into [img] tags

    :type entity: Base
    """
    # Existing images count
    img_index = len(entity.images)

    # Extracted images
    images = []

    def replace_func(match):
        nonlocal img_index, images
        img_index += 1
        images.append(_file.create(match.group(1)))

        return '[img:{}]'.format(img_index)

    body = _html_img_tag_re.sub(replace_func, entity.f_get('body', process_tags=False, remove_tags=False))

    return body, images


def _extract_video_links(entity) -> tuple:
    """Transforms embedded video players code into [vid] tags

    :type entity: Base
    """
    # Existing video links count
    vid_index = len(entity.video_links)

    vid_links = []

    def replace_func(match):
        nonlocal vid_index, vid_links
        vid_index += 1

        if 'youtube' in match.group(0):
            vid_links.append('https://youtu.be/' + match.group(1))
        elif 'facebook' in match.group(0):
            link = _re.sub('&.+$', '', _util.url_unquote(match.group(1)))
            vid_links.append(link)

        return '[vid:{}]'.format(vid_index)

    body = entity.f_get('body', process_tags=False)
    body = _html_video_youtube_re.sub(replace_func, body)
    body = _html_video_facebook_re.sub(replace_func, body)

    return body, vid_links


def _remove_tags(s: str) -> str:
    s = _body_img_tag_re.sub('', s)
    s = _body_vid_tag_re.sub('', s)

    return s


class Content(_odm_ui.model.UIEntity):
    """Base Content Model
    """

    @property
    def publish_time(self) -> _datetime:
        return self.f_get('publish_time')

    @property
    def publish_date_time_pretty(self) -> str:
        return self.f_get('publish_time', fmt='pretty_date_time')

    @property
    def publish_date_pretty(self) -> str:
        return self.f_get('publish_time', fmt='pretty_date')

    @property
    def publish_time_ago(self) -> str:
        return self.f_get('publish_time', fmt='ago')

    @property
    def prev_status(self) -> str:
        return self.f_get('prev_status')

    @property
    def status(self) -> str:
        return self.f_get('status')

    @property
    def title(self) -> str:
        """Title getter
        """
        return self.f_get('title')

    @property
    def description(self) -> str:
        """Description getter
        """
        return self.f_get('description')

    @property
    def body(self) -> str:
        """Body getter
        """
        return self.f_get('body', process_tags=True)

    @property
    def images(self) -> _Tuple[_file.model.AbstractImage]:
        """Images getter
        """
        return self.f_get('images')

    @property
    def video_links(self) -> tuple:
        """Video links getter
        """
        return self.f_get('video_links')

    @property
    def language(self) -> str:
        """Language getter
        """
        return self.f_get('language')

    @property
    def author(self) -> _auth.model.AbstractUser:
        """Author getter
        """
        return self.f_get('author')

    @property
    def options(self) -> _frozendict:
        """Options getter
        """
        return self.f_get('options')

    @property
    def likes_count(self) -> int:
        return self.f_get('likes_count')

    @property
    def bookmarks_count(self) -> int:
        return self.f_get('bookmarks_count')

    @classmethod
    def on_register(cls, model: str):
        super().on_register(model)

        perm_group = cls.odm_auth_permissions_group()
        mock = _odm.dispense(model)  # type: Content

        # Define 'bypass_moderation' permission
        if mock.has_field('status') and CONTENT_STATUS_WAITING in cls.content_statuses():
            perm_name = 'content@bypass_moderation.' + model
            perm_description = cls.resolve_lang_msg_id('content_perm_bypass_moderation_' + model)
            _permissions.define_permission(perm_name, perm_description, perm_group)

        # Define 'set_localization' permission
        if mock.has_field('localization_' + _lang.get_current()):
            perm_name = 'content@set_localization.' + model
            perm_description = cls.resolve_lang_msg_id('content_perm_set_localization_' + model)
            _permissions.define_permission(perm_name, perm_description, perm_group)

        # Define 'set_publish_time' permission
        if mock.has_field('publish_time'):
            perm_name = 'content@set_publish_time.' + model
            perm_description = cls.resolve_lang_msg_id('content_perm_set_publish_time_' + model)
            _permissions.define_permission(perm_name, perm_description, cls.odm_auth_permissions_group())

    @classmethod
    def odm_auth_permissions_group(cls) -> str:
        return 'content'

    @classmethod
    def odm_auth_permissions(cls) -> _Tuple[str, ...]:
        return 'create', 'view', 'modify', 'delete', 'view_own', 'modify_own', 'delete_own'

    @classmethod
    def content_statuses(cls) -> _List[str]:
        return [CONTENT_STATUS_PUBLISHED, CONTENT_STATUS_WAITING, CONTENT_STATUS_UNPUBLISHED]

    def _setup_fields(self):
        """Hook
        """
        now = _datetime.now()

        self.define_field(_odm.field.DateTime('publish_time', default=_datetime(now.year, now.month, now.day, 8, 0)))
        self.define_field(_odm.field.String('prev_status'))
        self.define_field(_odm.field.String('status', is_required=True, default=self.content_statuses()[0]))
        self.define_field(_odm.field.String('title', is_required=True))
        self.define_field(_odm.field.String('description'))
        self.define_field(_odm.field.String('body', strip_html=False))
        self.define_field(_file_storage_odm.field.Images('images'))
        self.define_field(_odm.field.UniqueStringList('video_links'))
        self.define_field(_odm.field.String('language', default=_lang.get_current()))
        self.define_field(_odm.field.String('language_db', is_required=True))
        self.define_field(_auth_storage_odm.field.User('author', is_required=True))
        self.define_field(_odm.field.Dict('options'))
        self.define_field(_odm.field.Integer('likes_count'))
        self.define_field(_odm.field.Integer('bookmarks_count'))

    def _setup_indexes(self):
        """Hook
        """
        self.define_index([('_created', _odm.I_DESC)])
        self.define_index([('_modified', _odm.I_DESC)])

        # Ordinary indexes
        for f in 'status', 'language', 'author', 'publish_time':
            if self.has_field(f):
                self.define_index([(f, _odm.I_ASC)])

        # Text index
        text_index_parts = []
        for f in 'title', 'description', 'body':
            if self.has_field(f):
                text_index_parts.append((f, _odm.I_TEXT))
        if text_index_parts:
            self.define_index(text_index_parts)

    def _on_f_get(self, field_name: str, value, **kwargs):
        """Hook
        """
        if field_name == 'body':
            if kwargs.get('process_tags'):
                value = _process_tags(self, value, kwargs.get('responsive_images', True),
                                      kwargs.get('images_width'))
            elif kwargs.get('remove_tags'):
                value = _remove_tags(value)

            return value

        return value

    def _on_f_set(self, field_name: str, value, **kwargs):
        """Hook
        """
        if field_name == 'language':
            if value not in _lang.langs():
                raise ValueError("Language '{}' is not supported".format(value))

            if value == 'en':
                self.f_set('language_db', 'english')
            elif value == 'ru':
                self.f_set('language_db', 'russian')
            else:
                self.f_set('language_db', 'none')

        elif field_name == 'status':
            if value not in self.content_statuses():
                raise ValueError("'{}' is invalid content status for model '{}'".format(value, self.model))
            self.f_set('prev_status', value)

        return super()._on_f_set(field_name, value, **kwargs)

    def _on_pre_save(self, **kwargs):
        """Hook
        """
        super()._on_pre_save(**kwargs)

        c_user = _auth.get_current_user()

        # Content must be reviewed by moderator
        if self.has_field('status'):
            sts = self.content_statuses()
            if CONTENT_STATUS_WAITING in sts and CONTENT_STATUS_PUBLISHED in sts \
                    and self.status == CONTENT_STATUS_PUBLISHED \
                    and not c_user.has_permission('content@bypass_moderation.' + self.model):
                self.f_set('status', CONTENT_STATUS_WAITING)

        # Language is required
        if not self.language or not self.f_get('language_db'):
            self.f_set('language', _lang.get_current())

        # Author is required
        if self.has_field('author') and self.get_field('author').is_required and not self.author:
            if not c_user.is_anonymous:
                self.f_set('author', c_user)
            else:
                raise RuntimeError('Cannot assign author, because current user is anonymous')

        # Extract inline images from the body
        if self.has_field('body') and self.has_field('images'):
            body, images = _extract_images(self)

            # If new images has been extracted
            if images:
                self.f_set('body', body)
                self.f_set('images', list(self.images) + images)

        # Extract inline videos from the body
        if self.has_field('body') and self.has_field('video_links'):
            body, video_links = _extract_video_links(self)

            # If new video links has been extracted
            if video_links:
                self.f_set('body', body)
                self.f_set('video_links', list(self.video_links) + video_links)

        _events.fire('content@entity.pre_save', entity=self)
        _events.fire('content@entity.{}.pre_save.'.format(self.model), entity=self)

    def _on_after_save(self, first_save: bool = False, **kwargs):
        """Hook
        """
        # Notify content status change
        if self.has_field('status') and self.has_field('prev_status') and self.f_is_modified('status'):
            self.content_on_status_change()

        _events.fire('content@entity.save', entity=self)
        _events.fire('content@entity.{}.save'.format(self.model), entity=self)

    def _on_after_delete(self, **kwargs):
        """Hook
        """
        # Delete all attached images
        if self.has_field('images'):
            for img in self.images:
                img.delete()

    def odm_auth_check_entity_permissions(self, perm: _Union[str, _Iterable[str]], user: _auth.AbstractUser = None):
        if not user:
            user = _auth.get_current_user()

        if perm == 'view' and self.has_field('status') and \
                self.status in (CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING) and \
                self.author != user and not user.is_admin:
            return False

        return super().odm_auth_check_entity_permissions(perm, user)

    def odm_ui_browser_setup(self, browser: _odm_ui.Browser):
        """Hook
        """
        c_user = _auth.get_current_user()
        browser.default_sort_field = '_modified'

        # Sort field
        if self.has_field('publish_time'):
            browser.default_sort_field = 'publish_time'
            browser.default_sort_order = 'desc'

        # Title
        if self.has_field('title'):
            browser.insert_data_field('title', 'content@title')

        # Status
        if self.has_field('status'):
            browser.insert_data_field('status', 'content@status')

        # Images
        if self.has_field('images'):
            browser.insert_data_field('images', 'content@images')

        # Author (visible only if current user has permission to modify any entity)
        if self.has_field('author') and c_user.has_permission('odm_auth@modify.{}'.format(browser.model)):
            browser.insert_data_field('author', 'content@author')

        # Publish time
        if self.has_field('publish_time'):
            browser.insert_data_field('publish_time', 'content@publish_time')

    def odm_ui_browser_setup_finder(self, finder: _odm.SingleModelFinder, args: _routing.ControllerArgs):
        super().odm_ui_browser_setup_finder(finder, args)

        finder.eq('language', _lang.get_current())

    def odm_ui_browser_row(self) -> dict:
        """Hook
        """
        r = {}

        # Title
        if self.has_field('title'):
            r['title'] = (str(_html.A(self.title, href=self.url)) if self.url else self.title)

        # Status
        if self.has_field('status'):
            status = self.status
            status_str = self.t('content_status_{}_{}'.format(self.model, status))
            label_css = badge_css = 'primary'
            if status == CONTENT_STATUS_WAITING:
                label_css = 'warning'
            elif status == CONTENT_STATUS_UNPUBLISHED:
                label_css = 'default'
                badge_css = 'secondary'
            status = str(_html.Span(status_str, css='label label-{} badge badge-{}'.format(label_css, badge_css)))
            r['status'] = status

        # Images
        if self.has_field('images'):
            label_css = 'default' if not len(self.images) else 'primary'
            badge_css = 'secondary' if not len(self.images) else 'primary'
            images_count = '<span class="label label-{} badge badge-{}">{}</span>'. \
                format(label_css, badge_css, len(self.images))
            r['images'] = images_count

        # Author
        u = _auth.get_current_user()
        if self.has_field('author') and u.has_permission('odm_auth@modify.{}'.format(self.model)):
            r['author'] = self.author.first_last_name if self.author else '&nbsp;'

        # Publish time
        if self.has_field('publish_time'):
            r['publish_time'] = self.f_get('publish_time', fmt='%d.%m.%Y %H:%M')

        return r

    def odm_ui_m_form_setup(self, frm: _form.Form):
        """Hook
        """
        if not self.is_new and self.has_field('language') and self.language != _lang.get_current():
            raise _errors.NotFound('Entity for this language does not exist')

        frm.css += ' content-m-form'

    def odm_ui_m_form_setup_widgets(self, frm: _form.Form):
        """Hook
        """
        from . import _widget as _content_widget
        c_user = _auth.get_current_user()

        # Title
        if self.has_field('title'):
            f = self.get_field('title')  # type: _odm.field.String
            frm.add_widget(_widget.input.Text(
                uid='title',
                label=self.t('title'),
                required=f.is_required,
                min_length=f.min_length,
                max_length=f.max_length,
                value=self.title,
            ))

        # Description
        if self.has_field('description'):
            f = self.get_field('description')  # type: _odm.field.String
            frm.add_widget(_widget.input.Text(
                uid='description',
                label=self.t('description'),
                required=self.get_field('description').is_required,
                min_length=f.min_length,
                max_length=f.max_length,
                value=self.description,
            ))

        # Images
        if self.has_field('images'):
            frm.add_widget(_file_ui.widget.ImagesUpload(
                uid='images',
                label=self.t('images'),
                value=self.f_get('images'),
                max_file_size=_reg.get('content.max_image_size', 5),
                max_files=_reg.get('content.max_images', 200),
            ))
            if self.get_field('images').is_required:
                frm.add_rule('images', _validation.rule.NonEmpty())

        # Video links
        if self.has_field('video_links'):
            frm.add_widget(_widget.input.StringList(
                uid='video_links',
                label=self.t('video'),
                add_btn_label=self.t('add_link'),
                value=self.video_links,
            ))
            frm.add_rule('video_links', _validation.rule.VideoHostingUrl())

        # Body
        if self.has_field('body'):
            frm.add_widget(_ckeditor.widget.CKEditor(
                uid='body',
                label=self.t('body'),
                value=self.f_get('body', process_tags=False),
            ))
            if self.get_field('body').is_required:
                frm.add_rule('body', _validation.rule.NonEmpty())

        # Status
        if self.has_field('status'):
            frm.add_widget(_content_widget.StatusSelect(
                uid='status',
                model=self.model,
                required=self.get_field('status').is_required,
                value=self.status,
            ))

        # Publish time
        if self.has_field('publish_time') and c_user.has_permission('content@set_publish_time.' + self.model):
            frm.add_widget(_widget.select.DateTime(
                uid='publish_time',
                label=self.t('publish_time'),
                value=self.publish_time,
                h_size='col-xs-12 col-12 col-sm-4 col-md-3',
                required=self.get_field('publish_time'),
            ))

        # Language
        lng = _lang.get_current() if self.is_new else self.language
        frm.add_widget(_widget.static.Text(
            uid='language',
            label=self.t('language'),
            text=_lang.lang_title(lng),
            value=lng,
            hidden=False if len(_lang.langs()) > 1 else True,
        ))

        # Localizations
        localization_perm = 'content@set_localization.' + self.model
        if _permissions.is_permission_defined(localization_perm) and c_user.has_permission(localization_perm) and \
                self.has_field('localization_' + lng):
            for i, l in enumerate(_lang.langs(False)):
                frm.add_widget(_content_widget.EntitySelect(
                    uid='localization_' + l,
                    label=self.t('localization', {'lang': _lang.lang_title(l)}),
                    model=self.model,
                    ajax_url_query={'language': l},
                    value=self.f_get('localization_' + l)
                ))

        # Author
        if self.has_field('author') and _auth.get_current_user().is_admin:
            frm.add_widget(_auth_ui.widget.UserSelect(
                uid='author',
                label=self.t('author'),
                value=_auth.get_current_user() if self.is_new else self.author,
                h_size='col-xs-12 col-12 col-sm-4',
                required=True,
            ))

    def odm_ui_mass_action_entity_description(self) -> str:
        """Hook
        """
        return self.title

    def odm_ui_widget_select_search_entities(self, f: _odm.MultiModelFinder, args: dict):
        """Hook
        """
        f.eq('language', args.get('language', _lang.get_current()))

        query = args.get('q')
        if query:
            f.regex('title', query, True)

    def odm_ui_widget_select_search_entities_is_visible(self, args: dict) -> bool:
        """Hook
        """
        return self.odm_auth_check_entity_permissions('view')

    def odm_ui_widget_select_search_entities_title(self, args: dict) -> str:
        """Hook
        """
        return self.title

    @classmethod
    def odm_http_api_get_entities(cls, finder: _odm.SingleModelFinder, args: _routing.ControllerArgs):
        """Called by 'odm_http_api@get_entities' route
        """
        if 'search' in args:
            query = args['search']
            if args.get('search_by') == 'title' and finder.mock.has_field('title'):
                finder.regex('title', query)
            else:
                finder.text(query, _lang.get_current())

    def _content_notify_admins_waiting_status(self):
        """Notify administrators about waiting content
        """
        if _auth.get_current_user().is_admin or self.status != CONTENT_STATUS_WAITING:
            return

        for u in _auth.get_admin_users():
            m_subject = _lang.t('content@content_waiting_mail_subject')
            m_body = _tpl.render('content@mail/{}/waiting-content'.format(_lang.get_current()), {
                'user': u,
                'entity': self,
            })
            _mail.Message(u.login, m_subject, m_body).send()

    def _content_notify_author_status_change(self):
        """Notify content author about status change by another user
        """
        if _auth.get_current_user() == self.author:
            return

        m_subject = _lang.t('content@content_status_change_mail_subject')
        m_body = _tpl.render('content@mail/{}/content-status-change'.format(_lang.get_current()), {
            'entity': self,
            'status': self.t('content_status_{}_{}'.format(self.model, self.status)),
        })
        _mail.Message(self.author.login, m_subject, m_body).send()

    def content_on_status_change(self):
        """Hook
        """
        if _reg.get('content.waiting_status_admin_notification', True):
            self._content_notify_admins_waiting_status()

        if _reg.get('content.status_change_author_notification', True):
            self._content_notify_author_status_change()

    def as_jsonable(self, **kwargs) -> dict:
        r = super().as_jsonable()

        if self.has_field('status'):
            r['status'] = self.status

        if self.has_field('title'):
            r['title'] = self.title

        if self.has_field('description'):
            r['description'] = self.description

        if self.has_field('video_links'):
            r['video_links'] = self.video_links

        if self.has_field('body'):
            r['body'] = self.body

        if self.has_field('options'):
            r['options'] = dict(self.options)

        if self.has_field('language'):
            r['language'] = self.language

        if self.has_field('images'):
            thumb_w = kwargs.get('images_thumb_width', 500)
            thumb_h = kwargs.get('images_thumb_height', 500)

            img_jsonable_args = {
                'thumb_width': thumb_w,
                'thumb_height': thumb_h,
            }
            r['images'] = [img.as_jsonable(**img_jsonable_args) for img in self.images]

            if self.images:
                r['thumbnail'] = self.images[0].get_url(width=thumb_w, height=thumb_h)

        if self.has_field('author') and self.author.is_public:
            r['author'] = self.author.as_jsonable()

        if self.has_field('publish_time'):
            r['publish_time'] = {
                'w3c': _util.w3c_datetime_str(self.publish_time),
                'pretty_date': self.publish_date_pretty,
                'pretty_date_time': self.publish_date_time_pretty,
                'ago': self.publish_time_ago,
            }

        return r


class ContentWithURL(Content):
    def _setup_fields(self):
        super()._setup_fields()

        self.define_field(_odm.field.String('tmp_route_alias_str'))
        self.define_field(_odm.field.Ref('route_alias', model='route_alias'))

    def _setup_indexes(self):
        super()._setup_indexes()

        if self.has_field('route_alias'):
            self.define_index([('route_alias', _odm.I_ASC)])

    @property
    def route_alias(self) -> _route_alias.model.RouteAlias:
        return self.f_get('route_alias')

    @classmethod
    def odm_ui_view_rule(cls) -> str:
        return 'content@view'

    def odm_ui_view_url(self, args: dict = None, **kwargs) -> str:
        target_path = _router.url(super().odm_ui_view_url(args, **kwargs), add_lang_prefix=False, as_list=True)[2]

        try:
            target_path = _route_alias.get_by_target(target_path, self.language).alias
        except _route_alias.error.RouteAliasNotFound:
            pass

        return _router.url(target_path, lang=self.language)

    def content_breadcrumb(self, breadcrumb: _widget.select.Breadcrumb):
        """Hook
        """
        if self.has_field('title'):
            breadcrumb.append_item(self.title)

    def _on_f_set(self, field_name: str, value, **kwargs):
        """Hook
        """
        if field_name == 'route_alias' and isinstance(value, str):
            # Delegate string generation to dedicated hook
            route_alias_str = self._alter_route_alias_str(value.strip())

            # Entity doesn't have attached route alias reference
            if not self.route_alias:
                # Route target cannot be built while entity is not saved,
                # so route alias needs to be saved temporary as a string
                if self.is_new:
                    self.f_set('tmp_route_alias_str', value)
                    value = None
                else:
                    target = _router.rule_path('content@view', {'model': self.model, 'eid': self.id})
                    value = _route_alias.create(route_alias_str, target, self.language).save()
            else:
                # Existing route alias needs to be changed
                if self.route_alias.alias != route_alias_str:
                    self.route_alias.f_set('alias', route_alias_str).save()
                value = self.route_alias

        return super()._on_f_set(field_name, value, **kwargs)

    def _on_after_save(self, first_save: bool = False, **kwargs):
        """Hook
        """
        super()._on_after_save(first_save, **kwargs)

        # Auto-generate a route alias
        if self.has_field('route_alias') and not self.route_alias:
            self.f_set('route_alias', self.f_get('tmp_route_alias_str')).f_rst('tmp_route_alias_str').save(fast=True)

    def _on_after_delete(self, **kwargs):
        """Hook
        """
        super()._on_after_delete()

        # Delete linked route alias
        if self.has_field('route_alias') and self.route_alias:
            try:
                self.route_alias.delete()
            except _odm.error.EntityDeleted:
                # Entity was deleted by another instance
                pass

    def odm_ui_m_form_setup_widgets(self, frm: _form.Form):
        """Hook
        """
        super().odm_ui_m_form_setup_widgets(frm)

        if self.has_field('route_alias') and _auth.get_current_user().is_admin:
            # Route alias
            frm.add_widget(_widget.input.Text(
                uid='route_alias',
                label=self.t('path'),
                value=self.route_alias.alias if self.route_alias else '',
            ))

    def _alter_route_alias_str(self, orig_str: str) -> str:
        """Alter route alias string
        """
        # Checking original string
        if not orig_str:
            # Route alias string generation is possible only if entity's title is not empty
            if self.title:
                orig_str = '{}/{}'.format(self.model, self.title)
            else:
                # Without entity's title we cannot construct route alias string
                raise RuntimeError('Cannot generate route alias because title is empty.')

        return orig_str

    def as_jsonable(self, **kwargs):
        r = super().as_jsonable(**kwargs)

        r['url'] = self.url

        return r
