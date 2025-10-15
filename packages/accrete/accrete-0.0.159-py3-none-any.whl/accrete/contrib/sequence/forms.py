from accrete.forms import TenantModelForm
from .models import Sequence


class SequenceCreateForm(TenantModelForm):
    class Meta:
        model = Sequence
        fields = [
            'name',
            'nextval',
            'step'
        ]
