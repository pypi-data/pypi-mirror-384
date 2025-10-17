# Copyright 2006-2023 Medstrat, Inc. All rights reserved.
# Copyright 2024-2025 Zimmer, Inc. All rights reserved.
# See the accompanying AUTHORS file for a complete list of authors.
# This file is subject to the terms and conditions defined in LICENSE.

import asyncio
import pytest
import pytest_asyncio
from bedrock.db.authorizationcolumns import STREAM_ID
from bedrock.lang.testsuite import TEST_SIUID
from bedrock.network.authenticatedwshandler import ClosureCode
from catapult.config.envvar import JOINTS_TWSD_REQUEST_TIMEOUT
from catapult.event.event import EVENT_DATA, EVENT_ID, EVENT_TYPE
from catapult.network.jsonrpc import CODE, ERROR, MESSAGE, METHOD, PARAMS, PARTIAL, RESULT, RPC_ID, toJSONRPCRequest
from joints.db.studycolumns import SIUID
from joints.event.studyviewed import STUDY_VIEWED
from joints.network.jsonrpcwshandler import *
from json import loads
from os import environ
from tornado.websocket import websocket_connect


@pytest.fixture(scope='module')
def daemon(module_mocker):
  yield module_mocker.MagicMock(isShuttingDown=False)


@pytest.fixture(scope='module')
def app(daemon):
  from tornado.web import Application

  rules = [
    (r'/ws/joints/rpc', JSONRPCWebSocketHandler),
    (r'/ws/grandcentral/rpc', JSONRPCWebSocketHandler),
  ]

  yield Application(rules, daemon=daemon)


@pytest.fixture(scope='module')
def event_loop():
  # Replace the default event_loop fixture with one that is module-scoped, so that it can be used by our app
  loop = asyncio.new_event_loop()

  yield loop
  loop.close()


@pytest_asyncio.fixture(scope='module')
async def appPort(app):
  from tornado.httpserver import HTTPServer
  from tornado.testing import bind_unused_port

  socket, port = bind_unused_port()
  server = HTTPServer(app)

  server.add_sockets([socket])
  yield port

  # Ensure sockets have had a chance to close to avoid warning logs
  await asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()})
  server.stop()
  await server.close_all_connections()


@pytest.fixture
def httpClient(mocker):
  from bedrock.db.authorizationcolumns import CAN_MANAGE_RAD_REPORTS, CAN_READ_ALL_STUDIES
  from json import dumps
  from tornado.httpclient import HTTPResponse

  async def mockAuthResponse(*args, **kwargs):
    return mocker.MagicMock(
      spec=HTTPResponse,
      body=dumps(
        {
          'result': {
            'isRadiologist': False,
            'auths': [
              {STREAM_ID: 2, CAN_READ_ALL_STUDIES: 1, CAN_MANAGE_RAD_REPORTS: 0, 'siuids': []},
              {STREAM_ID: 3, CAN_READ_ALL_STUDIES: 0, CAN_MANAGE_RAD_REPORTS: 0, 'siuids': [TEST_SIUID]},
            ],
          }
        }
      ),
    )

  client = mocker.MagicMock(**{'fetch.side_effect': [mockAuthResponse()]})

  mocker.patch('tornado.httpclient.AsyncHTTPClient', autospec=True, return_value=client)
  yield client


@pytest.fixture
def gcHTTPClient(httpClient, mocker):
  from json import dumps
  from tornado.httpclient import HTTPResponse

  async def mockAuthResponse(*args, **kwargs):
    return mocker.MagicMock(
      spec=HTTPResponse,
      body=dumps({'result': True}),
    )

  httpClient.fetch.side_effect = [mockAuthResponse()]

  yield httpClient


@pytest.fixture
def httpClientAuthFailure(mocker):
  from json import dumps
  from tornado.httpclient import HTTPResponse

  async def mockAuthResponse(*args, **kwargs):
    return mocker.MagicMock(
      spec=HTTPResponse,
      body=dumps({'error': {'code': 99, 'message': 'RPC error'}}),
    )

  client = mocker.MagicMock(**{'fetch.side_effect': [mockAuthResponse()]})

  mocker.patch('tornado.httpclient.AsyncHTTPClient', autospec=True, return_value=client)
  yield client


