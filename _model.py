"""Content Models
"""
import re as _re
from typing import Tuple as _Tuple
from frozendict import frozendict as _frozendict
from datetime import datetime as _datetime, timedelta as _timedelta
from pytsite import auth as _auth, odm_ui as _odm_ui, \
    file as _file, ckeditor as _ckeditor, odm as _odm, widget as _widget, validation as _validation, html as _html, \
    lang as _lang, events as _events, util as _util, form as _form, auth_storage_odm as _auth_storage_odm, \
    file_storage_odm as _file_storage_odm, mail as _mail, tpl as _tpl, reg as _reg, permissions as _permissions, \
    assetman as _assetman, router as _router, route_alias as _route_alias

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

_body_img_tag_re = _re.compile('\[img:(\d+)([^\]]*)\]')
_body_vid_tag_re = _re.compile('\[vid:(\d+)\]')
_html_img_tag_re = _re.compile('<img.*?src\s*=["\']([^"\']+)["\'][^>]*>')
_html_video_youtube_re = _re.compile(
    '<iframe.*?src=["\']?https?://www\.youtube\.com/embed/([a-zA-Z0-9_-]{11})[^"\']*["\']?.+?</iframe>'
)
_html_video_facebook_re = _re.compile(
    '<iframe.*?src=["\']?https?://www\.facebook\.com/plugins/video\.php\?href=([^"\']+)["\']?.+?</iframe>'
)


def _process_tags(entity, inp: str, responsive_images: bool = True, images_width: int = None) -> str:
    """Converts body tags like [img] into HTML tags.

    :type entity: Content
    """
    entity_images = entity.images if entity.has_field('images') else ()
    entity_images_count = len(entity_images)

    def process_img_tag(match):
        """Converts single body [img] tag into HTML <img> tag.
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
        enlarge = True
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
                link.set_attr('cls', _util.escape_html(link_class))

            r = str(link)

        return r

    def process_vid_tag(match):
        """Converts single body [vid] tag into video player HTML code.
        """
        vid_index = int(match.group(1))
        if len(entity.video_links) < vid_index:
            return ''

        return str(_widget.misc.VideoPlayer('content-video-' + str(vid_index), value=entity.video_links[vid_index - 1]))

    inp = _body_img_tag_re.sub(process_img_tag, inp)
    inp = _body_vid_tag_re.sub(process_vid_tag, inp)

    return inp


def _extract_images(entity) -> tuple:
    """Transforms inline HTML <img> tags into [img] tags.

    :type entity: Base
    """
    if not entity.author:
        raise RuntimeError('Entity author must be set before ')

    # Existing images count
    img_index = len(entity.images)

    # Extracted images
    images = []

    def replace_func(match):
        nonlocal img_index, images
        img_index += 1
        images.append(_file.create(match.group(1)))

        return '[img:{}]'.format(img_index)

    body = _html_img_tag_re.sub(replace_func, entity.body)

    return body, images


def _extract_video_links(entity) -> tuple:
    """Transforms embedded video players code into [vid] tags.

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


def _send_waiting_status_notification(entity):
    for u in _auth.get_users():
        if u.has_permission('pytsite.odm_auth.modify.' + entity.model):
            m_subject = _lang.t('content@content_waiting_mail_subject', {'app_name': _lang.t('app_name')})
            m_body = _tpl.render('content@mail/{}/propose'.format(_lang.get_current()), {
                'user': u,
                'entity': entity,
            })
            _mail.Message(u.email, m_subject, m_body).send()


