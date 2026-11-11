from pinnacle_google import GoogleReadonlyClient, Phase3ReadOnly


def test_connector_refuses_send():
    client = GoogleReadonlyClient(credentials=None)  # type: ignore[arg-type]
    try:
        client.send_email("nope")
        raise AssertionError("send must not succeed")
    except Phase3ReadOnly:
        pass


def test_connector_refuses_calendar_write():
    client = GoogleReadonlyClient(credentials=None)  # type: ignore[arg-type]
    try:
        client.create_calendar_event()
        raise AssertionError("calendar write must not succeed")
    except Phase3ReadOnly:
        pass
