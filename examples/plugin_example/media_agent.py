"""Example plugin: MediaActor agent type.

A non-state actor that monitors information flow and amplifies or
dampens narratives in the simulation. Demonstrates the plugin API
for registering custom agent types.
"""


class MediaActor:
    """A media actor that influences narrative spread.

    This is a minimal example showing how to create a custom agent
    type that integrates with the existing plugin system.

    Parameters
    ----------
    unique_id : int
        Agent identifier.
    model : GeopolModel
        Parent simulation model.
    bias : float
        Narrative bias in [-1, 1]. Negative = anti-government,
        positive = pro-government.
    reach : float
        Media reach multiplier in [0, 1].
    """

    def __init__(self, unique_id, model, bias=0.0, reach=0.5):
        self.unique_id = unique_id
        self.model = model
        self.bias = bias
        self.reach = reach
        self.region_id = "global"
        self.posture = "Deescalate"
        self.capabilities = {"military": 0.0, "economic": reach}

    def step(self):
        """Publish media output — modify nearby narrative credibility."""
        if self.model.propaganda is None:
            return

        # Amplify narratives that match our bias
        for narrative in self.model.propaganda.narratives:
            if (
                narrative.is_disinformation
                and self.bias < 0
                or not narrative.is_disinformation
                and self.bias > 0
            ):
                narrative.potency *= 1.0 + self.reach * 0.1


def register():
    """Register this plugin with the plugin system."""
    from strategify.plugins import register_agent

    register_agent("MediaActor", MediaActor)
