"""Tests for MultiScaleModel integration with GeopolModel."""

from strategify.sim.model import GeopolModel


def test_enable_multiscale():
    model = GeopolModel()
    msm = model.enable_multiscale()
    assert model.multiscale is not None
    assert msm.global_model is model


def test_multiscale_step():
    model = GeopolModel()
    msm = model.enable_multiscale()
    msm.step(regional_steps=1)
    summary = msm.get_scale_summary()
    assert summary["global_step"] == 1
    assert summary["global_agents"] == 4


def test_multiscale_with_regional_factory():
    global_model = GeopolModel()

    def alpha_factory():
        return GeopolModel()

    msm = global_model.enable_multiscale(regional_model_factories={"alpha": alpha_factory})
    assert msm.get_regional_model("alpha") is not None
    msm.step(regional_steps=2)
    summary = msm.get_scale_summary()
    assert "alpha" in summary["regional_models"]
    assert summary["regional_models"]["alpha"]["n_agents"] == 4


def test_multiscale_get_unknown_regional():
    model = GeopolModel()
    msm = model.enable_multiscale()
    assert msm.get_regional_model("nonexistent") is None
