def test_package_exports():
    import sibr_agent
    assert hasattr(sibr_agent, "Agent")
    assert hasattr(sibr_agent, "GoogleAuth")

