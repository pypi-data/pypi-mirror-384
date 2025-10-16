from unittest.mock import patch
from django.test import TestCase

from app_utils.testdata_factories import UserMainFactory
from app_utils.esi_testing import EsiClientStub, EsiEndpoint

from ..models import AllianceToken, AllianceContactLabel, AllianceContact, CorporationContact, CorporationContactLabel, CorporationToken
from ..tasks import update_alliance_contacts, update_corporation_contacts


class TestUpdateAllianceContacts(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = UserMainFactory()
        cls.alliance = user.profile.main_character.alliance
        token = user.token_set.first()

        cls.token = AllianceToken.objects.create(
            alliance=cls.alliance,
            token=token
        )

        cls.label_data = {
            str(cls.alliance.alliance_id): [
                {"label_id": 1, "label_name": "Test Label 1"},
                {"label_id": 2, "label_name": "Test Label 2"},
            ]
        }

        cls.contact_data = {
            str(cls.alliance.alliance_id): [
                {
                    "contact_id": 2,
                    "contact_type": "corporation",
                    'label_ids': [1, 2],
                    'standing': 5.0
                },
            ]
        }

    @patch("aa_contacts.models.ContactTokenQueryset.with_valid_tokens")
    def test_token_doesnt_exist(self, mock_with_valid_tokens):
        mock_with_valid_tokens.return_value = AllianceToken.objects.all()

        self.token.delete()
        with self.assertRaises(ValueError):
            update_alliance_contacts(self.alliance.alliance_id)

    @patch("aa_contacts.tasks.group.delay")
    @patch("aa_contacts.models.ContactTokenQueryset.with_valid_tokens")
    @patch("aa_contacts.tasks.esi")
    def test_ok(self, mock_esi, mock_with_valid_tokens, mock_delay):
        mock_with_valid_tokens.return_value = AllianceToken.objects.all()
        mock_delay.return_value = None

        labels_endpoint = EsiEndpoint(
            'Contacts',
            'get_alliances_alliance_id_contacts_labels',
            'alliance_id',
            needs_token=True,
            data=self.label_data
        )

        contacts_endpoint = EsiEndpoint(
            'Contacts',
            'get_alliances_alliance_id_contacts',
            'alliance_id',
            needs_token=True,
            data=self.contact_data
        )

        mock_esi.client = EsiClientStub.create_from_endpoints([labels_endpoint, contacts_endpoint])

        update_alliance_contacts(self.alliance.alliance_id)

        self.assertEqual(AllianceContact.objects.count(), 1)
        self.assertEqual(AllianceContactLabel.objects.count(), 2)

    @patch("aa_contacts.tasks.group.delay")
    @patch("aa_contacts.models.ContactTokenQueryset.with_valid_tokens")
    @patch("aa_contacts.tasks.esi")
    def test_update(self, mock_esi, mock_with_valid_tokens, mock_delay):
        mock_with_valid_tokens.return_value = AllianceToken.objects.all()
        mock_delay.return_value = None

        labels_endpoint = EsiEndpoint(
            'Contacts',
            'get_alliances_alliance_id_contacts_labels',
            'alliance_id',
            needs_token=True,
            data=self.label_data
        )

        contacts_endpoint = EsiEndpoint(
            'Contacts',
            'get_alliances_alliance_id_contacts',
            'alliance_id',
            needs_token=True,
            data=self.contact_data
        )

        mock_esi.client = EsiClientStub.create_from_endpoints([labels_endpoint, contacts_endpoint])

        update_alliance_contacts(self.alliance.alliance_id)

        self.assertEqual(AllianceContact.objects.count(), 1)
        self.assertEqual(AllianceContactLabel.objects.count(), 2)

        self.label_data[str(self.alliance.alliance_id)].pop()
        self.contact_data[str(self.alliance.alliance_id)][0]['label_ids'].pop()

        update_alliance_contacts(self.alliance.alliance_id)

        self.assertEqual(AllianceContact.objects.count(), 1)
        self.assertEqual(AllianceContactLabel.objects.count(), 1)

        self.contact_data[str(self.alliance.alliance_id)] = []

        contact = AllianceContact.objects.first()
        contact.notes = "Test"
        contact.save()

        update_alliance_contacts(self.alliance.alliance_id)

        self.assertEqual(AllianceContact.objects.count(), 1)
        contact.refresh_from_db()
        self.assertEqual(contact.standing, 0.0)
        self.assertEqual(contact.labels.count(), 0)

        contact.notes = ""
        contact.save()

        update_alliance_contacts(self.alliance.alliance_id)

        self.assertEqual(AllianceContact.objects.count(), 0)


class TestUpdateCorporationContacts(TestCase):

    @classmethod
    def setUpTestData(cls):
        user = UserMainFactory()
        cls.corporation = user.profile.main_character.corporation
        token = user.token_set.first()

        cls.token = CorporationToken.objects.create(
            corporation=cls.corporation,
            token=token
        )

        cls.label_data = {
            str(cls.corporation.corporation_id): [
                {"label_id": 1, "label_name": "Test Label 1"},
                {"label_id": 2, "label_name": "Test Label 2"},
            ]
        }

        cls.contact_data = {
            str(cls.corporation.corporation_id): [
                {
                    "contact_id": 2,
                    "contact_type": "alliance",
                    'label_ids': [1, 2],
                    'standing': 5.0
                },
            ]
        }

    @patch("aa_contacts.models.ContactTokenQueryset.with_valid_tokens")
    def test_token_doesnt_exist(self, mock_with_valid_tokens):
        mock_with_valid_tokens.return_value = CorporationToken.objects.all()

        self.token.delete()
        with self.assertRaises(ValueError):
            update_corporation_contacts(self.corporation.corporation_id)

    @patch("aa_contacts.tasks.group.delay")
    @patch("aa_contacts.models.ContactTokenQueryset.with_valid_tokens")
    @patch("aa_contacts.tasks.esi")
    def test_ok(self, mock_esi, mock_with_valid_tokens, mock_delay):
        mock_with_valid_tokens.return_value = CorporationToken.objects.all()
        mock_delay.return_value = None

        labels_endpoint = EsiEndpoint(
            'Contacts',
            'get_corporations_corporation_id_contacts_labels',
            'corporation_id',
            needs_token=True,
            data=self.label_data
        )

        contacts_endpoint = EsiEndpoint(
            'Contacts',
            'get_corporations_corporation_id_contacts',
            'corporation_id',
            needs_token=True,
            data=self.contact_data
        )

        mock_esi.client = EsiClientStub.create_from_endpoints([labels_endpoint, contacts_endpoint])

        update_corporation_contacts(self.corporation.corporation_id)

        self.assertEqual(CorporationContact.objects.count(), 1)
        self.assertEqual(CorporationContactLabel.objects.count(), 2)

    @patch("aa_contacts.tasks.group.delay")
    @patch("aa_contacts.models.ContactTokenQueryset.with_valid_tokens")
    @patch("aa_contacts.tasks.esi")
    def test_update(self, mock_esi, mock_with_valid_tokens, mock_delay):
        mock_with_valid_tokens.return_value = CorporationToken.objects.all()
        mock_delay.return_value = None

        labels_endpoint = EsiEndpoint(
            'Contacts',
            'get_corporations_corporation_id_contacts_labels',
            'corporation_id',
            needs_token=True,
            data=self.label_data
        )

        contacts_endpoint = EsiEndpoint(
            'Contacts',
            'get_corporations_corporation_id_contacts',
            'corporation_id',
            needs_token=True,
            data=self.contact_data
        )

        mock_esi.client = EsiClientStub.create_from_endpoints([labels_endpoint, contacts_endpoint])

        update_corporation_contacts(self.corporation.corporation_id)

        self.assertEqual(CorporationContact.objects.count(), 1)
        self.assertEqual(CorporationContactLabel.objects.count(), 2)

        self.label_data[str(self.corporation.corporation_id)].pop()
        self.contact_data[str(self.corporation.corporation_id)][0]['label_ids'].pop()

        update_corporation_contacts(self.corporation.corporation_id)

        self.assertEqual(CorporationContact.objects.count(), 1)
        self.assertEqual(CorporationContactLabel.objects.count(), 1)

        self.contact_data[str(self.corporation.corporation_id)] = []

        contact = CorporationContact.objects.first()
        contact.notes = "Test"
        contact.save()

        update_corporation_contacts(self.corporation.corporation_id)

        self.assertEqual(CorporationContact.objects.count(), 1)
        contact.refresh_from_db()
        self.assertEqual(contact.standing, 0.0)
        self.assertEqual(contact.labels.count(), 0)

        contact.notes = ""
        contact.save()

        update_corporation_contacts(self.corporation.corporation_id)

        self.assertEqual(CorporationContact.objects.count(), 0)