class Content(_odm_ui.model.UIEntity):
    """Base Content Model.

    Just minimum amount of fields.
    """

    @classmethod
    def odm_auth_permissions_group(cls) -> str:
        return 'content'

    def _setup_fields(self):
        """Hook.
        """
        self.define_field(_odm.field.String('status', required=True, default='waiting'))
        self.define_field(_odm.field.String('title', required=True, strip_html=True))
        self.define_field(_odm.field.String('description', strip_html=True))
        self.define_field(_odm.field.String('body', tidyfy_html=True))
        self.define_field(_file_storage_odm.field.Images('images'))
        self.define_field(_odm.field.StringList('video_links', unique=True))
        self.define_field(_odm.field.String('language', required=True, default=_lang.get_current()))
        self.define_field(_odm.field.String('language_db', required=True))
        self.define_field(_auth_storage_odm.field.User('author', required=True))
        self.define_field(_odm.field.Dict('options'))

    def _setup_indexes(self):
        """Hook.
        """
        self.define_index([('_created', _odm.I_DESC)])
        self.define_index([('_modified', _odm.I_DESC)])

        # Ordinary indexes
        for f in 'status', 'language', 'author', 'options':
            if self.has_field(f):
                self.define_index([(f, _odm.I_ASC)])

        # Text index
        text_index_parts = []
        for f in 'title', 'description', 'body':
            if self.has_field(f):
                text_index_parts.append((f, _odm.I_TEXT))
        if text_index_parts:
            self.define_index(text_index_parts)

    @property
    def status(self) -> str:
        return self.f_get('status')

    @property
    def title(self) -> str:
        """Title getter.
        """
        return self.f_get('title')

    @property
    def description(self) -> str:
        """Description getter.
        """
        return self.f_get('description')

    @property
    def body(self) -> str:
        """Body getter.
        """
        return self.f_get('body', process_tags=True)

    @property
    def images(self) -> _Tuple[_file.model.AbstractImage]:
        """Images getter.
        """
        return self.f_get('images')

    @property
    def video_links(self) -> tuple:
        """Video links getter.
        """
        return self.f_get('video_links')

    @property
    def language(self) -> str:
        """Language getter.
        """
        return self.f_get('language')

    @property
    def author(self) -> _auth.model.AbstractUser:
        """Author getter.
        """
        return self.f_get('author')

    @property
    def options(self) -> _frozendict:
        """Options getter.
        """
        return self.f_get('options')

    def _on_f_get(self, field_name: str, value, **kwargs):
        """Hook.
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
        """Hook.
        """
        if field_name == 'language':
            if value not in _lang.langs():
                raise ValueError("Language '{}' is not supported.".format(value))

            if value == 'en':
                self.f_set('language_db', 'english')
            elif value == 'ru':
                self.f_set('language_db', 'russian')
            else:
                self.f_set('language_db', 'none')

        elif field_name == 'status':
            from . import _api
            if value not in [v[0] for v in _api.get_statuses()]:
                raise RuntimeError("Invalid publish status: '{}'.".format(value))

        return super()._on_f_set(field_name, value, **kwargs)

    def _pre_save(self, **kwargs):
        """Hook.
        """
        super()._pre_save(**kwargs)

        current_user = _auth.get_current_user()

        # Language is required
        if not self.language or not self.f_get('language_db'):
            self.f_set('language', _lang.get_current())

        # If author is required
        if self.has_field('author') and self.get_field('author').required and not self.author:
            if not current_user.is_anonymous:
                self.f_set('author', current_user)
            else:
                raise RuntimeError('Cannot assign author, because current user is anonymous.')

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

        _events.fire('content.entity.pre_save', entity=self)
        _events.fire('content.entity.{}.pre_save.'.format(self.model), entity=self)

    def _after_save(self, first_save: bool = False, **kwargs):
        """Hook.
        """
        if first_save:
            # Notify content moderators about waiting content
            if self.status == 'waiting' and _reg.get('content.send_waiting_notifications', True):
                _send_waiting_status_notification(self)

        _events.fire('content.entity.save', entity=self)
        _events.fire('content.entity.{}.save'.format(self.model), entity=self)

    def _after_delete(self, **kwargs):
        """Hook.
        """
        # Delete all attached images
        if self.has_field('images'):
            for img in self.images:
                img.delete()

    @classmethod
    def odm_ui_browser_setup(cls, browser: _odm_ui.Browser):
        """Setup ODM UI browser hook.
        """
        browser.finder_adjust = lambda f: f.eq('language', _lang.get_current())
        browser.default_sort_field = '_modified'

        mock = _odm.dispense(browser.model)

        # Title
        if mock.has_field('title'):
            browser.insert_data_field('title', 'content@title')

        # Status
        if mock.has_field('status'):
            browser.insert_data_field('status', 'content@status')

        # Images
        if mock.has_field('images'):
            browser.insert_data_field('images', 'content@images')

        # Author
        if mock.has_field('author'):
            browser.insert_data_field('author', 'content@author')

    def odm_ui_browser_row(self) -> list:
        """Get single UI browser row hook.
        """
        r = []

        # Title
        if self.has_field('title'):
            r.append(str(_html.A(self.title, href=self.url)) if self.url else self.title)

        # Status
        if self.has_field('status'):
            status = self.status
            status_str = self.t('status_' + status)
            status_cls = 'primary'
            if status == 'waiting':
                status_cls = 'warning'
            elif status == 'unpublished':
                status_cls = 'default'
            status = str(_html.Span(status_str, cls='label label-' + status_cls))
            r.append(status)

        # Images
        if self.has_field('images'):
            images_cls = 'default' if not len(self.images) else 'primary'
            images_count = '<span class="label label-{}">{}</span>'.format(images_cls, len(self.images))
            r.append(images_count)

        # Author
        if self.has_field('author'):
            if self.author:
                r.append(str(_html.A(self.author.full_name, href=self.author.url)))
            else:
                r.append('&nbsp;')

        return r

    def odm_ui_m_form_setup(self, frm: _form.Form):
        """Hook.
        """
        frm.css += ' content-m-form'
        _assetman.add('content@js/content.js')

    def odm_ui_m_form_setup_widgets(self, frm: _form.Form):
        """Hook.
        """
        current_user = _auth.get_current_user()

        # Title
        if self.has_field('title'):
            frm.add_widget(_widget.input.Text(
                uid='title',
                weight=200,
                label=self.t('title'),
                value=self.title,
                required=self.get_field('title').required,
            ))

        # Description
        if self.has_field('description'):
            frm.add_widget(_widget.input.Text(
                uid='description',
                weight=400,
                label=self.t('description'),
                value=self.description,
                required=self.get_field('description').required,
            ))

        # Images
        if self.has_field('images'):
            frm.add_widget(_file.widget.ImagesUpload(
                uid='images',
                weight=600,
                label=self.t('images'),
                value=self.f_get('images'),
                max_file_size=5,
                max_files=50,
            ))
            if self.get_field('images').required:
                frm.add_rule('images', _validation.rule.NonEmpty())

        # Video links
        if self.has_field('video_links'):
            frm.add_widget(_widget.input.StringList(
                uid='video_links',
                weight=800,
                label=self.t('video'),
                add_btn_label=self.t('add_link'),
                value=self.video_links,
                unique=True,
            ))
            frm.add_rule('video_links', _validation.rule.VideoHostingUrl())

        # Body
        if self.has_field('body'):
            frm.add_widget(_ckeditor.widget.CKEditor(
                uid='body',
                weight=1000,
                label=self.t('body'),
                value=self.f_get('body', process_tags=False),
            ))
            if self.get_field('body').required:
                frm.add_rule('body', _validation.rule.NonEmpty())

        # Status
        if self.has_field('status') and current_user.has_permission('content.bypass_moderation.' + self.model):
            from . import _widget as _content_widget
            frm.add_widget(_content_widget.StatusSelect(
                uid='status',
                weight=1200,
                label=self.t('status'),
                value='published' if self.is_new else self.status,
                h_size='col-sm-4 col-md-3 col-lg-2',
                required=True,
            ))

        # Language
        lng = _lang.get_current() if self.is_new else self.language
        frm.add_widget(_widget.static.Text(
            uid='language',
            weight=1400,
            label=self.t('language'),
            title=_lang.lang_title(lng),
            value=lng,
            hidden=False if len(_lang.langs()) > 1 else True,
        ))

        # Localizations
        localization_perm = 'content.set_localization.' + self.model
        if _permissions.is_permission_defined(localization_perm) and current_user.has_permission(localization_perm):
            if self.has_field('localization_' + lng):
                from . import _widget as _content_widget
                for i, lng in enumerate(_lang.langs(False)):
                    frm.add_widget(_content_widget.EntitySelect(
                        uid='localization_' + lng,
                        weight=1600 + i,
                        label=self.t('localization', {'lang': _lang.lang_title(lng)}),
                        model=self.model,
                        language=lng,
                        value=self.f_get('localization_' + lng)
                    ))

        # Visible only for admins
        if _auth.get_current_user().is_admin:
            # Author
            if self.has_field('author'):
                frm.add_widget(_auth.widget.UserSelect(
                    uid='author',
                    weight=1800,
                    label=self.t('author'),
                    value=_auth.get_current_user() if self.is_new else self.author,
                    h_size='col-sm-4',
                    required=True,
                ))

    def odm_ui_mass_action_entity_description(self) -> str:
        """Get delete form description.
        """
        return self.title

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
            img_jsonable_args = {
                'thumb_width': kwargs.get('images_thumb_width', 450),
                'thumb_height': kwargs.get('images_thumb_height', 450),
            }
            r['images'] = [img.as_jsonable(**img_jsonable_args) for img in self.images]

        if self.has_field('author') and self.author.profile_is_public:
            r['author'] = self.author.as_jsonable()

        return r


class ContentWithURL(Content):
    def _setup_fields(self):
        super()._setup_fields()

        self.define_field(_odm.field.Ref('route_alias', model='route_alias', required=True))

    def _setup_indexes(self):
        super()._setup_indexes()

        self.define_index([('route_alias', _odm.I_ASC)])

    @property
    def route_alias(self) -> _route_alias.model.RouteAlias:
        return self.f_get('route_alias')

    def odm_ui_view_url(self) -> str:
        if self.is_new:
            raise RuntimeError("Cannot generate view URL for non-saved entity of model '{}'.".format(self.model))

        target_path = _router.ep_path('content@view', {'model': self.model, 'id': str(self.id)})
        r_alias = _route_alias.get_by_target(target_path, self.language)
        value = r_alias.alias if r_alias else target_path

        return _router.url(value, lang=self.language)

    def _on_f_set(self, field_name: str, value, **kwargs):
        """Hook.
        """
        if field_name == 'route_alias' and (isinstance(value, str) or value is None):
            if value is None:
                value = ''

            # Delegate string generation to dedicated hook
            route_alias_str = self._alter_route_alias_str(value.strip())

            # No route alias is attached, so we need to create a new one
            if not self.route_alias:
                value = _route_alias.create(route_alias_str, 'NONE', self.language).save()

            # Existing route alias is attached and its value needs to be changed
            elif self.route_alias and self.route_alias.alias != route_alias_str:
                with self.route_alias:
                    self.route_alias.delete()
                value = _route_alias.create(route_alias_str, 'NONE', self.language).save()

            # Keep old route alias
            else:
                value = self.route_alias

        return super()._on_f_set(field_name, value, **kwargs)

    def _pre_save(self, **kwargs):
        """Hook.
        """
        super()._pre_save(**kwargs)

        # Route alias is required
        if not self.route_alias:
            # Setting None leads to route alias auto-generation
            self.f_set('route_alias', None)

    def _after_save(self, first_save: bool = False, **kwargs):
        """Hook.
        """
        super()._after_save(first_save, **kwargs)

        # Update route alias target which has been created in self._pre_save()
        if self.route_alias.target == 'NONE':
            with self.route_alias:
                target = _router.ep_path('content@view', {'model': self.model, 'id': self.id})
                self.route_alias.f_set('target', target).save()

        if first_save:
            # Clean up not fully filled route aliases
            f = _route_alias.find()
            f.eq('target', 'NONE').lt('_created', _datetime.now() - _timedelta(1))
            for ra in f.get():
                with ra:
                    ra.delete()

    def _after_delete(self, **kwargs):
        """Hook.
        """
        super()._after_delete()

        # Delete linked route alias
        if self.has_field('route_alias') and self.route_alias:
            with self.route_alias:
                self.route_alias.delete()

    def odm_ui_m_form_setup_widgets(self, frm: _form.Form):
        """Hook.
        """
        super().odm_ui_m_form_setup_widgets(frm)

        # Visible only for admins
        if _auth.get_current_user().is_admin:
            # Route alias
            frm.add_widget(_widget.input.Text(
                uid='route_alias',
                weight=2000,
                label=self.t('path'),
                value=self.route_alias.alias if self.route_alias else '',
            ))

    def _alter_route_alias_str(self, orig_str: str) -> str:
        """Alter route alias string.
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
