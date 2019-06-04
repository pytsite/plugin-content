"""PytSite Content Plugin HTTP API
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import routing, mail, lang, tpl
from plugins import auth, odm, query
from plugins.odm_auth import PERM_MODIFY, PERM_DELETE
from . import _api


class PatchViewsCount(routing.Controller):
    """Increase content entity views counter by one
    """

    def exec(self) -> int:
        entity = _api.dispense(self.arg('model'), self.arg('uid'))
        if entity and entity.has_field('views_count'):
            try:
                auth.switch_user_to_system()
                entity.f_inc('views_count').save(fast=True)
            finally:
                auth.restore_user()

            return entity.f_get('views_count')

        return 0


class PostAbuse(routing.Controller):
    """Report Abuse
    """

    def exec(self):
        reporter = auth.get_current_user()
        if reporter.is_anonymous:
            raise self.forbidden()

        model = self.arg('model')

        try:
            entity = _api.dispense(model, self.arg('uid'))
        except odm.error.EntityNotFound:
            raise self.not_found()

        tpl_name = 'content@mail/{}/abuse'.format(lang.get_current())
        subject = lang.t('content@mail_subject_abuse')
        for recipient in auth.find_users(query.Query(query.Eq('status', 'active'))):
            if not entity.odm_auth_check_entity_permissions([PERM_MODIFY, PERM_DELETE], recipient):
                continue

            body = tpl.render(tpl_name, {'reporter': reporter, 'recipient': recipient, 'entity': entity})
            mail.Message(entity.author.login, subject, body).send()

        return {'message': lang.t('content@abuse_receipt_confirm')}
