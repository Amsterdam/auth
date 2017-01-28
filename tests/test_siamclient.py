"""
    auth.tests.test_siamclient
    ~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import pytest
import responses
import time
import urllib.parse
from auth import exceptions, siam

# shorthand
uenc = urllib.parse.urlencode


@pytest.mark.usefixtures('config', 'client')
def test_siam_server_error(config, client):
    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], status=500)
        with pytest.raises(exceptions.GatewayRequestException):
            client._request({}, 1.0)


@pytest.mark.usefixtures('config', 'client')
def test_get_authn_link(config, client):
    rid = '1'
    body = uenc({
        'as_url': config['SIAM_BASE_URL'] + '?request=login1',
        'a-select-server': config['SIAM_ASELECT_SERVER'],
        'rid': rid,
    })
    expected = '{}?request=login1&a-select-server={}&rid={}'.format(
        config['SIAM_BASE_URL'], config['SIAM_ASELECT_SERVER'], rid
    )
    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], status=200, body=body)
        resp = client.get_authn_link(False, 'http://some.callback.url')
    assert resp == expected


@pytest.mark.usefixtures('config', 'client')
def test_verify_creds(config, client):
    now = int(time.time())
    # 1. Test success
    with responses.RequestsMock() as rsps:
        result = {
            'result_code': client.RESULT_OK,
            'tgt_exp_time': '{}'.format(now+10),
            'uid': 'evert'}
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], body=uenc(result))
        response = client.verify_creds('aselect_credentials', 'rid')
        assert response == result
    # 2. Test failure
    with responses.RequestsMock() as rsps:
        result = {'result_code': client.RESULT_INVALID_CREDENTIALS}
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], body=uenc(result))
        response = client.verify_creds('aselect_credentials', 'rid')
        assert response == result
    # 3. Test malformed response I
    with responses.RequestsMock() as rsps:
        result = {'result_code': client.RESULT_OK}
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], body=uenc(result))
        with pytest.raises(exceptions.GatewayResponseException):
            client.verify_creds('aselect_credentials', 'rid')
    # 4. Test malformed response II
    with responses.RequestsMock() as rsps:
        result = {}
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], body=uenc(result))
        with pytest.raises(exceptions.GatewayResponseException):
            client.verify_creds('aselect_credentials', 'rid')
    # 5. Test malformed response III
    with responses.RequestsMock() as rsps:
        result = {
            'result_code': client.RESULT_OK,
            'tgt_exp_time': '{}'.format(now-10),
            'uid': 'evert'}
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], body=uenc(result))
        with pytest.raises(exceptions.GatewayResponseException):
            client.verify_creds('aselect_credentials', 'rid')


@pytest.mark.usefixtures('config', 'client')
def test_renew_session(config, client):
    # 1. Test success
    with responses.RequestsMock() as rsps:
        body = uenc({'result_code': client.RESULT_OK})
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], status=200, body=body)
        assert client.renew_session('aselect_credentials')
    # 2. Test malformed response
    with responses.RequestsMock() as rsps:
        body = uenc({'other param': 'some value'})
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], status=200, body=body)
        with pytest.raises(exceptions.GatewayResponseException):
            client.renew_session('aselect_credentials')


@pytest.mark.usefixtures('config', 'client')
def test_end_session(config, client):
    with responses.RequestsMock() as rsps:
        rsps.add(rsps.GET, config['SIAM_BASE_URL'], status=307)
        assert client.end_session('aselect_credentials') == 307
