from random import randint

from celery import shared_task, group
from celery_once import QueueOnce

from django.db import transaction
from django.utils import timezone

from allianceauth.eveonline.models import EveAllianceInfo, EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger

from .app_settings import TASK_JITTER
from .models import AllianceContact, AllianceContactLabel, AllianceToken, CorporationToken, CorporationContact, CorporationContactLabel
from .provider import esi

logger = get_extension_logger(__name__)


@shared_task(base=QueueOnce, once={'graceful': True})
def load_alliance_contact_name(contact_pk: int):
    contact = AllianceContact.objects.get(pk=contact_pk)
    contact.contact_name


@shared_task(base=QueueOnce, once={'graceful': True})
def load_corporation_contact_name(contact_pk: int):
    contact = CorporationContact.objects.get(pk=contact_pk)
    contact.contact_name


@shared_task(base=QueueOnce, once={'graceful': True})
def update_alliance_contacts(alliance_id: int):
    contacts_to_load = []

    try:
        alliance = EveAllianceInfo.objects.get(alliance_id=alliance_id)
    except EveAllianceInfo.DoesNotExist:
        alliance = EveAllianceInfo.objects.create_alliance(alliance_id)

    try:
        alliance_token = AllianceToken.objects.with_valid_tokens().select_related('token').get(alliance=alliance)
    except AllianceToken.DoesNotExist:
        raise ValueError(f"No valid token found for alliance {alliance}")

    labels_data = (
        esi.client
        .Contacts
        .get_alliances_alliance_id_contacts_labels(
            alliance_id=alliance_id,
            token=alliance_token.token.valid_access_token()
        )
        .results()
    )

    labels = {label['label_id']: label['label_name'] for label in labels_data}

    contacts_data = (
        esi.client
        .Contacts
        .get_alliances_alliance_id_contacts(
            alliance_id=alliance_id,
            token=alliance_token.token.valid_access_token()
        )
        .results()
    )

    contact_ids = {
        contact['contact_id']: {
            'contact_type': contact['contact_type'],
            'label_ids': contact.get('label_ids', []),
            'standing': contact['standing']
        } for contact in contacts_data
    }

    with transaction.atomic():
        AllianceContactLabel.objects.filter(
            alliance=alliance
        ).exclude(
            label_id__in=labels.keys()
        ).delete()

        for label_id, label_name in labels.items():
            label, _ = AllianceContactLabel.objects.update_or_create(
                alliance=alliance,
                label_id=label_id,
                defaults={'label_name': label_name}
            )

            labels[label_id] = label

        missing_contacts = AllianceContact.objects.filter(
            alliance=alliance
        ).exclude(
            contact_id__in=contact_ids.keys()
        )

        missing_contacts.filter(notes='').delete()
        AllianceContact.labels.through.objects.filter(
            alliancecontact_id__in=missing_contacts.values('pk')
        ).delete()
        missing_contacts.update(standing=0.0)

        for contact_id, contact_data in contact_ids.items():
            contact, _ = AllianceContact.objects.update_or_create(
                alliance=alliance,
                contact_id=contact_id,
                defaults={
                    'contact_type': contact_data['contact_type'],
                    'standing': contact_data['standing']
                }
            )

            contact.labels.clear()
            if contact_data['label_ids'] is not None:
                contact.labels.set([labels[label_id] for label_id in contact_data['label_ids']])

            contacts_to_load.append(contact.pk)

        alliance_token.last_update = timezone.now()
        alliance_token.save()

    contacts_to_load = AllianceContact.filter_missing_contact_name(contacts_to_load)
    if len(contacts_to_load) > 0:
        group(load_alliance_contact_name.si(pk) for pk in contacts_to_load).delay()


@shared_task(base=QueueOnce, once={'graceful': True})
def update_corporation_contacts(corporation_id: int):
    contacts_to_load = []

    try:
        corporation = EveCorporationInfo.objects.get(corporation_id=corporation_id)
    except EveCorporationInfo.DoesNotExist:
        corporation = EveCorporationInfo.objects.create_corporation(corporation_id)

    try:
        corporation_token = CorporationToken.objects.with_valid_tokens().select_related('token').get(corporation=corporation)
    except CorporationToken.DoesNotExist:
        raise ValueError(f"No valid token found for alliance {corporation}")

    labels_data = (
        esi.client
        .Contacts
        .get_corporations_corporation_id_contacts_labels(
            corporation_id=corporation_id,
            token=corporation_token.token.valid_access_token()
        )
        .results()
    )

    labels = {label['label_id']: label['label_name'] for label in labels_data}

    contacts_data = (
        esi.client
        .Contacts
        .get_corporations_corporation_id_contacts(
            corporation_id=corporation_id,
            token=corporation_token.token.valid_access_token()
        )
        .results()
    )

    contact_ids = {
        contact['contact_id']: {
            'contact_type': contact['contact_type'],
            'label_ids': contact.get('label_ids', []),
            'standing': contact['standing'],
            'is_watched': contact.get('is_watched', None)
        } for contact in contacts_data
    }

    with transaction.atomic():
        CorporationContactLabel.objects.filter(
            corporation=corporation
        ).exclude(
            label_id__in=labels.keys()
        ).delete()

        for label_id, label_name in labels.items():
            label, _ = CorporationContactLabel.objects.update_or_create(
                corporation=corporation,
                label_id=label_id,
                defaults={'label_name': label_name}
            )

            labels[label_id] = label

        missing_contacts = CorporationContact.objects.filter(
            corporation=corporation
        ).exclude(
            contact_id__in=contact_ids.keys()
        )

        missing_contacts.filter(notes='').delete()
        CorporationContact.labels.through.objects.filter(
            corporationcontact_id__in=missing_contacts.values('pk')
        ).delete()
        missing_contacts.update(standing=0.0)

        for contact_id, contact_data in contact_ids.items():
            contact, _ = CorporationContact.objects.update_or_create(
                corporation=corporation,
                contact_id=contact_id,
                defaults={
                    'contact_type': contact_data['contact_type'],
                    'standing': contact_data['standing'],
                    'is_watched': contact_data['is_watched']
                }
            )

            contact.labels.clear()
            if contact_data['label_ids'] is not None:
                contact.labels.set([labels[label_id] for label_id in contact_data['label_ids']])

            contacts_to_load.append(contact.pk)

        corporation_token.last_update = timezone.now()
        corporation_token.save()

    contacts_to_load = CorporationContact.filter_missing_contact_name(contacts_to_load)
    if len(contacts_to_load) > 0:
        group(load_corporation_contact_name.si(pk) for pk in contacts_to_load).delay()


@shared_task
def update_all_alliances_contacts():
    group(
        update_alliance_contacts.si(alliance_token.alliance.alliance_id).set(countdown=randint(0, TASK_JITTER))
        for alliance_token in AllianceToken.objects.with_valid_tokens().select_related('alliance')
    ).delay()


@shared_task
def update_all_corporations_contacts():
    group(
        update_corporation_contacts.si(corporation_token.corporation.corporation_id).set(countdown=randint(0, TASK_JITTER))
        for corporation_token in CorporationToken.objects.with_valid_tokens().select_related('corporation')
    ).delay()


@shared_task
def update_all_contacts():
    update_all_alliances_contacts.delay()
    update_all_corporations_contacts.delay()
