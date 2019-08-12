"""PytSite Content Plugin Content Models
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

import re
import htmler
from typing import Tuple, List, Union
from frozendict import frozendict
from datetime import datetime
from dicmer import dict_merge
from pytsite import validation, lang, events, util, mail, tpl, reg, router, errors, routing
from plugins import auth, ckeditor, route_alias, auth_ui, auth_storage_odm, file_storage_odm, odm_ui, odm, file, form, \
    widget, file_ui, tag, taxonomy, comments, flag
from plugins.odm_auth import PERM_CREATE, PERM_MODIFY, PERM_DELETE, PERM_MODIFY_OWN, PERM_DELETE_OWN
from ._constants import CONTENT_PERM_VIEW, CONTENT_PERM_VIEW_OWN, CONTENT_PERM_BYPASS_MODERATION, \
    CONTENT_PERM_SET_PUBLISH_TIME, CONTENT_PERM_SET_LOCALIZATION, CONTENT_STATUS_UNPUBLISHED, CONTENT_STATUS_WAITING, \
    CONTENT_STATUS_PUBLISHED

_body_img_tag_re = re.compile('\\[img:(\\d+)([^\\]]*)\\]')
_body_vid_tag_re = re.compile('\\[vid:(\\d+)\\]')
_html_img_tag_re = re.compile('<img.*?src\\s*=["\']([^"\']+)["\'][^>]*>')
_html_video_youtube_re = re.compile(
    '<iframe.*?src=["\']?(?:https?:)?//www\\.youtube\\.com/embed/([a-zA-Z0-9_-]{11})[^"\']*["\']?.+?</iframe>'
)
_html_video_facebook_re = re.compile(
    '<iframe.*?src=["\']?(?:https?:)?//www\\.facebook\\.com/plugins/video\\.php\\?href=([^"\']+)["\']?.+?</iframe>'
)


def _process_tags(entity, inp: str, responsive_images: bool = True, images_width: int = None) -> str:
    """Converts body tags like [img] into HTML tags

    :type entity: Content
    """
    enlarge_images_setting = reg.get('content.enlarge_images', True)
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
            r = img.get_responsive_html(alt, enlarge=enlarge, css=util.escape_html(img_css))
        else:
            r = img.get_html(alt, width=width, height=height, enlarge=enlarge, css=util.escape_html(img_css))

        # Link to original file
        if link_orig:
            link = htmler.A(r, href=img.url, target=link_target, title=util.escape_html(alt))
            if link_class:
                link.set_attr('css', util.escape_html(link_class))

            r = str(link)

        return r

    def process_vid_tag(match):
        """Converts single body [vid] tag into video player HTML code
        """
        vid_index = int(match.group(1))
        if len(entity.video_links) < vid_index:
            return ''

        return str(widget.misc.VideoPlayer('content-video-' + str(vid_index), value=entity.video_links[vid_index - 1]))

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
        images.append(file.create(match.group(1)))

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
            link = re.sub('&.+$', '', util.url_unquote(match.group(1)))
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


class Content(odm_ui.model.UIEntity):
    """Base Content Model
    """
    _deprecated_methods = dict_merge(odm_ui.model.UIEntity._deprecated_methods, {
        '_alter_route_alias_str': 'content_alter_route_alias_str',
    })

    @property
    def publish_time(self) -> datetime:
        """Publish time getter
        """
        return self.f_get('publish_time')

    @property
    def publish_date_time_pretty(self) -> str:
        """Publish time getter
        """
        return self.f_get('publish_time', fmt='pretty_date_time')

    @property
    def publish_date_pretty(self) -> str:
        """Publish time getter
        """
        return self.f_get('publish_time', fmt='pretty_date')

    @property
    def publish_time_ago(self) -> str:
        """Publish time getter
        """
        return self.f_get('publish_time', fmt='ago')

    @property
    def author(self) -> auth.AbstractUser:
        """Author getter
        """
        return self.f_get('author')

    @property
    def language(self) -> str:
        """Language getter
        """
        return self.f_get('language')

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
    def images(self) -> Tuple[file.model.AbstractImage]:
        """Images getter
        """
        return self.f_get('images')

    @property
    def tags(self) -> Tuple[tag.model.Tag]:
        """Tags getter
        """
        return self.f_get('tags', sort_by='weight', sort_reverse=True)

    @property
    def ext_links(self) -> Tuple[str]:
        """External links getter
        """
        return self.f_get('ext_links')

    @property
    def video_links(self) -> tuple:
        """Video links getter
        """
        return self.f_get('video_links')

    @property
    def views_count(self) -> int:
        """Views counter getter
        """
        return self.f_get('views_count')

    @property
    def comments_count(self) -> int:
        """Comments counter getter
        """
        return self.f_get('comments_count')

    @property
    def likes_count(self) -> int:
        """Likes counter getter
        """
        return self.f_get('likes_count')

    @property
    def bookmarks_count(self) -> int:
        """Bookmarks counter getter
        """
        return self.f_get('bookmarks_count')

    @property
    def status(self) -> str:
        """Status getter
        """
        return self.f_get('status')

    @property
    def prev_status(self) -> str:
        """Previous status getter
        """
        return self.f_get('prev_status')

    @property
    def options(self) -> frozendict:
        """Options getter
        """
        return self.f_get('options')

    def _setup_fields(self, **kwargs):
        """Hook
        """
        skip = kwargs.get('skip', [])

        # Publish time
        self.define_field(odm.field.DateTime('publish_time', default=datetime.now()))

        # Author
        self.define_field(auth_storage_odm.field.User('author', is_required=True))

        # Localizations
        self.define_field(odm.field.String('language', default=lang.get_current()))
        self.define_field(odm.field.String('language_db', is_required=True))
        for lng in lang.langs():
            self.define_field(odm.field.Ref('localization_' + lng, model=self.model))

        # Title
        if 'title' not in skip:
            self.define_field(odm.field.String('title', is_required=True))

        # Description
        if 'description' not in skip:
            self.define_field(odm.field.String('description'))

        # Body
        if 'body' not in skip:
            self.define_field(odm.field.String('body', is_required=True, strip_html=False))

        # Images
        if 'images' not in skip:
            self.define_field(file_storage_odm.field.Images('images'))

        # Tags
        if 'tags' not in skip:
            self.define_field(tag.field.Tags('tags'))

        # External links
        if 'ext_links' not in skip:
            self.define_field(odm.field.UniqueStringList('ext_links'))

        # Video links
        if 'video_links' not in skip:
            self.define_field(odm.field.UniqueStringList('video_links'))

        # Views counter
        if 'views_count' not in skip:
            self.define_field(odm.field.Integer('views_count'))

        # Comments counter
        if 'comments_count' not in skip:
            self.define_field(odm.field.Integer('comments_count'))

        # Likes counter
        if 'likes_count' not in skip:
            self.define_field(odm.field.Integer('likes_count'))

        # Bookmarks count
        if 'bookmarks_count' not in skip:
            self.define_field(odm.field.Integer('bookmarks_count'))

        # Status
        if 'status' not in skip:
            self.define_field(odm.field.String('prev_status', is_required=True, default=self.content_statuses()[0]))
            self.define_field(odm.field.String('status', is_required=True, default=self.content_statuses()[0]))

        # Options
        if 'options' not in skip:
            self.define_field(odm.field.Dict('options'))

    def _setup_indexes(self):
        """Hook
        """
        self.define_index([('_created', odm.I_DESC)])
        self.define_index([('_modified', odm.I_DESC)])

        # Ordinary indexes
        for f in 'status', 'language', 'author', 'publish_time', 'views_count', 'comments_count':
            if self.has_field(f):
                self.define_index([(f, odm.I_ASC)])

        # Text index
        text_index_parts = []
        for f in 'title', 'description', 'body':
            if self.has_field(f):
                text_index_parts.append((f, odm.I_TEXT))
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

        elif field_name == 'tags' and kwargs.get('as_string'):
            return ','.join([t.title for t in self.f_get('tags')])

        return value

    def _on_f_set(self, field_name: str, value, **kwargs):
        """Hook
        """
        if field_name == 'language':
            if value not in lang.langs():
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
            self.f_set('prev_status', self.f_get('status'))

        return super()._on_f_set(field_name, value, **kwargs)

    def _on_pre_save(self, **kwargs):
        """Hook
        """
        super()._on_pre_save(**kwargs)

        c_user = auth.get_current_user()

        # Content must be reviewed by moderator
        if self.has_field('status'):
            sts = self.content_statuses()
            if CONTENT_STATUS_WAITING in sts and CONTENT_STATUS_PUBLISHED in sts \
                    and self.status == CONTENT_STATUS_PUBLISHED \
                    and not self.odm_auth_check_entity_permissions(CONTENT_PERM_BYPASS_MODERATION):
                self.f_set('status', CONTENT_STATUS_WAITING)

        # Language is required
        if not self.language or not self.f_get('language_db'):
            self.f_set('language', lang.get_current())

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

        events.fire('content@entity.pre_save', entity=self)
        events.fire('content@entity.{}.pre_save.'.format(self.model), entity=self)

    def _on_after_save(self, first_save: bool = False, **kwargs):
        """Hook
        """
        from . import _api

        # Recalculate tags weights
        if first_save and self.has_field('tags'):
            for t in self.tags:
                weight = 0
                for model in _api.get_models().keys():
                    try:
                        weight += _api.find(model, language=self.language).inc('tags', [t]).count()
                    except odm.error.FieldNotDefined:
                        pass

                try:
                    auth.switch_user_to_system()
                    t.f_set('weight', weight).save(fast=True)
                finally:
                    auth.restore_user()

        # Update localization entities references
        # For each language except current one
        for lng in lang.langs(False):
            # Get localization ref for lng
            localization = self.f_get('localization_' + lng)

            # If localization is set
            if isinstance(localization, Content):
                # If localized entity hasn't reference to this entity, set it
                if localization.f_get('localization_' + self.language) != self:
                    localization.f_set('localization_' + self.language, self).save()

            # If localization is not set
            elif localization is None:
                # Clear references from localized entities
                f = _api.find(self.model, language=lng).eq('localization_' + self.language, self)
                for referenced in f.get():
                    referenced.f_set('localization_' + self.language, None).save()

        # Notify content status change
        if self.has_field('status') and self.has_field('prev_status') and self.status != self.prev_status:
            self.content_on_status_change()

        events.fire('content@entity.save', entity=self)
        events.fire('content@entity.{}.save'.format(self.model), entity=self)

    def _on_pre_delete(self, **kwargs):
        """Hook
        """
        super()._on_pre_delete(**kwargs)

        # Delete linkes, bookmarks, etc
        try:
            auth.switch_user_to_system()
            flag.delete_all(self)
        finally:
            auth.restore_user()

    def _on_after_delete(self, **kwargs):
        """Hook
        """
        # Delete all attached images
        if self.has_field('images'):
            for img in self.images:
                img.delete()

    @classmethod
    def odm_auth_permissions_group(cls) -> str:
        """Hook
        """
        return 'content'

    def odm_auth_permissions(self) -> List[str]:
        """Hook
        """
        r = [PERM_CREATE, CONTENT_PERM_VIEW, PERM_MODIFY, PERM_DELETE,
             CONTENT_PERM_VIEW_OWN, PERM_MODIFY_OWN, PERM_DELETE_OWN]

        if self.has_field('status') and CONTENT_STATUS_WAITING in self.content_statuses():
            r.append(CONTENT_PERM_BYPASS_MODERATION)

        if self.has_field('localization_' + lang.get_current()):
            r.append(CONTENT_PERM_SET_LOCALIZATION)

        if self.has_field('publish_time'):
            r.append(CONTENT_PERM_SET_PUBLISH_TIME)

        return r

    def odm_auth_check_entity_permissions(self, perm: Union[str, List[str]], user: auth.AbstractUser = None) -> bool:
        """Hook
        """
        user = user or auth.get_current_user()

        # Content should not be modified by author until it's waiting for moderation
        if perm == 'modify' \
                and self.has_field('status') \
                and self.status == CONTENT_STATUS_WAITING \
                and not self.f_is_modified('status') \
                and not self.odm_auth_check_model_permissions(self.model, CONTENT_PERM_BYPASS_MODERATION, user) \
                and not self.odm_auth_check_model_permissions(self.model, perm, user):
            return False

        return super().odm_auth_check_entity_permissions(perm, user)

    def odm_ui_browser_setup(self, browser: odm_ui.Browser):
        """Hook
        """
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
        if self.has_field('author') and self.odm_auth_check_model_permissions(self.model, PERM_MODIFY):
            browser.insert_data_field('author', 'content@author')

        # Publish time
        if self.has_field('publish_time'):
            browser.insert_data_field('publish_time', 'content@publish_time')

    def odm_ui_browser_setup_finder(self, finder: odm.SingleModelFinder, args: routing.ControllerArgs):
        super().odm_ui_browser_setup_finder(finder, args)

        finder.eq('language', lang.get_current())

    def odm_ui_browser_row(self) -> dict:
        """Hook
        """
        r = {}

        # Title
        if self.has_field('title'):
            r['title'] = (str(htmler.A(self.title, href=self.url)) if self.url else self.title)

        # Status
        if self.has_field('status'):
            status = self.status
            status_str = self.t('content_status_{}_{}'.format(self.model, status))
            label_css = badge_css = 'primary'
            if status == CONTENT_STATUS_WAITING:
                label_css = badge_css = 'warning'
            elif status == CONTENT_STATUS_UNPUBLISHED:
                label_css = 'default'
                badge_css = 'secondary'
            status = str(htmler.Span(status_str, css='label label-{} badge badge-{}'.format(label_css, badge_css)))
            r['status'] = status

        # Images
        if self.has_field('images'):
            label_css = 'default' if not len(self.images) else 'primary'
            badge_css = 'secondary' if not len(self.images) else 'primary'
            images_count = '<span class="label label-{} badge badge-{}">{}</span>'. \
                format(label_css, badge_css, len(self.images))
            r['images'] = images_count

        # Author
        if self.has_field('author') and self.odm_auth_check_model_permissions(self.model, PERM_MODIFY):
            r['author'] = self.author.first_last_name if self.author else '&nbsp;'

        # Publish time
        if self.has_field('publish_time'):
            r['publish_time'] = self.f_get('publish_time', fmt='%d.%m.%Y %H:%M')

        return r

    def odm_ui_m_form_setup(self, frm: form.Form):
        """Hook
        """
        if not self.is_new and self.has_field('language') and self.language != lang.get_current():
            raise errors.NotFound('Entity for this language does not exist')

        frm.css += ' content-m-form'

    def odm_ui_m_form_setup_widgets(self, frm: form.Form):
        """Hook
        """
        from . import widget as _content_widget

        # Title
        if self.has_field('title'):
            f = self.get_field('title')  # type: odm.field.String
            frm.add_widget(widget.input.Text(
                uid='title',
                label=self.t('title'),
                required=f.is_required,
                min_length=f.min_length,
                max_length=f.max_length,
                value=self.title,
            ))

        # Description
        if self.has_field('description'):
            f = self.get_field('description')  # type: odm.field.String
            frm.add_widget(widget.input.Text(
                uid='description',
                label=self.t('description'),
                required=self.get_field('description').is_required,
                min_length=f.min_length,
                max_length=f.max_length,
                value=self.description,
            ))

        # Images
        if self.has_field('images'):
            frm.add_widget(file_ui.widget.ImagesUpload(
                uid='images',
                label=self.t('images'),
                value=self.f_get('images'),
                max_file_size=reg.get('content.max_image_size', 5),
                max_files=reg.get('content.max_images', 200),
            ))
            if self.get_field('images').is_required:
                frm.add_rule('images', validation.rule.NonEmpty())

        # Video links
        if self.has_field('video_links'):
            frm.add_widget(widget.input.StringList(
                uid='video_links',
                label=self.t('video'),
                add_btn_label=self.t('add_link'),
                value=self.video_links,
            ))
            frm.add_rule('video_links', validation.rule.VideoHostingUrl())

        # Body
        if self.has_field('body'):
            frm.add_widget(ckeditor.widget.CKEditor(
                uid='body',
                label=self.t('body'),
                value=self.f_get('body', process_tags=False),
            ))
            if self.get_field('body').is_required:
                frm.add_rule('body', validation.rule.NonEmpty())

        # Tags
        if self.has_field('tags'):
            frm.add_widget(taxonomy.widget.TokensInput(
                uid='tags',
                weight=250,
                model='tag',
                label=self.t('tags'),
                value=self.tags,
                required=self.get_field('tags').is_required,
            ))

        # External links
        if self.has_field('ext_links'):
            frm.add_widget(widget.input.StringList(
                uid='ext_links',
                weight=550,
                label=self.t('external_links'),
                add_btn_label=self.t('add_link'),
                value=self.ext_links,
                required=self.get_field('ext_links').is_required,
            ))
            frm.add_rule('ext_links', validation.rule.Url())

        # Status
        if self.has_field('status'):
            frm.add_widget(_content_widget.StatusSelect(
                uid='status',
                entity=self,
            ))

        # Publish time
        if self.has_field('publish_time') and self.odm_auth_check_entity_permissions(CONTENT_PERM_SET_PUBLISH_TIME):
            frm.add_widget(widget.select.DateTime(
                uid='publish_time',
                label=self.t('publish_time'),
                value=self.publish_time,
                h_size='col-xs-12 col-12 col-sm-4 col-md-3',
                required=self.get_field('publish_time'),
            ))

        # Language
        lng = lang.get_current() if self.is_new else self.language
        frm.add_widget(widget.static.Text(
            uid='language',
            label=self.t('language'),
            text=lang.lang_title(lng),
            value=lng,
            hidden=False if len(lang.langs()) > 1 else True,
        ))

        # Localizations
        if self.has_field('localization_' + lng) and \
                self.odm_auth_check_entity_permissions(CONTENT_PERM_SET_LOCALIZATION):
            for i, l in enumerate(lang.langs(False)):
                frm.add_widget(_content_widget.EntitySelect(
                    uid='localization_' + l,
                    label=self.t('localization', {'lang': lang.lang_title(l)}),
                    model=self.model,
                    ajax_url_query={'language': l},
                    value=self.f_get('localization_' + l)
                ))

        # Author
        if self.has_field('author') and auth.get_current_user().is_admin:
            frm.add_widget(auth_ui.widget.UserSelect(
                uid='author',
                label=self.t('author'),
                value=auth.get_current_user() if self.is_new else self.author,
                h_size='col-xs-12 col-12 col-sm-4',
                required=True,
            ))

    def odm_ui_mass_action_entity_description(self) -> str:
        """Hook
        """
        return self.title if self.has_field('title') else super().odm_ui_mass_action_entity_description()

    def odm_ui_widget_select_search_entities(self, f: odm.MultiModelFinder, args: dict):
        """Hook
        """
        f.eq('language', args.get('language', lang.get_current()))

        query = args.get('q')
        if query:
            f.regex('title', query, True)

    def odm_ui_widget_select_search_entities_is_visible(self, args: dict) -> bool:
        """Hook
        """
        return self.odm_auth_check_entity_permissions(CONTENT_PERM_VIEW)

    def odm_ui_widget_select_search_entities_title(self, args: dict) -> str:
        """Hook
        """
        return self.title

    @classmethod
    def odm_http_api_get_entities(cls, finder: odm.SingleModelFinder, args: routing.ControllerArgs):
        """Called by 'odm_http_api@get_entities' route
        """
        if 'search' in args:
            query = args['search']
            if args.get('search_by') == 'title' and finder.mock.has_field('title'):
                finder.regex('title', query)
            else:
                finder.text(query, lang.get_current())

    @classmethod
    def content_statuses(cls) -> List[str]:
        """Hook
        """
        return [CONTENT_STATUS_PUBLISHED, CONTENT_STATUS_WAITING, CONTENT_STATUS_UNPUBLISHED]

    def content_status_select_items(self) -> List[str]:
        """Hook
        """
        statuses = self.content_statuses()
        if not self.odm_auth_check_entity_permissions(CONTENT_PERM_BYPASS_MODERATION) \
                and CONTENT_STATUS_WAITING in statuses \
                and CONTENT_STATUS_PUBLISHED in statuses:
            statuses.remove(CONTENT_STATUS_PUBLISHED)

        return statuses

    def _content_notify_admins_waiting_status(self):
        """Notify administrators about waiting content
        """
        if auth.get_current_user().is_admin or self.status != CONTENT_STATUS_WAITING:
            return

        for u in auth.get_admin_users():
            m_subject = lang.t('content@content_waiting_mail_subject')
            m_body = tpl.render('content@mail/{}/waiting-content'.format(lang.get_current()), {
                'user': u,
                'entity': self,
            })
            mail.Message(u.login, m_subject, m_body).send()

    def _content_notify_author_status_change(self):
        """Notify content author about status change by another user
        """
        if auth.get_current_user() == self.author:
            return

        m_subject = lang.t('content@content_status_change_mail_subject')
        m_body = tpl.render('content@mail/{}/content-status-change'.format(lang.get_current()), {
            'entity': self,
            'status': self.t('content_status_{}_{}'.format(self.model, self.status)),
        })
        mail.Message(self.author.login, m_subject, m_body).send()

    def content_on_status_change(self):
        """Hook
        """
        # Update publish time if entity is being published
        now = datetime.now()
        if self.prev_status == CONTENT_STATUS_UNPUBLISHED and \
                self.status in (CONTENT_STATUS_WAITING, CONTENT_STATUS_PUBLISHED) and \
                self.publish_time < now:
            self.f_set('publish_time', now).save(fast=True)

        if reg.get('content.waiting_status_admin_notification', True):
            self._content_notify_admins_waiting_status()

        if reg.get('content.status_change_author_notification', True):
            self._content_notify_author_status_change()

    def as_jsonable(self, **kwargs) -> dict:
        """Get JSONable representation of the entity
        """
        r = super().as_jsonable()

        # Publish time
        if self.has_field('publish_time'):
            r['publish_time'] = {
                'w3c': util.w3c_datetime_str(self.publish_time),
                'pretty_date': self.publish_date_pretty,
                'pretty_date_time': self.publish_date_time_pretty,
                'ago': self.publish_time_ago,
            }

        # Author
        if self.has_field('author') and self.author.is_public:
            r['author'] = self.author.as_jsonable()

        # Language
        if self.has_field('language'):
            r['language'] = self.language

        # Localizations
        for lng in lang.langs():
            if self.has_field('localization_' + lng):
                ref = self.f_get('localization_' + lng)
                if ref:
                    r['localization_' + lng] = ref.as_jsonable(**kwargs)

        # Title
        if self.has_field('title'):
            r['title'] = self.title

        # Description
        if self.has_field('description'):
            r['description'] = self.description

        # Body
        if self.has_field('body'):
            r['body'] = self.body

        # Images
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

        # Tags
        if self.has_field('tags'):
            r['tags'] = [t.as_jsonable() for t in self.tags]

        # External links
        if self.has_field('ext_links'):
            r['ext_links'] = self.ext_links

        # Video links
        if self.has_field('video_links'):
            r['video_links'] = self.video_links

        # Views counter
        if self.has_field('views_count'):
            r['views_count'] = self.views_count

        # Comments counter
        if self.has_field('comments_count'):
            r['comments_count'] = self.comments_count

        # Likes counter
        if self.has_field('likes_count'):
            r['likes_count'] = self.likes_count

        # Bookmarks counter
        if self.has_field('bookmarks_count'):
            r['bookmarks_count'] = self.bookmarks_count

        # Status
        if self.has_field('status'):
            r['status'] = self.status

        # Options
        if self.has_field('options'):
            r['options'] = dict(self.options)

        return r


class ContentWithURL(Content):
    """Content with URL model
    """

    @property
    def route_alias(self) -> route_alias.model.RouteAlias:
        """Route alias getter
        """
        return self.f_get('route_alias')

    def _setup_fields(self, **kwargs):
        """Hook
        """
        super()._setup_fields(**kwargs)

        self.define_field(odm.field.String('tmp_route_alias_str'))
        self.define_field(odm.field.Ref('route_alias', model='route_alias'))

    def _setup_indexes(self):
        """Hook
        """
        super()._setup_indexes()

        self.define_index([('route_alias', odm.I_ASC)])

    def _on_f_set(self, field_name: str, value, **kwargs):
        """Hook
        """
        if field_name == 'route_alias' and isinstance(value, str):
            # Delegate string generation to dedicated hook
            route_alias_str = self.content_alter_route_alias_str(value.strip())

            # Entity doesn't have attached route alias reference
            if not self.route_alias:
                # Route target cannot be built while entity is not saved,
                # so route alias needs to be saved temporary as a string
                if self.is_new:
                    self.f_set('tmp_route_alias_str', value)
                    value = None
                else:
                    target = router.rule_path('content@view', {'model': self.model, 'eid': self.id})
                    value = route_alias.create(route_alias_str, target, self.language).save()
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
        if not self.route_alias:
            self.f_set('route_alias', self.f_get('tmp_route_alias_str')).f_rst('tmp_route_alias_str').save(fast=True)

    def _on_after_delete(self, **kwargs):
        """Hook
        """
        super()._on_after_delete()

        # Delete comments
        try:
            auth.switch_user_to_system()
            comments.delete_thread(self.route_alias.alias)
        except (NotImplementedError, comments.error.NoDriversRegistered):
            pass
        finally:
            auth.restore_user()

        # Delete linked route alias
        try:
            self.route_alias.delete()
        except odm.error.EntityDeleted:
            # Entity was deleted by another instance
            pass

    @classmethod
    def odm_ui_view_rule(cls) -> str:
        """Hook
        """
        return 'content@view'

    def odm_ui_view_url(self, args: dict = None, **kwargs) -> str:
        """Hook
        """
        target_path = router.url(super().odm_ui_view_url(args, **kwargs), add_lang_prefix=False, as_list=True)[2]

        try:
            target_path = route_alias.get_by_target(target_path, self.language).alias
        except route_alias.error.RouteAliasNotFound:
            pass

        return router.url(target_path, lang=self.language)

    def odm_ui_m_form_setup_widgets(self, frm: form.Form):
        """Hook
        """
        super().odm_ui_m_form_setup_widgets(frm)

        if self.has_field('route_alias') and auth.get_current_user().is_admin:
            # Route alias
            frm.add_widget(widget.input.Text(
                uid='route_alias',
                label=self.t('path'),
                value=self.route_alias.alias if self.route_alias else '',
            ))

    def content_breadcrumb(self, breadcrumb: widget.select.Breadcrumb):
        """Hook
        """
        if self.has_field('title'):
            breadcrumb.append_item(self.title)

    def content_alter_route_alias_str(self, orig_str: str) -> str:
        """Hook
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
        """Get JSONable representation of the entity
        """
        r = super().as_jsonable(**kwargs)

        r['url'] = self.url

        return r
