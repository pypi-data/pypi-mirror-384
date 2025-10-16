from robust_json import Extraction, RobustJSONParser, extract_all, loads


def test_loads_recovers_sample_payload():
    message = """
    你好，我是招聘顾问。以下是岗位描述，用于你的匹配程度:
    ```json
    {"id": "algo", "position": "大模型算法工程师",
    # this is the keywords list used to analyze the candidate
     "keywords": {"positive": ["PEFT", "RLHF"], "negative": ["CNN", "RNN"]}, # negative keywords is supoorted
     "summary": '候选人具备一定AI背景，但经验不足。"
     }
    ```
    """
    payload = loads(message)
    assert payload["id"] == "algo"
    assert payload["keywords"]["negative"] == ["CNN", "RNN"]


def test_partial_object_is_completed():
    snippet = '{"outer": {"inner": "value"'
    payload = loads(snippet)
    assert payload["outer"]["inner"] == "value"


def test_comment_stripping_and_trailing_commas():
    snippet = """
    {
      "items": [
        1,
        2, // keep
      ],
      "note": 'single quoted', # comment
    }
    """
    payload = loads(snippet)
    assert payload["items"] == [1, 2]
    assert payload["note"] == "single quoted"


def test_extract_all_returns_locations():
    text = "prefix {\"a\": 1}{\"b\": 2}"
    extractions = extract_all(text)
    assert len(extractions) == 2
    assert isinstance(extractions[0], Extraction)
    assert extractions[0].start < extractions[0].end


def test_parser_parse_all_returns_both_objects():
    parser = RobustJSONParser()
    text = "prefix {\"a\": 1} middle {\"b\": 2}"
    payloads = parser.parse_all(text)
    assert payloads == [{"a": 1}, {"b": 2}]
