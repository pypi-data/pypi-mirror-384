from click.testing import CliRunner

from .__main__ import main


def test_schemas(tmp_path):
    runner = CliRunner()

    runner.invoke(main, ["schemas", "--path", tmp_path])

    assert len(list(tmp_path.glob("*.json"))) >= 5
