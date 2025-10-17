"""
import betamax
from cachecontrol.caches.file_cache import FileCache
import itkdb
from unittest import mock


def test_caching(tmpdir, auth_user):
    temp = tmpdir.join(".webcache")
    assert itkdb.Client(
        user=auth_user,
        expires_after=dict(weeks=7, days=6, hours=5, minutes=4, seconds=3),
        cache=FileCache(temp.strpath),
    )


def test_cache_component(tmpdir, mocker, auth_user):
    temp = tmpdir.join(".webcache")
    client = itkdb.Client(
        user=auth_user, expires_after=dict(minutes=10), cache=FileCache(temp.strpath)
    )

    def mock_factory(betamax_send):
        def wrap_betamax_send(self, request, **kwargs):
            resp = betamax_send(request, **kwargs)
            return client.adapters.get(client.prefix_url, None).build_response(
                request, resp
            )

        return wrap_betamax_send

    with betamax.Betamax(client).use_cassette('test_cache.test_cache_component'):
        mocker.patch(
            'betamax.adapter.BetamaxAdapter.send',
            new=mock_factory(client.adapters.get('https://', None).send),
        )
        client.mount(
            client.prefix_url,
            client.adapters.get('https://', None).old_adapters[client.prefix_url],
        )

        response = client.get(
            'getComponent', json={"project": "P", "component": "20UPGRA0000539"}
        )
        assert client._response.status_code == 200
        assert client._response.from_cache == False

        # check that we've cached it
        response = client.get(
            'getComponent', json={"project": "P", "component": "20UPGRA0000539"}
        )
        assert client._response.status_code == 200
        assert client._response.from_cache


def test_cache_component_but_not_other(tmpdir, mocker, auth_user):
    temp = tmpdir.join(".webcache")

    client = itkdb.Client(
        user=auth_user, expires_after=dict(minutes=10), cache=FileCache(temp.strpath)
    )

    def mock_factory(betamax_send):
        def wrap_betamax_send(self, request, **kwargs):
            resp = betamax_send(request, **kwargs)
            return client.adapters.get(client.prefix_url, None).build_response(
                request, resp
            )

        return wrap_betamax_send

    with betamax.Betamax(client).use_cassette(
        'test_cache.test_cache_component_but_not_other'
    ):
        mocker.patch(
            'betamax.adapter.BetamaxAdapter.send',
            new=mock_factory(client.adapters.get('https://', None).send),
        )
        client.mount(
            client.prefix_url,
            client.adapters.get('https://', None).old_adapters[client.prefix_url],
        )
        # def patch_betamax_send(self, *args, **kwargs):
        #    resp = self.send(*args, **kwargs)
        #    return client.adapters.get(client.prefix_url, None).build_response(request, resp)
        # mocker.patch('betamax.adapter.BetamaxAdapter.send', new=patch_betamax_send)
        response = client.get(
            'getComponent', json={"project": "P", "component": "20UPGRA0000539"}
        )
        assert client._response.status_code == 200
        assert client._response.from_cache == False

        # check that we didn't cache an entirely different request
        response = client.get(
            'getComponent', json={"project": "P", "component": "20UPGRA0000540"}
        )
        assert client._response.status_code == 200
        assert client._response.from_cache == False
"""
