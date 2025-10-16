def test_import_and_client() -> None:
    from unifiedai import UnifiedAI

    client = UnifiedAI(provider="cerebras", model="llama3")
    assert hasattr(client, "chat")
    assert hasattr(client.chat, "completions")
