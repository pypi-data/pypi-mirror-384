"""Test history on SBML models."""

import libsbml

from sbmlutils.factory import Creator, date_now, set_model_history


def test_date_now() -> None:
    """Test date now."""
    now = date_now()
    assert now


def test_set_model_history() -> None:
    """Test setting model history."""
    creators = [
        Creator(
            familyName="Koenig",
            givenName="Matthias",
            email="konigmatt@googlemail.com",
            organization="Test organisation",
        )
    ]
    sbmlns = libsbml.SBMLNamespaces(3, 1)
    doc = libsbml.SBMLDocument(sbmlns)
    model = doc.createModel()
    set_model_history(model, creators)

    # check if history was written correctly
    h = model.getModelHistory()
    assert h is not None
    assert h.getNumCreators() == 1
    c = h.getCreator(0)
    assert "Koenig" == c.getFamilyName()
    assert "Matthias" == c.getGivenName()
    assert "konigmatt@googlemail.com" == c.getEmail()
    assert "Test organisation" == c.getOrganization()
