def test_event_warns_on_missing_defaults(EventCls, recwarn):
    ev = EventCls("uuid-1")
    out = ev.dump()
    assert isinstance(out, dict)
    assert any("Event properties" in str(w.message) for w in recwarn.list)


def test_event_serializes_payload(EventCls, PayloadCls, recwarn):
    ev = EventCls("u-1")
    ev.set_user_name("alice").set_url("https://ex/").set_http_method("GET") \
        .set_ip_address("1.1.1.1").set_user_agent("custom-useragent") \
        .set_browser_language("en-gb").set_http_referer("test")

    p1 = PayloadCls().set_field_id("id1").set_old_value("a").set_new_value("b")
    p2 = PayloadCls().set_field_name("Name")
    ev.add_payload(p1).add_payload(p2)

    out = ev.dump()
    assert "payload" in out and isinstance(out["payload"], list)
    assert {"field_id": "id1", "old_value": "a", "new_value": "b"} in out["payload"]
    assert {"field_name": "Name"} in out["payload"]
