from . import setup_generator_base_test


def test_deposit_transactions_generator():
    generators = setup_generator_base_test("deposit_transactions")

    assert 1 == len(generators)

    generator = generators[0]

    assert generator.endpoint_path == "deposits/transactions:search"
    assert generator.endpoint_bookmark_field == "creationDate"
    assert generator.endpoint_sorting_criteria == {
            "field": "id",
            "order": "ASC"
        }
    assert generator.endpoint_filter_criteria == [
            {
                "field": "creationDate",
                "operator": "AFTER",
                "value": '2021-06-01T00:00:00.000000Z'
            }
        ]
