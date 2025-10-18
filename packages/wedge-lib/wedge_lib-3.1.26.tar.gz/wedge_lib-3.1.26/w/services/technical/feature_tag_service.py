from django.conf import settings

from w.services.abstract_service import AbstractService


class FeatureTagService(AbstractService):
    _settings_key = "FEATURE_TAGS"
    _feature_settings = None

    @classmethod
    def is_enabled(cls, feature_tag: str) -> bool:
        if cls._has_feature_tags_setting() is False:
            return False

        feature_settings = cls._get_settings()
        if feature_tag not in feature_settings:
            raise RuntimeError(
                f"feature '{feature_tag}' not found in settings FEATURE_TAGS"
            )
        return bool(int(feature_settings[feature_tag]))

    @classmethod
    def is_disabled(cls, feature_tag: str) -> bool:
        return not cls.is_enabled(feature_tag)

    @classmethod
    def clear(cls):
        cls._feature_settings = None

    @classmethod
    def _has_feature_tags_setting(cls) -> bool:
        return hasattr(settings, cls._settings_key)

    @classmethod
    def _get_settings(cls):
        if cls._feature_settings is None:
            cls._feature_settings = getattr(settings, cls._settings_key)
        return cls._feature_settings
