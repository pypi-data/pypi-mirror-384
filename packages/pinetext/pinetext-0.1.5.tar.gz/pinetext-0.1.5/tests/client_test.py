import builtins


def test_get_or_create_assistant(pinetext):
    assistant = pinetext.get_or_create_assistant("foo")
    assert assistant is pinetext.pinecone.assistant


def test_upload_files(pinetext, tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "test.txt").write_text("TEST")
    pinetext.upload_files(str(data))
    assert "test.txt" in pinetext.pinecone.assistant.list_files()


def test_chat(pinetext):
    resp = pinetext.chat("This is a test", model="test-model")
    assert resp == "Test"


def test_run(pinetext, monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(iter(["exit"])))
    res = pinetext.run()
    assert res is None
