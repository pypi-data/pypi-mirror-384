
import sys, threading, time
from PyQt5.QtWidgets import QApplication
from PyQtPaint.form import PainterWindow
from abc import ABC

class App(ABC):
    '''An abstract class to setup and run a painter window.'''

    def __init__(self, **kwargs):
        self.auto_updates = kwargs.pop('auto_update', True)
        self.fps = kwargs.pop('fps', 30)
        self.init_qapp(**kwargs)

    def init_qapp(self, **kwargs):
        self.app = QApplication(sys.argv)
        self.window = PainterWindow(**kwargs)

        # Define width and height from the window after defined
        self.width = self.window.width()
        self.height = self.window.height()

        # Link key and mouse events to the form
        self.window.keyPress = self.keyPress
        self.window.keyRelease = self.keyRelease

        self.window.mousePress = self.mousePress
        self.window.mouseRelease = self.mouseRelease
        self.window.mouseDouble = self.mouseDouble
        self.window.mouseMove = self.mouseMove
        self.window.mouseEnter = self.mouseEnter
        self.window.mouseLeave = self.mouseLeave
        self.window.mouseWheel = self.mouseWheel

    def run(self):
        '''Starts an update thread and the app thread.'''
        self.window.show()
        self.window.destroyed.connect(lambda: setattr(self, "window_closed", True))
        
        self.setup_objects()
        if self.auto_updates:
            threading.Thread(target=self.update_wrapper, daemon=True).start()
        sys.exit(self.app.exec_())

    def update_wrapper(self):
        update_time = 1/self.fps

        # Update loop
        while not getattr(self, "window_closed", False):
            self.update()
            self.window.update_signal.emit()
            time.sleep(update_time)
            
    def setup_objects(self): 
        '''Add objects to self.window, PainterWindow'''
        pass
    
    def update(self): 
        '''Update calls every so often based on self.fps'''
        pass

    # Key Events
    def keyPress(self, event): pass
    def keyRelease(self, event): pass

    # Mouse Events
    def mousePress(self, event): pass
    def mouseRelease(self, event): pass
    def mouseDouble(self, event): pass
    def mouseMove(self, event): pass
    def mouseEnter(self, event): pass
    def mouseLeave(self, event): pass
    def mouseWheel(self, event): pass
