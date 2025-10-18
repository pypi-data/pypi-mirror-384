from devopso.cli import get_hello_string


def test_decode_repo_list():
    hello_string = get_hello_string()
    assert hello_string == "The overseer is in the room"
