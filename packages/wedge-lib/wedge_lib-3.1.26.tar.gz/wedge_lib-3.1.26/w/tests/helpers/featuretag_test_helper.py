from contextlib import contextmanager
from unittest.mock import patch

from w.services.technical.feature_tag_service import FeatureTagService


@contextmanager
def feature_enabled(feature_tag: str):
    with feature_is(feature_tag, True) as m:
        yield m


@contextmanager
def feature_disabled(feature_tag: str):
    with feature_is(feature_tag, False) as m:
        yield m


@contextmanager
def feature_is(feature_tag: str, is_enabled: bool):
    mock_settings = _set_feature_tag(feature_tag, is_enabled)
    with patch.object(
        FeatureTagService, "_get_settings", return_value=mock_settings
    ) as m:
        yield m


def _set_feature_tag(feature_tag: str, is_enabled: bool):
    if FeatureTagService._has_feature_tags_setting():
        current_settings = FeatureTagService._get_settings()
    else:
        current_settings = {}
    mock_settings = {**current_settings, feature_tag: is_enabled}
    return mock_settings
