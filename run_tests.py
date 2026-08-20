import unittest
suite=unittest.defaultTestLoader.discover('tests')
raise SystemExit(0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1)
