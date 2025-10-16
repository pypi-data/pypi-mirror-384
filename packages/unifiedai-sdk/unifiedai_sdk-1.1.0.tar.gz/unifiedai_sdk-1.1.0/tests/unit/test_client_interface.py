from unifiedai import UnifiedAI


def test_client_has_chat_completions() -> None:
    client = UnifiedAI(provider="cerebras", model="llama3")
    assert hasattr(client, "chat")
    assert hasattr(client.chat, "completions")
    assert hasattr(client.chat.completions, "create")
