# tests/test_raasrest.py
import pytest
from unittest.mock import patch, MagicMock
from workday_tools_nosrednakram.RaaSRest import RaaSRest
from workday_tools_nosrednakram.rest import rest_call

@pytest.fixture
def sample_config(tmp_path):
    config_file = tmp_path / "workday.yaml"
    config_file.write_text(
        "account: test_user\n"
        "password: test_pass\n"
        "tenant: test_tenant\n"
        "prod_url: https://example.com\n"
        "devel_url: https://dev.example.com\n"
        "environment: PROD\n"
    )
    return str(config_file)

def test_raasrest_report(sample_config):
    with patch("workday_tools_nosrednakram.RaaSRest.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "report data"
        mock_get.return_value = mock_response

        raas = RaaSRest(config_file=sample_config)
        response = raas.report(report="Test_Report", format="json")
        assert response.text == "report data"
        mock_get.assert_called_once()

def test_rest_call(sample_config):
    with patch("workday_tools_nosrednakram.RaaSRest.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "rest call data"
        mock_get.return_value = mock_response

        result = rest_call(
            report="Test_Report",
            extra_params="&param1=foo",
            report_format="json",
            raas_config=sample_config
        )
        assert result == "rest call data"
        mock_get.assert_called_once()
