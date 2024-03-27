import gc
import re
import time
import random
from cosmic import CosmicUnicorn, Channel
from picographics import PicoGraphics, DISPLAY_COSMIC_UNICORN, PEN_P8
from ulab import numpy
import math
import jpegdec

# 0 = all sound, 1 = only fx, 2 = no sound
class BitFont:
    def __init__(self, graphics):
        self.graphics = graphics

    # DRAW A SINGLE BITMAP FONT CHARACTER
    @micropython.native  # noqa: F821
    def draw_char(self,d,x,y,f):
        # LOOP THROUGH ROWS
        for i in range(f[d]["h"]):
            # LOOP THROUGH COLUMNS
            for j in range(f[d]["w"]):
                # IF THIS BIT IS SET THEN DRAW A PIXEL
                if f[d]["data"] & (0b1 << ((i*f[d]["w"])+j)):
                    self.graphics.pixel(f[d]["w"]-1-j+x,f[d]["h"]-1-i+y)

    # DRAW A STRING WITH BITMAP FONT
    @micropython.native  # noqa: F821
    def draw_text(self,s,x,y,f,d=1):
        # LEFT JUSTIFIED
        if d == 1:
            for i in range(len(s)):
                self.draw_char(s[i],x,y,f)
                x += f[s[i]]["w"] + f[s[i]]["s"]
        else:
        # RIGHT JUSTIFIED
            for i in reversed(range(len(s))):
                x -= f[s[i]]["w"]
                self.draw_char(s[i],x,y,f)
                x -= f[s[i]]["s"]

# FONT DATA
# x,y are unused - could be used for drawing above below line
# w, h are width and height
# s is spacing
# data is binary bit representation of pixels, starting at top left

font2x5 = {
    " ": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0000000000},
    "!": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0101010001},
    "'": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0100000000},
    ",": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0000010110},
    "-": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0000110000},
    ".": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0000000010},
    "0": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1111111111},
    "1": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0101010101},
    "2": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1101111011},
    "3": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1101110111},
    "4": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1010110101},
    "5": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1110110111},
    "6": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1010111111},
    "7": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1101010101},
    "8": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1111001111},
    "9": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1111110101},
    ":": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0001000100},
    ";": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0001000110},
    "<": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0001100100},
    "=": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0011001100},
    ">": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b0010011000},
    "?": {"x": 0, "y": 0, "w": 2, "h": 5, "s": 1, "data": 0b1101111000},
    }
font3x5 = {
    " ": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b000000000000000},
    "🚶": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b010110111010101},
    "✋": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b000010110111110},
    "!": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b010010010000010},
    "0": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111101101101111},
    "1": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b110010010010111},
    "2": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111001111100111},
    "3": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111001011001111},
    "4": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101101111001001},
    "5": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111100111001111},
    "6": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111100111101111},
    "7": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111001010010010},
    "8": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111101111101111},
    "9": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111101111001111},
    "A": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b010101111101101},
    "B": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b110101110101110},
    "C": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b011100100100011},
    "D": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b110101101101110},
    "E": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111100110100111},
    "F": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111100110100100},
    "G": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b011100101101011},
    "H": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101101111101101},
    "I": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111010010010111},
    "J": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b011001001101010},
    "K": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101101110101101},
    "L": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b100100100100111},
    "M": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101111111101101},
    "N": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111101101101101},
    "O": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111101101101111},
    "P": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b110101110100100},
    "Q": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b010101101110011},
    "R": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b110101110101101},
    "S": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b011100010001110},
    "T": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111010010010010},
    "U": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101101101101111},
    "V": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101101101101010},
    "W": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101101111111101},
    "X": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101101010101101},
    "Y": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b101101111001111},
    "Z": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b111001010100111},
    "-": {"x":0,"y":0,"w":3,"h":5,"s":1,"data":0b000000111000000},
    ":": {"x":0,"y":0,"w":1,"h":5,"s":1,"data":0b01010},
    ".": {"x":0,"y":0,"w":1,"h":5,"s":1,"data":0b00001}
    }

