import requests
import random
import gevent
import six

from holster.enum import Enum

from disco.util.logging import LoggingClass
from disco.api.ratelimit import RateLimiter

# Enum of all HTTP methods used
HTTPMethod = Enum(
    GET='GET',
    POST='POST',
    PUT='PUT',
    PATCH='PATCH',
    DELETE='DELETE',
)


class Routes(object):
    """
    Simple Python object-enum of all method/url route combinations available to
    this client.
    """
    # Gateway
    GATEWAY_GET = (HTTPMethod.GET, '/gateway')
    GATEWAY_BOT_GET = (HTTPMethod.GET, '/gateway/bot')

    # Channels
    CHANNELS = '/channels/{channel}'
    CHANNELS_GET = (HTTPMethod.GET, CHANNELS)
    CHANNELS_MODIFY = (HTTPMethod.PATCH, CHANNELS)
    CHANNELS_DELETE = (HTTPMethod.DELETE, CHANNELS)
    CHANNELS_TYPING = (HTTPMethod.POST, CHANNELS + '/typing')
    CHANNELS_MESSAGES_LIST = (HTTPMethod.GET, CHANNELS + '/messages')
    CHANNELS_MESSAGES_GET = (HTTPMethod.GET, CHANNELS + '/messages/{message}')
    CHANNELS_MESSAGES_CREATE = (HTTPMethod.POST, CHANNELS + '/messages')
    CHANNELS_MESSAGES_MODIFY = (HTTPMethod.PATCH, CHANNELS + '/messages/{message}')
    CHANNELS_MESSAGES_DELETE = (HTTPMethod.DELETE, CHANNELS + '/messages/{message}')
    CHANNELS_MESSAGES_DELETE_BULK = (HTTPMethod.POST, CHANNELS + '/messages/bulk_delete')
    CHANNELS_PERMISSIONS_MODIFY = (HTTPMethod.PUT, CHANNELS + '/permissions/{permission}')
    CHANNELS_PERMISSIONS_DELETE = (HTTPMethod.DELETE, CHANNELS + '/permissions/{permission}')
    CHANNELS_INVITES_LIST = (HTTPMethod.GET, CHANNELS + '/invites')
    CHANNELS_INVITES_CREATE = (HTTPMethod.POST, CHANNELS + '/invites')
    CHANNELS_PINS_LIST = (HTTPMethod.GET, CHANNELS + '/pins')
    CHANNELS_PINS_CREATE = (HTTPMethod.PUT, CHANNELS + '/pins/{pin}')
    CHANNELS_PINS_DELETE = (HTTPMethod.DELETE, CHANNELS + '/pins/{pin}')
    CHANNELS_WEBHOOKS_CREATE = (HTTPMethod.POST, CHANNELS + '/webhooks')
    CHANNELS_WEBHOOKS_LIST = (HTTPMethod.GET, CHANNELS + '/webhooks')

    # Guilds
    GUILDS = '/guilds/{guild}'
    GUILDS_GET = (HTTPMethod.GET, GUILDS)
    GUILDS_MODIFY = (HTTPMethod.PATCH, GUILDS)
    GUILDS_DELETE = (HTTPMethod.DELETE, GUILDS)
    GUILDS_CHANNELS_LIST = (HTTPMethod.GET, GUILDS + '/channels')
    GUILDS_CHANNELS_CREATE = (HTTPMethod.POST, GUILDS + '/channels')
    GUILDS_CHANNELS_MODIFY = (HTTPMethod.PATCH, GUILDS + '/channels')
    GUILDS_MEMBERS_LIST = (HTTPMethod.GET, GUILDS + '/members')
    GUILDS_MEMBERS_GET = (HTTPMethod.GET, GUILDS + '/members/{member}')
    GUILDS_MEMBERS_MODIFY = (HTTPMethod.PATCH, GUILDS + '/members/{member}')
    GUILDS_MEMBERS_KICK = (HTTPMethod.DELETE, GUILDS + '/members/{member}')
    GUILDS_BANS_LIST = (HTTPMethod.GET, GUILDS + '/bans')
    GUILDS_BANS_CREATE = (HTTPMethod.PUT, GUILDS + '/bans/{user}')
    GUILDS_BANS_DELETE = (HTTPMethod.DELETE, GUILDS + '/bans/{user}')
    GUILDS_ROLES_LIST = (HTTPMethod.GET, GUILDS + '/roles')
    GUILDS_ROLES_CREATE = (HTTPMethod.POST, GUILDS + '/roles')
    GUILDS_ROLES_MODIFY_BATCH = (HTTPMethod.PATCH, GUILDS + '/roles')
    GUILDS_ROLES_MODIFY = (HTTPMethod.PATCH, GUILDS + '/roles/{role}')
    GUILDS_ROLES_DELETE = (HTTPMethod.DELETE, GUILDS + '/roles/{role}')
    GUILDS_PRUNE_COUNT = (HTTPMethod.GET, GUILDS + '/prune')
    GUILDS_PRUNE_BEGIN = (HTTPMethod.POST, GUILDS + '/prune')
    GUILDS_VOICE_REGIONS_LIST = (HTTPMethod.GET, GUILDS + '/regions')
    GUILDS_INVITES_LIST = (HTTPMethod.GET, GUILDS + '/invites')
    GUILDS_INTEGRATIONS_LIST = (HTTPMethod.GET, GUILDS + '/integrations')
    GUILDS_INTEGRATIONS_CREATE = (HTTPMethod.POST, GUILDS + '/integrations')
    GUILDS_INTEGRATIONS_MODIFY = (HTTPMethod.PATCH, GUILDS + '/integrations/{integration}')
    GUILDS_INTEGRATIONS_DELETE = (HTTPMethod.DELETE, GUILDS + '/integrations/{integration}')
    GUILDS_INTEGRATIONS_SYNC = (HTTPMethod.POST, GUILDS + '/integrations/{integration}/sync')
    GUILDS_EMBED_GET = (HTTPMethod.GET, GUILDS + '/embed')
    GUILDS_EMBED_MODIFY = (HTTPMethod.PATCH, GUILDS + '/embed')
    GUILDS_WEBHOOKS_LIST = (HTTPMethod.GET, GUILDS + '/webhooks')

    # Users
    USERS = '/users'
    USERS_ME_GET = (HTTPMethod.GET, USERS + '/@me')
    USERS_ME_PATCH = (HTTPMethod.PATCH, USERS + '/@me')
    USERS_ME_GUILDS_LIST = (HTTPMethod.GET, USERS + '/@me/guilds')
    USERS_ME_GUILDS_LEAVE = (HTTPMethod.DELETE, USERS + '/@me/guilds/{guild}')
    USERS_ME_DMS_LIST = (HTTPMethod.GET, USERS + '/@me/channels')
    USERS_ME_DMS_CREATE = (HTTPMethod.POST, USERS + '/@me/channels')
    USERS_ME_CONNECTIONS_LIST = (HTTPMethod.GET, USERS + '/@me/connections')
    USERS_GET = (HTTPMethod.GET, USERS + '/{user}')

    # Invites
    INVITES = '/invites'
    INVITES_GET = (HTTPMethod.GET, INVITES + '/{invite}')
    INVITES_DELETE = (HTTPMethod.DELETE, INVITES + '/{invite}')

    # Webhooks
    WEBHOOKS = '/webhooks/{webhook}'
    WEBHOOKS_GET = (HTTPMethod.GET, WEBHOOKS)
    WEBHOOKS_MODIFY = (HTTPMethod.PATCH, WEBHOOKS)
    WEBHOOKS_DELETE = (HTTPMethod.DELETE, WEBHOOKS)
    WEBHOOKS_TOKEN_GET = (HTTPMethod.GET, WEBHOOKS + '/{token}')
    WEBHOOKS_TOKEN_MODIFY = (HTTPMethod.PATCH, WEBHOOKS + '/{token}')
    WEBHOOKS_TOKEN_DELETE = (HTTPMethod.DELETE, WEBHOOKS + '/{token}')
    WEBHOOKS_TOKEN_EXECUTE = (HTTPMethod.POST, WEBHOOKS + '/{token}')


