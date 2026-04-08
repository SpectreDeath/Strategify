# Plugin Example: Custom Media Actor

This example demonstrates how to create a custom plugin for strategify.

## Custom Agent: MediaActor

A non-state actor that monitors information flow and can amplify or dampen
narratives in the simulation.

## Custom Game: Media Influence

A game type where media actors compete for narrative control.

## Usage

```python
from strategify.plugins import register_agent, register_game
from plugin_example.media_agent import MediaActor
from plugin_example.media_game import media_influence_game

register_agent("MediaActor", MediaActor)
register_game("media_influence", media_influence_game)
```

Or register via entry points by adding to your `pyproject.toml`:

```toml
[project.entry-points."strategify.plugins"]
media_agent = "plugin_example:register_all"
```
