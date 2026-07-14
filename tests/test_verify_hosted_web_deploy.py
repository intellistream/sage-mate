from tools.verify_hosted_web_deploy import runtime_repo_identity, runtime_repo_remote


def test_runtime_repo_identity_matches_https_and_ssh_without_credentials() -> None:
    expected = "github.com/qixin-gaoke/sage-mate-runtime-private"

    assert (
        runtime_repo_identity(
            "https://github.com/Qixin-Gaoke/sage-mate-runtime-private.git"
        )
        == expected
    )
    assert (
        runtime_repo_identity(
            "git@github.com:Qixin-Gaoke/sage-mate-runtime-private.git"
        )
        == expected
    )
    assert (
        runtime_repo_identity(
            "https://x-access-token:must-not-appear@github.com/"
            "Qixin-Gaoke/sage-mate-runtime-private.git"
        )
        == expected
    )


def test_runtime_repo_remote_returns_empty_for_non_checkout(tmp_path) -> None:
    assert runtime_repo_remote(tmp_path) == ""
