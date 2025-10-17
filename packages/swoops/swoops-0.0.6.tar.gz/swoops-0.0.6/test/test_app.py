"""
Written by Jason Krist
05/01/2024
"""

import time
starttime = time.time()
print(f"Start time: {starttime}")

from os import path
import sys
#import cProfile
#from PySide6.QtWidgets import QApplication  # pylint: disable=E0611,E0401
print(f"Import Time 1: {time.time() - starttime}")

testdir = path.dirname(path.realpath(__file__))
appendpath = path.join(testdir, "../src")
sys.path.insert(0, appendpath)

from swoops import app as swa  # type: ignore # pylint: disable=E0611,E0401,C0413
print(f"Import Time 2: {time.time() - starttime}")

appendpath = path.realpath(path.join(testdir, ".."))
print(appendpath)
sys.path.insert(0, appendpath)

import test_cases as tc
print(f"Import Time 3: {time.time() - starttime}")

def test_app():
    """test app"""
    #qapp = QApplication(sys.argv)
    #app.setStyle("Fusion")  # "plastique"
    #ses = tc.session_5()
    app = swa.App() # session = ses
    app.run()
    #sys.exit(qapp.exec())


if __name__ == "__main__":
    #cProfile.run("test_app()")
    test_app()
