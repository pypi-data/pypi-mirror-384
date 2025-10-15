import colorsys

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.template.loader import render_to_string


class Theme(models.Model):

    class Meta:
        verbose_name = _('Theme')
        verbose_name_plural = _('Themes')
        db_table = 'accrete_theme'
        ordering = ['pk']
        constraints = [
            models.CheckConstraint(
                name='check_user_or_tenant',
                violation_error_message=_(
                    'A theme must be assigned either to a user or a tenant.'
                ),
                condition=(
                    models.Q(user__isnull=True) ^ models.Q(tenant__isnull=True)
                )
            )
        ]

    user = models.ForeignKey(
        verbose_name=_('User'),
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_themes',
        null=True,
        blank=True
    )

    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='accrete.Tenant',
        on_delete=models.CASCADE,
        related_name='tenant_themes',
        null=True,
        blank=True
    )

    force_tenant_theme = models.BooleanField(
        verbose_name=_('Force Tenant Theme'),
        default=False,
        help_text=_('Apply this theme regardless of user preferences')
    )

    base_theme = models.CharField(
        verbose_name=_('Base Theme'),
        choices=[
            ('light', _('Light')),
            ('dark', _('Dark')),
        ],
        default='light'
    )

    color_primary = models.CharField(
        verbose_name=_('Primary Color'),
        max_length=7,
        default='#46C68D'
    )

    color_success = models.CharField(
        verbose_name=_('Success Color'),
        max_length=7,
        default='#46C68D'
    )

    color_link = models.CharField(
        verbose_name=_('Link Color'),
        max_length=7,
        default='#65D0FE'
    )

    color_warning = models.CharField(
        verbose_name=_('Warning Color'),
        max_length=7,
        default='#FEB600'
    )

    color_danger = models.CharField(
        verbose_name=_('Danger Color'),
        max_length=7,
        default='#FF6584'
    )

    theme_markup = models.TextField(
        verbose_name=_('Theme Markup'),
        null=True,
        blank=True
    )

    def generate_markup(self) -> str:
        def hex_to_hsl(hex_color: str) -> dict:
            hex_color = hex_color.removeprefix('#')
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            rgb = [x/255.0 for x in rgb]
            h, l, s = colorsys.rgb_to_hls(*rgb)

            return {
                'h': round(h * 360),
                's': round(s * 100),
                'l': round(l * 100)
            }
        ctx = {
            'primary': hex_to_hsl(self.color_primary),
            'success': hex_to_hsl(self.color_success),
            'link': hex_to_hsl(self.color_link),
            'warning': hex_to_hsl(self.color_warning),
            'danger': hex_to_hsl(self.color_danger)
        }
        return render_to_string('ui/custom_theme.html', ctx)

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.theme_markup = self.generate_markup()
        super().save(force_insert, force_update, using, update_fields)
