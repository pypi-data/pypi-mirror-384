from risiko.core.shell import InvalidShell, RisikoShell
from risiko.core.shell.base import RisikoShell as ShellBase
from risiko.service.processors import eject_magazine_shell, load_shell_to_magazine
from risiko.service.risiko_state import RisikoState


def test_insert_shell_to_magazine():
    state = RisikoState()
    shell = ShellBase(shell_type="live", damage=1)
    new_state = load_shell_to_magazine(game_state=state, shell=shell)
    assert len(new_state.shotgun.magazine.tube) == 1
    assert new_state.shotgun.magazine.tube[0] == shell


def test_insert_invalid_shell_to_magazine():
    state = RisikoState()
    shell = "invalid_shell"
    try:
        load_shell_to_magazine(game_state=state, shell=shell)
    except InvalidShell:
        assert True
    else:
        assert False


def test_eject_magazine_shell():
    state = RisikoState()
    shell = RisikoShell(shell_type="live", damage=1)
    state = load_shell_to_magazine(game_state=state, shell=shell)

    ejected_shell, new_state = eject_magazine_shell(game_state=state)
    assert ejected_shell == shell
    assert len(new_state.shotgun.magazine.tube) == 0
