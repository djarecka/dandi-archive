import pytest

from dandi.publish.models import Asset
from .fuzzy import TIMESTAMP_RE


@pytest.mark.django_db
def test_asset_from_girder(version, girder_file, mock_girder_client):
    asset = Asset.from_girder(version, girder_file, mock_girder_client)
    assert asset


@pytest.mark.django_db
def test_asset_rest_list(api_client, asset):
    assert api_client.get(
        f'/api/dandisets/{asset.version.dandiset.identifier}/'
        f'versions/{asset.version.version}/assets/'
    ).data == {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [
            {
                'version': {
                    'dandiset': {
                        'identifier': asset.version.dandiset.identifier,
                        'created': TIMESTAMP_RE,
                        'updated': TIMESTAMP_RE,
                    },
                    'version': asset.version.version,
                    'name': asset.version.name,
                    'description': asset.version.description,
                    'created': TIMESTAMP_RE,
                    'updated': TIMESTAMP_RE,
                    'count': 1,
                },
                'uuid': str(asset.uuid),
                'path': asset.path,
                'size': asset.size,
                'sha256': asset.sha256,
                'created': TIMESTAMP_RE,
                'updated': TIMESTAMP_RE,
                'metadata': asset.metadata,
            }
        ],
    }


@pytest.mark.django_db
def test_asset_rest_retrieve(api_client, asset):
    assert api_client.get(
        f'/api/dandisets/{asset.version.dandiset.identifier}/'
        f'versions/{asset.version.version}/assets/{asset.uuid}/'
    ).data == {
        'version': {
            'dandiset': {
                'identifier': asset.version.dandiset.identifier,
                'created': TIMESTAMP_RE,
                'updated': TIMESTAMP_RE,
            },
            'version': asset.version.version,
            'name': asset.version.name,
            'description': asset.version.description,
            'created': TIMESTAMP_RE,
            'updated': TIMESTAMP_RE,
            'count': 1,
        },
        'uuid': str(asset.uuid),
        'path': asset.path,
        'size': asset.size,
        'sha256': asset.sha256,
        'created': TIMESTAMP_RE,
        'updated': TIMESTAMP_RE,
        'metadata': asset.metadata,
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    'new_path,expected',
    [
        # Partial
        (lambda path: path[: int(len(path) / 2)], True),
        # Full
        (lambda path: path, True),
        # Extra at beginning
        (lambda path: 'extra-string' + path, False),
        # Extra at end
        (lambda path: path + 'extra-string', False),
        # Case insensitive 1
        (lambda path: path.upper(), True),
        # Case insensitive 2
        (lambda path: path.lower(), True),
    ],
)
def test_asset_path_filter(api_client, asset, new_path, expected):
    path = new_path(asset.path)
    partial_path_assets = api_client.get(
        f'/api/dandisets/{asset.version.dandiset.identifier}/'
        f'versions/{asset.version.version}/assets/',
        {'path': path},
    ).data['results']

    matching_results = [res for res in partial_path_assets if res['uuid'] == str(asset.uuid)]
    assert bool(matching_results) is expected
