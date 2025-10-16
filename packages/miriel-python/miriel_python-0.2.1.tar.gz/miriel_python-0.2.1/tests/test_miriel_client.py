"""
these are integration tests that require a working api key.
key and base url specified by env vars, see fixtures below.
"""

import logging
import os
import random
from datetime import datetime, timedelta

import pytest

from miriel import Miriel

logging.basicConfig(level=logging.DEBUG)
_logger = logging.getLogger(__name__)

# suppress chatty logs from other libs
for logger_name in ['urllib3']:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.WARNING)


@pytest.fixture
def test_client(dev_api_key, dev_url):
    yield Miriel(api_key=dev_api_key, base_url=dev_url)


@pytest.fixture
def dev_api_key():
    yield os.getenv('MIRIEL_DEV_API_KEY')


@pytest.fixture
def dev_url():
    yield os.getenv('MIRIEL_DEV_BASE_URL')


@pytest.fixture
def test_project():
    yield 'test_python_client'


@pytest.fixture
def test_resource_path(test_data_folder):
    yield f'{test_data_folder}/resource_id.txt'


@pytest.fixture
def test_data_folder():
    yield 'tests/data'


def test_get_all_docs(test_client):
    docs = test_client.get_all_documents()
    assert isinstance(docs, dict)
    assert 'documents' in docs
    assert len(docs['documents']) > 0, 'expected at least 1 document'


def test_learn_add(test_client, test_project, test_data_folder, test_resource_path):
    input = f'{test_data_folder}/test.log'
    response = test_client.learn(input, command='add', project=test_project, wait_for_complete=True)
    _logger.debug(response)
    expected_fields = ['details', 'job_ids', 'details']
    for field in expected_fields:
        assert field in response, f'Missing expected field: {field}'
    assert len(response['details']) == 1
    resource_id = response['details'][0].get('resource_id')
    assert resource_id
    with open(test_resource_path, 'w') as f:
        f.write(resource_id)
        _logger.info(f'Wrote resource_id to {test_resource_path} for future tests')


def test_learn_upsert(test_client, test_project):
    pass


def test_learn_append(test_client, test_project, test_resource_path):
    """
    run after test_learn_add to use the resource_id created in that test
    """
    resource_id = None
    with open(test_resource_path, 'r') as f:
        resource_id = f.read().strip()

    assert resource_id, 'this test expects a valid resource id'

    input = _generate_test_logs(10)
    upsert_ids = {
        'dummy_key': resource_id,
    }
    response = test_client.learn(
        input, command='append', project=test_project, upsert_ids=upsert_ids, wait_for_complete=True
    )
    _logger.debug(response)
    assert response['job_ids']


def test_query(test_client, test_project):
    query = 'What temperature is the oven?'
    result = test_client.query(query, project=test_project)
    assert result
    assert 'results' in result
    assert 'llm_result' in result['results']
    llm_result = result['results']['llm_result']
    assert llm_result
    _logger.info(f'Query result: {llm_result}')


def test_update_document(test_client):
    pass


def test_get_document_by_id(test_client):
    pass


def test_get_users(test_client):
    response = test_client.get_users()
    _logger.info(f'Get users response: {response}')
    assert 'users' in response
    assert len(response['users']) > 0, 'expected at least current user'


def test_get_projects(test_client):
    response = test_client.get_projects()
    _logger.info(f'Get projects response: {response}')
    assert 'projects' in response
    assert len(response['projects']) >= 0


def test_delete_project_documents(test_client, test_project):
    response = test_client.remove_all_documents(project=test_project)
    _logger.info(f'Delete project documents response: {response}')
    assert response['message'].lower() == 'documents removed successfully'


def test_delete_project(test_client, test_project):
    response = test_client.delete_project(test_project)
    _logger.info(f'Delete project response: {response}')
    assert response['message'].lower() == 'project deleted successfully'


def _generate_test_logs(num_lines):
    lines = []
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    timestamp = datetime.now()

    for _ in range(num_lines):
        log_level = random.choice(LOG_LEVELS)
        delta_seconds = random.randint(5, 10)
        timestamp += timedelta(seconds=delta_seconds)
        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        lines.append(f'{time_str} {log_level:<7} {_gen_message()}')
    return '\n'.join(lines)


def _gen_message():
    verbs = ['mixing', 'baking', 'preheating', 'cooling', 'slicing', 'dicing', 'whisking']
    nouns = ['eggs', 'flour', 'sugar', 'butter', 'milk', 'chocolate', 'vanilla']
    units = ['cups', 'tablespoons', 'teaspoons', 'grams', 'ounces', 'liters']
    return f'{random.choice(verbs)} {random.randint(1, 1000)} {random.choice(units)} of {random.choice(nouns)}...'
