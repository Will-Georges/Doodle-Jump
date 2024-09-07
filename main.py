# Import Statements
import os
import random
import pygame
import shelve

# Initialise Pygame
pygame.init()

# Set the name and icon for the game
pygame.display.set_caption("Doodle Jump")
icon = pygame.image.load("Doodle Jump.jpeg")
pygame.display.set_icon(icon)

# game constants
black = (0, 0, 0)
background = black
WIDTH = 800
HEIGHT = 1000
mask_dude_image = pygame.transform.scale(pygame.image.load("mask_dude.png"), (48, 48))
ninja_frog_image = pygame.transform.scale(pygame.image.load("ninja_frog.png"), (48, 48))
pink_man_image = pygame.transform.scale(pygame.image.load("pink_man.png"), (48, 48))
virtual_guy_image = pygame.transform.scale(pygame.image.load("virtual_guy.png"), (48, 48))
fps = 60
font = pygame.font.Font("freesansbold.ttf", 32)
title_font = pygame.font.Font("doodle.ttf", 60)
timer = pygame.time.Clock()
score = 0
high_score = 0
game_over = False
screen = pygame.display.set_mode((WIDTH, HEIGHT))
shelf_file = shelve.open("score.txt")  # Open the high score file

# load the high score from shelf file
if "high_score" in shelf_file:
    high_score = shelf_file["high_score"]

# Title screen background
title_background = pygame.image.load("background.jpeg")
title_background = pygame.transform.scale(title_background, screen.get_size())

# sounds
menu_sound = pygame.mixer.Sound("menu_sound.wav")
game_sound = pygame.mixer.Sound("game.wav")
pop_sound = pygame.mixer.Sound("pop.wav")

# value used to determine difficulty and mode modifiers
jump_height_difficulty = 0
gravity_difficulty = 0

# Manually initialise initial platforms (x, y, width, height)
platforms = [[350, 960, 140, 20], [170, 740, 140, 20], [530, 740, 140, 20], [350, 520, 140, 20],
             [170, 300, 140, 20], [530, 300, 140, 20], [350, 80, 140, 20]]

# create empty list for collectables
collectables = []

# loop through each platform to generate collectables
for platform in platforms:
    # calculate the position of the collectable
    collectable_x = platform[0] + 45
    collectable_y = platform[1] - 20
    collectable_width = 50
    collectable_height = 50

    # Append the collectable to the collectable list
    collectables.append([collectable_x, collectable_y, collectable_width, collectable_height])

# randomly shuffle collectables
random.shuffle(collectables)

# Calculate the number of collectables to draw (approximately 20% of total)
num_collectables_to_draw = max(1, int(len(collectables) * 0.2))

# create empty list for hazards
hazards = []

# loop through each platform to generate hazards
for platform in platforms:
    # calculate the position of the hazard on each platform
    hazard_x = platform[0] + 45
    hazard_y = platform[1] - 20
    hazard_width = 50
    hazard_height = 50

    # Append the hazard to the hazards list
    hazards.append([hazard_x, hazard_y, hazard_width, hazard_height])

# randomly shuffle the decks
random.shuffle(hazards)

# Calculate the number of hazards to draw (approximately 20% of total)
num_hazards_to_draw = max(1, int(len(hazards) * 0.2))

# game variables
jump = False
y_change = 0
x_change = 0
score_last = 0
super_jumps = 2
jump_last = 0

level = 0
level_to_go_to = 0


# Function to flip sprites horizontally
def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


# Function to load sprite sheets
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = os.path.join("assets", dir1, dir2)
    images = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(os.path.join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


# Load player sprite sheets
PLAYER_SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)


# Creates a player class
class Player:
    WIDTH = 32  # player's width is 32 pixels
    HEIGHT = 32  # player's height is 32 pixels
    ANIMATION_DELAY = 3

    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.speed = speed
        self.direction = "left"
        self.animation_count = 0
        self.sprite = PLAYER_SPRITES["idle_left"][0]
        self.rect = pygame.Rect(self.x, self.y, self.WIDTH, self.HEIGHT)

    # Function so player moves in x direction (dx is x_change)
    def move(self, dx):
        self.x += dx

    # Update player position and handle jumps
    def update(self, jump_power, jump_gravity):
        global jump
        global y_change
        jump_height = jump_power
        gravity = jump_gravity
        if jump:
            y_change = -jump_height
            jump = False
        self.y += y_change
        y_change += gravity

    def update_sprite(self):
        if self.speed != 0:
            sprite_sheet_name = "run_" + self.direction
        else:
            sprite_sheet_name = "idle_" + self.direction
        sprites = PLAYER_SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1

    def draw(self, surface):
        surface.blit(self.sprite, (self.x, self.y))


