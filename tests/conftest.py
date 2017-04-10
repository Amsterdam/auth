import os
import pytest
import auth.config
import auth.siam
import authorization.map
import authorization_levels


def _patched_server(monkeypatch):
    """ Patches siam to not check whether the server is reachable, then imports
    and returns server.
    """

    def get_authn_redirect(*args, **kwargs):
        return 'http://redirect.url'

    def get_user_attributes(*args, **kwargs):
        return {
            'result_code': auth.siam.Client.RESULT_OK,
            'uid': 'testuser'
        }

    monkeypatch.setattr(auth.siam.Client, 'get_authn_redirect', get_authn_redirect)
    monkeypatch.setattr(auth.siam.Client, 'get_user_attributes', get_user_attributes)

    from auth import server
    server.app.config['TESTING'] = True
    return server


@pytest.fixture(autouse=True)
def no_database(monkeypatch):
    authzmap = {
        'employee': authorization_levels.LEVEL_EMPLOYEE,
        'employeeplus': authorization_levels.LEVEL_EMPLOYEE_PLUS,
    }

    def AuthzMap(*args, **kwargs):
        return authzmap
    monkeypatch.setattr(authorization.map, 'AuthzMap', AuthzMap)


@pytest.fixture(scope='session')
def config():
    return auth.config.load(configpath=os.getenv('CONFIG'))


@pytest.fixture()
def app(monkeypatch):
    """ Fixture for tests that need to import auth.server.app. Patches siam to
    not check whether the server is reachable.
    """
    return _patched_server(monkeypatch).app


@pytest.fixture()
def refreshtokenbuilder(monkeypatch):
    """ Fixture for tests that need to import auth.server.app. Patches siam to
    not check whether the server is reachable.
    """
    return _patched_server(monkeypatch).refreshtokenbuilder


@pytest.fixture(scope='session')
def client(config):
    client = auth.siam.Client(
        base_url=config['siam']['base_url'],
        app_id=config['siam']['app_id'],
        aselect_server=config['siam']['aselect_server'],
        shared_secret=config['siam']['shared_secret']
    )
    return client
