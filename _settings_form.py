"""Content Settings Form.
"""
from pytsite import settings as _settings, widget as _widget, lang as _lang
from . import _api

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class Form(_settings.Form):
    def _on_setup_widgets(self):
        i = 10
        for l in _lang.langs():
            self.add_widget(_widget.input.Text(
                uid='setting_home_title_' + l,
                label=_lang.t('content@home_page_title', {'lang_code': l.upper()}, language=l),
                weight=i,
            ))
            i += 10

            self.add_widget(_widget.input.Text(
                uid='setting_home_description_' + l,
                label=_lang.t('content@home_page_description', {'lang_code': l.upper()}, language=l),
                weight=i,
            ))
            i += 10

            self.add_widget(_widget.input.Tokens(
                uid='setting_home_keywords_' + l,
                label=_lang.t('content@home_page_keywords', {'lang_code': l.upper()}, language=l),
                weight=i,
            ))
            i += 10

        self.add_widget(_widget.input.TextArea(
            uid='setting_add_js',
            weight=1000,
            label=_lang.t('content@additional_js_code'),
            rows=10,
        ))

        model_items = []
        for k in sorted(_api.get_models().keys()):
            if _api.dispense(k).has_field('route_alias'):
                model_items.append((k, _api.get_model_title(k)))

        if model_items:
            self.add_widget(_widget.select.Checkboxes(
                uid='setting_rss_models',
                weight=1010,
                label=_lang.t('content@generate_rss_feed_for'),
                items=model_items,
            ))

            self.add_widget(_widget.select.Checkboxes(
                uid='setting_sitemap_models',
                weight=1020,
                label=_lang.t('content@generate_sitemap_for'),
                items=model_items,
            ))

        super()._on_setup_widgets()
