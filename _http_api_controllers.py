"""PytSite Content Plugin HTTP API
"""
__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import routing as _routing, mail as _mail, lang as _lang, tpl as _tpl
from plugins import auth as _auth, odm as _odm, query as _query
from . import _api


class PatchViewsCount(_routing.Controller):
    """Increase content entity views counter by one
    """

    def exec(self) -> int:
        entity = _api.dispense(self.arg('model'), self.arg('uid'))
        if entity and entity.has_field('views_count'):
            try:
                _auth.switch_user_to_system()
                entity.f_inc('views_count').save(update_timestamp=False, pre_hooks=False, after_hooks=False)
            finally:
                _auth.restore_user()

            return entity.f_get('views_count')

        return 0


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
            _auth.switch_user_to_system()
            entity.f_set('status', 'waiting').save()
        except _odm.error.EntityNotFound:
            raise self.not_found()
        finally:
            _auth.restore_user()

        tpl_name = 'content@mail/{}/abuse'.format(_lang.get_current())
        subject = _lang.t('content@mail_subject_abuse')
        for recipient in _auth.find_users(_query.Query(_query.Eq('status', 'active'))):
            perms = ('odm_auth@modify.{}'.format(model), 'odm_auth@delete.{}'.format(model))
            if not recipient.has_permission(perms):
                continue

            body = _tpl.render(tpl_name, {'reporter': reporter, 'recipient': recipient, 'entity': entity})
            _mail.Message(entity.author.login, subject, body).send()

        return {'message': _lang.t('content@abuse_receipt_confirm')}