@pytest.fixture
def handleRPC(httpClient, mocker):
  from tornado.httpclient import HTTPResponse

  async def mockRPCResponse(*args, **kwargs):
    return mocker.MagicMock(spec=HTTPResponse, body='rpcresponsehere')

  httpClient.fetch.side_effect = list(httpClient.fetch.side_effect) + [mockRPCResponse()]


@pytest.fixture
def httpHeaders(mocker, testVars):
  from bedrock.auth.authentication import getAuthenticatorCookieName
  from bedrock.auth.authenticator import Authenticator
  from tornado.httputil import HTTPHeaders

  auth = Authenticator(testVars.cAll)

  yield HTTPHeaders({'Cookie': f'{getAuthenticatorCookieName()}={str(auth)}'})


@pytest.fixture
def rpcKey(testVars):
  from bedrock.db.authenticationcolumns import RPC_KEY

  return convertBase64URLSafetoUnsafe(testVars.cAll.read(RPC_KEY))


@pytest_asyncio.fixture
async def client(appPort, httpClient, httpHeaders, daemon, rpcKey):
  from tornado.httpclient import HTTPRequest

  # Because the daemon mock is created once for the module, reset it for each websocket we open
  daemon.reset_mock()

  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  yield client
  client.close()


@pytest_asyncio.fixture
async def certClient(appPort, httpClient, daemon, testVars):
  from bedrock.lang.testsuite import flaskRequest
  from tornado.httpclient import HTTPRequest
  from tornado.httputil import HTTPHeaders

  # Because the daemon mock is created once for the module, reset it for each websocket we open
  daemon.reset_mock()

  with flaskRequest(certified=True, certifiedAs=testVars.cAll) as request:
    cookieString = '; '.join([f'{k}={v}' for k, v in request.cookies.items()])
    headers = HTTPHeaders({'Cookie': cookieString})
    req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=headers)
    client = await websocket_connect(req, subprotocols=[VOUCH_SUBPROTOCOL])

  yield client
  client.close()


# -----
# Tests
# -----

def test_convertBase64URLSafetoUnsafe():
  assert convertBase64URLSafetoUnsafe('Ncr-uvi_') == 'Ncr+uvi/'
  assert convertBase64URLSafetoUnsafe('Ncr-uvi_m') == 'Ncr+uvi/m==='


@pytest.mark.asyncio
async def test_handlerRegistersWithDaemonAfterAuthCheck(client, daemon):
  daemon.register.assert_called_once()


@pytest.mark.asyncio
async def test_handlerClosesIfOpenedWithoutSubprotocol(appPort, daemon):
  daemon.reset_mock()

  client = await websocket_connect(f'ws://localhost:{appPort}/ws/joints/rpc')

  assert await client.read_message() is None
  assert client.close_code == ClosureCode.AUTHENTICATION_REQUIRED
  daemon.register.assert_not_called()


@pytest.mark.asyncio
async def test_handlerClosesIfOpenedDuringDaemonShutdown(appPort, daemon):
  daemon.reset_mock()

  daemon.isShuttingDown = True
  client = await websocket_connect(f'ws://localhost:{appPort}/ws/joints/rpc')

  assert await client.read_message() is None
  assert client.close_code == ClosureCode.SERVICE_RESTART
  daemon.register.assert_not_called()

  daemon.isShuttingDown = False


@pytest.mark.asyncio
async def test_handlerClosesIfOpenedWithoutCookies(appPort, daemon):
  daemon.reset_mock()

  client = await websocket_connect(f'ws://localhost:{appPort}/ws/joints/rpc', subprotocols=[JSONRPC_SUBPROTOCOL])

  assert await client.read_message() is None
  assert client.close_code == 4013
  daemon.register.assert_not_called()


@pytest.mark.asyncio
async def test_handlerMarksAsClosedOnClose(client, daemon):
  client.close()
  assert await client.read_message() is None

  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  assert handler.isClosed


@pytest.mark.asyncio
async def test_handlerClosesIfAuthCookieExpires(mocker, client, daemon):
  import datetime

  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  assert not handler.isClosed

  # Mock datetime.now() so the cookie is expired
  mockdatetime = mocker.patch.object(datetime, 'datetime', wraps=datetime.datetime)
  mockdatetime.now.return_value = datetime.datetime(2222, 1, 1, 1, 1)

  assert handler.closeIfInvalidAuth()

  # Assert the socket has closed
  assert await client.read_message() is None
  assert client.close_code == ClosureCode.AUTHENTICATION_REQUIRED


