import pytest

from payloop import Payloop


def test_attribution_exceptions():
    with pytest.raises(RuntimeError) as e:
        Payloop(api_key="abc").attribution(parent_name="Abc")

    assert str(e.value) == "a string parent_id is required"

    with pytest.raises(RuntimeError) as e:
        Payloop(api_key="abc").attribution(parent_id=123, subsidiary_name="Def")

    assert str(e.value) == (
        "a string subsidiary_id is required if a subsidiary_name is provided"
    )


def test_attribution():
    payloop = Payloop(api_key="abc")
    assert payloop.config.attribution is None

    payloop.attribution(
        parent_id=123,
        parent_name="Abc",
        subsidiary_id=456,
        subsidiary_name="Def",
        # These are deprecated but here to test backwards compatibility.
        parent_uuid="f1cafd68-c438-4b6b-9c65-0e0199f9f549",
        subsidiary_uuid="83d388a8-20ce-40d5-b48b-5ae2a7968b25",
    )

    assert payloop.config.attribution == {
        "parent": {
            "id": "123",
            "name": "Abc",
        },
        "subsidiary": {
            "id": "456",
            "name": "Def",
        },
    }


def test_new_transaction():
    payloop = Payloop(api_key="abc")

    first_tx_uuid = payloop.config.tx_uuid
    assert first_tx_uuid is not None

    second_tx_uuid = payloop.new_transaction()
    assert second_tx_uuid is not None

    assert second_tx_uuid != first_tx_uuid


def test_attribution_only_parent():
    payloop = Payloop(api_key="abc")
    assert payloop.config.attribution is None

    payloop.attribution(
        parent_id=123,
        parent_name="Abc",
        # This is deprecated but here to test backwards compatibility.
        parent_uuid="f1cafd68-c438-4b6b-9c65-0e0199f9f549",
    )

    assert payloop.config.attribution == {
        "parent": {
            "id": "123",
            "name": "Abc",
        },
        "subsidiary": None,
    }


def test_attribution_only_parent_only_id():
    payloop = Payloop(api_key="abc")
    assert payloop.config.attribution is None

    payloop.attribution(
        parent_id=123,
        parent_name=None,
        # This is deprecated but here to test backwards compatibility.
        parent_uuid=None,
    )

    assert payloop.config.attribution == {
        "parent": {"id": "123", "name": None},
        "subsidiary": None,
    }


def test_attribution_parent_id_greater_than_100_chars():
    with pytest.raises(RuntimeError) as e:
        payloop = Payloop(api_key="abc").attribution(parent_id="a" * 101)

    assert str(e.value) == "parent_id cannot be greater than 100 characters"

    Payloop(api_key="abc").attribution(parent_id="a" * 100)


def test_attribution_parent_name_greater_than_100_chars():
    with pytest.raises(RuntimeError) as e:
        payloop = Payloop(api_key="abc").attribution(
            parent_id="a" * 100, parent_name="b" * 101
        )

    assert str(e.value) == "parent_name cannot be greater than 100 characters"

    Payloop(api_key="abc").attribution(parent_id="a" * 100, parent_name="b" * 100)


def test_attribution_subsidiary_id_greater_than_100_chars():
    with pytest.raises(RuntimeError) as e:
        payloop = Payloop(api_key="abc").attribution(
            parent_id="a" * 100, parent_name="b" * 100, subsidiary_id="c" * 101
        )

    assert str(e.value) == "subsidiary_id cannot be greater than 100 characters"

    Payloop(api_key="abc").attribution(
        parent_id="a" * 100, parent_name="b" * 100, subsidiary_id="c" * 100
    )


def test_attribution_subsidiary_name_greater_than_100_chars():
    with pytest.raises(RuntimeError) as e:
        payloop = Payloop(api_key="abc").attribution(
            parent_id="a" * 100,
            parent_name="b" * 100,
            subsidiary_id="c" * 100,
            subsidiary_name="d" * 101,
        )

    assert str(e.value) == "subsidiary_name cannot be greater than 100 characters"

    Payloop(api_key="abc").attribution(
        parent_id="a" * 100,
        parent_name="b" * 100,
        subsidiary_id="c" * 100,
        subsidiary_name="d" * 100,
    )
