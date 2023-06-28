import time
import random
import _thread
import urequests
import ujson
import network

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
    "hue_enabled_1": DISPLAY.create_pen(249, 228, 41),
    "hue_enabled_2": DISPLAY.create_pen(250, 231, 62),
    "hue_enabled_3": DISPLAY.create_pen(250, 233, 84),
    
}

def getRandomColor():
    return random.choice(list(pens.values()))

CURRENTTICK = 0
#------------------------------------------------------------------------------------------------- 
class Lock:
    def __init__(self):
        self.locked = False

    def acquire(self):
        while self.locked:
            pass  # busy wait (not ideal)
        self.locked = True

    def release(self):
        self.locked = False
        

class Point(object):
    x = 0
    y = 0
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Dimensions(object):
    dx = 0
    dy = 0
    
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy
    
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
        
    def isInside(self, point):
        if point.x >= self.left and point.x <= self.right and point.y >= self.top and point.y <= self.bottom:
            return True
        return False

class Component():
    _dimensions = Dimensions(0,0)
    _pos = Point(0,0)
    _isSelected = False
    def setPos(self, pos):
        self._pos = pos
    def tick(self):
        pass
    def doAction(self):
        pass
    def getAbsoluteBounds(self):
        return Rect(self._pos.x,
                    self._pos.y,
                    self._dimensions.dx+self._pos.x,
                    self._dimensions.dy+self._pos.y)
    def getDimensions(self):
        return self._dimensions
    def doNext(self):
        pass
    def doPrevious(self):
        pass
    def clearBounds(self):
        DISPLAY.set_pen(pens["black"])
        aB = self.getAbsoluteBounds()
        DISPLAY.rectangle(aB.left,aB.top,aB.right-aB.left,aB.bottom-aB.top)
        
    def drawBorder(self, borderWidth):
        aB = self.getAbsoluteBounds()
        
        DISPLAY.rectangle(aB.left, aB.top, self._dimensions.dx, borderWidth)
        DISPLAY.rectangle(aB.left, aB.bottom - borderWidth, self._dimensions.dx, borderWidth)
        DISPLAY.rectangle(aB.left, aB.top, borderWidth, self._dimensions.dy)
        DISPLAY.rectangle(aB.right - borderWidth, aB.top, borderWidth, self._dimensions.dy)
        
#-------------------------------------------------------------------------------------------------         
class Panel(Component):
    _components = list()
    _currentIndex = 0
    _tickLock = Lock()
    def __init__(self, w, h):
        self._dimensions = Dimensions(w, h)
    
    def attach(self, component):
        if(self.fit(component)):
            self._components.append(component)
            
    def collidesWithAny(self, x, y, component):
        if not self._components:
            return False
        
        for existingComponent in self._components:
            component.setPos(Point(x, y))
            
            existingAB = existingComponent.getAbsoluteBounds()
            newAB = component.getAbsoluteBounds()
            
            if existingAB.isInside(Point(newAB.left, newAB.top)) or existingAB.isInside(Point(newAB.left, newAB.bottom)) or existingAB.isInside(Point(newAB.right, newAB.bottom)) or existingAB.isInside(Point(newAB.right, newAB.top)):
                return True
        return False
    
    def fit(self, component):
        aB = self.getAbsoluteBounds()
        
        for y in range(aB.top, aB.bottom):
            for x in range(aB.left, aB.right):
                if not self.collidesWithAny(x, y, component):
                    component.setPos(Point(x, y))
                    return True
        return False
    
    def doAction(self):
        self.getCurrentComponent().doAction()
    
    def tick(self):
        self._tickLock.acquire()
        for component in self._components:
            component.tick()
        self._tickLock.release()
        
    def doNext(self):
        self._tickLock.acquire()
        while not self.getCurrentComponent().doNext():
            self._currentIndex += 1
        self._tickLock.release()
        
    def doPrevious(self):
        self._tickLock.acquire()
        while not self.getCurrentComponent().doPrevious():
            self._currentIndex += -1
        self._tickLock.release()
        
    def getCurrentComponent(self):
        print(self._currentIndex % len(self._components))
        return self._components[self._currentIndex % len(self._components)]