@pytest.mark.asyncio
async def test_handlerClosesIfAuthenticationFails(daemon, appPort, httpClientAuthFailure, httpHeaders, rpcKey):
  from tornado.httpclient import HTTPRequest

  daemon.reset_mock()

  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  assert await client.read_message() is None
  assert client.close_code == ClosureCode.AUTH_SERVICE_ERROR
  daemon.register.assert_not_called()


@pytest.mark.asyncio
async def test_handlerDoesNotCloseOnLogoutForUnrelatedCookie(client, daemon, httpHeaders):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  assert not handler.closeIfLogout('somecookie')

  # Check the connection still works
  assert not handler.isClosed
  handler.respondToClient('testid', result='foo')
  assert 'foo' in await client.read_message()


@pytest.mark.asyncio
async def test_certHandlerDoesNotCloseOnLogout(certClient, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  assert not handler.closeIfLogout('somecookie')

  # Check the connection still works
  assert not handler.isClosed
  handler.respondToClient('testid', result='foo')
  assert 'foo' in await certClient.read_message()


@pytest.mark.asyncio
async def test_handlerClosesOnLogoutForCookieUsedToOpenWebSocket(client, daemon, httpHeaders):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]
  authCookie = httpHeaders['Cookie'].split('=', 1)[-1]

  assert handler.closeIfLogout(authCookie)

  # Assert the socket has closed
  assert await client.read_message() is None
  assert client.close_code == ClosureCode.LOGOUT


@pytest.mark.asyncio
async def test_handlerCanMakeRPCRequestToClient(client, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  handler.requestOnClient('testuid', 'foo.bar', {'a': 'b'})

  msg = await client.read_message()
  msg = loads(msg)

  assert msg[RPC_ID] == 'testuid'
  assert msg[METHOD] == 'foo.bar'
  assert msg[PARAMS] == {'a': 'b'}


@pytest.mark.asyncio
@pytest.mark.parametrize('envValue,expectedTimeout', [(None, 40.0), ('1', 1.0), ('invalid', 40.0)])
async def test_asyncRequestConfiguration(
  daemon, appPort, httpClient, handleRPC, httpHeaders, rpcKey, mocker, envValue, expectedTimeout
):
  from tornado.httpclient import HTTPRequest

  daemon.reset_mock()

  if envValue is None:
    if JOINTS_TWSD_REQUEST_TIMEOUT in environ:
      del environ[JOINTS_TWSD_REQUEST_TIMEOUT]
  else:
    mocker.patch.dict(environ, {JOINTS_TWSD_REQUEST_TIMEOUT: envValue})

  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))
    assert await client.read_message() == 'rpcresponsehere'
    assert httpClient.fetch.call_args[0][0].request_timeout == expectedTimeout
  finally:
    client.close()


@pytest.mark.asyncio
async def test_handlerSendsDelayedRPCResponsesWithResults(client, daemon):
  handler = daemon.register.call_args[0][0]

  handler.respondToClient('testuid', 17, partial=True)

  msg = await client.read_message()
  msg = loads(msg)

  assert msg[RPC_ID] == 'testuid'
  assert msg[RESULT] == 17
  assert msg[PARTIAL]


