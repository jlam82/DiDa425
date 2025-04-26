import pygame

class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        self.action = "" # start of new code
        self.anim_offset = (-3,-3) # animations themselves will have varying dimensions unless there's padding
        self.flip = False # this will allow us to make our character either look left or look right
        self.set_action("idle") # new method implemented
        
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action): # action parameter is the string name of the given animation
        if action != self.action: # check if the animation type has actually change to prevent being permanently stuck at the 0th frame
            self.action = action # update the instance attribute
            self.animation = self.game.assets[self.type + "/" + self.action].copy() # pull the assets 
    
    def update(self, tilemap, movement=(0, 0)): 
        self.collisions = {"up": False, "down": False, "right": False, "left": False} 
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        self.pos[0] += frame_movement[0] 
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect): 
                if frame_movement[0] > 0: 
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right 
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x 
                
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect() 
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top 
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y

        if movement[0] > 0: # if you're moving right
            self.flip = False # the images by default face right, so this is false
        if movement[0] < 0: # and vice versa
            self.flip = True

        self.velocity[1] = min(5, self.velocity[1] + 0.1) 
        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0

        self.animation.update() # important code to call link the update functions() together

    def render(self, surf, offset=(0, 0)):
        surf.blit(
            pygame.transform.flip(self.animation.img(), self.flip, False),
            (self.pos[0] - offset[0] + self.anim_offset[0], # a pattern can be seen to emerge here;
             self.pos[1] - offset[1] + self.anim_offset[1]) # any offset that benefit us need to be accounted for during rendering
        )

class Player(PhysicsEntity): # child class of the PhysicsEntity class
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size) # inheritance method; initialize the parent class
        self.air_time = 0
        
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        self.air_time += 1
        if self.collisions["down"]:
            self.air_time = 0

        if movement[0] != 0: #  if the x-axis of our movement is not 0
            self.set_action("walking") # it means we should be walking
        else: # and if nothing else we're definitely idle
            self.set_action("idle")