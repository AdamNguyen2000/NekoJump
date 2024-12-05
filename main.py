import os
import random
import math
import pygame
# Loads folders and files
from os import listdir
from os.path import isfile, join
pygame.init()

# Name of program
pygame.display.set_caption("NekoJump")

# Global variables
WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 7

# Window variable to set width and height
window = pygame.display.set_mode((WIDTH, HEIGHT))

# Sprites are in one direction so this allows flipping sprite when moving a different direction
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))] # for loop in list is to split images in folder

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        # Example if given 32 pixels then it would know how to cut sprite into 32 pixel images
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32) # SRCALPHA allows transparent images, 32 = depth, surface is to create the desired individual frame
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface)) # double the size

        # Added sprites and flip(sprites) as keys to the dictionary
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 128, size, size) # Pixel location of where to get terrain, top left location
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface) # Double the size


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 1
    SPRITES = load_sprite_sheets("MainCharacters", "Mango", 32, 32, True) # Directory names and size of character
    ANIMATION_DELAY = 3 # Increase or decrease speed of character 

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        # Speed of the character moves
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left" # Keep track of what direction the character is facing
        self.animation_count = 0 # Reset count
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel # -vel because in order to move left you must be negative values
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        # Gravity but with 9.8m/s real life acceleration to an extent
        # min 1 is crucial as you want to fall 1 pixel a frame since without it can be in the decimals
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        
        # Call once every frame
        # Move character in correct direction
        # Update animations
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    # Hit head
    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0
    # Hit head
    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    # Walking animation
    def update_sprite(self):
        sprite_sheet = "idle" # Standing still
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0: 
            if self.jump_count == 1: # Jump
                sprite_sheet = "jump"
            elif self.jump_count == 2: # Double Jump
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0: # If not standing still then use run sprites
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites) # Animation count divided by delay (5) modulus to the length of frame to show
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y)) # Rectangle that is bound to character is adjusted
        self.mask = pygame.mask.from_surface(self.sprite) # Differentiate pixels to transparent ones to allow pixel perfect collision, must be called mask


    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


def get_background(name):
    # assets path and background path
    image = pygame.image.load(join("assets", "Background", name))
    # x, y, width, height (the _ means no value since we don't need it)
    _, _, width, height = image.get_rect()
    tiles = []
    # Integer divide the screen width by the width of the tile
    # To determine how many tiles needed
    # +1 extra tile is to ensure no gaps
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            # Position of the top left tile
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    # Loop through every tile to draw at that position which fills background 
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom # When you move up, you hit the bottom of an object so you don't go through it
                player.hit_head()

            collided_objects.append(obj) # Differentiate if you hit a block or fire

    return collided_objects

# Added collision
def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object

# Allow character to be able to move
def handle_move(player, objects):
    keys = pygame.key.get_pressed() # Keyboard left and right arrow keys

    player.x_vel = 0 
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    # Only moves when holding down arrow key
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire":
            player.make_hit()


def main(window):
    clock = pygame.time.Clock()
    # Background file
    background, bg_image = get_background("Sky.png")

    # Terrain Blocks
    block_size = 96

    player = Player(100, 100, 50, 50)
    fire1 = Fire(384, HEIGHT - block_size - 160, 16, 32)
    fire2 = Fire(576, HEIGHT - block_size - 448, 16, 32)  # Example: new fire trap
    fire3 = Fire(1440, HEIGHT - block_size - 256, 16, 32)  # Another new fire trap

    fire1.on()
    fire2.on()
    fire3.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(-WIDTH // block_size, (WIDTH * 20) // block_size)]
    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size),
                Block(block_size * 0, HEIGHT - block_size * 3, block_size),
                Block(block_size * 0, HEIGHT - block_size * 4, block_size),
                Block(block_size * 0, HEIGHT - block_size * 5, block_size),
                Block(block_size * 0, HEIGHT - block_size * 6, block_size),
                Block(block_size * 0, HEIGHT - block_size * 7, block_size),
                Block(block_size * 0, HEIGHT - block_size * 8, block_size),
                Block(block_size * 0, HEIGHT - block_size * 3, block_size),
                Block(block_size * 1, HEIGHT - block_size * 3, block_size),
                Block(block_size * 2, HEIGHT - block_size * 4, block_size),
                Block(block_size * 3, HEIGHT - block_size * 4, block_size),
                Block(block_size * 4, HEIGHT - block_size * 2, block_size),
                Block(block_size * 5, HEIGHT - block_size * 2, block_size),
                Block(block_size * 6, HEIGHT - block_size * 5, block_size),
                Block(block_size * 8, HEIGHT - block_size * 5, block_size),
                Block(block_size * 9, HEIGHT - block_size * 6, block_size),
                Block(block_size * 10, HEIGHT - block_size * 6, block_size),
                Block(block_size * 11, HEIGHT - block_size * 4, block_size),
                Block(block_size * 13, HEIGHT - block_size * 4, block_size),
                Block(block_size * 14, HEIGHT - block_size * 3, block_size),
                Block(block_size * 15, HEIGHT - block_size * 3, block_size),
               fire1, fire2, fire3]

    offset_x = 0
    scroll_area_width = 200

    run = True
    while run:
        clock.tick(FPS) # Keeps FPS to 60 to regulate across multiple platforms

        for event in pygame.event.get():
            # When user exits program quit, stop look and quit the program 
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        player.loop(FPS) # Loop moves the character every frame
        fire1.loop()
        fire2.loop()
        fire3.loop()  # Make sure all traps update
        handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x) # Use sprites to create ingame images by calling draw

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