@pytest.mark.asyncio
async def test_handlerSendsDelayedRPCResponsesWithErrors(client, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  handler.respondToClient('testuid', None, 42, 'test failure')

  msg = await client.read_message()
  msg = loads(msg)

  assert msg[RPC_ID] == 'testuid'
  assert msg[ERROR][CODE] == 42
  assert msg[ERROR][MESSAGE] == 'test failure'


@pytest.mark.asyncio
async def test_handlerClosesIfRPCResponseToClientIsRPCDisallowed(client, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  # XXX: The error code '1' indicates RPC Disallowed
  handler.respondToClient('testuid', None, 1, 'test failure')
  assert await client.read_message() is None
  assert client.close_code == ClosureCode.RPC_DISALLOWED


@pytest.mark.asyncio
async def test_handlerDoesNotDisconnectOnInvalidMessageReceived(client, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  # Send a non-JSON message
  client.write_message('{"something"')

  # Check the connection still works
  assert not handler.isClosed
  handler.respondToClient('testid', result='foo')
  assert 'foo' in await client.read_message()


@pytest.mark.asyncio
async def test_clientCanSubscribeForEvents(testVars, client, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  # Send an event before the client has subscribed
  await handler.receiveEvent(
    {
      EVENT_ID: 'e1',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )

  # Subscribe for STUDY_VIEWED events
  params = {
    'subscriptions': [
      {
        'eventType': STUDY_VIEWED,
        'criteria': {STREAM_ID: 2},
      }
    ]
  }

  client.write_message(toJSONRPCRequest('websocket.subscribe', 'testuid', params=params))

  msg = await client.read_message()
  msg = loads(msg)

  # Assert the RPC response for the subscribe is correct
  assert msg[RPC_ID] == 'testuid'
  assert msg[RESULT] is None

  # Send a second event now that the client has subscribed
  await handler.receiveEvent(
    {
      EVENT_ID: 'e2',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )

  # Verify the second event was received, per the subscription
  msg = await client.read_message()
  msg = loads(msg)

  assert msg[EVENT_ID] == 'e2'
  assert msg[EVENT_TYPE] == STUDY_VIEWED
  assert msg[EVENT_DATA] == {STREAM_ID: 2, SIUID: TEST_SIUID}


@pytest.mark.asyncio
async def test_clientCanSubscribeForMultipleEvents(testVars, client, daemon):
  from joints.event.newstudy import NEW_STUDY

  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  # Send events before the client has subscribed
  await handler.receiveEvent(
    {
      EVENT_ID: 'nope1',
      EVENT_TYPE: NEW_STUDY,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )
  await handler.receiveEvent(
    {
      EVENT_ID: 'nope2',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )

  # Subscribe for NEW_STUDY and STUDY_VIEWED events
  params = {
    'subscriptions': [
      {'eventType': NEW_STUDY, 'criteria': {STREAM_ID: 2}},
      {'eventType': STUDY_VIEWED, 'criteria': {STREAM_ID: 2}},
    ]
  }

  client.write_message(toJSONRPCRequest('websocket.subscribe', 'testuid', params=params))

  msg = await client.read_message()
  msg = loads(msg)

  # Assert the RPC response for the subscribe is correct
  assert msg[RPC_ID] == 'testuid'
  assert msg[RESULT] is None

  # Send events now that the client is subscribed
  await handler.receiveEvent(
    {
      EVENT_ID: 'e1',
      EVENT_TYPE: NEW_STUDY,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )
  await handler.receiveEvent(
    {
      EVENT_ID: 'e2',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )

  # Assert the 2 expected events are received
  msg = await client.read_message()
  e1 = loads(msg)
  msg = await client.read_message()
  e2 = loads(msg)

  assert e1[EVENT_ID] == 'e1'
  assert e2[EVENT_ID] == 'e2'


@pytest.mark.asyncio
async def test_subscribeWithReplaceOverridesPastSubscriptions(client, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  # Subscribe for STUDY_VIEWED events, then override that subscription
  params = {
    'subscriptions': [
      {
        'eventType': STUDY_VIEWED,
        'criteria': {STREAM_ID: 2},
      }
    ]
  }
  overrideParams = {
    'replace': True,
    'subscriptions': [
      {
        'eventType': STUDY_VIEWED,
        'criteria': {STREAM_ID: 3},
      }
    ],
  }

  client.write_message(toJSONRPCRequest('websocket.subscribe', 'testuid', params=params))
  client.write_message(toJSONRPCRequest('websocket.subscribe', 'testuid', params=overrideParams))

  # Discard the subscribe confirmations
  await client.read_message()
  await client.read_message()

  # Send 2 events, with the first matching the original criteria and the second matching the new criteria
  await handler.receiveEvent(
    {
      EVENT_ID: 'e1',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )
  await handler.receiveEvent(
    {
      EVENT_ID: 'e2',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 3, SIUID: TEST_SIUID},
    },
    True,
  )

  # Assert that only the last event is forwarded to the client
  msg = await client.read_message()
  event = loads(msg)

  assert event[EVENT_ID] == 'e2'


@pytest.mark.asyncio
async def test_handlerReturnsRPCErrorsForInvalidEventSubscribeRequests(client, daemon):
  # Subscribe without giving an eventType
  client.write_message(
    toJSONRPCRequest('websocket.subscribe', 'testuid', params={'subscriptions': [{'criteria': {'foo': 'bar'}}]})
  )

  msg = await client.read_message()
  msg = loads(msg)

  # Assert the error looks correct
  assert msg[ERROR][CODE] == -1
  assert msg[RPC_ID] == 'testuid'


@pytest.mark.asyncio
async def test_handlerFiltersEventsBasedOnSubscribedEventCriteria(client, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  # Subscribe for STUDY_VIEWED events
  params = {
    'subscriptions': [
      {
        'eventType': STUDY_VIEWED,
        'criteria': {STREAM_ID: 2},
      }
    ]
  }

  client.write_message(toJSONRPCRequest('websocket.subscribe', 'testuid', params=params))

  # Discard the subscribe confirmation
  await client.read_message()

  # Send 2 STUDY_VIEWED events
  await handler.receiveEvent(
    {
      EVENT_ID: 'e1',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 1, SIUID: TEST_SIUID},
    },
    True,
  )
  await handler.receiveEvent(
    {
      EVENT_ID: 'e2',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )

  # Verify the second event was received, per the subscription
  msg = await client.read_message()
  msg = loads(msg)

  assert msg[EVENT_ID] == 'e2'
  assert msg[EVENT_TYPE] == STUDY_VIEWED
  assert msg[EVENT_DATA] == {STREAM_ID: 2, SIUID: TEST_SIUID}


@pytest.mark.asyncio
async def test_handlerFiltersEventsBasedOnPermissions(client, daemon):
  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  # Subscribe for STUDY_VIEWED events
  params = {
    'subscriptions': [
      {
        'eventType': STUDY_VIEWED,
        'criteria': {STREAM_ID: 3},
      }
    ]
  }

  client.write_message(toJSONRPCRequest('websocket.subscribe', 'testuid', params=params))

  # Discard the subscribe confirmation
  await client.read_message()

  # Send 2 STUDY_VIEWED events
  await handler.receiveEvent(
    {
      EVENT_ID: 'e1',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 3, SIUID: '1.2.3.4.5'},
    },
    True,
  )
  await handler.receiveEvent(
    {
      EVENT_ID: 'e2',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 3, SIUID: TEST_SIUID},
    },
    True,
  )

  # Verify only the second event was sent to the client, due to permissions filtering
  msg = await client.read_message()
  msg = loads(msg)

  assert msg[EVENT_ID] == 'e2'
  assert msg[EVENT_TYPE] == STUDY_VIEWED
  assert msg[EVENT_DATA] == {STREAM_ID: 3, SIUID: TEST_SIUID}


@pytest.mark.asyncio
async def test_handlerChecksAuthExpirationBeforeForwardingEvent(mocker, client, daemon):
  import datetime

  # Grab the handler for this client, which was registered with the daemon mock
  handler = daemon.register.call_args[0][0]

  # Subscribe for STUDY_VIEWED events
  params = {
    'subscriptions': [
      {
        'eventType': STUDY_VIEWED,
        'criteria': {STREAM_ID: 2},
      }
    ]
  }

  client.write_message(toJSONRPCRequest('websocket.subscribe', 'testuid', params=params))

  # Discard the subscribe confirmation
  await client.read_message()

  # Mock datetime.now() so the cookie is expired
  mockdatetime = mocker.patch.object(datetime, 'datetime', wraps=datetime.datetime)
  mockdatetime.now.return_value = datetime.datetime(2222, 1, 1, 1, 1)

  # Send an event that matches the subscription
  await handler.receiveEvent(
    {
      EVENT_ID: 'e1',
      EVENT_TYPE: STUDY_VIEWED,
      EVENT_DATA: {STREAM_ID: 2, SIUID: TEST_SIUID},
    },
    True,
  )

  # Assert the socket has closed
  assert await client.read_message() is None
  assert client.close_code == ClosureCode.AUTHENTICATION_REQUIRED


@pytest.mark.asyncio
async def test_handlerMakesRPCToJointsAPI_ContainerEnv(
  asContainer, asNonMonolithic, daemon, appPort, httpClient, handleRPC, httpHeaders, rpcKey
):
  from tornado.httpclient import HTTPRequest

  daemon.reset_mock()  # Because the daemon mock is created once for the module, reset it for each websocket we open

  # Open a websocket
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    # Make an RPC as client would
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))

    # Assert the client gets the RPC response back
    assert await client.read_message() == 'rpcresponsehere'

    # Assert the proxied RPC request looks correct
    request = httpClient.fetch.call_args[0][0]
    requestBody = loads(request.body)

    assert request.url == 'http://japid:4444/api/joints/rpc.wsgi'
    assert request.headers['Cookie'] == httpHeaders['Cookie']
    assert requestBody[RPC_ID] == 'testuid'
    assert requestBody[METHOD] == 'stream.getstuff'
    assert requestBody[PARAMS] == {'foo': 'bar'}
  finally:
    client.close()


@pytest.mark.asyncio
async def test_certClientCannotSubscribeForEvents(testVars, certClient):
  # Subscribe for STUDY_VIEWED events
  params = {
    'subscriptions': [
      {
        'eventType': STUDY_VIEWED,
        'criteria': {STREAM_ID: 2},
      }
    ]
  }

  certClient.write_message(toJSONRPCRequest('websocket.subscribe', 'testuid', params=params))

  msg = await certClient.read_message()
  msg = loads(msg)

  assert msg[RPC_ID] == 'testuid'
  assert msg[ERROR][CODE] == -32600
  assert 'Cannot subscribe to events' in msg[ERROR][MESSAGE]


@pytest.mark.asyncio
async def test_handlerMakesRPCToGrandcentralAPI_ContainerEnv(
  asContainer, asNonMonolithic, daemon, appPort, gcHTTPClient, handleRPC, httpHeaders, rpcKey
):
  from tornado.httpclient import HTTPRequest

  daemon.reset_mock()  # Because the daemon mock is created once for the module, reset it for each websocket we open

  # Open a websocket
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/grandcentral/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    # Make an RPC as client would
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))

    # Assert the client gets the RPC response back
    assert await client.read_message() == 'rpcresponsehere'

    # Assert the proxied RPC request looks correct
    request = gcHTTPClient.fetch.call_args[0][0]
    requestBody = loads(request.body)

    assert request.url == 'http://gapid:4444/api/grandcentral/rpc.wsgi'
    assert request.headers['Cookie'] == httpHeaders['Cookie']
    assert requestBody[RPC_ID] == 'testuid'
    assert requestBody[METHOD] == 'stream.getstuff'
    assert requestBody[PARAMS] == {'foo': 'bar'}
  finally:
    client.close()


@pytest.mark.asyncio
async def test_handlerMakesRPCToJointsAPI_NonContainerEnv(
  asNonContainer, daemon, appPort, httpClient, handleRPC, httpHeaders, rpcKey
):
  from tornado.httpclient import HTTPRequest

  daemon.reset_mock()  # Because the daemon mock is created once for the module, reset it for each websocket we open

  # Open a websocket
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    # Make an RPC as client would
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))

    # Assert the client gets the RPC response back
    assert await client.read_message() == 'rpcresponsehere'

    # Assert the proxied RPC request looks correct
    request = httpClient.fetch.call_args[0][0]
    requestBody = loads(request.body)

    assert request.url == 'http://127.0.0.1:8000/api/joints/rpc.wsgi'
    assert request.headers['Cookie'] == httpHeaders['Cookie']
    assert requestBody[RPC_ID] == 'testuid'
    assert requestBody[METHOD] == 'stream.getstuff'
    assert requestBody[PARAMS] == {'foo': 'bar'}
  finally:
    client.close()


@pytest.mark.asyncio
async def test_handlerMakesRPCToGrandcentralAPI_NonContainerEnv(
  asNonContainer, daemon, appPort, gcHTTPClient, handleRPC, httpHeaders, rpcKey
):
  from tornado.httpclient import HTTPRequest

  daemon.reset_mock()  # Because the daemon mock is created once for the module, reset it for each websocket we open

  # Open a websocket
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/grandcentral/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    # Make an RPC as client would
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))

    # Assert the client gets the RPC response back
    assert await client.read_message() == 'rpcresponsehere'

    # Assert the proxied RPC request looks correct
    request = gcHTTPClient.fetch.call_args[0][0]
    requestBody = loads(request.body)

    assert request.url == 'http://127.0.0.1:8002/api/grandcentral/rpc.wsgi'
    assert request.headers['Cookie'] == httpHeaders['Cookie']
    assert requestBody[RPC_ID] == 'testuid'
    assert requestBody[METHOD] == 'stream.getstuff'
    assert requestBody[PARAMS] == {'foo': 'bar'}
  finally:
    client.close()


@pytest.mark.asyncio
async def test_handlerLogsWarningWhenRPCExceeds90PercentTimeout(
  daemon, appPort, httpClient, httpHeaders, rpcKey, mocker
):
  import asyncio
  from time import time
  from tornado.httpclient import HTTPRequest, HTTPResponse

  daemon.reset_mock()

  # Mock the HTTP client to simulate a slow RPC that takes 37 seconds (92.5% of 40 second timeout)
  async def slowRPCResponse(*args, **kwargs):
    await asyncio.sleep(0)  # Yield control but don't actually wait
    return mocker.MagicMock(spec=HTTPResponse, body='slowresponse')

  # Mock time.time() to simulate elapsed time for the auth RPC
  from time import time

  realTimeFunc = time
  startTime = realTimeFunc()
  callCount = {'count': 0}

  def mockTimeFunc():
    callCount['count'] += 1

    if callCount['count'] == 1:
      return startTime  # First call: auth RPC start time
    elif callCount['count'] == 2:
      return startTime + 37.0  # Second call: auth RPC end time (37 seconds elapsed - slow!)
    else:
      return realTimeFunc()  # All other calls: use real time

  # Patch the time function in authenticatedwshandler module
  mocker.patch('bedrock.network.authenticatedwshandler.time', side_effect=mockTimeFunc)

  httpClient.fetch.side_effect = list(httpClient.fetch.side_effect) + [slowRPCResponse()]

  # Mock logger to capture warning
  mockLogger = mocker.patch('bedrock.network.authenticatedwshandler.logger')
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))
    assert await client.read_message() == 'slowresponse'

    # Assert warning was logged for the slow auth RPC
    mockLogger.warning.assert_called_once()

    warningMsg = mockLogger.warning.call_args[0][0]

    assert 'Slow RPC' in warningMsg
    assert 'user.websocketAuth' in warningMsg
    assert '37.00s' in warningMsg
    assert 'timeout is 40.0s' in warningMsg
    assert 'client disconnect risk' in warningMsg
  finally:
    client.close()


