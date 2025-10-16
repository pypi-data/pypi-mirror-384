from datetime import timedelta
from itertools import chain
from logging import getLogger
from typing import Dict, Iterable, Optional

import requests
from NEMO.forms import nice_errors
from NEMO.models import Comment, Reservation, Task, Tool, User
from NEMO.utilities import (
    export_format_datetime,
    extract_optional_beginning_and_end_times,
    format_datetime,
    render_combine_responses,
)
from NEMO.views.tool_control import tool_status as original_tool_status
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.template import Context, Template
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from NEMO_osticket.customizations import OsTicketCustomization
from NEMO_osticket.exceptions import OsTicketException
from NEMO_osticket.forms import OsTicketForm, OsTicketSearchForm
from NEMO_osticket.models import OstHelpTopic, OstListItems, OstTicket
from NEMO_osticket.osticket_search import OsTicketSearchObject

osticket_logger = getLogger(__name__)


TICKETS_PATH = "/api/tickets.json"


@login_required
@require_http_methods(["GET", "POST"])
def tickets(request):
    user: User = request.user
    search_form = OsTicketSearchForm(request.POST or None, initial={"email": user.email, "is_open": True})
    dictionary = {"form": search_form, "search_done": request.method == "POST"}
    if request.method == "POST" and search_form.is_valid():
        matching_tickets = search_form.get_search_object().search_tickets()
        dictionary["tickets"] = matching_tickets
    return render(request, "NEMO_osticket/tickets/ticket_search.html", dictionary)


@login_required
@require_GET
def tool_status(request, tool_id):
    original_response = original_tool_status(request, tool_id)
    no_osticket = not get_os_ticket_service().get("available", False) and not settings.DATABASES.get("osticket", False)
    if no_osticket or original_response.status_code != 200:
        return original_response

    dictionary = {
        "tool_id": tool_id,
        "replace_problems_tab": OsTicketCustomization.get_bool("osticket_tool_control_replace_problem_tab"),
        "tab_name": OsTicketCustomization.get("osticket_tool_control_tab_name"),
    }

    return render_combine_responses(
        request, original_response, "NEMO_osticket/tool_control/osticket_tab.html", dictionary
    )


@login_required
@require_GET
def tool_status_tickets(request, tool_id):
    tool = get_object_or_404(Tool, pk=tool_id)
    create_ticket_include_reservations = OsTicketCustomization.get_bool("osticket_create_ticket_include_reservations")
    past_week_reservations = Reservation.objects.none()
    if create_ticket_include_reservations:
        # since a week ago
        start = timezone.now() - timedelta(days=7)
        past_week_reservations = Reservation.objects.filter(
            tool_id=tool_id, missed=False, cancelled=False, shortened=False
        )
        past_week_reservations = past_week_reservations.filter(start__gte=start)
        past_week_reservations = past_week_reservations.order_by("-start")
        past_week_reservations = past_week_reservations.prefetch_related("user")

    dictionary = get_dictionary_tickets_display()
    dictionary.update(
        {
            "reservations": past_week_reservations,
            "osticket_api_available": get_os_ticket_service().get("available", False),
            "ostickets": OsTicketSearchObject(tool=tool, is_open=True).search_tickets(),
            "form": OsTicketForm(),
            "tool_id": tool_id,
        }
    )
    return render(request, "NEMO_osticket/tool_control/osticket_tab_content.html", dictionary)


@login_required
@require_http_methods(["GET", "POST"])
def create_ticket(request):
    form = OsTicketForm(request.POST or None, include_reservations=False)
    dictionary = {"form": form}
    if form.is_valid():
        try:
            create_os_ticket(request.user, form.cleaned_data, None)
            messages.success(request, "Your ticket was successfully created")
            return redirect("osticket_tickets")
        except OsTicketException as e:
            osticket_logger.exception(e)
            form.add_error(None, f"There was an error creating the ticket: {str(e)}")
    return render(request, "NEMO_osticket/tickets/create_ticket.html", dictionary)


