from unittest import TestCase
from pathlib import Path
from btb import LoggedCmd


class TestException(Exception):
    pass


class TestLoggedCmd(TestCase):
    """blah"""

    def test_run(self):
        """This is supposed to fail and print a trace similar to:

            16:37:18   LoggedCmd.run(...) raised [ FileNotFoundError: [Errno 2] No such file or directory: 'asdfasdf': 'asdfasdf' ]
            16:37:18   return code: -1


            Ran 1 test in 0.008s

            FAILED (errors=1)

            Error
            Traceback (most recent call last):
              File "/Users/user/.pyenv/versions/3.6.6/Python.framework/Versions/3.6/lib/python3.6/unittest/case.py", line 59, in testPartExecutor
                yield
              File "/Users/user/.pyenv/versions/3.6.6/Python.framework/Versions/3.6/lib/python3.6/unittest/case.py", line 605, in run
                testMethod()
              File "/Users/user/code/build_scripts/o_bob/test_loggedCmd.py", line 9, in test_run
                utility.LoggedCmd.run(['asdfasdf'], exc=TestException('foobar'))
              File "/Users/user/code/build_scripts/o_bob/utility.py", line 216, in run
                raise exc
            test_loggedCmd.TestException: foobar
        """
        try:
            LoggedCmd.run(['asdfasdf'], exc=TestException('foobar'))
        except TestException:
            pass
        except:
            assert False

        LoggedCmd.run(['echo'], exc=TestException('foobar'))

        LoggedCmd.run(['echo', Path('.')], exc=TestException('foobar'))

    def test_check(self):
        test_res = LoggedCmd.check(['echo', 'oh hi'])
        assert ('oh hi\n' == test_res)
