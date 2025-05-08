import os
import pygame

BASE_IMG_PATH = "final game project/data/TinyHouse_Tiles_0.05/"

def load_image(path):
    img = pygame.image.load(BASE_IMG_PATH + path).convert() # ALWAYS REMEMBER TO CALL .convert() AT THE END! WILL SAVE ON PERFORMANCE COST!
    img.set_colorkey((0, 0, 0)) # black will become transparent

    return img

def load_images(path):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + "/" + img_name))
    
    return images