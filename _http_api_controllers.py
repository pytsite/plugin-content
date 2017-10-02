"""PytSite Content Plugin HTTP API
"""
from pytsite import auth as _auth, odm as _odm, routing as _routing
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
        if user.has_permission('pytsite.odm_auth.view.' + model):
            f = _api.find(model, status='*', check_publish_time=None, language=language)

        # User can browse only its OWN entities
        elif user.has_permission('pytsite.odm_auth.view_own.' + model):
            f = _api.find(model, status='*', check_publish_time=None, language=language)
            f.eq('author', user.uid)

        # User cannot browse entities, so its rights equals to the anonymous user
        else:
            f = _api.find(model, language=language)

        f.sort([('title', _odm.I_ASC)]).where('title', 'regex_i', query)
        r = [{'id': e.model + ':' + str(e.id), 'text': e.title} for e in f.get(20)]

        return {'results': r}
