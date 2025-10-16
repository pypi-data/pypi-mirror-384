from risiko.core.player.base import RisikoPlayer
from risiko.core.player.interface import PlayerInterface


def test_player_base_conforms_to_interface():
    """Tests that RisikoPlayer correctly implements PlayerInterface."""
    # 1. Create an instance of the concrete class
    player = RisikoPlayer(id="p1", charges=5)

    # 2. Assert that it is an instance of the interface
    #    This works because the protocol is decorated with @runtime_checkable
    assert isinstance(player, PlayerInterface)

    # 3. Perform a simple behavioral check to ensure a core method works
    #    and that the returned object also conforms to the interface.
    new_player = player.lose_charges(2)

    assert new_player.charges == 3
    assert isinstance(new_player, PlayerInterface)

    # 4. Check immutability (the original object should be unchanged)
    assert player.charges == 5


def test_incomplete_player_fails_conformance():
    """
    Tests that a class missing attributes from PlayerInterface fails to conform.
    This demonstrates the enforcement of the protocol.
    """

    class IncompletePlayer:
        # Missing 'id' and 'charges' attributes
        def _lose_charges(self, amt: int) -> "IncompletePlayer":
            # Dummy implementation for the test
            return self

        def _gain_charges(self, amt: int) -> "IncompletePlayer":
            # Dummy implementation for the test
            return self

    player = IncompletePlayer()

    # 1. Static Check (This line would be flagged by Pylance/Mypy in your IDE)
    #    var: PlayerInterface = player # This line would show a static type error

    # 2. Runtime Check
    #    Because PlayerInterface is @runtime_checkable, isinstance will return False
    #    if the class does not conform to the protocol's structure.
    assert not isinstance(player, PlayerInterface)
