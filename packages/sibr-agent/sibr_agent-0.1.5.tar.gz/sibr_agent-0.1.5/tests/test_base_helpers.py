import types


def make_agent():
    from sibr_agent import base as base_mod
    class _Logger:
        def set_level(self, *_a, **_k):
            pass
        def info(self, *_a, **_k):
            pass
        def error(self, *_a, **_k):
            pass
    base_mod.logger = _Logger()
    from sibr_agent.base import Agent
    dummy_llms = {}
    dummy_tools = []
    agent = Agent(llms=dummy_llms, tools=dummy_tools, prompt="p", domain="d", checkpointer=object())
    return agent


def test_safe_parse_content_json_and_literal():
    agent = make_agent()
    assert agent._safe_parse_content('{"a": 1}') == {"a": 1}
    assert agent._safe_parse_content('[1,2]') == [1, 2]
    assert agent._safe_parse_content("{'x': 2}") == {"x": 2}
    assert agent._safe_parse_content(123) is None
    assert agent._safe_parse_content("not json or literal") is None


def test_format_tool_result_variants():
    agent = make_agent()
    # dict/list become JSON strings
    s = agent._format_tool_result({"a": 1})
    assert isinstance(s, str) and '"a": 1' in s
    s2 = agent._format_tool_result([1, 2, 3])
    assert isinstance(s2, str) and s2.startswith("[")
    # others become str
    assert agent._format_tool_result(42) == "42"


def test_should_continue_checks_tool_calls():
    agent = make_agent()
    from langchain_core.messages import AIMessage
    state = {"messages": [AIMessage(content="hi", tool_calls=[]), AIMessage(content="ok", tool_calls=[{"name": "t", "args": {}}]) ]}
    assert agent._should_continue(state) is True
    state2 = {"messages": [AIMessage(content="ok", tool_calls=[])]}
    assert agent._should_continue(state2) is False


def test_truncate_tokens_basic():
    agent = make_agent()
    from langchain_core.messages import BaseMessage
    msgs = [BaseMessage(content="a" * 10), BaseMessage(content="b" * 10), BaseMessage(content="c" * 10)]
    out = agent._truncate_tokens(msgs, max_tokens=15)  # encoder counts chars in stub
    # Should keep as many from the end as fit within the limit
    assert len(out) >= 1
    assert out[-1].content == "c" * 10
