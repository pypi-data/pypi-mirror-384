from . import setup_generator_base_test


def test_branches_generator_endpoint_config_init():
    generators = setup_generator_base_test("index_rate_sources")

    assert 1 == len(generators)

    generator = generators[0]

    assert generator.endpoint_path == 'indexratesources'
    assert generator.endpoint_api_method == "GET"
    assert generator.endpoint_sorting_criteria == {}
    assert generator.endpoint_filter_criteria == []
    assert generator.endpoint_params == {
        "detailsLevel": "FULL",
        "paginationDetails": "OFF"
    }
    assert generator.endpoint_bookmark_field == ""
