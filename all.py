import time
import random
import _thread

from pimoroni import Button as Control
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P8

DISPLAY = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P8)
DISPLAY.set_backlight(0.7)
button_a = Control(12)
button_b = Control(13)
button_x = Control(14)
button_y = Control(15)

pens = {
    "black": DISPLAY.create_pen(0, 0, 0),
    "white": DISPLAY.create_pen(255, 255, 255),
    "red": DISPLAY.create_pen(255, 0, 0),
    "green": DISPLAY.create_pen(0, 255, 0),
    "blue": DISPLAY.create_pen(0, 0, 255),
    "yellow": DISPLAY.create_pen(255, 255, 0),
    "cyan": DISPLAY.create_pen(0, 255, 255),
    "magenta": DISPLAY.create_pen(255, 0, 255),
    "orange": DISPLAY.create_pen(255, 165, 0),
    "purple": DISPLAY.create_pen(128, 0, 128),
    "pink": DISPLAY.create_pen(255, 192, 203),
    "brown": DISPLAY.create_pen(165, 42, 42),
    "gray": DISPLAY.create_pen(128, 128, 128),
    "light_blue": DISPLAY.create_pen(173, 216, 230),
    "lime": DISPLAY.create_pen(0, 255, 0),
    "maroon": DISPLAY.create_pen(128, 0, 0),
    "navy": DISPLAY.create_pen(0, 0, 128),
    "olive": DISPLAY.create_pen(128, 128, 0),
    "teal": DISPLAY.create_pen(0, 128, 128),
    "indigo": DISPLAY.create_pen(75, 0, 130),
    "violet": DISPLAY.create_pen(238, 130, 238),
    "gold": DISPLAY.create_pen(255, 215, 0),
    "silver": DISPLAY.create_pen(192, 192, 192),
    "bronze": DISPLAY.create_pen(205, 127, 50),
    "coral": DISPLAY.create_pen(255, 127, 80),
    "salmon": DISPLAY.create_pen(250, 128, 114),
    "lime_green": DISPLAY.create_pen(50, 205, 50),
    "light_green": DISPLAY.create_pen(144, 238, 144),
    "turquoise": DISPLAY.create_pen(64, 224, 208),
    "sky_blue": DISPLAY.create_pen(135, 206, 235),
    "plum": DISPLAY.create_pen(221, 160, 221),
    "dark_red": DISPLAY.create_pen(139, 0, 0),
    "dark_green": DISPLAY.create_pen(0, 100, 0),
    "dark_blue": DISPLAY.create_pen(0, 0, 139),
    "beige": DISPLAY.create_pen(245, 245, 220),
    "mint": DISPLAY.create_pen(189, 252, 201),
    "lavender": DISPLAY.create_pen(230, 230, 250),
    "peach": DISPLAY.create_pen(255, 218, 185),
    "light_yellow": DISPLAY.create_pen(255, 255, 224),
    "light_cyan": DISPLAY.create_pen(224, 255, 255),
    "light_magenta": DISPLAY.create_pen(255, 224, 255),
    "dark_yellow": DISPLAY.create_pen(204, 204, 0),
    "dark_cyan": DISPLAY.create_pen(0, 204, 204),
    "dark_magenta": DISPLAY.create_pen(204, 0, 204),
}

def getRandomColor():
    return random.choice(list(pens.values()))

CURRENTTICK = 0
#------------------------------------------------------------------------------------------------- 
class Point(object):
    x = 0
    y = 0
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Rect(object):
    left = 0
    top = 0
    right = 0
    bottom = 0
    
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

class Component():
    _boundaries = Rect(0,0,0,0)
    _pos = Point(0,0)
    _selected = False
    def setPos(self, pos):
        self._pos = pos
    def tick(self):
        pass
    def doAction(self, offsetPoint):
        pass
    def getAbsoluteBounds(self):
        return Rect(self._boundaries.left+self._pos.x,
                    self._boundaries.top+self._pos.y,
                    self._boundaries.right+self._pos.x,
                    self._boundaries.bottom+self._pos.y)
    def getRelativeBounds(self):
        return self._boundaries
    def doNext(self):
        pass
    def doPrevious(self):
        pass
    def clearBounds(self):
        DISPLAY.set_pen(pens["black"])
        aB = self.getAbsoluteBounds()
        DISPLAY.rectangle(aB.left,aB.top,aB.right,aB.bottom)
        
#-------------------------------------------------------------------------------------------------         
class Panel(Component):
    _components = list()


class Button(Component):
    def __init__(self):
        WIDTH, HEIGHT = DISPLAY.get_bounds()
        self._boundaries = Rect(0,0,300,300)
        self.currentColor = getRandomColor()
    
    def tick(self):
        self.clearBounds()
        DISPLAY.set_pen(self.currentColor)
        if self._selected:
            self.drawSelected()
            return
        self.drawNormal()
    
    def doAction(self):
        pass
        
    def drawSelected(self):
        aB = self.getAbsoluteBounds()
        pixel_size = 4  # size of one side of the square pixel

        for x in range(aB.left, aB.right + 1, pixel_size):
            for y in range(aB.top, aB.bottom + 1, pixel_size):
                color = random.choice(["turquoise", "light_blue", "dark_cyan"])
                DISPLAY.set_pen(pens[color])
                # Color each pixel in the 4x4 square the same
                for sub_x in range(x, min(aB.right + 1, x + pixel_size)):
                    for sub_y in range(y, min(aB.bottom + 1, y + pixel_size)):
                        DISPLAY.pixel(sub_x, sub_y)

        
                
    def drawNormal(self):
        DISPLAY.set_pen(self.currentColor)
        aB = self.getAbsoluteBounds()
        DISPLAY.rectangle(aB.left,aB.top,aB.right,aB.bottom)
        
    def doNext(self):
        self._selected = True
    def doPrevious(self):
        self._selected = False
#-------------------------------------------------------------------------------------------------         
class Action:
    NONE = 0
    NEXT = 1
    PREVIOUS = 2
    SELECT = 3
    BACK = 4
    
class InputManager(object):
    def getAction(self):
        if button_a.read():                                   
            return Action.NEXT                                    
        elif button_b.read():
            return Action.PREVIOUS
        elif button_x.read():
            return Action.SELECT
        elif button_y.read():
            return Action.BACK
        else:
           return Action.NONE
#------------------------------------------------------------------------------------------------- 
class TickGenerator(object):
    def __init__(self, component):
        self._theComponent = component
        self.inputManager = InputManager()
        
    def startTick(self):
        global CURRENTTICK
        while(True):
            self._theComponent.tick()
            CURRENTTICK = CURRENTTICK + 1
            DISPLAY.update()
            time.sleep(0.01)

class ActionManager(object):
    actions = {
        Action.NEXT: lambda self: self._theComponent.doNext(),
        Action.PREVIOUS: lambda self: self._theComponent.doPrevious(),
        Action.SELECT: lambda self: self._theComponent.doAction(),
        Action.BACK: lambda self: self._theComponent.doAction(),
        Action.NONE: lambda _: None,
    }
    def __init__(self, component):
        self._theComponent = component
        self.inputManager = InputManager()
        
    def monitorActions(self):
        while(True):
            self.actions[self.inputManager.getAction()](self)
            time.sleep(0.0001)
        
firstComponent = Button()
ticker = TickGenerator(firstComponent)
actionManager = ActionManager(firstComponent)

_thread.start_new_thread(ticker.startTick, ())
actionManager.monitorActions()