SOUND_ENABLE=2
playhead = 0

# thanks chatgpt, sounds fine to me. just like it! 
song_notes = pachelbel_canon_in_d_with_length = [   
    (14, 4), (11, 4), (7, 4), (9, 4), (14, 4), (11, 4), (7, 4), (9, 4), 
    (14, 4), (11, 4), (7, 4), (9, 4), (10, 2), (10, 2), (11, 2), (12, 2), 
    (14, 4), (16, 4), (16, 4), (14, 4), (12, 4), (11, 4), (9, 4), (7, 4), 
    (7, 4), (9, 4), (11, 4), (12, 4), (11, 4), (9, 4), 
    ('@', 8), 
    (14, 4), (11, 4), (7, 4), (9, 4), (14, 4), (11, 4), (7, 4), (9, 4), 
    (14, 4), (11, 4), (7, 4), (9, 4), (10, 2), (10, 2), (11, 2), (12, 2), 
    (14, 4), (16, 4), (16, 4), (14, 4), (12, 4), (11, 4), (9, 4), (7, 4), 
    (7, 4), (9, 4), (11, 4), (12, 4), (11, 4), (9, 4), 
    ('@', 8), 
    (11, 4), (11, 4), (12, 4), (14, 4), (16, 4), (16, 4), (14, 4), (12, 4), 
    (11, 4), (9, 4), (7, 4), (7, 4), (9, 4), (11, 4), (12, 4), (11, 4), (9, 4), 
    (7, 4), (7, 4), (9, 4), (7, 4), (11, 4), (12, 4), (14, 4), (16, 4), 
    (14, 4), (11, 4), (12, 4), (11, 4), (9, 4), (7, 4), (7, 4), (9, 4), 
    (11, 4), (12, 4), (11, 4), (9, 4), (7, 4), (7, 4), (9, 4), (7, 4), 
    (11, 4), (12, 4), (14, 4), (16, 4), (14, 4), (12, 4), (11, 4), (9, 4), 
    (7, 4), (7, 4), (9, 4), (11, 4), (12, 4), (11, 4), (9, 4)
]


cu = CosmicUnicorn()
cu.set_brightness(0.6)
graphics = PicoGraphics(DISPLAY_COSMIC_UNICORN, pen_type=PEN_P8)


bitfont = BitFont(graphics)

width = CosmicUnicorn.WIDTH
height = CosmicUnicorn.HEIGHT

loadImages = True
t_count = 0
t_total = 0
OFFSET = 0
base = 1
vbase = 1  

   
black_pen = graphics.create_pen(0,0,0)
blue_pen = graphics.create_pen(0,0,255)
red_pen = graphics.create_pen(255,0,0)

pen_Q = graphics.create_pen(0,155,255)
pen_ = graphics.create_pen(102,40,90)
pen_O = graphics.create_pen(30,30,80)
pen_r = graphics.create_pen(255,0,0)
pen_F = graphics.create_pen(0,255,0)
pen_k = graphics.create_pen(155,9,0)
pen_m = graphics.create_pen(100,40,80)
pen_g = graphics.create_pen(0,100,30)
pen_b = graphics.create_pen(0,255,0)
pen_tilde = graphics.create_pen(0,13,105)
pen_tilde_2 = graphics.create_pen(0,55,245)
pen_c = graphics.create_pen(0,255,245)
pen_o = graphics.create_pen(255,165,0)
pen_n = graphics.create_pen(139,69,19)
pen_p = graphics.create_pen(255,92,203)
pen_y = graphics.create_pen(250,250,2)
pen_W = graphics.create_pen(255,255,255)
pen_dot = graphics.create_pen(2,2,2)
pen_t = graphics.create_pen(199,20,20)
pen_T = graphics.create_pen(255,55,0)
pen_T2 = pen_Q

pen_snake = graphics.create_pen(0,155,30)
pen_yellow = graphics.create_pen(255,255,0)
pen_frog_green = graphics.create_pen(50,255,90)
pen_frog_eyes = graphics.create_pen(255,255,0)

