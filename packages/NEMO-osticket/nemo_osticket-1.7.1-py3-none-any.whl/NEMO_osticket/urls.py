from django.urls import include, path

from NEMO_osticket.views import osticket

urlpatterns = [
    path(
        "osticket/",
        include(
            [
                path("tickets/", osticket.tickets, name="osticket_tickets"),
                path("create_ticket/<int:tool_id>/", osticket.create_tool_ticket, name="osticket_create_tool_ticket"),
                path("create_ticket/", osticket.create_ticket, name="osticket_create_ticket"),
                path(
                    "tool_status_tickets/<int:tool_id>/",
                    osticket.tool_status_tickets,
                    name="osticket_tool_status_tickets",
                ),
            ]
        ),
    ),
    # Override tool status to add our own osticket tab
    path("tool_status/<int:tool_id>/", osticket.tool_status, name="tool_status"),
    # Override searching in past comments and tasks
    path("past_comments_and_tasks/", osticket.past_comments_and_tasks, name="past_comments_and_tasks"),
    path(
        "ten_most_recent_past_comments_and_tasks/<int:tool_id>/",
        osticket.ten_most_recent_past_comments_and_tasks,
        name="ten_most_recent_past_comments_and_tasks",
    ),
]