@login_required
@require_POST
def create_tool_ticket(request, tool_id):
    tool = get_object_or_404(Tool, pk=tool_id)

    form = OsTicketForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(nice_errors(form).as_ul())

    try:
        create_os_ticket(request.user, form.cleaned_data, tool)
        messages.success(request, "Your ticket was successfully created")
    except OsTicketException as e:
        osticket_logger.exception(e)
        messages.error(request, f"There was an error creating the ticket: {str(e)}")

    return redirect("tool_control")


@login_required
@require_GET
def past_comments_and_tasks(request):
    user: User = request.user
    start, end = extract_optional_beginning_and_end_times(request.GET)
    search = request.GET.get("search")
    if not start and not end and not search:
        return HttpResponseBadRequest("Please enter a search keyword, start date or end date.")
    tool = get_object_or_404(Tool, pk=request.GET["tool_id"])
    search_object = OsTicketSearchObject(**{"tool": tool, "search": search, "start": start, "end": end})
    try:
        matching_tickets = search_object.search_tickets()
        tasks = Task.objects.filter(tool_id=tool.id)
        comments = Comment.objects.filter(tool_id=tool.id)
        if not user.is_staff:
            comments = comments.filter(staff_only=False)
        if start:
            tasks = tasks.filter(creation_time__gt=start)
            comments = comments.filter(creation_date__gt=start)
        if end:
            tasks = tasks.filter(creation_time__lt=end)
            comments = comments.filter(creation_date__lt=end)
        if search:
            tasks = tasks.filter(problem_description__icontains=search)
            comments = comments.filter(content__icontains=search)
    except:
        osticket_logger.exception("Task and comment lookup failed.")
        return HttpResponseBadRequest("Task and comment lookup failed.")
    past = list(chain(matching_tickets, tasks, comments))
    past.sort(
        key=lambda x: getattr(x, "created", None)
        or getattr(x, "creation_time", None)
        or getattr(x, "creation_date", None)
    )
    past.reverse()
    if request.GET.get("export"):
        return export_comments_and_tasks_to_text(past)
    dictionary = get_dictionary_tickets_display()
    dictionary["past"] = past
    return render(request, "NEMO_osticket/tool_control/osticket_past_tasks_and_comments.html", dictionary)


@login_required
@require_GET
def ten_most_recent_past_comments_and_tasks(request, tool_id):
    user: User = request.user
    tool = get_object_or_404(Tool, pk=tool_id)
    matching_tickets = list(OsTicketSearchObject(tool=tool, is_open=True).search_tickets())[:10]
    tasks = Task.objects.filter(tool_id=tool_id).order_by("-creation_time")[:10]
    comments = Comment.objects.filter(tool_id=tool_id).order_by("-creation_date")
    if not user.is_staff:
        comments = comments.filter(staff_only=False)
    comments = comments[:10]
    past = list(chain(matching_tickets, tasks, comments))
    past.sort(
        key=lambda x: getattr(x, "created", None)
        or getattr(x, "creation_time", None)
        or getattr(x, "creation_date", None)
    )
    past.reverse()
    past = past[0:10]
    if request.GET.get("export"):
        return export_comments_and_tasks_to_text(past)
    dictionary = get_dictionary_tickets_display()
    dictionary["past"] = past
    return render(request, "NEMO_osticket/tool_control/osticket_past_tasks_and_comments.html", dictionary)


