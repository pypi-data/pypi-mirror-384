from __future__ import annotations

import functools
import weakref
from typing import TYPE_CHECKING, ClassVar

from cachecontrol.adapter import CacheControlAdapter as BaseAdapter
from cachecontrol.filewrapper import CallbackFileWrapper

if TYPE_CHECKING:
    from urllib3 import HTTPResponse

from . import utils


class CacheControlAdapter(BaseAdapter):
    """
    Adapter for handling cache requests.
    """

    invalidating_methods: ClassVar[set[str]] = {"POST", "PUT", "DELETE"}

    def build_response(
        self, request, response, from_cache=False, cacheable_methods=None
    ):
        """
        Build a response by making a request or using the cache.
        This will end up calling send and returning a potentially
        cached response
        """
        cacheable = cacheable_methods or self.cacheable_methods
        if not from_cache and request.method in cacheable:
            # Check for any heuristics that might update headers
            # before trying to cache.
            if self.heuristic:
                response = self.heuristic.apply(response)

            # apply any expiration heuristics
            if response.status == 304:
                # We must have sent an ETag request. This could mean
                # that we've been expired already or that we simply
                # have an etag. In either case, we want to try and
                # update the cache if that is the case.
                cached_response = self.controller.update_cached_response(
                    request, response
                )

                if cached_response is not response:
                    from_cache = True

                # We are done with the server response, read a
                # possible response body (compliant servers will
                # not return one, but we cannot be 100% sure) and
                # release the connection back to the pool.
                response.read(decode_content=False)
                response.release_conn()

                response = cached_response

            # We always cache the 301 responses
            elif response.status == 301:
                self.controller.cache_response(request, response)
            else:
                # Wrap the response file with a wrapper that will cache the
                #   response when the stream has been consumed.
                response._fp = CallbackFileWrapper(  # pylint: disable=protected-access
                    response._fp,  # pylint: disable=protected-access
                    functools.partial(
                        self.controller.cache_response, request, weakref.ref(response)
                    ),
                )
                if response.chunked:
                    super_update_chunk_length = (
                        response.__class__._update_chunk_length  # pylint: disable=protected-access
                    )

                    def _update_chunk_length(
                        weak_self: weakref.ReferenceType[HTTPResponse],
                    ) -> None:
                        self = weak_self()
                        if self is None:
                            return

                        super_update_chunk_length(self)

                    # pylint: disable-next=protected-access
                    response._update_chunk_length = functools.partial(  # type: ignore[method-assign]
                        _update_chunk_length, weakref.ref(response)
                    )

        resp = super().build_response(request, response)

        # See if we should invalidate the cache.
        if request.method in self.invalidating_methods and resp.ok:
            cache_url = self.controller.cache_url(utils.build_url(request))
            self.cache.delete(cache_url)

        # Give the request a from_cache attr to let people use it
        resp.from_cache = from_cache

        return resp
