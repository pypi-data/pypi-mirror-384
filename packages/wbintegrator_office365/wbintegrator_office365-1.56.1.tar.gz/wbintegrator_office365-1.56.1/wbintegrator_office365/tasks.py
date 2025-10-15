import os
from collections import defaultdict
from datetime import date, timedelta

import boto3
import humanize
from celery import shared_task
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import DurationField, ExpressionWrapper, F, Q
from wbcore.contrib.directory.models import Person
from wbcore.contrib.notifications.dispatch import send_notification
from wbcore.permissions.shortcuts import get_internal_users

from wbintegrator_office365.importer import MicrosoftGraphAPI
from wbintegrator_office365.models.event import CallEvent
from wbintegrator_office365.models.subscription import Subscription


def format_td(td: timedelta) -> str:
    total_seconds = td.total_seconds()
    if total_seconds == 0:
        return "Missed"
    elif total_seconds < 60:
        return "< 1min"
    return humanize.precisedelta(td, suppress=["hours"], minimum_unit="seconds", format="%0.0f")


#################################################
################# TEMPORARY #####################
#################################################


def convert_user(user):
    email = user["Attributes"][0]["Value"]
    first = user["Attributes"][3]["Value"]
    last = user["Attributes"][2]["Value"]

    return f"{email} ({first} {last})"


def get_fundy_users():
    access_key = os.environ["FUNDY_BOTO_ACCESS_KEY"]
    secret_access_key = os.environ["FUNDY_BOTO_SECRET_ACCESS_KEY"]

    client = boto3.client(
        "cognito-idp", region_name="eu-north-1", aws_access_key_id=access_key, aws_secret_access_key=secret_access_key
    )

    pagination_token = None
    users = []
    while True:
        if not pagination_token:
            response = client.list_users(
                UserPoolId="eu-north-1_IFRQriJAf",
            )
        else:
            response = client.list_users(
                UserPoolId="eu-north-1_IFRQriJAf",
                PaginationToken=pagination_token,
            )

        users.extend(response["Users"])
        if response.get("PaginationToken", None) is None:
            break
        else:
            pagination_token = response["PaginationToken"]

    users_date = defaultdict(list)
    for user in sorted(users, key=lambda x: x["UserCreateDate"]):
        users_date[user["UserCreateDate"].date()].append(convert_user(user))
    return users_date, len(users)


def get_fundy_user_statistics():
    today = date.today()
    users, total_users = get_fundy_users()

    yesterday_users = users.get(today - timedelta(days=1), [])
    return yesterday_users, len(yesterday_users), total_users


#################################################
################ TEMPORARY END ##################
#################################################


@shared_task
def send_call_summary(
    to_emails: list,
    profile_ids: list[int] | None = None,
    group_id: int | None = None,
    offset: int = 0,
    include_detail: bool = True,
):
    internal_users = get_internal_users().filter(is_active=True)
    profiles = Person.objects.filter(user_account__in=internal_users)
    if profile_ids:
        profiles = profiles.filter(id__in=profile_ids)
    elif group_id:
        profiles = profiles.filter(user_account__in=Group.objects.get(id=group_id).user_set.all())

    end_date = date.today()
    start_date = end_date - timedelta(days=offset + 1)
    if offset == 0:
        frequency_repr = "Daily"
        date_repr = start_date.strftime("%Y-%m-%d")
    elif offset == 7:
        frequency_repr = "Weekly"
        date_repr = f"From {start_date:%Y-%m-%d} To {end_date:%Y-%m-%d}"
    else:
        frequency_repr = f"{offset} days"
        date_repr = f"From {start_date:%Y-%m-%d} To {end_date:%Y-%m-%d}"

    date_repr = f"{date_repr} ({frequency_repr})"
    calls = CallEvent.objects.filter(
        start__date__gte=start_date,
        end__date__lte=end_date,
    ).annotate(duration=ExpressionWrapper(F("end") - F("start"), output_field=DurationField()))
    if profiles.exists():
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

        ######## TEMPORARY START ########
        yesterday_users, yesterday_users_count, total_users_count = get_fundy_user_statistics()
        message += f"""
        <div>
        <h3>FUNDY USER STATISTICS</h3>
        <strong>Yesterday Users:</strong> {yesterday_users_count}
        <strong>Total Users:</strong> {total_users_count}
        <ul>
        """
        for user in yesterday_users:
            message += f"<li>{user}</li>"
        message += "</ul></div>"
        ######## TEMPORARY END ########

        title = f"Call summary - {date_repr}"
        if include_detail:
            title = "Detailed " + title
        for to_email in to_emails:
            recipient = get_user_model().objects.get(email=to_email)
            send_notification(
                code="wbintegrator_office365.callevent.call_summary",
                title=title,
                body=message,
                user=recipient,
            )


@shared_task
def notify_no_active_call_record_subscription(to_email):
    recipient = get_user_model().objects.filter(email=to_email)
    ms_subscriptions = [elt.get("id") for elt in MicrosoftGraphAPI().subscriptions()]
    qs_subscriptions = Subscription.objects.filter(
        Q(is_enable=True) & Q(subscription_id__isnull=False) & Q(type_resource=Subscription.TypeResource.CALLRECORD)
    )
    enable_subcriptions = qs_subscriptions.filter(subscription_id__in=ms_subscriptions)
    if recipient.exists() and (
        len(ms_subscriptions) == 0 or (qs_subscriptions.count() > 0 and enable_subcriptions.count() == 0)
    ):
        _day = date.today()
        send_notification(
            code="wbintegrator_office365.callevent.notify",
            title=f"No active Call Record subscriptions in Microsoft - {_day}",
            body=f"""<p>There are currently no active Call record subscriptions in Microsoft, so we are no longer receiving calls, Please check</p>
            <ul>
                <li>Number of subscriptions on Microsoft: <b>{len(ms_subscriptions)}</b></li>
                <li>Number of Call subscriptions: <b>{qs_subscriptions.count()}</b></li>
                <li>Number of enabled calling subscriptions: <b>{enable_subcriptions.count()}</b></li>

            </ul>
            """,
            user=recipient.first(),
        )


@shared_task
def periodic_resubscribe_task():
    for subscription in Subscription.objects.filter(
        is_enable=True, type_resource=Subscription.TypeResource.CALLRECORD, subscription_id__isnull=False
    ):
        subscription.resubscribe()
