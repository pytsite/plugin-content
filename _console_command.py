"""Content Console Commands.
"""
import requests as _requests
import re as _re
from random import shuffle as _shuffle, randint as _randint
from pytsite import file as _file, auth as _auth, console as _console, lang as _lang, events as _events
from . import _api

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

_TEXT_CLEANUP_RE = _re.compile('[,:;\?\-\.]')
_SPACES_CLEANUP_RE = _re.compile('\s{2,}')


class Generate(_console.Command):
    """Abstract command.
    """
    lorem_txt_url = 'https://baconipsum.com/api'
    lorem_txt_args = {'type': 'meat-and-filler', 'format': 'html', 'paras': 3}
    lorem_img_url = 'http://pipsum.com/1024x768'

    def __init__(self):
        super().__init__()

        self._define_option(_console.option.Bool('short'))
        self._define_option(_console.option.Bool('no-html'))
        self._define_option(_console.option.Bool('no-tags'))
        self._define_option(_console.option.Bool('no-sections'))
        self._define_option(_console.option.Str('author'))
        self._define_option(_console.option.Str('lang', default=_lang.get_current()))
        self._define_option(_console.option.PositiveInt('num', default=10))
        self._define_option(_console.option.PositiveInt('title-len', default=7))
        self._define_option(_console.option.PositiveInt('description-len', default=28))
        self._define_option(_console.option.PositiveInt('images', default=1))

        self._define_argument(_console.argument.Argument('model', True))

    @property
    def name(self) -> str:
        """Get command's name.
        """
        return 'content:generate'

    @property
    def description(self) -> str:
        """Get command's description.
        """
        return 'content@console_generate_command_description'

    def execute(self):
        """Execute teh command.
        """
        _auth.switch_user_to_system()

        model = self.get_argument_value(0)

        # Checking if the content model registered
        if not _api.is_model_registered(model):
            raise _console.error.Error("'{}' is not a registered content model.".format(model))

        author_login = self.get_option_value('author')
        num = self.get_option_value('num')
        images_num = self.get_option_value('images')
        language = self.get_option_value('lang')
        no_html = self.get_option_value('no-html')
        short = self.get_option_value('short')
        title_len = self.get_option_value('title-len')
        description_len = self.get_option_value('description-len')

        if no_html:
            self.lorem_txt_args['format'] = 'text'

        if short:
            self.lorem_txt_args['paras'] = 1

        users = list(_auth.get_users({'status': 'active'}, limit=10))

        # Generate content entities
        for m in range(0, num):
            entity = _api.dispense(model)

            # Author
            if entity.has_field('author'):
                if author_login:
                    author = _auth.get_user(author_login)
                    if not author:
                        raise _console.error.Error("'{}' is not a registered user.".format(author_login))
                else:
                    if not users:
                        raise _console.error.Error(_lang.t('content@no_users_found'))
                    rand = _randint(0, len(users) - 1)
                    author = users[rand:rand + 1][0]

                entity.f_set('author', author.uid)

            # Title
            if entity.has_field('title'):
                entity.f_set('title', self._generate_title(title_len))

            # Description
            if entity.has_field('description'):
                entity.f_set('description', self._generate_title(description_len))

            # Body
            if entity.has_field('body'):
                body = []
                for n in range(1, (images_num or 1) + 1):
                    body.append(_requests.get(self.lorem_txt_url, self.lorem_txt_args).content.decode('utf-8'))
                    if not no_html and n > 1:
                        body.append('\n<p>[img:{}]</p>\n'.format(n))

                entity.f_set('body', ''.join(body))

            # Images
            if entity.has_field('images') and images_num:
                for n in range(0, images_num):
                    entity.f_add('images', _file.create(self.lorem_img_url))

            # Language
            if entity.has_field('language'):
                entity.f_set('language', language)

            # Status
            if entity.has_field('status'):
                entity.f_set('status', 'published')

            _events.fire('content.generate', entity=entity)

            entity.save()

            _console.print_info(_lang.t('content@new_content_created', {'model': entity.model, 'title': entity.title}))

    def _generate_title(self, max_words: int = 7) -> str:
        lorem_txt_args = {'type': 'meat-and-filler', 'format': 'text', 'paras': 1}
        title = str(_requests.get(self.lorem_txt_url, lorem_txt_args).content.decode('utf-8')).strip()

        title = _SPACES_CLEANUP_RE.sub(' ', _TEXT_CLEANUP_RE.sub('', title)).split(' ')
        _shuffle(title)
        title[0] = title[0].title()
        title = ' '.join(title[0:max_words])

        return title
