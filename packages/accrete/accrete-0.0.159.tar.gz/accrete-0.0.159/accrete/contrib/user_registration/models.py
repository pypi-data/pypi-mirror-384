from django.db import models
from django.conf import settings


class UserConfirmationToken(models.Model):
    class Meta:
        db_table = 'user_registration_token'

    user = models.OneToOneField(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='token'
    )

    token = models.CharField(
        verbose_name='Token',
        max_length=255
    )