class HueButton(Component):
    
    def __init__(self, w, h, lampID, hueComs):
        self._dimensions = Dimensions(w,h)
        self.currentColors = [pens["hue_enabled_1"],pens["hue_enabled_2"],pens["hue_enabled_3"]]
        self.currentColor = pens["red"]
        self._isEnabled = False
        self._lampID = lampID
        self._hueComs = hueComs
    
    def tick(self):
        self.clearBounds()
        
        if self._isEnabled:
            self.drawEnabled()
            
        
        if self._isSelected:
            self.drawSelected()
            return
        self.drawNormal()
    
    def doAction(self):
        self.toggleEnable()
        self._hueComs.setState(self._lampID, self._isEnabled)
        
    def doNext(self):
        return self.toggleSelect()
        
    def doPrevious(self):
        return self.toggleSelect()
        
    def drawSelected(self):
        DISPLAY.set_pen(self.currentColor)
        self.drawBorder(3)
                
    def drawNormal(self):
        DISPLAY.set_pen(pens["white"])
        self.drawBorder(1)
        
    def drawEnabled(self):
        aB = self.getAbsoluteBounds()
        pixel_size = 4  # size of one side of the square pixel

        for x in range(aB.left, aB.right - pixel_size + 1, pixel_size):
            for y in range(aB.top, aB.bottom - pixel_size + 1, pixel_size):
                color = random.choice(self.currentColors)
                DISPLAY.set_pen(color)
                DISPLAY.rectangle(x, y, pixel_size, pixel_size)
                        
    def drawDisabled(self):
        DISPLAY.set_pen(self.currentColor)
        aB = self.getAbsoluteBounds()
        DISPLAY.rectangle(aB.left,aB.top,aB.right-aB.left,aB.bottom-aB.top)
        
    def toggleSelect(self):
        self._isSelected = not self._isSelected
        return self._isSelected
    
    def toggleEnable(self):
        self._isEnabled = not self._isEnabled
#-------------------------------------------------------------------------------------------------
class HueCommunicator:
    MAX_RETRIES = 5
    def __init__(self, ip, username):
        self._ip = ip
        self._username = username

    def getAll(self):
        def getAll():
            print(f'http://{self._ip}/api/{self._username}/lights')
            response = urequests.get(f'http://{self._ip}/api/{self._username}/lights')
            response.close
            return list(ujson.loads(response.text).keys())
        self.doWithRetry(getAll)
            
    def setState(self, id, state):
        def setState():
            body = ujson.dumps({'on': state})
            print(f'http://{self._ip}/api/{self._username}/lights/{id}/state')
            res = urequests.put(f'http://{self._ip}/api/{self._username}/lights/{id}/state', data=body)
            res.close()
            
        self.doWithRetry(setState)
        
    def doWithRetry(self, action):
        retryCount = 0
        while retryCount <= self.MAX_RETRIES:
            try:
                return action()
            except:
                retryCount += 1
       
        
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
            DISPLAY.set_pen(pens["black"])
            DISPLAY.clear()
            self._theComponent.tick()
            CURRENTTICK = CURRENTTICK + 1
            DISPLAY.update()
            time.sleep(0.001)

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

class ConnectionManager(object):
    ssid = 'asusasus'  # Placeholder
    password = 'susasusa' # Placeholder
    WAIT_DURATION = 1
    MAX_WAITS = 50
    MAX_RETRIES = 10
    
    def __init__(self):
        self.connectWithRetries()
    
    def connectWithRetries(self):
        totalRetries = 0
        success = False
        while success == False:
            try:
                self.connect()
                success = True
            except Exception as e:  # capture the exception
                print("EXCEPTION:", str(e))  # print the exception
                if totalRetries > self.MAX_RETRIES:
                    machine.reset()
                totalRetries += 1
    
    def connect(self):
        totalWaits = 0
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(self.ssid, self.password)
            
        while wlan.isconnected() == False and totalWaits <= self.MAX_WAITS:
            print('Waiting for connection...')
            time.sleep(self.WAIT_DURATION)
            totalWaits += 1
                
        if wlan.isconnected() == False:
            machine.reset() 
        print(wlan.ifconfig())

connectionManager = ConnectionManager()

hue = HueCommunicator("192.168.50.125", "XNA5ReISIUJLvaK2ejyWXnZUFuNI6aXlqNAMFrx8")

WIDTH, HEIGHT = DISPLAY.get_bounds()  
panel = Panel(WIDTH, HEIGHT)
lamps = hue.getAll()
for lamp in lamps:
    panel.attach(HueButton(int((WIDTH / 5)-1), 100, lamp, hue))



ticker = TickGenerator(panel)
actionManager = ActionManager(panel)

_thread.start_new_thread(ticker.startTick, ())
actionManager.monitorActions()