# coding: utf-8

import pytest
from common.entities import FakeEntity
from common.url import api_url


@pytest.fixture
def fake_goal():
    return FakeEntity('goal')


@pytest.fixture
def mocked_fake_goal(net_mock, client, fake_goal):
    net_mock.get(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=fake_goal.json)

    return client.goal.get(fake_goal.idx)


def test_goal_add_key_result(net_mock, client, fake_goal, mocked_fake_goal):
    net_mock.patch(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=fake_goal.json)

    mocked_fake_goal.add_key_result('Key result', kind='binary', assignee='username1')
    real_request = net_mock.request_history[1].json()

    assert real_request == {
        'fields': {
            'keyResultItems': {
                'add': {
                    'type': 'binary',
                    'text': 'Key result',
                    'assignee': 'username1',
                }
            }
        }
    }
    assert net_mock.request_history[1].qs.get('fields') == ['keyresultitems']


def test_goal_add_key_result_value(net_mock, client, fake_goal, mocked_fake_goal):
    net_mock.patch(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=fake_goal.json)

    mocked_fake_goal.add_key_result(
        'Key result',
        kind='value',
        assignee='username1',
        deadline='2025-06-03',
        progress={'start': 1, 'end': 10, 'current': 5},
    )
    real_request = net_mock.request_history[1].json()

    assert real_request == {
        'fields': {
            'keyResultItems': {
                'add': {
                    'type': 'value',
                    'text': 'Key result',
                    'assignee': 'username1',
                    'deadline': {'date': '2025-06-03', 'deadlineType': 'date'},
                    'progress': {'start': 1, 'end': 10, 'current': 5},
                }
            }
        }
    }


def test_goal_set_key_results(net_mock, client, fake_goal, mocked_fake_goal):
    net_mock.patch(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=fake_goal.json)

    items = [
        {'type': 'value', 'text': 'Key result 1'},
        {'type': 'binary', 'text': 'Key result 2', 'achieved': False},
    ]
    mocked_fake_goal.set_key_results(items)
    real_request = net_mock.request_history[1].json()

    assert real_request == {'fields': {'keyResultItems': items}}


def test_goal_set_key_results_strips_readonly(net_mock, client, fake_goal, mocked_fake_goal):
    net_mock.patch(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=fake_goal.json)

    # An item as read back from the goal: nested user object, read-only status,
    # full ISO deadline with isExceeded, server-generated id.
    items = [{
        'id': '111',
        'type': 'binary',
        'text': 'KR',
        'assignee': {'id': 'username1', 'display': 'User One'},
        'deadline': {'date': '2025-06-03T00:00:00.000+0000',
                     'deadlineType': 'date', 'isExceeded': False},
        'achieved': True,
        'status': {'id': 'achieved'},
    }]
    mocked_fake_goal.set_key_results(items)
    real_request = net_mock.request_history[1].json()

    assert real_request == {'fields': {'keyResultItems': [{
        'type': 'binary',
        'text': 'KR',
        'achieved': True,
        'assignee': 'username1',
        'deadline': {'date': '2025-06-03', 'deadlineType': 'date'},
    }]}}


def test_goal_delete_one_via_set(net_mock, client, fake_goal, mocked_fake_goal):
    # Deleting a single key result is a deliberate full-list replace: read the
    # list, drop the item, pass the rest to set_key_results (read-only fields
    # are stripped by normalization).
    items = [
        {'id': '111', 'type': 'binary', 'text': 'KR 1', 'achieved': False,
         'status': {'id': 'draft'}},
        {'id': '222', 'type': 'value', 'text': 'KR 2',
         'progress': {'start': 1, 'end': 10, 'current': 5}},
    ]
    net_mock.get(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=dict(fake_goal.json, fields={'keyResultItems': items}))
    net_mock.patch(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=fake_goal.json)

    remaining = [kr for kr in mocked_fake_goal.key_results if kr['id'] != '111']
    mocked_fake_goal.set_key_results(remaining)
    real_request = net_mock.request_history[-1].json()

    assert real_request == {'fields': {'keyResultItems': [
        {'type': 'value', 'text': 'KR 2',
         'progress': {'start': 1, 'end': 10, 'current': 5}},
    ]}}


def test_goal_clear_key_results(net_mock, client, fake_goal, mocked_fake_goal):
    net_mock.patch(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=fake_goal.json)

    mocked_fake_goal.clear_key_results()
    real_request = net_mock.request_history[1].json()

    assert real_request == {'fields': {'keyResultItems': None}}


def test_goal_key_results(net_mock, client, fake_goal, mocked_fake_goal):
    key_result_items = [{
        'id': '6789',
        'type': 'binary',
        'text': 'Key result',
        'achieved': False,
    }]
    # Non-default entity attributes are returned nested under "fields".
    json = dict(fake_goal.json, fields={'keyResultItems': key_result_items})
    net_mock.get(
        api_url('/entities/goal/{idx}'.format(idx=fake_goal.idx)),
        json=json)

    assert mocked_fake_goal.key_results == key_result_items
    assert net_mock.request_history[1].qs.get('fields') == ['keyresultitems']