# Check for collisions with block (by player)
def check_collisions(rect_list, j):
    global player
    for i in range(len(rect_list)):
        # Adjust the position to check for collision 32 pixels higher than the player's current position
        if rect_list[i].colliderect([player.x - 4, player.y + 120 - 64, 70, 10]) and not jump and y_change > 0:
            pop_sound.play()
            j = True
    return j


# check if player collides with collectable and handle function
def check_collectable(rect_list, num_to_draw):
    global player
    global super_jumps
    for collectable in rect_list[:num_to_draw]:
        collectable_rect = pygame.Rect(collectable[0] - 10, collectable[1], collectable[2] + 20, collectable[3])
        player_rect = pygame.Rect(player.x, player.y, player.WIDTH, player.HEIGHT)
        if collectable_rect.colliderect(player_rect):  # Check for collision between player and collectable
            super_jumps += 1
            collectables.remove(collectable)  # remove the collided collectable from the list


# check if player collides with hazard and handle function
def check_hazard(rect_list, num_to_draw):
    global player
    global super_jumps
    for hazard in rect_list[:num_to_draw]:
        hazard_rect = pygame.Rect(hazard[0] - 10, hazard[1], hazard[2] + 20, hazard[3])
        player_rect = pygame.Rect(player.x, player.y, player.WIDTH, player.HEIGHT)
        if hazard_rect.colliderect(player_rect):  # Check for collision between player and hazard
            if super_jumps > 0:
                super_jumps -= 1
            hazards.remove(hazard)  # remove the collided hazard from the list


# Handle movement of platform
def update_platforms(my_list, y_pos, change, is_platform, width):
    global score
    if y_pos < 1000 and change < 0:
        for i in range(len(my_list)):
            my_list[i][1] -= change
    else:
        pass
    for item in range(len(my_list)):
        if my_list[item][1] > 1000:
            if is_platform:  # if a platform goes below floor, spawn a new one
                my_list[item] = [random.randint(-70, 730), random.randint(35, 60), width, 20]
            else:  # if a collectable/hazard goes below floor, spawn a new one
                my_list[item] = [random.randint(0, 640), random.randint(35, 60), 50, 50]
            score += 1
    return my_list


# Create the player
player = Player(340, 800, 0)

# Sets the game to running = true
running = True

# initially start playing the menu sound
menu_sound.play(-1)

# variable to keep track of whether the sound is playing or not
sound_playing = False

