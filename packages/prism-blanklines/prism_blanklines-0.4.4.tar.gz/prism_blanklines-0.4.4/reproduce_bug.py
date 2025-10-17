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
