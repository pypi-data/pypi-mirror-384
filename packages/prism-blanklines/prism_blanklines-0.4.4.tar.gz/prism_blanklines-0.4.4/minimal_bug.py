async def test_handlerLogs401ErrorWithNoResponse(daemon, appPort):
  from tornado.httpclient import HTTPError
  daemon.reset_mock()
  # Mock the HTTP client
  async def mockHTTP401ErrorNoResponse(*args, **kwargs):
    raise HTTPError(401, message='Unauthorized', response=None)

  httpClient.fetch.side_effect = list(httpClient.fetch.side_effect) + [mockHTTP401ErrorNoResponse()]
