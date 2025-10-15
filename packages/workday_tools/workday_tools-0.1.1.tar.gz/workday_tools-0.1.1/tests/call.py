from workday_tools_nosrednakram.rest import rest_call
import yaml
import os

try:
    with open('config.yaml', 'r') as stream:
        config = yaml.load(stream, Loader=yaml.Loader)
except Exception as e:
    print(f'Reading YAML Error: {e}')

# Make REST RaaS Call
try:
    cfg_file_base = os.path.abspath(os.path.dirname(__file__))
    raas_config = os.path.join(cfg_file_base, config['raas_config'])
    rest_response = rest_call(report=config['raas_report'],
                              extra_params=config['raas_extra_params'],
                              report_format=config['raas_format'],
                              raas_config=raas_config)
    print(rest_response)

except Exception as e:
    print(f'REST Error: {e}')
