from w.tests.fixtures.datasets.data_test_factory import factory_boy

base_city = {"factory": factory_boy.CityFactory, "ref": "base_city"}
base_author = {"factory": factory_boy.AuthorFactory, "ref": "base_author"}
base_series = {"factory": factory_boy.SeriesFactory, "ref": "base_series"}
base_department = {"factory": factory_boy.DepartmentFactory, "ref": "base_department"}
base_book = {"factory": factory_boy.BookFactory, "ref": "base_book"}
base_character = {
    "factory": factory_boy.CharacterFactory,
    "ref": "base_character",
}
base_autonow_model = {"factory": factory_boy.AutoNowModelFactory}

books_series_recipe = {
    "context": [
        {"nb": 2, **base_series},
        {"nb": 3, **base_character},
        {**base_department, "ref": "dpt_sf", "values": {"name": "Science Fiction"}},
        {**base_department, "ref": "dpt_fantasy", "values": {"name": "Fantasy"}},
        {**base_department, "ref": "dpt_suspense", "values": {"name": "Suspense"}},
        base_author,
    ],
    **base_book,
    "values": {
        "author": {"data_ref": "base_author"},
        "series": {"data_ref": "base_series_2"},
        "characters": [
            {"data_ref": "base_character"},
            {"data_ref": "base_character_3"},
        ],
        "departments": [{"data_ref": "dpt_fantasy"}, {"data_ref": "dpt_suspense"}],
    },
}
base_one2one = {"factory": factory_boy.One2OneCityFactory, "ref": "base_one2one"}
