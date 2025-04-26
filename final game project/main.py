import pygame
import sys

pygame.init()

pygame.display.set_caption("ninja game") 
screen = pygame.display.set_mode((640, 480)) 

clock = pygame.time.Clock() 

# while True:
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT: 
#             pygame.quit()
#             sys.exit()

#     pygame.display.update() 
#     clock.tick(60)

def play():


class Game:
    def __init__(self):
        pygame.init()
        
        pygame.display.set_caption("ninja game")
        self.screen = pygame.display.set_mode((640, 480))
        
        self.clock = pygame.time.Clock()

        self.img = pygame.image.load("data/images/clouds/cloud_1.png") # .png is typically recommended because its lossless
    def run(self):
        while True:
            self.screen.blit(self.img, (100, 200)) # .blit() is used to put images onto our screen
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit() 
                    sys.exit()
        
            pygame.display.update()
            self.clock.tick(60) # self here is important

Game().run() # call our object and run it