class lane:
  def __init__(self, x, image, lanemap, velocity ):
    self.image = image
    self.lanemap = lanemap
    self.velocity = velocity
    self.colour = 'rgb(40,40,40)'
    self.lanetype = 'road'
    self.x = x
    self.y = x
    if "~" in self.lanemap:
      self.lanetype = 'water'

  def draw(self, image):
      if "~" in self.lanemap:
          self.lanetype = 'water'
      self.image = image
  

      for ( y, pixel) in enumerate(self.lanemap):
          x = self.x-1
          colour = black_pen

          if pixel == '_':
              colour = pen_
          if pixel == 'Q':
              colour = pen_Q              
          if pixel == 'O':
              colour = pen_O
          if pixel == 'r':
              colour = pen_r
          if pixel == 'W':
              colour = pen_W
          if pixel == 'F':
              colour = pen_F
          if pixel == 'k':
              colour = pen_k
          if pixel == 'm':
              colour = pen_m
          if pixel == 'g':
              colour = pen_g
          if pixel == 's':
              colour = pen_snake
              if (y % 2 == 0):
                  colour = pen_
          if pixel == 'S':
              colour = pen_
              if (y % 2 == 0):
                  colour = pen_snake
          if pixel == 'b':
              colour = pen_b
          if pixel == '~':
              colour = pen_tilde 
          if pixel == 'c':
              colour = pen_c
          if pixel == 'o':
              colour = pen_o
          if pixel == 'n':
              colour = pen_n
          if pixel == 'p':
              colour = pen_p
          if pixel == 'y':
              colour = pen_y
          if pixel == 'w':
              colour = pen_W
          if pixel == '.':
              colour = pen_dot
          if pixel == 't':
              colour = pen_t
          if pixel == 'T':
             if(y % 3 == 0):
                colour = pen_T2
             else:
                colour = pen_T
                  
          if pixel == '+':
              colour = pen_tilde
          if colour != "none":
            graphics.set_pen(colour)
            graphics.pixel(y,x)
          if(self.lanetype == 'water' and pixel == '~' and y % 2 == 0):
            graphics.set_pen(pen_tilde_2)
            graphics.pixel(y,x)
      return self.image

class gameui:
    lives = 0
    score = 0
    
    def drawLifeCounter(self):
        
        for life in range(self.lives):
            space=6
            offset = 1
            
            graphics.set_pen(pen_frog_green)
            graphics.pixel(offset+2+life*space,1)
            graphics.pixel(offset +life*space,1)
            graphics.set_pen(pen_g)
            graphics.pixel(1+offset +life*space,0)
            
            #legs
            graphics.set_pen(pen_g)
            graphics.pixel(offset + 3+life*space,1)
            graphics.pixel(offset +life*space-1,1)
            
            graphics.set_pen(pen_frog_green)
            graphics.pixel(offset +1+life*space,1)

            graphics.set_pen(pen_frog_eyes)
            graphics.pixel(offset +life*space,0)
            graphics.pixel(offset +life*space+2,0)
            
    def drawTimer(self):
        global game
        now = time.time();
        elapsed = now - game.startTime
        timeLimit = game.timeLimit
        remaining = timeLimit - elapsed
        
        for quanta in range(remaining/5):
            graphics.set_pen(pen_y)
            graphics.pixel(quanta,height-1)
        
        
    def draw(self, lives):
        self.lives = lives
        self.drawLifeCounter()
        self.drawTimer()



