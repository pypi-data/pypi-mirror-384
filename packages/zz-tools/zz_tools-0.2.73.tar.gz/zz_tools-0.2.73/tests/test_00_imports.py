def test_import_mcgt():
    import mcgt

    assert hasattr(mcgt, "__version__")


def test_import_submodules():
    # Fumée: s'assurer que les sous-modules s'importent sans side-effects fatals
    import mcgt.phase  # noqa: F401
    import mcgt.scalar_perturbations  # noqa: F401