@pytest.mark.asyncio
async def test_handlerDoesNotLogWarningWhenRPCUnder90PercentTimeout(
  daemon, appPort, httpClient, httpHeaders, rpcKey, mocker
):
  import asyncio
  from time import time
  from tornado.httpclient import HTTPRequest, HTTPResponse

  daemon.reset_mock()

  # Mock the HTTP client to simulate a fast RPC that takes 30 seconds (75% of 40 second timeout)
  async def fastRPCResponse(*args, **kwargs):
    await asyncio.sleep(0)
    return mocker.MagicMock(spec=HTTPResponse, body='fastresponse')

  # Mock time.time() to simulate elapsed time - use a callable that tracks calls
  realTimeFunc = time
  startTime = realTimeFunc()
  callCount = {'count': 0}

  def mockTimeFunc():
    callCount['count'] += 1

    if callCount['count'] == 1:
      return startTime  # First call: start time
    elif callCount['count'] == 2:
      return startTime + 30.0  # Second call: 30 seconds later
    else:
      return realTimeFunc()  # All other calls: use real time

  mocker.patch('bedrock.network.authenticatedwshandler.time', side_effect=mockTimeFunc)

  httpClient.fetch.side_effect = list(httpClient.fetch.side_effect) + [fastRPCResponse()]

  # Mock logger to verify no warning
  mockLogger = mocker.patch('bedrock.network.authenticatedwshandler.logger')
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))
    assert await client.read_message() == 'fastresponse'

    # Assert no warning was logged
    mockLogger.warning.assert_not_called()
  finally:
    client.close()


