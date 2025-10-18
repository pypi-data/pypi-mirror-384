import inspect
import json
import os

from django.db.models import QuerySet
from var_dump import var_dump
from sys import exit

from w import utils


class Debug:
    @staticmethod
    def d(var):
        """Prints HTML human-readable information about a variable"""
        Debug.dump(var, False)

    @staticmethod
    def dd(var):
        """Prints (and DIE) HTML human-readable information about a variable"""
        Debug.dump(var)

    @staticmethod
    def s(var):
        """Prints human-readable information about a variable"""
        Debug.dump(var, False, False)

    @staticmethod
    def sd(var):
        """Prints (and DIE) human-readable information about a variable"""
        Debug.dump(var, True, False)

    @staticmethod
    def j(var):
        """Prints human-readable json information about a variable"""
        Debug.dump(var, False, False, True)

    @staticmethod
    def jd(var):
        """Prints (and DIE) human-readable json information about a variable"""
        Debug.dump(var, True, False, True)

    @classmethod
    def dump(cls, var, die=True, html=True, into_json=False):
        """Prints human-readable information about a variable

        Args:
            var (mixed): variable to dump
            die (bool) : exit script. Defaults True
            html (bool): dump as HTML. Defautls True
            into_json (bool): dump as json. Defautls False
        """
        # build resultset filename from caller filename
        caller = inspect.getouterframes(inspect.currentframe(), 2)[2]
        working_dir = os.getcwd()
        filename = caller.filename.replace(working_dir, "")

        if into_json:
            var = json.dumps(utils.to_json_dumpable(var), indent=4)

        print("\n\n=== DEBUG FROM {}:{}\n".format(filename, caller.lineno))
        if html:
            print("<pre>")

        if not isinstance(var, QuerySet):
            var_dump(var)
        else:
            print(var)

        if html:
            print("</pre>")

        print("\n=== FIN DEBUG {}:{}\n".format(filename, caller.lineno))

        if die:
            exit()
