from datetime import date, timedelta

import humanize
from django.contrib.auth.models import Group
from django.db.models import DurationField, ExpressionWrapper, F, Q, QuerySet
from django.dispatch import receiver
from wbcore.contrib.directory.models import Person
from wbcore.permissions.shortcuts import get_internal_users
from wbhuman_resources.signals import add_employee_activity_to_daily_brief

from wbintegrator_office365.models import CallEvent


def format_td(td: timedelta) -> str:
    total_seconds = td.total_seconds()
    if total_seconds == 0:
        return "Missed"
    elif total_seconds < 60:
        return "< 1min"
    return humanize.precisedelta(td, suppress=["hours"], minimum_unit="seconds", format="%0.0f")


def generate_call_summary(
    profiles: QuerySet[Person],
    start_date: date,
    end_date: date,
    include_detail: bool = True,
) -> str:
    calls = CallEvent.objects.filter(
        start__date__gte=start_date,
        end__date__lte=end_date,
    ).annotate(duration=ExpressionWrapper(F("end") - F("start"), output_field=DurationField()))
    message = """
    <div style="background-color: white; width: 720px;  margin-bottom: 50px">
    """
    for profile in profiles:
        call_events = calls.filter(
            participants__tenant_user__profile=profile,
        ).order_by("start")

        message += f"""
        <div style="text-align: left;">
            <p><b>{profile.computed_str}</b></p>
            <table width="100%; table-layout: fixed; border-collapse: collapse;">
                <tr>
                    <td style="width: 33.33%; text-align: center;">Total Calls: <b>{call_events.count()}</b></td>
                    <td style="width: 33.33%; text-align: center;">under 1 minute: <b>{call_events.filter(duration__lte=timedelta(seconds=60)).count()}</b></td>
                    <td style="width: 33.33%; text-align: center;">above 1 minute: <b>{call_events.filter(duration__gt=timedelta(seconds=60)).count()}</b></td>
                </tr>
            </table>
        </div>
        """
        if include_detail:
            for call_date in call_events.dates("start", "day", order="DESC"):
                call_day_events = call_events.filter(start__date=call_date)
                if call_day_events.exists():
                    message += f"<p><b>{call_date:%Y-%m-%d}:</b></p>"
                    message += "<table style='border-collapse: collapse; width: 720px; table-layout: fixed;'> \
                                <tr style='color: white; background-color: #1868ae;'> \
                                    <th style='border: 1px solid #ddd;padding: 2px 7px; width: 20px;' >Start</th> \
                                    <th style='border: 1px solid #ddd;padding: 2px 7px; width: 20px;' >End</th> \
                                    <th style='border: 1px solid #ddd;padding: 2px 7px; width: 60px;' >Duration</th> \
                                    <th style='border: 1px solid #ddd;padding: 2px 7px; width: 80px;' >Organized by</th> \
                                    <th style='border: 1px solid #ddd;padding: 2px 7px; width: 150px;' >Participants</th> \
                                </tr>"
                    for call in call_day_events:
                        participants = ",".join(
                            filter(
                                None,
                                [
                                    p.get_humanized_repr()
                                    for p in call.participants.exclude(tenant_user__profile=profile)
                                ],
                            )
                        )
                        message += f"<tr> \
                                    <td style='border: 1px solid #ddd;padding: 2px; width: 20px;' >{call.start.astimezone():%H:%M}</td> \
                                    <td style='border: 1px solid #ddd;padding: 2px; width: 20px;' >{call.end.astimezone():%H:%M}</td> \
                                    <td style='border: 1px solid #ddd;padding: 2px; width: 60px;' text-align:center;><b>{format_td(call.end - call.start)}</b></td> \
                                    <td style='border: 1px solid #ddd;padding: 2px; width: 80px;' ><b>{call.organizer.get_humanized_repr()}</b></td> \
                                    <td style='border: 1px solid #ddd;padding: 2px; width: 150px;' >{participants}</td> \
                                </tr>"
                    message += "</table><br/>"
    message += "</div>"
    return message


@receiver(add_employee_activity_to_daily_brief, sender="directory.Person")
def send_call_daily_summary(
    sender,
    instance: Person,
    val_date: date,
    daily_call_summary_receiver_group_ids: list[int] | None = None,
    daily_call_summary_profile_ids: list[int] | None = None,
    daily_call_summary_profile_group_ids: list[int] | None = None,
    **kwargs,
) -> tuple[str, str] | None:
    # if either sales or management
    if daily_call_summary_receiver_group_ids:
        groups = Group.objects.filter(id__in=daily_call_summary_receiver_group_ids)
    else:
        groups = Group.objects.filter(Q(name__iexact="sales") | Q(name__iexact="management"))
    if instance.user_account.groups.filter(id__in=groups.values("id")).exists():
        internal_users = get_internal_users().filter(is_active=True)
        profiles = Person.objects.filter(user_account__in=internal_users)
        if daily_call_summary_profile_ids:
            profiles = profiles.filter(id__in=daily_call_summary_profile_ids)
        elif daily_call_summary_profile_group_ids:
            profiles = profiles.filter(
                user_account__groups__in=Group.objects.filter(id__in=daily_call_summary_profile_group_ids)
            )

        end_date = val_date
        if val_date.weekday() == 0:
            start_date = end_date - timedelta(days=8)
            title = f"Call summary - From {start_date:%Y-%m-%d} To {end_date:%Y-%m-%d} (Weekly)"
            message = generate_call_summary(profiles, start_date=start_date, end_date=end_date, include_detail=False)
        else:
            start_date = end_date - timedelta(days=1)
            title = "Detailed Daily Call summary"
            message = generate_call_summary(profiles, start_date=start_date, end_date=end_date, include_detail=True)
        return title, message