class frog:
    x = 15
    y = 29
    lives = 3
    level = 1
    initialLives = 3
    score = 0
    alive = True
    direction = 'up'
    lanetype = 'road'
    legs = True
    fcstart = 0
  
    def __init__(self):
        self.lives = self.initialLives
        self.alive=True
        
    def drawLegs(self):
        if self.legs:
           
            if self.direction == 'up':
                graphics.set_pen(pen_frog_green)
                graphics.pixel(self.x-1,self.y+2)
                graphics.pixel(self.x+2,self.y+2)
            if self.direction == 'down':
                graphics.set_pen(pen_frog_green)
                graphics.pixel(self.x-1,self.y-1)
                graphics.pixel(self.x+2,self.y-1)
            if self.direction == 'left':
                graphics.set_pen(pen_frog_green)
                graphics.pixel(self.x+2,self.y-1)
                graphics.pixel(self.x+2,self.y+2)
            if self.direction == 'right':
                graphics.set_pen(pen_frog_green)
                graphics.pixel(self.x-1,self.y-1)
                graphics.pixel(self.x-1,self.y+2)
        
        if self.fcstart == 0:
            self.fcstart = t_count
        if t_count - self.fcstart > 3:
            self.legs = False
    
    def draw(self):
        if not self.alive:
            graphics.set_pen(pen_r)
            if self.lanetype == 'water':
                graphics.set_pen(pen_W)
            graphics.rectangle(self.x-1,self.y,3,3)
            
        else:    
            self.drawLegs()
            if self.direction == 'down': 
                graphics.set_pen(pen_frog_eyes)                          
                graphics.rectangle(self.x,self.y,2,2)        
                graphics.set_pen(pen_frog_green)
                graphics.rectangle(self.x,self.y,2,1)
                
            if self.direction == 'up' or self.direction == None: 
                graphics.set_pen(pen_frog_green)
                graphics.rectangle(self.x,self.y,2,2)        
                graphics.set_pen(pen_frog_eyes)
                graphics.rectangle(self.x,self.y,2,1)        


            if self.direction == 'left': 
                graphics.set_pen(pen_frog_eyes)
                graphics.rectangle(self.x,self.y,1,2)
                graphics.set_pen(pen_frog_green)
                graphics.rectangle(self.x+1,self.y,1,2)        
                


            if self.direction == 'right': 
                graphics.set_pen(pen_frog_green)
                graphics.rectangle(self.x,self.y,1,2)
                graphics.set_pen(pen_frog_eyes)
                graphics.rectangle(self.x+1,self.y,1,2)        
                
