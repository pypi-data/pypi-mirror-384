import logging
from typing import Optional
import workday_tools_nosrednakram.RaaSRest

def rest_call(
        report: str,
        extra_params: str = '',
        report_format: str = 'csv',
        raas_config: str = "workday.yaml",
        logger: Optional[logging.Logger] = None
) -> Optional[str]:
    if logger is None:
        logger = logging.getLogger(__name__)
    print(f'{__name__}: Using config file at {raas_config}')
    try:
        raas_endpoint = workday_tools_nosrednakram.RaaSRest.RaaSRest(config_file=raas_config)
        logger.info(f'Report: {report}')
        logger.info(f'Extra Parameters: {extra_params}')
        response = raas_endpoint.report(report=report, format=report_format, extra_params=extra_params)
        return response.text
    except Exception as e:
        logger.error(f"Error in rest_call: {e}", exc_info=True)
        return None
