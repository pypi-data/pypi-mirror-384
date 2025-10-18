from datetime import date

from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Q
from wbcore.contrib.notifications.dispatch import send_notification

from wbintegrator_office365.importer import MicrosoftGraphAPI
from wbintegrator_office365.models.subscription import Subscription


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