class Game:
    timeLimit = 60
    framecount = 0
    # These are the lane speeds. They are in pairs as the frog moves 2 of these lanes per one jump. This was so I could make better cars. 
    speedmap = [ 0, 0, 2, 2, -4, -4, 3, 3 , -2, -2, 4, 4, -3, -3, 5,5, -2, -2, 4, 4, -5, -5 , 3, 3,   0,0,0,0,0,0] 
    image = graphics
    #once you fill all 5, this is used to reset the top
    bridgemap = [
         "kmkWkmkmkWkmkmkWkmkmkWkmkmkWkmkm",
         "kmkWkmkmkWkmkmkWkmkmkWkmkmkWkmkm",
         "mk111kmk222kmk333kmk444kmk555kmk",
         "mk111kmk222kmk333kmk444kmk555kmk",
    ]
    
    def resetLevel(self):
        self.addLanes()
        for (idx, m) in enumerate(self.bridgemap):
            self.lanemap[idx] = m           
            self.lanes[len(self.lanes)-idx-1].lanemap = m

        
    
    # This is the lane data. Each character represents a type of tile, and there are some colours for each defined in lane.py 
    lanemap = [
         "kmkWkmkmkWkmkmkWkmkmkWkmkmkWkmkm",
         "kmkWkmkmkWkmkmkWkmkmkWkmkmkWkmkm",
         "mk111kmk222kmk333kmk444kmk555kmk",
         "mk111kmk222kmk333kmk444kmk555kmk",
         "~~~~~~~~~~~~~~nnno~~~~~~~~~~~~~~~~nnno~~~~no~~nnno~~~~~",     # LOGS 1
         "~~~~~~~~~~~~~~nnno~~~~~~~~~~~~~~~~nnno~~~~no~~nnno~~~~~",     # LOGS 1
         "~~~~nnno~~~~~~~~~nno~~~~~~~~~~~~~~~~~nno~~nno~~~~~",     # LOGS 1
         "~~~~nnno~~~~~~~~~nno~~~~~~~~~~~~~~~~~nno~~nno~~~~~",     # LOGS 1
         "~~nno~~~~~~~~~~~~~~~~~~~~~~~~~~nnno~~~~~~~~~nno~~nno~~~~~", #LOGS 2
         "~~nno~~~~~~~~~~~~~~~~~~~~~~~~~~nnno~~~~~~~~~nno~~nno~~~~~", #LOGS 2
         "~~~~~tt+tt+tt~~~~~~~~~tt+tt~~~~~~~~~~tt+tt+tt~~~~~~~~~~", #LOGS 2
         "~~~~~TT+TT+TT~~~~~~~~~TT+TT~~~~~~~~~~TT+TT+TT~~~~~~~~~~", #LOGS 2
         "_______SSSg_____________________________",         # Safe zone
         "_______sss______________________________",         # Safe zone
 
         "..p..........c.................p...........",    
         ".w.w........OcO...............ObO..........",
         "....O......r..........O..................",         # CAR LANE 1 
         "...bbb....OrO........ggg.................",         # CAR LANE 1
         "....ccc.........rrr............gwg..........", # CAR LANE 2
         "...bObO........rOrO...........gOgO..........", # CAR LANE 2
         ".ppp.........c.................b........",    
         ".OppO.......O.O...............ObO.......",
         "....ccc....cwc............yyyW..........", # CAR LANE 2
         "...bObO...bObO...........yOyyO..........", # CAR LANE 2
         "....O......r.....p................c.....",         # CAR LANE 1 
         "...bbb....OrO...ObO..............O.O....",         # CAR LANE 1
         "________________________________________",               # Safe zone
         "________________________________________"               # Safe zone
         
    ]

    # Anything in this list is safe for frogger to be on. put ~ in it and suddenly your frog can swim, like every other frog in the world! 
    safeSpaces = [  ".", ",", "_", "n", "o", "W", "Q", "t", "T", "+" ,"1","2","3","4","5"]
    lanes = []

    def drawLanes(self):
      self.level = self.player.level
      level = int(self.player.level)
      self.player.lanetype='road'
      for (idx, l) in enumerate(self.lanes): 
          newlane =  l.lanemap
          if(l.velocity > 0):
            if(self.framecount % (max(1,l.velocity - level)) == 0 ):
              if(l.lanetype == 'water' and self.player.y+1 == l.x ): #Move the player with the logs if they're in one of the water lanes
                self.player.lanetype='water'
                self.player.x += 1
                if self.player.x < 0:
                    self.player.alive=False
                if self.player.x > 32:
                    self.player.alive=False
              lastChar = l.lanemap[-1]
              newlane = lastChar + l.lanemap[:-1]
          elif(l.velocity < 0):
            if(self.framecount %  (abs(l.velocity) + level) == 0 ):
              if(l.lanetype == 'water' and self.player.y+1 == l.x ): #Move the player with the logs if they're in one of the water lanes
                self.player.lanetype='water'
                self.player.x -= 1
                if self.player.x < 0:
                    self.player.alive=False
                if self.player.x > 32:
                    self.player.alive=False
              firstChar = l.lanemap[0]
              newlane =  l.lanemap[1:] + firstChar
          l.lanemap = newlane
          self.lanes[idx] = l;
          l.draw(self.image)
          
    def addLanes(self):
        self.lanes = []
        for (idx, l) in enumerate(self.lanemap[::-1]): 
          self.lanes.append(lane(31 - (idx),self.image, l,self.speedmap[idx] )) 

    def draw(self, player):
        self.player = player
        self.drawLanes()
        self.player.draw()
        self.framecount += 1

    
    
    def __init__(self, player):
       self.player = player

       lanes = []
       gamestate = True 
       won = False 
       level = 1
       self.startTime = time.time()
       self.resetLevel()

    def checkPlayerState(self, player):
      #lanes = lanes[::-1] #Reverse this array to make it make sense
      lanes = self.lanes[::-1]
      lane_offset = 2


      try:
        lmap = lanes[self.player.y-lane_offset].lanemap
        lmap2 = lanes[self.player.y-lane_offset-1].lanemap
        #print(lmap2)
        #print(self.player.y-lane_offset-1)
        currentTile = lmap[self.player.x] # This is where we check what the tile type we are on is and if it's safe
        currentTile2 = lmap[self.player.x+1] # the frog is 2 dots wide
        if currentTile == "~" or currentTile2 == '~':
            self.player.lanetype = 'water' #changes the death effect from red to white
        else:
            self.player.lanetype = 'road'
        if str(currentTile) not in self.safeSpaces or str(currentTile2) not in self.safeSpaces:
            self.player.alive=False # The frog is dead, let the game class handle it. 
         
        if (re.search("^[1-5]$", currentTile)): # Frog got to the bridge! W for Winner 
           self.player.score += 1


               
           self.resetFrog()
           print("Player scored! ", self.player.score, " Level: ", self.player.level)
  
           lmap = lmap.replace(str(currentTile) + str(currentTile) + str(currentTile), "ygy")
           lmap2 = lmap2.replace(str(currentTile) + str(currentTile) + str(currentTile), "ggg")

           self.lanes[len(lanes) - self.player.y - lane_offset].lanemap = lmap
           self.lanes[len(lanes) - self.player.y - lane_offset-1].lanemap = lmap2
           if(self.player.score % 5 == 0):
               self.resetLevel()
               self.player.level += 1
               
        if str(currentTile) not in self.safeSpaces:
            self.player.alive=False # The frog is dead, let the game handle it.
            print("player died at", currentTile, " x:", self.player.x, " y:", self.player.y, " lanetype", self.player.lanetype)

            
            
  
      except Exception as e: 
           err = True
           print(e)
      if self.player.alive == False:
          player = frog()
      return lanes
      #return lanes[::-1]
    
    def showTimeUpSplash(self):
        j = jpegdec.JPEG(graphics)
        gameoverimages = ['frogger_timeup.jpg']
        img = random.choice(gameoverimages)
        
        j.open_file(img)

        # Decode the JPEG
        j.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=False)

        # Display the result
        graphics.update()


        cu.update(graphics)
        time.sleep(3)
        
        
    def checkGameState(self):
       now = time.time();
       elapsed = now - game.startTime
       timeLimit = game.timeLimit
       remaining = timeLimit - elapsed

       if remaining < 0:
           self.showTimeUpSplash()
           self.player.alive = False
           
       if not self.player.alive:
           kill_frog()

           self.resetFrog()
           self.player.lives -= 1

           print("Player has lives:", self.player.lives)
           self.player.alive = True
       if player.lives < 1:
           self.gameOver()

    def resetFrog(self):
        self.player.x = 15
        self.player.y = 29
        self.player.direction="up"
        self.startTime = time.time()

    def gameOver(self):

        song_synth.volume(0)
        self.player.draw()
        graphics.update()
        cu.update(graphics)
        time.sleep(1)
        # Create a new JPEG decoder for our PicoGraphics
        j = jpegdec.JPEG(graphics)

        # Open the JPEG file
        
        gameoverimages = ['gameover3.jpg']
        img = random.choice(gameoverimages)
        
        j.open_file(img)

        # Decode the JPEG
        j.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=False)

        # Display the result
        graphics.update()


        cu.update(graphics)
        time.sleep(3)

        j = jpegdec.JPEG(graphics)
        # Open the JPEG file
        j.open_file("/frogger_score3.jpg")

        # Decode the JPEG
        j.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=False)

        # Display the result

        #graphics.clear()                                                                                                                                                                                                                                                  
        graphics.set_pen(pen_W)


        bitfont.draw_text(str(self.player.score), 14,24,font3x5)
        graphics.update()
        cu.update(graphics)
        time.sleep(3)
        
        self.player.lives = self.player.initialLives
        self.player.level = 1
        self.player.score = 0
        self.resetFrog()
        if SOUND_ENABLE == 0: 
            song_synth.volume(0.1)
        self.resetLevel()
    


