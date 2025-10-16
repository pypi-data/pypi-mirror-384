from datetime import datetime
from logging import getLogger
from typing import Iterable, Optional, Set

from NEMO.models import Tool
from django.conf import settings
from django.db.models import Q

from NEMO_osticket.models import OstFormEntry, OstFormEntryValues, OstObjectType, OstThread, OstThreadEntry, OstTicket

search_logger = getLogger(__name__)


class OsTicketSearchObject:
    def __init__(
        self,
        email: str = None,
        is_open=None,
        search: str = None,
        start: datetime = None,
        end: datetime = None,
        tool: Tool = None,
    ):
        self.email = email
        self.is_open = is_open
        self.search = search
        self.start = start
        self.end = end
        self.tool = tool
        self.allowed_ids: Optional[Set[int]] = None

    def update_allowed_ids(self, new_allowed_ids: Optional[Iterable[int]]):
        if new_allowed_ids is not None:
            if self.allowed_ids is None:
                self.allowed_ids = set(new_allowed_ids)
            else:
                self.allowed_ids = self.allowed_ids.intersection(set(new_allowed_ids))

    def search_tickets(self) -> Set[OstTicket]:
        if not settings.DATABASES.get("osticket", False):
            return set()
        if self.email:
            self.update_allowed_ids(
                OstTicket.objects.filter(user__ostuseremail__address=self.email).values_list("ticket_id", flat=True)
            )
        # is_open can be True (open), False (closed) or None (both)
        if self.is_open is not None:
            if self.is_open:
                self.update_allowed_ids(
                    OstTicket.objects.filter(status__state="open").values_list("ticket_id", flat=True)
                )
            else:
                self.update_allowed_ids(
                    OstTicket.objects.exclude(status__state="open").values_list("ticket_id", flat=True)
                )
        if self.search:
            threads = OstThreadEntry.objects.filter(
                thread__object_type=OstObjectType.TICKET, body__icontains=self.search
            )
            form_entries = OstFormEntryValues.objects.filter(
                entry__object_type=OstObjectType.TICKET, value__icontains=self.search
            )
            if self.start:
                form_entries = form_entries.filter(entry__created__gte=self.start)
            if self.end:
                form_entries = form_entries.filter(entry__created__lte=self.end)
            if self.allowed_ids is not None:
                threads = threads.filter(thread__object_id__in=self.allowed_ids)
                form_entries = form_entries.filter(entry__object_id__in=self.allowed_ids)
            valid_thread_ticket_ids = list(threads.values_list("thread__object_id", flat=True))
            valid_form_ticket_ids = list(form_entries.values_list("entry__object_id", flat=True))
            self.update_allowed_ids(set(valid_thread_ticket_ids + valid_form_ticket_ids))
        if self.tool:
            self.update_allowed_ids(filter_tickets_for_tool(self.tool, self.allowed_ids))
        if self.allowed_ids is None:
            self.allowed_ids = OstTicket.objects.values_list("ticket_id", flat=True)
        return get_preloaded_os_tickets(self.allowed_ids, self.start, self.end)


def filter_tickets_for_tool(tool: Tool, allowed_ticket_ids=None) -> Set[int]:
    # We are making sure we are only getting tickets linked to the given tool
    from NEMO_osticket.customizations import OsTicketCustomization

    list_item = OsTicketCustomization.get_osticket_tool_matching_value(tool)
    form_field = OsTicketCustomization.get_osticket_tool_matching_field()
    form_entry_values = OstFormEntryValues.objects.filter(field=form_field, entry__object_type=OstObjectType.TICKET)
    if allowed_ticket_ids is not None:
        # Filter by specific ticket ids if available
        form_entry_values = form_entry_values.filter(entry__object_id__in=allowed_ticket_ids)
    ticket_ids = set()
    if list_item:
        # do some pre-filtering even if not perfect to see if the list id is even in there
        # we are checking for both single and double quotes for the id, should narrow it down quite a bit
        for form_entry_value in form_entry_values.filter(
            Q(value__icontains=f"'{list_item.id}'") | Q(value__icontains=f'"{list_item.id}"')
        ).prefetch_related("entry"):
            try:
                if str(list_item.id) == form_entry_value.get_list_item_id():
                    ticket_ids.add(form_entry_value.entry.object_id)
            except Exception as e:
                search_logger.debug(e)
    else:
        # just get corresponding tickets with value
        ticket_ids = (
            form_entry_values.filter(value=OsTicketCustomization.get_tool_matching_nemo_property(tool))
            .values_list("entry__object_id", flat=True)
            .distinct()
        )
    return ticket_ids


def get_preloaded_os_tickets(ticket_ids: Iterable[int], start: datetime = None, end: datetime = None) -> Set[OstTicket]:
    tickets = set()
    threads = list(
        OstThread.objects.filter(object_id__in=ticket_ids, object_type=OstObjectType.TICKET).prefetch_related(
            "ostthreadentry_set"
        )
    )
    form_entries = list(
        OstFormEntry.objects.filter(object_id__in=ticket_ids, object_type=OstObjectType.TICKET).prefetch_related(
            "ostformentryvalues_set__field"
        )
    )
    filtered_tickets = OstTicket.objects.filter(ticket_id__in=ticket_ids).order_by("-created")
    if start:
        filtered_tickets = filtered_tickets.filter(created__gte=start)
    if end:
        filtered_tickets = filtered_tickets.filter(created__lte=end)
    for ticket in filtered_tickets:
        ticket.ostthread_set = set([thread for thread in threads if thread.object_id == ticket.ticket_id])
        ticket.ostformentry_set = set(
            [form_entry for form_entry in form_entries if form_entry.object_id == ticket.ticket_id]
        )
        tickets.add(ticket)
    return tickets
