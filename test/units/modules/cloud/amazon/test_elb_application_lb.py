#
# (c) 2017 Michael Tinning
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)

from nose.plugins.skip import SkipTest
import json
import pytest
from ansible.module_utils._text import to_bytes
from ansible.module_utils import basic
from ansible.module_utils.ec2 import HAS_BOTO3

if not HAS_BOTO3:
    raise SkipTest("test_api_gateway.py requires the `boto3` and `botocore` modules")

import ansible.modules.cloud.amazon.elb_application_lb as elb_module


@pytest.fixture
def listener():
    return {
        'Protocol': 'HTTP',
        'Port': 80,
        'DefaultActions': [{
            'Type': 'forward',
            'TargetGroupName': 'target-group'
        }],
        'Rules': [{
            'Conditions': [{
                'Field': 'host-header',
                'Values': [
                    'www.example.com'
                ]
            }],
            'Priority': 1,
            'Actions': [{
                'TargetGroupName': 'other-target-group',
                'Type': 'forward'
            }]
        }]
    }


@pytest.fixture
def compare_listeners(mocker):
    return mocker.Mock()


@pytest.fixture
def elb(mocker, monkeypatch, compare_listeners):
    monkeypatch.setattr(elb_module, "ensure_listeners_default_action_has_arn", lambda _a, _b, _c: [])
    monkeypatch.setattr(elb_module, "get_elb_listeners", mocker.Mock())
    monkeypatch.setattr(elb_module, "ensure_rules_action_has_arn", mocker.Mock())
    monkeypatch.setattr(elb_module, "get_listener", mocker.Mock())
    monkeypatch.setattr(elb_module, "compare_rules", lambda _a, _b, _c, _d: ([], [], []))
    monkeypatch.setattr(elb_module, "compare_listeners", compare_listeners)
    return elb_module


@pytest.fixture
def connection(mocker):
    return mocker.Mock()


@pytest.fixture
def existing_elb():
    return {'LoadBalancerArn': 'fake'}


def test_create_listeners_called_with_correct_args(mocker, connection, listener, elb, compare_listeners, existing_elb):
    compare_listeners.return_value = ([listener], [], [])

    elb.create_or_update_elb_listeners(connection, mocker.Mock(), existing_elb)

    connection.create_listener.assert_called_once_with(
        Protocol=listener['Protocol'],
        Port=listener['Port'],
        DefaultActions=listener['DefaultActions'],
        LoadBalancerArn=existing_elb['LoadBalancerArn']
    )


def test_modify_listeners_called_with_correct_args(mocker, connection, listener, elb, compare_listeners, existing_elb):
    # In the case of modify listener, LoadBalancerArn is set in compare_listeners
    listener['LoadBalancerArn'] = existing_elb['LoadBalancerArn']
    compare_listeners.return_value = ([], [listener], [])

    elb.create_or_update_elb_listeners(connection, mocker.Mock(), existing_elb)

    connection.modify_listener.assert_called_once_with(
        Protocol=listener['Protocol'],
        Port=listener['Port'],
        DefaultActions=listener['DefaultActions'],
        LoadBalancerArn=existing_elb['LoadBalancerArn']
    )
