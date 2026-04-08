"""Example plugin: Media Influence game type.

A custom game type where actors compete for narrative control.
Demonstrates the plugin API for registering custom game types.
"""

import nashpy as nash
import numpy as np


def media_influence_game():
    """Create a media influence game (2x2 normal form).

    Players choose between Amplify (spread narratives) and Suppress
    (contain information). Payoffs reflect information advantage.

    Returns
    -------
    nash.Game
        The media influence game.
    """
    # Row: Amplify / Suppress
    # Col: Amplify / Suppress
    # Payoffs: (row_utility, col_utility)
    row_payoffs = np.array(
        [
            [0.3, 0.7],  # Row Amplify
            [0.1, 0.5],  # Row Suppress
        ]
    )
    col_payoffs = np.array(
        [
            [0.3, 0.1],  # Col Amplify
            [0.7, 0.5],  # Col Suppress
        ]
    )
    return nash.Game(row_payoffs, col_payoffs)


def register():
    """Register this plugin with the plugin system."""
    from strategify.plugins import register_game

    register_game("media_influence", media_influence_game)
