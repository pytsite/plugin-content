"""Content Console Commands.
"""
import requests as _requests
import re as _re
from random import shuffle as _shuffle, randint as _randint
from pytsite import file as _file, auth as _auth, console as _console, lang as _lang, events as _events, \
    validation as _validation
from . import _api

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

_TEXT_CLEANUP_RE = _re.compile('[,:;\?\-\.]')
_SPACES_CLEANUP_RE = _re.compile('\s{2,}')


class Generate(_console.command.Abstract):
    """Abstract command.
    """
    lorem_txt_url = 'https://baconipsum.com/api'
    lorem_txt_args = {'type': 'meat-and-filler', 'format': 'html', 'paras': 3}
    lorem_img_url = 'http://pipsum.com/1024x768'

    def get_name(self) -> str:
        """Get command's name.
        """
        return 'content:generate'

    def get_description(self) -> str:
        """Get command's description.
        """
        return _lang.t('content@console_generate_command_description')

    def get_options_help(self) -> str:
        """Get help for command's options.
        """
        return '[--author=LOGIN] [--description-len=LEN] [--images=NUM] [--lang=LANG] [--num=NUM] [--no-html] ' \
               '[--no-tags] [--no-sections] [--short] [--title-len=LEN] --model=MODEL'

    def get_options(self) -> tuple:
        """Get command options.
        """
        return (
            ('model', _validation.rule.NonEmpty(msg_id='content@model_required')),
            ('num', _validation.rule.Integer()),
            ('images', _validation.rule.Integer()),
            ('title-len', _validation.rule.Integer()),
            ('description-len', _validation.rule.Integer()),
            ('lang', _validation.rule.Regex(pattern='^[a-z]{2}$')),
            ('no-html', _validation.rule.Pass()),
            ('short', _validation.rule.Pass()),
            ('author', _validation.rule.Pass()),
            ('no-tags', _validation.rule.Pass()),
        )

    def execute(self, args: tuple = (), **kwargs):
        """Execute teh command.
        """
        _auth.switch_user_to_system()

        model = kwargs['model']

        # Checking if the content model registered
        if not _api.is_model_registered(model):
            raise _console.error.Error("'{}' is not a registered content model.".format(model))

        author_login = kwargs.get('author')
        num = int(kwargs.get('num', 10))
        images_num = int(kwargs.get('images', 1))
        language = kwargs.get('lang', _lang.get_current())
        no_html = kwargs.get('no-html')
        short = kwargs.get('short')

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
                entity.f_set('title', self._generate_title(int(kwargs.get('title-len', 7))))

            # Description
            if entity.has_field('description'):
                entity.f_set('description', self._generate_title(int(kwargs.get('description-len', 28))))

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
