from types import SimpleNamespace

import acri


def test_schema_change_cannot_reuse_an_old_response():
    def create(**kwargs):
        schema = kwargs["tools"][0]["function"]["parameters"]
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
            content=str(schema), tool_calls=None))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    tool = acri.Tool("weather", "Get weather")
    corpus = acri.index([tool])
    cache = {}
    before = acri.run("weather", corpus, client, cache=cache)
    tool.parameters["required"] = ["city"]
    after = acri.run("weather", corpus, client, cache=cache)
    assert before.text != after.text