while running:
    if level == 0:  # check which mode/level the game should be on
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                quit()
            if event.type == pygame.KEYDOWN:
                # Reset everything when the player plays again
                if event.key == pygame.K_SPACE:
                    background = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))
                    menu_sound.stop()
                    if not sound_playing:  # check if the sound is not already playing
                        game_sound.play(-1)
                        sound_playing = True
                    level = level_to_go_to
                # Change player sprite to MaskDude if 1 is pressed
                elif event.key == pygame.K_1:
                    PLAYER_SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
                    jump_height_difficulty = 25
                    gravity_difficulty = 0.8
                # Change player sprite to NinjaFrog if 2 is pressed
                elif event.key == pygame.K_2:
                    PLAYER_SPRITES = load_sprite_sheets("MainCharacters", "NinjaFrog", 32, 32, True)
                    jump_height_difficulty = 25
                    gravity_difficulty = 1
                # Change player sprite to PinkMan if 3 is pressed
                elif event.key == pygame.K_3:
                    PLAYER_SPRITES = load_sprite_sheets("MainCharacters", "PinkMan", 32, 32, True)
                    jump_height_difficulty = 25
                    gravity_difficulty = 0.8
                # Change player sprite to VirtualGuy if 4 is pressed
                elif event.key == pygame.K_4:
                    PLAYER_SPRITES = load_sprite_sheets("MainCharacters", "VirtualGuy", 32, 32, True)
                    jump_height_difficulty = 20
                    gravity_difficulty = 1
                # following if statements set the mode/level
                elif event.key == pygame.K_a:
                    level_to_go_to = 1
                elif event.key == pygame.K_b:
                    level_to_go_to = 2
                elif event.key == pygame.K_c:
                    level_to_go_to = 3

        # blit the menu background
        screen.blit(title_background, (0, 0))

        # render different bits of text
        instruction_text = font.render("Select Player and Level Difficulty", True, black)
        screen.blit(instruction_text, (150, 200))

        high_score_text = font.render("High Score: " + str(high_score), True, black)
        screen.blit(high_score_text, (265, 10))

        title_text = title_font.render("Doodle Jump", True, black)
        screen.blit(title_text, (100, 100))

        start_text = font.render("Press Space to Start", True, black)
        screen.blit(start_text, (225, 900))

        mask_dude_text = font.render("Easy (1)", True, black)
        screen.blit(mask_dude_text, (150, 300))
        screen.blit(mask_dude_image, (100, 290))

        ninja_frog_text = font.render("Medium (2)", True, black)
        screen.blit(ninja_frog_text, (150, 380))
        screen.blit(ninja_frog_image, (100, 370))

        pink_man_text = font.render("Hard (3)", True, black)
        screen.blit(pink_man_text, (150, 460))
        screen.blit(pink_man_image, (100, 450))

        virtual_guy_text = font.render("Extreme (4)", True, black)
        screen.blit(virtual_guy_text, (150, 540))
        screen.blit(virtual_guy_image, (100, 530))

        normal_mode_text = font.render("Normal (a)", True, black)
        screen.blit(normal_mode_text, (400, 300))

        fun_mode_text = font.render("Fun (b)", True, black)
        screen.blit(fun_mode_text, (400, 380))

        impossible_mode_text = font.render("Impossible (c)", True, black)
        screen.blit(impossible_mode_text, (400, 460))

        pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(100, 745, 40, 40))
        hazard_text = font.render("Avoid Hazards", True, black)
        screen.blit(hazard_text, (150, 750))

        pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(100, 825, 40, 40))
        collectable_text = font.render("Collect Powerups", True, black)
        screen.blit(collectable_text, (150, 830))

        # displays all the things that need to be drawn, in order that they were placed in code
        pygame.display.flip()
        timer.tick(60)  # limits FPS to 60

    # Checks if it is level 1
    if level == 1:
        timer.tick(fps)
        screen.fill(background)

        blocks = []
        score_text = font.render("Score: " + str(score), True, black)
        screen.blit(score_text, (620, 40))

        high_score_text = font.render("High Score: " + str(high_score), True, black)
        screen.blit(high_score_text, (540, 0))

        air_jumps_text = font.render("Super Jumps (Space bar): " + str(super_jumps), True, black)
        screen.blit(air_jumps_text, (20, 20))

        player.draw(screen)

        # Draw collectables
        for collectable in collectables[:num_collectables_to_draw]:
            pygame.draw.rect(screen, (30, 255, 30), collectable)

        # Draw Hazards
        for hazard in hazards[:num_hazards_to_draw]:
            pygame.draw.rect(screen, (255, 30, 30), hazard)

        # Create the platforms
        for i in range(len(platforms)):
            block = pygame.draw.rect(screen, black, platforms[i], 0, 6)
            blocks.append(block)

        # Check if you click the cross (close)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Check if pressing a key
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over and super_jumps > 0:  # Use a super jump
                    super_jumps -= 1
                    y_change = -25
                if event.key == pygame.K_a:
                    player.speed = -5  # move left
                    player.direction = "left"
                if event.key == pygame.K_d:
                    player.speed = 5  # move right
                    player.direction = "right"
                if event.key == pygame.K_ESCAPE:
                    level = 4  # pause menu
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a or event.key == pygame.K_d:
                    player.speed = 0

        # Check if colliding with a platform. (Jump if you are)
        jump = check_collisions(blocks, jump)

        # Call check_collectable function
        check_collectable(collectables, num_collectables_to_draw)

        # Call check_hazard function
        check_hazard(hazards, num_hazards_to_draw)

        # move the player
        player.move(x_change)

        # Checks if the player is at the bottom of the screen
        if player.y < 968:  # handle code for if it is still on screen
            player.update(jump_height_difficulty, gravity_difficulty)
        else:  # reset variables
            game_sound.stop()
            sound_playing = False
            menu_sound.play(-1)
            game_over = False
            score = 0
            player.x = 340
            player.y = 800
            background = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))
            platforms = [[350, 960, 140, 20], [170, 740, 140, 20], [530, 740, 140, 20], [350, 520, 140, 20],
                         [170, 300, 140, 20], [530, 300, 140, 20], [350, 80, 140, 20]]
            collectables = []

            for platform in platforms:
                collectable_x = platform[0] + 45
                collectable_y = platform[1] - 20
                collectable_width = 50
                collectable_height = 50
                collectables.append([collectable_x, collectable_y, collectable_width, collectable_height])

            score_last = 0
            super_jumps = 2
            jump_last = 0
            level = 0
            y_change = 0
            x_change = 0

        # Creates the platforms, hazards and collectables
        platforms = update_platforms(platforms, player.y, y_change, True, 140)
        collectables = update_platforms(collectables, player.y, y_change, False, 140)
        hazards = update_platforms(hazards, player.y, y_change, False, 140)

        # adds borders (Reset player when get to edge)
        if player.x < 0:
            player.x = 0
        elif player.x > 736:
            player.x = 736

        # Flips the player if required, depending on direction
        if x_change > 0:
            player.image = pygame.transform.flip(pygame.transform.scale(pygame.image.load("doodle.png"), (180, 140)), 1,
                                                 0)
        elif x_change < 0:
            player.image = pygame.transform.scale(pygame.image.load("doodle.png"), (180, 140))

        # Assigns high score
        if score > high_score:
            high_score = score
            shelf_file["high_score"] = high_score  # Store the high score in shelf file

        # Changes background to random colour every 15 score
        if score - score_last >= 15:
            score_last = score
            background = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))

        player.update_sprite()  # Update player sprite based on actions

        # adds movement/value to player x coordinate
        player.x += player.speed

        # Draws things on screen in order of where they are in the function
        pygame.display.flip()

    # handle functionality if level 2
    if level == 2:
        timer.tick(fps)
        screen.fill(background)

        blocks = []
        score_text = font.render("Score: " + str(score), True, black)
        screen.blit(score_text, (620, 40))

        high_score_text = font.render("High Score: " + str(high_score), True, black)
        screen.blit(high_score_text, (540, 0))

        air_jumps_text = font.render("Super Jumps (Space bar): " + str(super_jumps), True, black)
        screen.blit(air_jumps_text, (20, 20))

        player.draw(screen)

        # Create the platforms
        for i in range(len(platforms)):
            block = pygame.draw.rect(screen, black, platforms[i], 0, 6)
            blocks.append(block)

        # Check if you click the cross (close)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Check if pressing a key
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over and super_jumps > 0:  # Use a super jump
                    super_jumps -= 1
                    y_change = -25
                if event.key == pygame.K_a:
                    player.speed = -5  # move left
                    player.direction = "left"
                if event.key == pygame.K_d:
                    player.speed = 5  # move right
                    player.direction = "right"
                if event.key == pygame.K_ESCAPE:
                    level = 4  # pause the game
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a or event.key == pygame.K_d:
                    player.speed = 0

        # Check if colliding with a platform. (Jump if you are)
        jump = check_collisions(blocks, jump)

        # move the player
        player.move(x_change)

        # Checks if the player is at the bottom of the screen
        if player.y < 968:
            player.update(jump_height_difficulty, gravity_difficulty)
        else:  # reset variables
            game_sound.stop()
            sound_playing = False
            menu_sound.play(-1)
            game_over = False
            score = 0
            player.x = 340
            player.y = 800
            background = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))
            platforms = [[350, 960, 140, 20], [170, 740, 140, 20], [530, 740, 140, 20], [350, 520, 140, 20],
                         [170, 300, 140, 20], [530, 300, 140, 20], [350, 80, 140, 20]]
            collectables = []

            for platform in platforms:
                collectable_x = platform[0] + 45
                collectable_y = platform[1] - 20
                collectable_width = 50
                collectable_height = 50
                collectables.append([collectable_x, collectable_y, collectable_width, collectable_height])

            score_last = 0
            super_jumps = 2
            jump_last = 0
            level = 0
            y_change = 0
            x_change = 0

        # Creates the platforms
        platforms = update_platforms(platforms, player.y, y_change, True, 140)

        # Effectively adds borders (Reset player when get to edge)
        if player.x < 0:
            player.x = 0
        elif player.x > 736:
            player.x = 736

        # Flips the player if required, depending on direction
        if x_change > 0:
            player.image = pygame.transform.flip(pygame.transform.scale(pygame.image.load("doodle.png"), (180, 140)), 1,
                                                 0)
        elif x_change < 0:
            player.image = pygame.transform.scale(pygame.image.load("doodle.png"), (180, 140))

        # Assigns high score
        if score > high_score:
            high_score = score
            shelf_file["high_score"] = high_score  # Store the high score in shelf file

        # Changes background to random colour, every 15 score
        if score - score_last >= 15:
            score_last = score
            background = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))

        # Gives the player an extra super jump, every 50 score
        if score - jump_last >= 50:
            jump_last = score
            super_jumps += 1

        player.update_sprite()  # Update player sprite based on actions

        # adjusts the players x coordinate
        player.x += player.speed

        # Draws things on screen in order of where they are in the function
        pygame.display.flip()

    # code for level/mode 3
    if level == 3:
        timer.tick(fps)
        screen.fill(background)

        blocks = []
        score_text = font.render("Score: " + str(score), True, black)
        screen.blit(score_text, (620, 40))

        high_score_text = font.render("High Score: " + str(high_score), True, black)
        screen.blit(high_score_text, (540, 0))

        air_jumps_text = font.render("Super Jumps (Space bar): " + str(super_jumps), True, black)
        screen.blit(air_jumps_text, (20, 20))

        player.draw(screen)

        # Draw collectables
        for collectable in collectables[:num_collectables_to_draw]:
            pygame.draw.rect(screen, (30, 255, 30), collectable)

        for hazard in hazards[:num_hazards_to_draw]:
            pygame.draw.rect(screen, (255, 30, 30), hazard)

        # Create the platforms
        for i in range(len(platforms)):
            block = pygame.draw.rect(screen, black, platforms[i], 0, 6)
            blocks.append(block)

        # Check if you click the cross (close)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Check if pressing a key
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over and super_jumps > 0:  # Use a super jump
                    super_jumps -= 1
                    y_change = -25
                if event.key == pygame.K_a:
                    player.speed = -5  # move left
                    player.direction = "left"
                if event.key == pygame.K_d:
                    player.speed = 5  # move right
                    player.direction = "right"
                if event.key == pygame.K_ESCAPE:
                    level = 4  # pause game
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a or event.key == pygame.K_d:
                    player.speed = 0

        # Check if colliding with a platform. (Jump if you are)
        jump = check_collisions(blocks, jump)

        # Call check_collectable function
        check_collectable(collectables, num_collectables_to_draw)

        # Call check_hazard function
        check_hazard(hazards, num_hazards_to_draw)

        # move the player
        player.move(x_change)

        # Checks if the player is at the bottom of the screen
        if player.y < 968:
            player.update(jump_height_difficulty, gravity_difficulty)
        else:  # reset variables
            game_sound.stop()
            sound_playing = False
            menu_sound.play(-1)
            game_over = False
            score = 0
            player.x = 340
            player.y = 800
            background = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))
            platforms = [[350, 960, 140, 20], [170, 740, 140, 20], [530, 740, 140, 20], [350, 520, 140, 20],
                         [170, 300, 140, 20], [530, 300, 140, 20], [350, 80, 140, 20]]
            collectables = []

            for platform in platforms:
                collectable_x = platform[0] + 45
                collectable_y = platform[1] - 20
                collectable_width = 50
                collectable_height = 50
                collectables.append([collectable_x, collectable_y, collectable_width, collectable_height])

            score_last = 0
            super_jumps = 2
            jump_last = 0
            level = 0
            y_change = 0
            x_change = 0

        # Creates the platforms
        platforms = update_platforms(platforms, player.y, y_change, True, 80)
        collectables = update_platforms(collectables, player.y, y_change, False, 80)
        hazards = update_platforms(hazards, player.y, y_change, False, 80)

        # Effectively adds borders (Reset player when get to edge)
        if player.x < 0:
            player.x = 0
        elif player.x > 736:
            player.x = 736

        # Flips the player if required, depending on direction
        if x_change > 0:
            player.image = pygame.transform.flip(pygame.transform.scale(pygame.image.load("doodle.png"), (180, 140)), 1,
                                                 0)
        elif x_change < 0:
            player.image = pygame.transform.scale(pygame.image.load("doodle.png"), (180, 140))

        # Assigns high score
        if score > high_score:
            high_score = score
            shelf_file["high_score"] = high_score  # Store the high score in shelf file

        # Changes background to random colour, in score increments of 15
        if score - score_last >= 15:
            score_last = score
            background = (random.randint(20, 255), random.randint(20, 255), random.randint(20, 255))

        player.update_sprite()  # Update player sprite based on actions

        # adjusts the players x position
        player.x += player.speed

        # Draws things on screen in order of where they are in the function
        pygame.display.flip()

    # pause menu
    if level == 4:
        timer.tick(fps)
        screen.blit(title_background, (0, 0))

        pause_text = font.render("Game Paused (Space bar)", True, black)
        screen.blit(pause_text, (200, 100))

        # Check if you click the cross (close)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Check if pressing a key
            if event.type == pygame.KEYDOWN:
                # unpauses the game
                if event.key == pygame.K_SPACE:
                    level = level_to_go_to

        # Draws things on screen in order of where they are in the function
        pygame.display.flip()


# Close the shelf file
shelf_file.close()

# Quits the game.
pygame.quit()
