"""PytSite Content Plugin Helper Models
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from plugins import auth_storage_odm, odm
from . import _model


class ModelEntity(odm.Entity):
    """Authors to content entities relation
    """
    @property
    def entity_model(self) -> str:
        return self.f_get('entity_model')

    @property
    def entity(self) -> _model.Content:
        return self.f_get('entity')

    def _setup_fields(self):
        self.define_field(odm.field.String('entity_model', required=True))
        self.define_field(odm.field.Ref('entity', required=True))
        self.define_field(odm.field.DateTime('publish_time'))
        self.define_field(odm.field.String('language'))
        self.define_field(odm.field.String('status'))
        self.define_field(auth_storage_odm.field.User('author'))

    def _setup_indexes(self):
        self.define_index([('entity_model', odm.I_ASC), ('entity', odm.I_ASC)], True)
        self.define_index([('publish_time', odm.I_ASC)])
        self.define_index([('language', odm.I_ASC)])
        self.define_index([('status', odm.I_ASC)])
        self.define_index([('author', odm.I_ASC)])

    def _on_f_set(self, field_name: str, value, **kwargs):
        if field_name == 'entity':
            if not isinstance(value, _model.Content):
                raise TypeError('{} expected, got {}'.format(_model.Content, type(value)))

            self.f_set('entity_model', value.model)

            for f in ('publish_time', 'language', 'status', 'author'):
                if value.has_field(f):
                    self.f_set(f, value.f_get(f))

        return value