@pytest.mark.asyncio
async def test_handlerLogsWarningAtExactly90PercentTimeout(daemon, appPort, httpClient, httpHeaders, rpcKey, mocker):
  import asyncio
  from time import time
  from tornado.httpclient import HTTPRequest, HTTPResponse

  daemon.reset_mock()

  # Mock the HTTP client to simulate RPC at exactly 90% of 40 second timeout (36 seconds)
  async def exactRPCResponse(*args, **kwargs):
    await asyncio.sleep(0)
    return mocker.MagicMock(spec=HTTPResponse, body='exactresponse')

  # Mock time.time() to simulate elapsed time - use a callable that tracks calls
  realTimeFunc = time
  startTime = realTimeFunc()
  callCount = {'count': 0}

  def mockTimeFunc():
    callCount['count'] += 1

    if callCount['count'] == 1:
      return startTime  # First call: start time
    elif callCount['count'] == 2:
      return startTime + 36.0  # Second call: 36 seconds later (exactly 90%)
    else:
      return realTimeFunc()  # All other calls: use real time

  mocker.patch('bedrock.network.authenticatedwshandler.time', side_effect=mockTimeFunc)

  httpClient.fetch.side_effect = list(httpClient.fetch.side_effect) + [exactRPCResponse()]

  # Mock logger to verify warning is NOT logged (only > 90%, not >=)
  mockLogger = mocker.patch('bedrock.network.authenticatedwshandler.logger')
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))
    assert await client.read_message() == 'exactresponse'

    # Assert no warning was logged (condition is >, not >=)
    mockLogger.warning.assert_not_called()
  finally:
    client.close()


