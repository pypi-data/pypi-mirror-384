from NEMO.models import Tool
from django.apps import apps
from django.test import TestCase

from NEMO_osticket.customizations import OsTicketCustomization


class OsTicketTest(TestCase):

    def test_plugin_is_installed(self):
        assert apps.is_installed("NEMO_osticket")

    def test_matching(self):
        tool = Tool(id=2, name="Test tool", _serial="123")
        # no matching regular expression -> no match
        self.assertFalse(OsTicketCustomization.is_tool_match(tool, "2"))
        # now let's set one
        OsTicketCustomization.set("osticket_tool_matching_property_extract_re", "(\d+)")
        self.assertTrue(
            OsTicketCustomization.is_tool_match(
                tool, "2", OsTicketCustomization.get("osticket_tool_matching_property_extract_re")
            )
        )
        # try with serial number for example
        OsTicketCustomization.set("osticket_tool_matching_nemo_property_template", "{{ tool.serial }}")
        OsTicketCustomization.set("osticket_tool_matching_property_extract_re", "(\d+):")
        self.assertTrue(
            OsTicketCustomization.is_tool_match(
                tool, "123: This tool", OsTicketCustomization.get("osticket_tool_matching_property_extract_re")
            )
        )
