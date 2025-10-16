import json

from NEMO.models import Reservation, Tool
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from NEMO_osticket.customizations import OsTicketCustomization
from NEMO_osticket.models import OstHelpTopic, get_osticket_form_fields
from NEMO_osticket.osticket_search import OsTicketSearchObject


# This custom model choice field doesn't use the field queryset to check validity
class CustomModelChoiceField(forms.ModelChoiceField):
    def to_python(self, value):
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or "pk"
            if isinstance(value, self.queryset.model):
                value = getattr(value, key)
            value = self.queryset.model.objects.all().get(**{key: value})
        except (ValueError, TypeError, self.queryset.model.DoesNotExist):
            raise ValidationError(
                self.error_messages["invalid_choice"],
                code="invalid_choice",
                params={"value": value},
            )
        return value


class OsTicketForm(forms.Form):
    message = forms.CharField(label="Description", widget=forms.Textarea())
    reservation = CustomModelChoiceField(required=False, label="Reservation", queryset=Reservation.objects.none())

    def __init__(self, *args, **kwargs):
        create_ticket_include_reservations = kwargs.pop(
            "include_reservations", OsTicketCustomization.get_bool("osticket_create_ticket_include_reservations")
        )
        super().__init__(*args, **kwargs)
        field_ordering = ["reservation", "topicId"]
        if not create_ticket_include_reservations:
            del self.fields["reservation"]
        topic_choices = []
        if settings.DATABASES.get("osticket", False):
            topic_choices = [
                (item.topic_id, item.topic)
                for item in OstHelpTopic.objects.exclude(
                    topic_id__in=OsTicketCustomization.get_list_int("osticket_create_ticket_help_topic_exclude_list")
                )
            ]
        self.fields["topicId"] = forms.ChoiceField(choices=topic_choices)
        self.fields["topicId"].label = OsTicketCustomization.get("osticket_create_ticket_help_topic_label")
        self.fields["topicId"].required = True
        for ostField in get_osticket_form_fields():
            if ostField.label not in field_ordering:
                field_ordering.append(ostField.name)
            required = ostField.flags not in [13057, 12289, 769]
            max_length = None
            if ostField.configuration:
                config_json = json.loads(ostField.configuration)
                max_length = config_json.get("length", None) or None
            if ostField.type == "text":
                self.fields[ostField.name] = forms.CharField(max_length=max_length)
                self.fields[ostField.name].label = ostField.label
                self.fields[ostField.name].required = required
            elif ostField.type == "memo":
                self.fields[ostField.name] = forms.CharField(max_length=max_length, widget=forms.Textarea())
                self.fields[ostField.name].label = ostField.label
                self.fields[ostField.name].required = required
            elif ostField.is_list_type():
                choices = [(item.id, item.value) for item in ostField.get_list_options()]
                self.fields[ostField.name] = forms.ChoiceField(choices=choices)
                self.fields[ostField.name].label = ostField.label
                self.fields[ostField.name].required = required
        if "subject" in self.fields:
            self.fields["subject"].label = OsTicketCustomization.get("osticket_create_ticket_issue_summary_label")
        if "message" in self.fields:
            self.fields["message"].label = OsTicketCustomization.get("osticket_create_ticket_message_label")
        if "subject" in field_ordering:
            field_ordering.remove("subject")
        if "message" in field_ordering:
            field_ordering.remove("message")
        field_ordering.extend(["subject", "message"])
        self.order_fields(field_ordering)


class OsTicketSearchForm(forms.Form):
    email = forms.EmailField(required=False)
    is_open = forms.NullBooleanField(required=False)
    search = forms.CharField(required=False)
    start = forms.DateTimeField(required=False)
    end = forms.DateTimeField(required=False)
    tool = forms.ModelChoiceField(required=False, queryset=Tool.objects.all())

    def get_search_object(self):
        if self.is_valid():
            return OsTicketSearchObject(**self.cleaned_data)
        return None
