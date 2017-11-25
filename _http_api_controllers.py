"""PytSite Content Plugin HTTP API
"""
from pytsite import routing as _routing, mail as _mail, lang as _lang, tpl as _tpl
from plugins import auth as _auth, odm as _odm
from . import _api

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class PatchViewsCount(_routing.Controller):
    """Increase content entity views counter by one
    """

    def exec(self) -> int:
        entity = _api.dispense(self.arg('model'), self.arg('uid'))
        if entity and entity.has_field('views_count'):
            _auth.switch_user_to_system()
            entity.f_inc('views_count').save(update_timestamp=False, pre_hooks=False, after_hooks=False)
            _auth.restore_user()

            return entity.f_get('views_count')

        return 0


class GetWidgetEntitySelectSearch(_routing.Controller):
    def exec(self) -> dict:
        # Query is mandatory parameter
        query = self.arg('q')
        if not query:
            return {'results': ()}

        # Anonymous users cannot perform search
        user = _auth.get_current_user()
        if user.is_anonymous:
            raise self.forbidden()

        model = self.arg('model')
        language = self.arg('language')

        # User can browse ANY entities
        if user.has_permission('odm_auth.view.' + model):
            f = _api.find(model, status='*', check_publish_time=None, language=language)

        # User can browse only its OWN entities
        elif user.has_permission('odm_auth.view_own.' + model):
            f = _api.find(model, status='*', check_publish_time=None, language=language)
            f.eq('author', user.uid)

        # User cannot browse entities, so its rights equals to the anonymous user
        else:
            f = _api.find(model, language=language)

        f.sort([('title', _odm.I_ASC)]).where('title', 'regex_i', query)
        r = [{'id': e.model + ':' + str(e.id), 'text': e.title} for e in f.get(20)]

        return {'results': r}


class PostAbuse(_routing.Controller):
    """Report Abuse
    """

    def exec(self):
        reporter = _auth.get_current_user()
        if reporter.is_anonymous:
            raise self.forbidden()

        model = self.arg('model')

        try:
            entity = _api.dispense(model, self.arg('uid'))
        except _odm.error.EntityNotFound:
            raise self.not_found()

        _auth.switch_user_to_system()
        entity.f_set('status', 'waiting').save()
        _auth.restore_user()

        tpl_name = 'content@mail/{}/abuse'.format(_lang.get_current())
        subject = _lang.t('content@mail_subject_abuse')
        for recipient in _auth.get_users({'status': 'active'}):
            perms = ('odm_auth.modify.{}'.format(model), 'odm_auth.delete.{}'.format(model))
            if not recipient.has_permission(perms):
                continue

            body = _tpl.render(tpl_name, {'reporter': reporter, 'recipient': recipient, 'entity': entity})
            _mail.Message(entity.author.email, subject, body).send()

        return {'message': _lang.t('content@abuse_receipt_confirm')}
