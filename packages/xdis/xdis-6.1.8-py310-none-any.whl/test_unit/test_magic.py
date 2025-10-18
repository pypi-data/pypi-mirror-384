import unittest, sys
from xdis.version_info import PYTHON_VERSION_STR, IS_PYPY, version_tuple_to_str
import xdis.magics as magics

class TestMagics(unittest.TestCase):

    def test_basic(self):
        """Basic test of magic numbers"""
        if hasattr(sys, 'version_info'):
            version = version_tuple_to_str()
            if IS_PYPY:
                version += 'pypy'
            self.assertTrue(version in magics.magics.keys(),
                            "version %s is not in magic.magics.keys: %s" %
                            (version, magics.magics.keys()))

        self.assertEqual(magics.MAGIC, magics.int2magic(magics.magic2int(magics.MAGIC)))
        lookup = PYTHON_VERSION_STR
        if IS_PYPY:
            lookup += 'pypy'
        self.assertTrue(lookup in magics.magics.keys(),
                        "PYTHON VERSION %s is not in magic.magics.keys: %s" %
                        (lookup, magics.magics.keys()))

        if not (3, 5, 2) <= sys.version_info < (3, 6, 0):
            self.assertEqual(magics.sysinfo2magic(), magics.MAGIC,
                            "magic from imp.get_magic() for %s "
                            "should be sysinfo2magic()" % lookup)


if __name__ == '__main__':
    unittest.main()