def update():
    graphics.set_pen(black_pen)
    graphics.rectangle(0, 0, width, height) 
    game.draw(player)
    game.checkPlayerState(player)
    game.checkGameState()
    gameui_.draw(player.lives)
    cu.update(graphics)

    
    
last_note_advance = time.ticks_ms()
last_action = time.ticks_ms()

def debounce(button, duration=20):
    global last_action
    if cu.is_pressed(button) and time.ticks_ms() - last_action > duration:
        last_action = time.ticks_ms()
        return True
    return False


def note_to_frequency(note_number):
    return int((2 ** ((note_number - 69.0) / 12)) * 440)

boopety_beepety = cu.synth_channel(0)
boopety_beepety.configure(
    waveforms=Channel.SQUARE | Channel.SINE,
    attack=0.1,
    decay=0.1,
    sustain=0.0,
    release=0.2,
    volume=0.05
)
deadfrog_beep= cu.synth_channel(1)
deadfrog_beep.configure(
    waveforms=Channel.SQUARE | Channel.SINE,
    attack=0,
    decay=0.2,
    sustain=0,
    release=0.1,
    volume=0.4
)
song_synth= cu.synth_channel(2)
song_synth.configure(
    waveforms=Channel.SQUARE | Channel.SINE,
    attack=0.1,
    decay=0.3,
    sustain=0.2,
    release=0.1,
    volume=0.2
)

