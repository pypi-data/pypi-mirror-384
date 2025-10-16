from unittest.mock import patch, call
import json

from .utils import fixtures_path
from hestia_earth.extend_bibliography import extend, get_node_values, missing_bibliographies


mock_path = 'hestia_earth.extend_bibliography'


def fake_extend(api='mendeley'):
    with open(f"{fixtures_path}/{api}/results.json", 'r') as f:
        content = json.load(f).get('results')
    return (
        list(filter(lambda x: x['type'] == 'Actor', content)),
        list(filter(lambda x: x['type'] == 'Bibliography', content))
    )


@patch(f"{mock_path}.missing_bibliographies", return_value=[[]])
@patch(f"{mock_path}.extend_mendeley", return_value=fake_extend())
def test_extend_mendeley(mock_extend, *args):
    with open(f"{fixtures_path}/sample.json", 'r') as f:
        content = json.load(f)
    with open(f"{fixtures_path}/sample-extended.json", 'r') as f:
        expected = json.load(f)

    result = extend(content, mendeley_api_url='url')
    assert result == expected
    assert mock_extend.call_count == 4


@patch(f"{mock_path}.missing_bibliographies", return_value=[[]])
@patch(f"{mock_path}.extend_wos", return_value=fake_extend())
def test_extend_wos(mock_extend, *args):
    with open(f"{fixtures_path}/sample.json", 'r') as f:
        content = json.load(f)
    with open(f"{fixtures_path}/sample-extended.json", 'r') as f:
        expected = json.load(f)

    result = extend(content, wos_api_key='api-key')
    assert result == expected
    mock_extend.assert_called_once()


@patch(f"{mock_path}.missing_bibliographies", return_value=[[]])
@patch(f"{mock_path}.extend_unpaywall_source_license", side_effect=lambda x: x)
@patch(f"{mock_path}.extend_unpaywall", return_value=fake_extend())
def test_extend_unpaywall(mock_extend, *args):
    with open(f"{fixtures_path}/sample.json", 'r') as f:
        content = json.load(f)
    with open(f"{fixtures_path}/sample-extended.json", 'r') as f:
        expected = json.load(f)

    result = extend(content, enable_unpaywall=True)
    assert result == expected
    mock_extend.assert_called_once()


@patch(f"{mock_path}.missing_bibliographies", return_value=[[]])
@patch(f"{mock_path}.extend_crossref_source_license", side_effect=lambda x: x)
@patch(f"{mock_path}.extend_crossref", return_value=fake_extend())
def test_extend_crossref(mock_extend, *args):
    with open(f"{fixtures_path}/sample.json", 'r') as f:
        content = json.load(f)
    with open(f"{fixtures_path}/sample-extended.json", 'r') as f:
        expected = json.load(f)

    result = extend(content, enable_crossref=True)
    assert result == expected
    mock_extend.assert_called_once()


@patch(f"{mock_path}.missing_bibliographies", return_value=[[]])
@patch(f"{mock_path}.extend_crossref_source_license", side_effect=lambda x: x)
@patch(f"{mock_path}.extend_unpaywall_source_license", side_effect=lambda x: x)
@patch(f"{mock_path}.extend_crossref", return_value=fake_extend('crossref'))
@patch(f"{mock_path}.extend_unpaywall", return_value=fake_extend('unpaywall'))
@patch(f"{mock_path}.extend_mendeley", return_value=fake_extend())
@patch(f"{mock_path}.mendeley_client", return_value=(None, None))
def test_extend_multiple_apis(_m, mock_mendeley, mock_unpaywall, mock_crossref, *args):
    with open(f"{fixtures_path}/sample.json", 'r') as f:
        content = json.load(f)
    extend(content, mendeley_api_url='url', enable_unpaywall=True, enable_crossref=True)
    mock_mendeley.assert_has_calls([
        call(None, None, [], 'mendeleyID'),
        call(None, None, [], 'documentDOI'),
        call(None, None, [], 'scopus'),
        call(None, None, [
            'Bilan des éléments minéraux sous une rotation sorgho-cotonnier en lysimètres',
            'How plants communicate using the underground information superhighway',
            'Long-term continuous cropping, fertilisation, and manuring effects on physical properties '
            'and organic carbon content of a sandy loam soil',
            'Nitrogen dynamics and maize growth in a Zimbabwean sandy soil under manure fertilisation'
        ], 'title')
    ])
    mock_unpaywall.assert_called_once_with([
        'Bilan des éléments minéraux sous une rotation sorgho-cotonnier en lysimètres'
    ], enable_unpaywall=True, enable_crossref=True, mendeley_api_url='url')
    mock_crossref.assert_called_once_with([
        'Bilan des éléments minéraux sous une rotation sorgho-cotonnier en lysimètres'
    ], enable_unpaywall=True, enable_crossref=True, mendeley_api_url='url')


@patch(f"{mock_path}.missing_bibliographies", return_value=[[]])
@patch(f"{mock_path}.extend_bibliography_pdf", return_value={})
def test_no_extend(*args):
    with open(f"{fixtures_path}/sample.json", 'r') as f:
        content = json.load(f)

    result = extend(content)
    assert result == content


def test_get_node_values():
    nodes = [{
        'bibliography': {
            'type': 'Bibliography',
            'title': 'random title'
        },
        'source': {
            'bibliography': {
                'type': 'Bibliography',
                'title': '',
                'documentDOI': '10.35648/20.500.12413/11781/ii250'
            }
        }
    }, {
        'source': {
            'bibliography': {
                'type': 'Bibliography',
                'name': 'name',
                # check all required fields on https://www-staging.hestia.earth/schema/Bibliography
                'title': 'all required fields are set',
                'authors': [{
                    'type': 'Actor',
                    'name': 'Name'
                }],
                'outlet': 'outlet',
                'year': 1991
            }
        }
    }]
    assert sorted(get_node_values(nodes)) == ['random title']
    assert sorted(get_node_values(nodes, 'documentDOI')) == ['10.35648/20.500.12413/11781/ii250']


def test_missing_bibliographies():
    with open(f"{fixtures_path}/sample-extended.json", 'r') as f:
        nodes = json.load(f).get('nodes')

    errors = missing_bibliographies(nodes)
    assert list(filter(lambda e: len(e) > 0, errors)) == [
        [{
            'level': 'error',
            'dataPath': '.bibliography',
            'message': 'is missing required bibliographic information'
        }]
    ]
