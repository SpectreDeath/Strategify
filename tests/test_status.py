"""Tests for Mesa visualization TextElement."""

from strategify.sim.model import GeopolModel
from strategify.viz.status import ActorStatusElement


class TestActorStatusElement:
    def test_render_returns_html(self):
        model = GeopolModel()
        model.step()
        element = ActorStatusElement()
        html = element.render(model)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_render_contains_world_state(self):
        model = GeopolModel()
        model.step()
        element = ActorStatusElement()
        html = element.render(model)
        assert "World State" in html

    def test_render_contains_actor_status(self):
        model = GeopolModel()
        model.step()
        element = ActorStatusElement()
        html = element.render(model)
        assert "Actor Status" in html

    def test_render_lists_all_regions(self):
        model = GeopolModel()
        model.step()
        element = ActorStatusElement()
        html = element.render(model)
        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "")
            if rid:
                assert rid.upper() in html

    def test_render_shows_postures(self):
        model = GeopolModel()
        model.step()
        element = ActorStatusElement()
        html = element.render(model)
        # Should contain either Escalate or Deescalate
        assert "Escalate" in html or "Deescalate" in html

    def test_render_without_influence_map(self):
        """Render should work even if influence_map is not yet computed."""
        model = GeopolModel()
        assert model.influence_map is None
        element = ActorStatusElement()
        html = element.render(model)
        assert isinstance(html, str)

    def test_render_multiple_steps(self):
        model = GeopolModel()
        element = ActorStatusElement()
        for _ in range(5):
            model.step()
            html = element.render(model)
            assert isinstance(html, str)
            assert len(html) > 0
