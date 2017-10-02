"""PytSite Content Plugin Settings Form
"""
from pytsite import settings as _settings, widget as _widget, lang as _lang
from . import _api

__author__ = 'Alexander Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'


class Form(_settings.Form):
    def _on_setup_widgets(self):
        self.add_widget(_widget.select.Checkbox(
            uid='setting_enlarge_images',
            weight=10,
            label=_lang.t('content@enlarge_responsive_images'),
            default=True,
        ))

        model_items = []
        for k in sorted(_api.get_models().keys()):
            if _api.dispense(k).has_field('route_alias'):
                model_items.append((k, _api.get_model_title(k)))

        if model_items:
            self.add_widget(_widget.select.Checkboxes(
                uid='setting_rss_models',
                weight=20,
                label=_lang.t('content@generate_rss_feed_for'),
                items=model_items,
            ))

            self.add_widget(_widget.select.Checkboxes(
                uid='setting_sitemap_models',
                weight=30,
                label=_lang.t('content@generate_sitemap_for'),
                items=model_items,
            ))

        super()._on_setup_widgets()