def export_comments_and_tasks_to_text(comments_and_tasks: Iterable):
    subject_label = OsTicketCustomization.get("osticket_create_ticket_issue_summary_label")
    topic_label = OsTicketCustomization.get("osticket_create_ticket_help_topic_label")
    content = "No tickets, tasks or comments were created between these dates." if not comments_and_tasks else ""
    for item in comments_and_tasks:
        if isinstance(item, OstTicket):
            ticket: OstTicket = item
            if ticket.topic_id:
                content += f"{topic_label}: {ticket.topic.topic}\n"
            for entry in ticket.ostformentry_set:
                for entry_value in entry.ostformentryvalues_set.all():
                    if entry_value.field.name == "subject":
                        content += f"{subject_label}: {entry_value.value}\n"
            for thread in ticket.ostthread_set:
                for thread_entry in thread.ostthreadentry_set.all():
                    content += f"\nOn {format_datetime(ticket.created)}\n"
                    content += f"{strip_tags(thread_entry.body)}\n"
        if isinstance(item, Comment):
            comment: Comment = item
            staff_only = "staff only " if comment.staff_only else ""
            content += f"On {format_datetime(comment.creation_date)} {comment.author} wrote this {staff_only}comment:\n"
            content += f"{comment.content}\n"
            if comment.hide_date:
                content += f"{comment.hidden_by} hid the comment on {format_datetime(comment.hide_date)}.\n"
        elif isinstance(item, Task):
            task: Task = item
            content += f"On {format_datetime(task.creation_time)} {task.creator} created this task:\n"
            if task.problem_category:
                content += f"{task.problem_category.name}\n"
            if task.force_shutdown:
                content += "\nThe tool was shut down because of this task.\n"
            if task.progress_description:
                content += f"\n{task.progress_description}\n"
            if task.resolved:
                resolution_category = f"({task.resolution_category}) " if task.resolution_category else ""
                content += (
                    f"\nResolved {resolution_category}On {format_datetime(task.resolution_time)} by {task.resolver }.\n"
                )
                if task.resolution_description:
                    content += f"{task.resolution_description}\n"
            elif task.cancelled:
                content += f"\nCancelled On {format_datetime(task.resolution_time)} by {task.resolver}.\n"
        content += "\n---------------------------------------------------\n\n"
    response = HttpResponse(content, content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename={0}".format(
        f"comments_and_tasks_export_{export_format_datetime()}.txt"
    )
    return response


def get_dictionary_tickets_display() -> dict:
    return {
        "topic_label": OsTicketCustomization.get("osticket_create_ticket_help_topic_label"),
        "issue_summary_label": OsTicketCustomization.get("osticket_create_ticket_issue_summary_label"),
        "message_label": OsTicketCustomization.get("osticket_create_ticket_message_label"),
        "list_items": (
            {str(item.id): item.value for item in OstListItems.objects.all()}
            if settings.DATABASES.get("osticket", False)
            else {}
        ),
        "tool_matching_field_id": OsTicketCustomization.get_int("osticket_tool_matching_field_id"),
    }


def create_os_ticket(user: User, data: Dict, tool: Optional[Tool] = None):
    os_ticket_service = get_os_ticket_service()
    if os_ticket_service.get("available", False):
        try:
            full_tickets_url = os_ticket_service["url"] + TICKETS_PATH
            keyword_arguments = os_ticket_service.get("keyword_arguments", {})
            json_data = data
            # reservation cannot be serialized
            reservation = json_data.get("reservation")
            if "reservation" in json_data:
                del json_data["reservation"]
            # update with matching form field if applicable
            form_field = OsTicketCustomization.get_osticket_tool_matching_field()
            if form_field:
                if form_field.is_list_type():
                    json_data.update({form_field.name: OsTicketCustomization.get_osticket_tool_matching_value(tool).id})
                else:
                    json_data.update({form_field.name: OsTicketCustomization.get_tool_matching_nemo_property(tool)})
            json_data.update({"email": user.email, "name": user.username})
            topic = OstHelpTopic.objects.filter(topic_id=json_data.get("topicId")).first()
            topic = topic.topic if topic else None
            json_data["subject"] = format_ticket_subject(json_data["subject"], topic, tool, user, reservation)
            json_data["message"] = format_ticket_message(json_data["message"], topic, tool, user, reservation)
            response = requests.post(full_tickets_url, json=json_data, **keyword_arguments)
            response.raise_for_status()
        except Exception as e:
            raise OsTicketException(e)
    else:
        raise OsTicketException("OsTicket is not available")


def format_ticket_subject(subject: str, topic, tool: Tool, user: User, reservation: Reservation = None) -> str:
    return Template(OsTicketCustomization.get("osticket_create_ticket_subject_template")).render(
        Context({"subject": subject, "topic": topic, "tool": tool, "user": user, "reservation": reservation})
    )


def format_ticket_message(message: str, topic, tool: Tool, user: User, reservation: Reservation = None) -> str:
    return Template(OsTicketCustomization.get("osticket_create_ticket_message_template")).render(
        Context({"message": message, "topic": topic, "tool": tool, "user": user, "reservation": reservation})
    )


def get_os_ticket_service():
    return getattr(settings, "OSTICKET_SERVICE", {})


# TODO: add a hook to kiosk as well
