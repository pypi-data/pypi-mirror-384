from django.forms import widgets


class DateWeekday(widgets.DateInput):
    template_name = 'ui/widgets/date_weekday.html'
    input_type = 'date'
