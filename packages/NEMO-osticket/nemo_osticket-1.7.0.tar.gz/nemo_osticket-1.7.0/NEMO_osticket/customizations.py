import re
from logging import getLogger
from typing import Dict, Optional

from NEMO.decorators import customization
from NEMO.exceptions import InvalidCustomizationException
from NEMO.models import Reservation, Tool, User
from NEMO.views.customization import CustomizationBase
from django.core.exceptions import ValidationError
from django.core.validators import validate_comma_separated_integer_list
from django.template import Context, Template

from NEMO_osticket.models import OstFormField, OstHelpTopic, OstListItems, get_osticket_form_fields

osticket_customization_logger = getLogger(__name__)


@customization(key="osticket", title="OsTicket")
class OsTicketCustomization(CustomizationBase):
    variables = {
        "osticket_tool_control_replace_problem_tab": "",
        "osticket_tool_control_tab_name": "Help desk",
        "osticket_create_ticket_include_reservations": "",
        "osticket_create_ticket_help_topic_label": "Help Topic",
        "osticket_create_ticket_help_topic_exclude_list": "",
        "osticket_create_ticket_issue_summary_label": "Issue Summary",
        "osticket_create_ticket_message_label": "Description",
        "osticket_create_ticket_subject_template": "{% if tool %}[{{ tool.name }}] {% endif %}{{ subject }}",
        "osticket_create_ticket_message_template": "{% if tool %}Tool name: {{ tool.name }}\n{% endif %}Created by: {{ user.get_name }}\n{% if reservation %}Reservation: {{ reservation.start|date:'SHORT_DATETIME_FORMAT' }} to {{ reservation.end|date:'SHORT_DATETIME_FORMAT' }}\n{% endif %}Help topic: {{ topic }}\n\n{{ message }}",
        "osticket_tool_matching_field_id": "",
        "osticket_tool_matching_nemo_property_template": "{{ tool.id }}",
        "osticket_tool_matching_property_extract_re": "",
        "osticket_view_ticket_display_description": "",
    }

    def context(self) -> Dict:
        context_dict = super().context()
        context_dict["ticket_form_fields"] = get_osticket_form_fields(exclude_matching=False)
        context_dict["help_topics"] = OstHelpTopic.objects.all()
        context_dict["excluded_help_topic_ids"] = self.get_list_int("osticket_create_ticket_help_topic_exclude_list")
        return context_dict

    def validate(self, name, value):
        if name == "osticket_create_ticket_help_topic_exclude_list" and value:
            validate_comma_separated_integer_list(value)
        if name == "osticket_tool_matching_nemo_property_template" and value:
            try:
                Template(value).render(Context({"tool": Tool.objects.first()}))
            except Exception as e:
                raise ValidationError(str(e))
        if value and name in ["osticket_create_ticket_subject_template", "osticket_create_ticket_message_template"]:
            try:
                Template(value).render(
                    Context(
                        {
                            "subject": "Subject",
                            "message": "Message",
                            "tool": Tool.objects.first(),
                            "topic": "Topic",
                            "user": User.objects.first(),
                            "reservation": Reservation.objects.first(),
                        }
                    )
                )
            except Exception as e:
                raise ValidationError(str(e))

    def save(self, request, element=None) -> Dict[str, Dict[str, str]]:
        errors = super().save(request, element)
        excluded_topics = ",".join(request.POST.getlist("osticket_create_ticket_help_topic_exclude_list", []))
        try:
            self.validate("osticket_create_ticket_help_topic_exclude_list", excluded_topics)
            type(self).set("osticket_create_ticket_help_topic_exclude_list", excluded_topics)
        except (ValidationError, InvalidCustomizationException) as e:
            errors["osticket_create_ticket_help_topic_exclude_list"] = {
                "error": str(e.message or e.msg),
                "value": excluded_topics,
            }
        return errors

    @classmethod
    def get_osticket_tool_matching_field(cls) -> Optional[OstFormField]:
        return OstFormField.objects.filter(id=cls.get_int("osticket_tool_matching_field_id") or None).first()

    @classmethod
    def get_osticket_tool_matching_value(cls, tool: Tool) -> Optional[OstListItems]:
        field = cls.get_osticket_tool_matching_field()
        osticket_re_matching = cls.get("osticket_tool_matching_property_extract_re")
        if field:
            if field.is_list_type():
                list_options = field.get_list_options()
                if list_options:
                    for item in list_options:
                        if cls.is_tool_match(tool, item.value, osticket_re_matching):
                            return item
        return None

    @classmethod
    def get_tool_matching_nemo_property(cls, tool: Tool) -> str:
        return Template(cls.get("osticket_tool_matching_nemo_property_template")).render(Context({"tool": tool}))

    @classmethod
    def is_tool_match(cls, tool: Tool, osticket_field_value: str, osticket_re_matching=None):
        try:
            nemo_property = cls.get_tool_matching_nemo_property(tool)
            osticket_property = None
            if osticket_re_matching:
                match = re.match(rf"{osticket_re_matching}", osticket_field_value)
                if match:
                    osticket_property = match.group(1)
            if nemo_property and osticket_property:
                return nemo_property == osticket_property
        except Exception as e:
            osticket_customization_logger.error(e)
        return False