@pytest.mark.asyncio
async def test_handlerLogs401ErrorDetailsAndClosesSocket(daemon, appPort, httpClient, httpHeaders, rpcKey, mocker):
  from tornado.httpclient import HTTPError, HTTPRequest, HTTPResponse

  daemon.reset_mock()

  # Mock the HTTP client to simulate an HTTP 401 error
  async def mockHTTP401Error(*args, **kwargs):
    errorResponse = mocker.MagicMock(spec=HTTPResponse, body=b'Unauthorized access')

    raise HTTPError(401, message='Unauthorized', response=errorResponse)

  httpClient.fetch.side_effect = list(httpClient.fetch.side_effect) + [mockHTTP401Error()]

  # Mock logger to capture error messages
  mockLogger = mocker.patch('bedrock.network.authenticatedwshandler.logger')
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))

    # Socket should close due to 401 error
    assert await client.read_message() is None
    assert client.close_code == ClosureCode.AUTHENTICATION_REQUIRED

    # Verify logger.error was called with the expected message
    assert mockLogger.error.call_count == 1

    errorMsg = mockLogger.error.call_args_list[0][0][0]

    # Verify error message contains detailed information
    assert 'Closing' in errorMsg
    assert 'HTTP 401' in errorMsg
    assert 'stream.getstuff' in errorMsg
    assert 'testuid' in errorMsg
    assert "response body: b'Unauthorized access'" in errorMsg or 'Unauthorized access' in errorMsg
  finally:
    if not client.close_code:
      client.close()


