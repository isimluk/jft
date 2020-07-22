from .cfg import config
from .logging import log
from jira import JIRA, JIRAError


class ConnectionError(Exception):
    pass


def connect():
    url = config.get('url')
    username = config.get('username')
    password = config.get('password')

    options = {
        'server': url,
        'check_update': False,
    }

    try:
        try:
            conn = JIRA(options, basic_auth=(username, password))
        except AttributeError as e:
            # monkey patch https://github.com/pycontribs/jira/pull/329
            # discussion is stalled in this pull request
            if str(e) == "'bool' object has no attribute 'error'":
                conn = JIRA(options, basic_auth=(username, password), logging=log)
            else:
                raise e
    except KeyError as e:
        if str(e) == "'versionNumbers'":
            # Dear future me please forgive me.
            # This happpens when authentication fails this is the error from JIRA package.
            # So, let's skip the version info check
            conn = JIRA(options, basic_auth=(username, password), get_server_info=False)
        else:
            raise e

    assert_authenticated(conn, username)
    return conn


def assert_authenticated(connection, username):
    url = connection._get_url('serverInfo')
    response = connection._session.get(url)

    hint = ('Try yourself: curl -D- -u {} -X GET -H "Content-Type: application/json"'
            '-s -o /dev/null {} | grep -e X-Seraph-LoginReason').format(username, url)

    if response.headers['X-Seraph-LoginReason'] in ['AUTHENTICATION_DENIED', 'AUTHENTICATED_FAILED']:
        raise ConnectionError(
            'Jira authentication failed. Please test your JIRA credentials with:\n' + hint)

    if 'OK' not in response.headers['X-Seraph-LoginReason'] or not response.text:
        raise ConnectionError(
            'Jira authentication failed. X-Seraph-LoginReason="{}" response-body="{}"\n{}'
            .format(response.headers['X-Seraph-LoginReason'], response.text, hint))
