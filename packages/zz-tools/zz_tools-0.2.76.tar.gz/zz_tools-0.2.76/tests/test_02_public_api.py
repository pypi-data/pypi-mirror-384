def test_public_api_surface():
    import mcgt

    # durcir/élargir au fil du temps
    for name in ["__version__"]:
        assert hasattr(mcgt, name)