@pytest.mark.asyncio
async def test_handlerLogs401ErrorWithNoResponse(daemon, appPort, httpClient, httpHeaders, rpcKey, mocker):
  from tornado.httpclient import HTTPError, HTTPRequest

  daemon.reset_mock()

  # Mock the HTTP client to simulate an HTTP 401 error with no response body
  async def mockHTTP401ErrorNoResponse(*args, **kwargs):
    raise HTTPError(401, message='Unauthorized', response=None)

  httpClient.fetch.side_effect = list(httpClient.fetch.side_effect) + [mockHTTP401ErrorNoResponse()]

  # Mock logger to capture error messages
  mockLogger = mocker.patch('bedrock.network.authenticatedwshandler.logger')
  req = HTTPRequest(f'ws://localhost:{appPort}/ws/joints/rpc', headers=httpHeaders)
  client = await websocket_connect(req, subprotocols=[JSONRPC_SUBPROTOCOL, rpcKey])

  try:
    client.write_message(toJSONRPCRequest('stream.getstuff', 'testuid', params={'foo': 'bar'}))

    # Socket should close due to 401 error
    assert await client.read_message() is None
    assert client.close_code == ClosureCode.AUTHENTICATION_REQUIRED

    # Verify logger.error was called
    assert mockLogger.error.call_count == 1

    errorMsg = mockLogger.error.call_args_list[0][0][0]

    # Verify error message indicates no response
    assert 'HTTP 401' in errorMsg
    assert 'no response' in errorMsg
  finally:
    if not client.close_code:
      client.close()
