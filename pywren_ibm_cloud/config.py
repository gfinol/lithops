#
# Copyright 2018 PyWren Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import json
import importlib
from pywren_ibm_cloud.version import __version__

COMPUTE_BACKEND_DEFAULT = 'ibm_cf'
STORAGE_BACKEND_DEFAULT = 'ibm_cos'
STORAGE_PREFIX_DEFAULT = "pywren.jobs"

EXECUTION_TIMEOUT = 600  # Default: 600 seconds => 10 minutes
DATA_CLEANER_DEFAULT = False
MAX_AGG_DATA_SIZE = 4e6
INVOCATION_RETRY_DEFAULT = True
RETRY_SLEEPS_DEFAULT = [1, 2, 4, 8]
RETRIES_DEFAULT = 5
AMQP_URL_DEFAULT = None


def load(config_filename):
    import yaml
    with open(config_filename, 'r') as config_file:
        res = yaml.safe_load(config_file)

    return res


def get_default_home_filename():
    default_home_filename = os.path.join(os.path.expanduser("~/.pywren_config"))
    return default_home_filename


def get_default_config_filename():
    """
    First checks .pywren_config
    then checks PYWREN_CONFIG_FILE environment variable
    then ~/.pywren_config
    """
    if 'PYWREN_CONFIG_FILE' in os.environ:
        config_filename = os.environ['PYWREN_CONFIG_FILE']
        # FIXME log this

    elif os.path.exists(".pywren_config"):
        config_filename = os.path.abspath('.pywren_config')

    else:
        config_filename = get_default_home_filename()

    return config_filename


def default_config(config_data=None):
    """
    First checks .pywren_config
    then checks PYWREN_CONFIG_FILE environment variable
    then ~/.pywren_config
    """
    if not config_data:
        if 'CB_CONFIG' in os.environ:
            config_data = json.loads(os.environ.get('CB_CONFIG'))
        else:
            config_filename = get_default_config_filename()
            if config_filename is None:
                raise ValueError("could not find configuration file")

            config_data = load(config_filename)

    if 'pywren' not in config_data:
        raise Exception("pywren section is mandatory in the configuration")

    if 'storage_backend' not in config_data['pywren']:
        config_data['pywren']['storage_backend'] = STORAGE_BACKEND_DEFAULT
    if 'storage_prefix' not in config_data['pywren']:
        config_data['pywren']['storage_prefix'] = STORAGE_PREFIX_DEFAULT
    if 'data_cleaner' not in config_data['pywren']:
        config_data['pywren']['data_cleaner'] = DATA_CLEANER_DEFAULT
    if 'invocation_retry' not in config_data['pywren']:
        config_data['pywren']['invocation_retry'] = INVOCATION_RETRY_DEFAULT
    if 'retry_sleeps' not in config_data['pywren']:
        config_data['pywren']['retry_sleeps'] = RETRY_SLEEPS_DEFAULT
    if 'retries' not in config_data['pywren']:
        config_data['pywren']['retries'] = RETRIES_DEFAULT
    if 'compute_backend' not in config_data['pywren']:
        config_data['pywren']['compute_backend'] = COMPUTE_BACKEND_DEFAULT

    if 'rabbitmq' not in config_data or not config_data['rabbitmq'] \
       or 'amqp_url' not in config_data['rabbitmq']:
        config_data['rabbitmq'] = {}
        config_data['rabbitmq']['amqp_url'] = None

    cb = config_data['pywren']['compute_backend']
    cb_config = importlib.import_module('pywren_ibm_cloud.compute.backends.{}.config'.format(cb))
    cb_config.load_config(config_data)

    sb = config_data['pywren']['storage_backend']
    sb_config = importlib.import_module('pywren_ibm_cloud.storage.backends.{}.config'.format(sb))
    sb_config.load_config(config_data)

    return config_data


def extract_storage_config(config):
    storage_config = dict()
    sb = config['pywren']['storage_backend']
    storage_config['backend'] = sb
    storage_config['prefix'] = config['pywren']['storage_prefix']
    storage_config['bucket'] = config['pywren']['storage_bucket']
    storage_config[sb] = config[sb]
    storage_config[sb]['user_agent'] = 'pywren-ibm-cloud/{}'.format(__version__)

    return storage_config


def extract_compute_config(config):
    compute_config = dict()
    cb = config['pywren']['compute_backend']
    compute_config['backend'] = cb
    compute_config['invocation_retry'] = config['pywren']['invocation_retry']
    compute_config['retry_sleeps'] = config['pywren']['retry_sleeps']
    compute_config['retries'] = config['pywren']['retries']
    compute_config[cb] = config[cb].copy()
    compute_config[cb]['user_agent'] = 'pywren-ibm-cloud/{}'.format(__version__)
    if 'compute_backend_region' in config['pywren']:
        compute_config[cb]['region'] = config['pywren']['compute_backend_region']

    return compute_config