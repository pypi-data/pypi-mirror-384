from w.services.abstract_service import AbstractService


class ListService(AbstractService):
    @staticmethod
    def list_differences(list1, list2):
        """List elements from list1 not in list2 and elements from list2 not in list1"""
        # Convert lists to sets
        set1 = set(list1)
        set2 = set(list2)
        # Get the differences between two sets
        diff = (set1 - set2).union(set2 - set1)
        return list(diff)

    @classmethod
    def are_same(cls, list1, list2):
        """
        Check if elements from list1 are all in list2 or
        elements from list2 are all in list1
        """
        return cls.list_differences(list1, list2) == []

    @classmethod
    def are_different(cls, list1, list2):
        """
        Check if elements from list1 are not in list2 or
        elements from list2 are not in list1
        """
        return not cls.are_same(list1, list2)

    @classmethod
    def convert_elements_to_string(cls, list1):
        """Convert elements in list into string"""
        return [str(i) for i in list1]