cu.play_synth()

player = frog()
game = Game(player)
game.addLanes()
gameui_ = gameui()

def frog_hop():
    current_freq = note_to_frequency(86)
    player.legs = True
    if(SOUND_ENABLE <2):
        deadfrog_beep.frequency(current_freq)
        deadfrog_beep.trigger_attack()
        deadfrog_beep.trigger_release()
        deadfrog_beep.frequency(current_freq+12)
        deadfrog_beep.trigger_attack()


def kill_frog():
    player.draw()
    current_freq = note_to_frequency(24)
    if(SOUND_ENABLE <2):
        deadfrog_beep.frequency(current_freq)
        deadfrog_beep.trigger_attack()

last_pixels = ""
def set_pixels(data):
    global last_pixels
    print("got data")
    
    # save for later
    last_pixels = data
        
    arr = list(data)
    
    for j in range(31):
        for i in range(31):
            index = (j * 32 + i) * 4
                        
            #convert rgba to rgb
            r = int(data[index])
            g = int(data[index+1])
            b = int(data[index+2])
            a = int(data[index+3]) / 255
            
            r = round(a * r)
            g = round(a * g)
            b = round(a * b)
            
            # set the pixel
            print(r,g,b)
            graphics.set_pen(graphics.create_pen(r, g, b))
            graphics.pixel(i, j)
    cu.update(graphics)
  
playticks=1
playcount = 0
song_octave = 5
def playsong():
    if (SOUND_ENABLE > 0):
        return
    
    global playhead, song_octave, playticks, playcount
    if not player.alive:
        return
    
    
    if(playhead > len(song_notes)-1):
        playhead = 0
        song_octave += 1
        if(song_octave > 5):
            song_octave = 3    
    if(playcount == 0):
        current_note, note_length = song_notes[playhead]
        if current_note is not "@":
            # Pacabels Canon in F (the +3) for Frogger with no timing information and errors introduced by chatGPT, so... I mean, I like it. 
            current_freq = note_to_frequency(current_note + 3 + (12*song_octave))
            song_synth.frequency(current_freq)
            song_synth.trigger_attack()
    playcount+=1

    
    if( playcount >= playticks):
        playcount = 0
        playhead += 1
        


