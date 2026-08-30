from acri._openai_wire import extract_text


def test_extract_text_passes_a_plain_string_through():
    assert extract_text("what's the weather in Tokyo") == "what's the weather in Tokyo"


def test_extract_text_joins_text_parts_of_a_multimodal_list():
    content = [
        {"type": "text", "text": "what's in this image?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
    ]
    assert extract_text(content) == "what's in this image?"


def test_extract_text_on_an_image_only_message_returns_empty_string():
    content = [{"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]
    assert extract_text(content) == ""