class APIException(Exception):
    """
    Exception thrown when an HTTP-client level error occurs. Usually this will
    be a non-success status-code, or a transient network issue.

    Attributes
    ----------
    status_code : int
        The status code returned by the API for the request that triggered this
        error.
    """
    def __init__(self, msg, status_code=0, content=None):
        self.status_code = status_code
        self.content = content
        self.msg = msg

        if self.status_code:
            self.msg += ' code: {}'.format(status_code)

        super(APIException, self).__init__(self.msg)


class HTTPClient(LoggingClass):
    """
    A simple HTTP client which wraps the requests library, adding support for
    Discords rate-limit headers, authorization, and request/response validation.
    """
    BASE_URL = 'https://discordapp.com/api/v6'
    MAX_RETRIES = 5

    def __init__(self, token):
        super(HTTPClient, self).__init__()

        self.limiter = RateLimiter()
        self.headers = {
            'Authorization': 'Bot ' + token,
        }

    def __call__(self, route, args=None, **kwargs):
        return self.call(route, args, **kwargs)

    def call(self, route, args=None, **kwargs):
        """
        Makes a request to the given route (as specified in
        :class:`disco.api.http.Routes`) with a set of URL arguments, and keyword
        arguments passed to requests.

        Parameters
        ----------
        route : tuple(:class:`HTTPMethod`, str)
            The method.URL combination that when compiled with URL arguments
            creates a requestable route which the HTTPClient will make the
            request too.
        args : dict(str, str)
            A dictionary of URL arguments that will be compiled with the raw URL
            to create the requestable route. The HTTPClient uses this to track
            rate limits as well.
        kwargs : dict
            Keyword arguments that will be passed along to the requests library

        Raises
        ------
        APIException
            Raised when an unrecoverable error occurs, or when we've exhausted
            the number of retries.

        Returns
        -------
        :class:`requests.Response`
            The response object for the request
        """
        args = args or {}
        retry = kwargs.pop('retry_number', 0)

        # Merge or set headers
        if 'headers' in kwargs:
            kwargs['headers'].update(self.headers)
        else:
            kwargs['headers'] = self.headers

        # Build the bucket URL
        filtered = {k: (v if v in ('guild', 'channel') else '') for k, v in six.iteritems(args)}
        bucket = (route[0].value, route[1].format(**filtered))

        # Possibly wait if we're rate limited
        self.limiter.check(bucket)

        # Make the actual request
        url = self.BASE_URL + route[1].format(**args)
        r = requests.request(route[0].value, url, **kwargs)

        # Update rate limiter
        self.limiter.update(bucket, r)

        # If we got a success status code, just return the data
        if r.status_code < 400:
            return r
        elif r.status_code != 429 and 400 <= r.status_code < 500:
            raise APIException('Request failed', r.status_code, r.content)
        else:
            if r.status_code == 429:
                self.log.warning('Request responded w/ 429, retrying (but this should not happen, check your clock sync')

            # If we hit the max retries, throw an error
            retry += 1
            if retry > self.MAX_RETRIES:
                self.log.error('Failing request, hit max retries')
                raise APIException('Request failed after {} attempts'.format(self.MAX_RETRIES), r.status_code, r.content)

            backoff = self.random_backoff()
            self.log.warning('Request to `{}` failed with code {}, retrying after {}s ({})'.format(
                url, r.status_code, backoff, r.content
            ))
            gevent.sleep(backoff)

            # Otherwise just recurse and try again
            return self(route, args, retry_number=retry, **kwargs)

    @staticmethod
    def random_backoff():
        """
        Returns a random backoff (in milliseconds) to be used for any error the
        client suspects is transient. Will always return a value between 500 and
        5000 milliseconds.

        :returns: a random backoff in milliseconds
        :rtype: float
        """
        return random.randint(500, 5000) / 1000.0