"""playticks = 0  # Represents the number of ticks for each note
playcount = 0  # Keeps track of the current tick count
song_octave = 4

def playsong():
    global playcount
    global playticks
    global playhead, song_octave
    
    if (SOUND_ENABLE > 0) or (not player.alive):
        return

    if playhead >= len(song_notes):
        playhead = 0
        song_octave += 1
        if(song_octave > 5):
            song_octave = 3


    current_note,note_length = song_notes[playhead]
    speed=1
    if current_note != "@":
        if playcount == 0:  # If it's the first tick of a note
            current_freq = note_to_frequency(current_note + (12 * song_octave))
            song_synth.frequency(current_freq)
            song_synth.trigger_attack()


        playcount += speed

        if playcount >= note_length:  # If the note duration is reached
            song_synth.trigger_release()
            playcount = 0
            playhead += 1

    else:  # If it's a rest, advance to the next note
        
        if playcount == 0:  # If it's the first tick of a note
            current_freq = note_to_frequency(1)
            song_synth.frequency(current_freq)
            song_synth.volume(0)
            song_synth.trigger_attack()



        playcount += speed

        if playcount >= note_length:  # If the note duration is reached
            song_synth.trigger_release()
            playcount = 0
            playhead += 1
            song_synth.volume(0.2)

     playhead += 1
"""

while True:
    
    playsong()
    
    if cu.is_pressed(CosmicUnicorn.SWITCH_BRIGHTNESS_UP):
        cu.adjust_brightness(+0.1)

    if cu.is_pressed(CosmicUnicorn.SWITCH_BRIGHTNESS_DOWN):
        cu.adjust_brightness(-0.1)    
    
    if debounce(CosmicUnicorn.SWITCH_VOLUME_UP):

        frog_hop()
        player.x = player.x + 1
        player.direction = 'right'
        if player.x > width:
            player.x = 0

    if debounce(CosmicUnicorn.SWITCH_VOLUME_DOWN):
        frog_hop()
        player.x = player.x - 1
        player.direction = 'left'
        if player.x < 0:
            player.x = width

    if debounce(CosmicUnicorn.SWITCH_A):
        frog_hop()
        player.direction = 'up'
        player.y -= 2
        

    if debounce(CosmicUnicorn.SWITCH_B):
        frog_hop()
        player.direction = 'down'
        player.y += 2
        if player.y > height-3:
            player.y = height-3

    if debounce(CosmicUnicorn.SWITCH_D):
        SOUND_ENABLE += 1
        if(SOUND_ENABLE > 3):
            SOUND_ENABLE = 0
        if(SOUND_ENABLE > 0):
            song_synth.volume(0)
            
        else:
            song_synth.volume(0.1)





        
    tstart = time.ticks_ms()
    gc.collect()
  
    update()

  
    tfinish = time.ticks_ms()

    total = tfinish - tstart
    t_total += total
    t_count += 1

    if t_count == 60:
        per_frame_avg = t_total / t_count
        #print(f"60 frames in {t_total}ms, avg {per_frame_avg:.02f}ms per frame, {1000/per_frame_avg:.02f} FPS")
        t_count = 0
        t_total = 0

    time.sleep(1/120)  # 120fps @ 16x16 you knows it!

    # pause for a moment (important or the USB serial device will fail)
    # try to pace at 60fps or 30fps
    """if total > 1000 / 30:
        time.sleep(0.0001)
    elif total > 1000 / 60:
        t = 1000 / 30 - total
        time.sleep(t / 500)
    else:
        t = 1000 / 60 - total
        time.sleep(t / 500)
    """
    
"""
    if loadImages:
    print("Starting Load")
    try:
        
       # Open the JPEG file
        j.open_file("/gameover.jpg")

        # Decode the JPEG
        j.decode(0, 0, jpegdec.JPEG_SCALE_FULL, dither=True)

        # Display the result
        display.update()
        print("finished loading image")
        time.sleep(1)
        loadImages = False



    except Exception as e:
        print("play_frogger asset image /frogger_play.jpg missing, did you upload it?")
        print(e)
        loadImages = False
"""