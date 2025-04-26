import sys
import pygame

from scripts.utils import load_images # some imports were not needed
from scripts.tilemap import Tilemap

RENDER_SCALE = 2.0 # render scale to determine how much to multiply the pixels

class Editor:
    def __init__(self):
        pygame.init()
        
        pygame.display.set_caption("editor") # change the name
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()
 
        self.assets = { # trim this down
            "floor": load_images("")

            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
        }

        self.movement = [False, False, False, False] # you'd still want to keep this so you can move your camera around
        # removed the Player and Clouds class
        
        self.tilemap = Tilemap(self, tile_size=16)

        try: # simple try-except clause to load in our map
            self.tilemap.load("map.json") # if this file exists (which it should)
        except FileNotFoundError:
            pass # continue as a blank editor
            
        self.scroll = [0, 0] 

        self.tile_list = list(self.assets) # normally you can implement an interface to choose a tile to map, but this is easier for the tutorial
        self.tile_group = 0 # these variables tell us which tile we're using
        self.tile_variant = 0 # and which variant

        self.clicking = False
        self.right_clicking = False
        self.shift = False # using key combination to help select variant
        self.ongrid = True # set the default mode of placing tiles as true

    def run(self):
        while True:
            self.display.fill((0, 0, 0)) # we can return to just a simple black background; change method
            # trim out the rendering for Player and Clouds instances

            self.scroll[0] += (self.movement[1] - self.movement[0]) * 2 # multiply by 2 so that it moves faster
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 2
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            f"""
            It would be nice if we have an indication system on where the next tile would be placed
            """
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy() # index the assets dictionary and copy the asset
            current_tile_img.set_alpha(100) # varies between 0 and 255; 100 will make the tile semi-transparent

            mpos = pygame.mouse.get_pos() # will return the pixel coordinate of your mouse with respect to the window
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE) # but we also have to scale down our mouse position in order to get the correct coordinates
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size)) # this will give us the coordinate of our mouse in terms of the tile system

            f"""
            Takes in the tile position calculated above, and converting it back to pixel coordinates via multiplying by tile size,
            adjusting the camera position offset.

            Simple conditional to blit the transparent next tile image according to ongrid or not
            """
            if self.ongrid:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size - self.scroll[0], tile_pos[1] * self.tilemap.tile_size - self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos) # off-grid tile position requires no crazy math
            
            if self.clicking and self.ongrid: # for placing tiles ongrid
                self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {"type": self.tile_list[self.tile_group], "variant": self.tile_variant, "pos": tile_pos} # converting the index selection to the string name of the group and variant
            if self.right_clicking: # for deleting tiles
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap: # this means that the location that we're hovering exits
                    del self.tilemap.tilemap[tile_loc]
                f"""
                Unoptimized for the level editor but that's ok because it's not the main game.
                """
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile["type"]][tile["variant"]] # next we need to get the bounding box of the image to delete
                    tile_r = pygame.Rect(tile["pos"][0] - self.scroll[0], tile["pos"][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height()) # can do it the other way around by just adding the mouse position
                    if tile_r.collidepoint(mpos): # you can collide with points just like with rectangles
                        self.tilemap.offgrid_tiles.remove(tile) # remove the tile (same as using the 'del' keyword)
                        
            self.display.blit(current_tile_img, (5, 5))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit() 
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN: # new event type; can trigger on scroll wheel too
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid: # if this is not accounted for, then offgrid tiles would be placed 60 times per second
                            self.tilemap.offgrid_tiles.append({"type": self.tile_list[self.tile_group], "variant": self.tile_variant, "pos": (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1])}) # we must account for the scroll position because the coordinate of the camera is not the same as the coordinate of the world
                    if event.button == 3: # for right clicking; very similar layout to tkinter
                        self.right_clicking = True
                    if self.shift: # nested loop for variant choosing
                        if event.button == 4: # scroll up
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]]) # this will give us the number of variants
                        if event.button == 5: # scroll down
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]]) 
                    else:
                        if event.button == 4: # scroll up
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list) # again getting something to loop via modulo
                            self.tile_variant = 0 # reset variant attribute so that we don't run into an index error
                        if event.button == 5: # scroll down
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list) # change order
                            self.tile_variant = 0 
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False # so now these clicking variables will be updated based on whatever our mouse state is
                    if event.button == 3:
                        self.right_clicking = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a: # wasd is nicer for this purpose
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w: # add new movements for the camera
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_LSHIFT: # left shift (please no right)
                        self.shift = True
                    if event.key == pygame.K_g: # now account for offgrid tiles
                        self.ongrid = not self.ongrid # essentially a toggle button for on-grid vs off-grid
                    if event.key == pygame.K_o: # 'o' for output; I really wonder if there's an application menu for this instead
                        self.tilemap.save("map.json")
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w: # same here
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Editor().run()