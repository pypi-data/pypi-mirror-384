import subprocess


def test_hello_from_bandai() -> None:
    result = subprocess.run(
        [
            "bandai",
        ],
        capture_output=True,
        text=True,
    )

    expected = """Hello from bandai!"""

    assert result.returncode == 0
    assert result.stdout.strip() == expected.strip()
