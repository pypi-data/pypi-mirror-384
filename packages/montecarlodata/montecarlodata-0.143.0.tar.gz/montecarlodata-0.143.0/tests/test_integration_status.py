from unittest import TestCase
from unittest.mock import Mock

from montecarlodata.common.user import UserService
from montecarlodata.integrations.info.status import OnboardingStatusService
from tests.helpers import capture_function
from tests.test_common_user import _SAMPLE_CONFIG


class OnboardingStatusTest(TestCase):
    def setUp(self) -> None:
        self._user_service_mock = Mock(autospec=UserService)

        self._service = OnboardingStatusService(
            _SAMPLE_CONFIG,
            command_name="test",
            user_service=self._user_service_mock,
        )

    def test_display_integrations_with_no_connections(self):
        self._user_service_mock.warehouses = None
        self._user_service_mock.bi_containers = None
        self._user_service_mock.etl_containers = None

        std_out = capture_function(
            self._service.display_integrations, {"table_format": "plain"}
        ).std_out
        self.assertEqual(
            std_out.getvalue().strip(),
            "Integration    Name    ID    Connection    Created on (UTC)",
        )

    def test_display_integrations_with_connections(self):
        (
            sample_uuid,
            sample_type1,
            sample_type2,
            sample_time,
            sample_uuid3,
            sample_type3,
        ) = ("1", "foo", "bar", "now", "3", "fivetran")
        sample_connection_identifier1 = {"key": "host", "value": "foo"}
        sample_connection_identifier2 = {"key": "host", "value": "bar"}
        sample_connection_identifier3 = {"key": "host", "value": "bar3"}
        self._user_service_mock.warehouses = [
            {
                "name": "Sample 1",
                "connections": [
                    {
                        "uuid": sample_uuid,
                        "type": sample_type1,
                        "connectionIdentifiers": [
                            sample_connection_identifier1,
                            sample_connection_identifier2,
                        ],
                        "createdOn": sample_time,
                    }
                ],
            }
        ]
        self._user_service_mock.bi_containers = [
            {
                "name": "Sample 2",
                "connections": [
                    {
                        "uuid": sample_uuid,
                        "type": sample_type2,
                        "connectionIdentifiers": [sample_connection_identifier2],
                        "createdOn": sample_time,
                    }
                ],
            }
        ]
        self._user_service_mock.etl_containers = [
            {
                "name": "Test Fivetran",
                "connections": [
                    {
                        "uuid": sample_uuid3,
                        "type": sample_type3,
                        "connectionIdentifiers": [sample_connection_identifier3],
                        "createdOn": sample_time,
                    }
                ],
            }
        ]

        expected_output = (
            "Integration    Name             ID  Connection    Created on (UTC)\n"
            "foo            Sample 1          1  host: foo     now\n"
            "                                    host: bar\n"
            "bar            Sample 2          1  host: bar     now\n"
            "Fivetran       Test Fivetran     3  host: bar3    now"
        )
        std_out = capture_function(
            self._service.display_integrations, {"table_format": "plain"}
        ).std_out
        self.assertEqual(std_out.getvalue().strip(), expected_output)
