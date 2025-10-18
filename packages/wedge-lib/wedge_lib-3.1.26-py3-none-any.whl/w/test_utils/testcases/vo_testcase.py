from w.test_utils.mixins.testcase_mixin import TestCaseMixin


class VoTestCase(TestCaseMixin):
    @staticmethod
    def assert_comparing_failed(vo, vo2, vo_same):
        assert (vo == vo2) is False, "== failed"
        assert (vo != vo_same) is False, "!= failed"
        assert (vo > vo2) is False, "> failed"
        assert (vo2 < vo) is False, "< failed"
        assert (vo >= vo2) is False, ">=  failed"
        assert (vo2 <= vo) is False, "<=  failed"

    @staticmethod
    def assert_comparing_succeed(vo, vo2, vo_same):
        assert vo == vo_same, "== failed"
        assert vo != vo2, "!= failed"
        assert vo2 > vo, "> failed"
        assert vo < vo2, "< failed"
        assert vo2 >= vo, ">=  failed"
        assert vo_same >= vo, ">=  failed"
        assert vo <= vo2, "<=  failed"
        assert vo <= vo_same, "<=  failed"

    @staticmethod
    def assert_copy(vo):
        copy = vo.copy()
        assert copy is not vo
        assert copy == vo
