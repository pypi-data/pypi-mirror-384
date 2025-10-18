import datetime
from unittest.mock import Mock

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.test.utils import override_settings
from django.utils import timezone

from parameterized import parameterized

from pbx_admin.form_fields import DateTimeRangePickerField
from pbx_admin.templatetags.admin_tags import humanize_number
from pbx_admin.utils import is_from_trusted_network
from pbx_admin.views.mixins import PaginationMixin
from pbx_admin.widgets import DateTimeRangePickerWidget


class AdminListViewTests(TestCase):
    def test_adjacent_pages(self):
        self.assertEqual(
            PaginationMixin._get_adjacent_pages(7, range(1, 12), 2), ([5, 6], [8, 9])
        )
        self.assertEqual(
            PaginationMixin._get_adjacent_pages(3, range(1, 7), 2), ([1, 2], [4, 5])
        )


class DateTimeRangePickerFieldTest(SimpleTestCase):
    def setUp(self) -> None:
        self.test_field = DateTimeRangePickerField()

    def test_valid_widget(self) -> None:
        self.assertIsInstance(self.test_field.widget, DateTimeRangePickerWidget)

    def test_valid_time_range(self) -> None:
        date_range = [
            timezone.now(),
            timezone.now() + datetime.timedelta(days=10),
        ]

        test_case = self.test_field.clean(date_range)

        self.assertEqual(date_range, test_case)

    def test_invalid_time_range(self) -> None:
        invalid_date_range = [
            timezone.now(),
            timezone.now() - datetime.timedelta(days=10),
        ]

        with self.assertRaisesMessage(ValidationError, "Invalid date range"):
            self.test_field.clean(invalid_date_range)


class TemplateTagsTests(TestCase):
    @parameterized.expand(
        (
            (0, "0"),
            (999, "999"),
            (1_000, "1K"),
            (99_999, "99K"),
            (100_000, "100K"),
            (324_324, "324K"),
            (1_000_000, "1M"),
            (1_888_000, "1.8M"),
        )
    )
    def test_humanize_number(self, num, expected):
        self.assertEqual(humanize_number(num), expected)


class NetworkTrustedTests(SimpleTestCase):
    def _create_request(self, ip):
        request = Mock()
        request.META = {"REMOTE_ADDR": ip}
        return request

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.100"])
    def test_individual_ip(self):
        self.assertTrue(is_from_trusted_network(self._create_request("192.168.1.100")))
        self.assertFalse(is_from_trusted_network(self._create_request("192.168.1.101")))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["80.82.28.0/24"])
    def test_cidr_range(self):
        self.assertTrue(is_from_trusted_network(self._create_request("80.82.28.42")))
        self.assertFalse(is_from_trusted_network(self._create_request("80.82.29.1")))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.100", "80.82.28.0/24"])
    def test_mixed(self):
        self.assertTrue(is_from_trusted_network(self._create_request("192.168.1.100")))
        self.assertTrue(is_from_trusted_network(self._create_request("80.82.28.42")))
        self.assertFalse(is_from_trusted_network(self._create_request("172.16.1.1")))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.1"])
    def test_invalid(self):
        with self.assertLogs("pbx_admin.utils", level="WARNING") as cm:
            self.assertFalse(is_from_trusted_network(self._create_request("invalid")))
        self.assertIn("Invalid client IP address", cm.output[0])

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=[])
    def test_empty_trusted_list(self):
        self.assertTrue(is_from_trusted_network(self._create_request("192.168.1.1")))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["invalid", "192.168.1.100"])
    def test_invalid_trusted_range(self):
        with self.assertLogs("pbx_admin.utils", level="WARNING") as cm:
            self.assertTrue(is_from_trusted_network(self._create_request("192.168.1.100")))
        self.assertIn("Invalid trusted IP range", cm.output[0])

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.100", "10.0.0.0/8"])
    def test_forwarded_for_priority(self):
        request = Mock()
        request.META = {
            "HTTP_X_ORIGINAL_FORWARDED_FOR": "192.168.1.100",
            "HTTP_X_FORWARDED_FOR": "192.168.1.101",
            "REMOTE_ADDR": "192.168.1.102",
        }
        self.assertTrue(is_from_trusted_network(request))

        request.META = {
            "HTTP_X_FORWARDED_FOR": "10.0.0.5",
            "REMOTE_ADDR": "192.168.1.102",
        }
        self.assertTrue(is_from_trusted_network(request))

    @override_settings(OAUTH_TRUSTED_IP_ADDRESSES=["192.168.1.100"])
    def test_ip_list_first_item(self):
        request = Mock()
        request.META = {"HTTP_X_FORWARDED_FOR": "192.168.1.100, 192.168.1.101, 192.168.1.102"}
        self.assertTrue(is_from_trusted_network(request))

        request.META = {"HTTP_X_FORWARDED_FOR": "192.168.1.101, 192.168.1.100"}
        self.assertFalse(is_from_trusted_network(request))
