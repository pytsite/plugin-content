"""PytSite Content Plugin Settings Form
"""
__author__ = 'Oleksandr Shepetko'
__email__ = 'a@shepetko.com'
__license__ = 'MIT'

from pytsite import lang
from plugins import widget, settings
from . import _api


class Form(settings.Form):
    def _on_setup_widgets(self):
        self.add_widget(widget.select.Checkbox(
            uid='setting_enlarge_images',
            weight=10,
            label=lang.t('content@enlarge_responsive_images'),
            default=True,
        ))

        self.add_widget(widget.select.Checkbox(
            uid='setting_send_waiting_notifications',
            weight=20,
            label=lang.t('content@send_waiting_notifications'),
            default=True,
        ))

        model_items = []
        for k in sorted(_api.get_models().keys()):
            if _api.dispense(k).has_field('route_alias'):
                model_items.append((k, _api.get_model_title(k)))

        if model_items:
            self.add_widget(widget.select.Checkboxes(
                uid='setting_rss_models',
                weight=20,
                label=lang.t('content@generate_rss_feed_for'),
                items=model_items,
            ))

            self.add_widget(widget.select.Checkboxes(
                uid='setting_sitemap_models',
                weight=30,
                label=lang.t('content@generate_sitemap_for'),
                items=model_items,
            ))

        super()._on_setup_widgets()
