import pygame
import neat
import time
import os
import random # for random height of tubes
pygame.font.init()
WIN_WIDTH = 500 # a constant (remains unchanged)
WIN_HEIGHT = 800

#list for images, 2x is to make them bigger
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_img(name):
    return pygame.transform.scale2x(
        pygame.image.load(os.path.join(BASE_DIR, "assets", name))
    )

bird_imgs = [load_img("bird1.png"), load_img("bird2.png"), load_img("bird3.png")]
pipe_img = load_img("pipe.png")
base_img = load_img("base.png")
backg_img = load_img("bg.png")

stat_font = pygame.font.SysFont("comicsans", 50)
small_font = pygame.font.SysFont("comicsans", 30)

generation = 0
best_score = 0
class Bird:
    # constants
    imgs = bird_imgs
    max_rotation = 25 # How much the bird tilts itself (25°)
    rotation_vel = 20 # How much bird rotates on each frame
    animation_time = 5 # How long bird stays in animation (flap)

    # __init__ attributes methods expect it to have
    def __init__(self, x,y): #sets position of bird
        self.x = x
        self.y = y
        self.tilt = 0 # how much bird image tilts
        self.tick_count = 0 # physics for bird
        self.vel = 0 # 0 vel = (don't move)
        self.height = self.y
        self.img_count = 0
        self.img = self.imgs[0]
    
    def jump(self):
        self.vel = -10.5 # negative vel makes bird go up for this, pos vel makes bird go down
        self.tick_count = 0 # keeps track of when player last jumped, at 0 
        self.height = self.y
    
    def move(self):
        self.tick_count += 1 # keeps count of how many times jumped

        displacement = self.vel*self.tick_count + 1.5*self.tick_count**2 # calculates how many pixels move up or down in y position frame
        
        if displacement >= 16: # d is moving down more than 16 pixels, can't exceed that
            displacement = 16
        
        if displacement < 0:
            displacement -= 3 # jump distance
            
        self.y = self.y + displacement
        
        if displacement < 0 or self.y < self.height + 50: # tilts bird up, checks for certain position
            if self.tilt < self.max_rotation: # makes sure bird doesn't tilt to weird pos
                self.tilt = self.max_rotation
        else:
            if self.tilt > -90:
                self.tilt -= self.rotation_vel # accounts for bird going down
    
    def draw(self, win):
        self.img_count += 1 

        # checks what img should show based on img count
        if self.img_count < self.animation_time: # less than 5, display bird img
            self.img = self.imgs[0] 
        elif self.img_count < self.animation_time*2: # if animation count is less than 10 (5*2), show second bird.2
            self.img = self.imgs[1]
        elif self.img_count < self.animation_time*3: # less than 15 (3*5), shows bird.3 img
            self.img = self.imgs[2]
        elif self.img_count < self.animation_time*4:
            self.img = self.imgs[1]
        elif self.img_count == self.animation_time*4 + 1:
            self.img = self.imgs[0]
            self.img_count = 0
        
        if self.tilt <= -80:
            self.img = self.imgs[1] # displays img to show bird going down
            self.img_count = self.animation_time*2
        
        rotated_img = pygame.transform.rotate(self.img, self.tilt) # rotates img for us
        new_rect = rotated_img.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_img, new_rect.topleft) # rotates img
    
    def get_mask(self): # collision for objects
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200 # space between pipe
    vel = 5

    def __init__(self, x): # x is for random pipes
        self.x = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img
        
        self.passed = False # for collisions
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP
    
    def move(self):
        self.x -= self.vel

    def draw(self, window): #draws pipe
        window.blit(self.PIPE_TOP, (self.x, self.top))
        window.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset) # detects if points collide, tells us point of collision
        t_point = bird_mask.overlap(top_mask, top_offset) 

        if t_point or b_point:
            return True
        return False
    
class Base:
    vel = 5
    width = base_img.get_width()
    img = base_img

    def __init__(self, y):
        self.y = y 
        self.x1 = 0
        self.x2 = self.width
    def move(self):
        self.x1 -= self.vel
        self.x2 -= self.vel

        if self.x1 + self.width < 0:
            self.x1 = self.x2 + self.width

        if self.x2 + self.width < 0:
            self.x2 = self.x1 + self.width
    
    def draw(self, window):
        window.blit(self.img, (self.x1, self.y))
        window.blit(self.img, (self.x2, self.y))

def draw_window(window, birds, pipes, base, score, generation, best_score):
    window.blit(backg_img, (0,0)) # blit = draw/put img on window
    for pipe in pipes:
        pipe.draw(window)
        
    # current score
    text = stat_font.render("Score: " + str(score), 1,(255,255,255))
    window.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10)) # however big the score gets, this will keep in check
    
    # stats
    window.blit(small_font.render("Gen: " + str(generation), 1, (255, 255, 255)), (10, 10))
    window.blit(small_font.render("Alive: " + str(len(birds)), 1, (255, 255, 255)), (10, 40))
    window.blit(small_font.render("Gen: " + str(best_score), 1, (255, 255, 255)), (10, 70))

    
    base.draw(window)
    for bird in birds:
        bird.draw(window)
    
    pygame.display.update()
    
# creates the pop-up menu
def draw_button(window, rect, label, mouse_pos):
    color = (255, 200, 60) if rect.collidepoint(mouse_pos) else (240, 160, 30)
    pygame.draw.rect(window, color, rect, border_radius=10)
    pygame.draw.rect(window, (255, 255, 255), rect, 3, border_radius=10)
    text = small_font.render(label, 1, (255, 255, 255))
    window.blit(text, text.get_rect(center=rect.center))

# shows the start menu. 
# returns the chosen number of generations, or None if the player quits.
def show_menu():
    window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    options = [10, 25, 50, 100, 200]  # generation choices
    index = 2  # starts on 50

    left_btn = pygame.Rect(90, 340, 50, 50)
    right_btn = pygame.Rect(360, 340, 50, 50)
    start_btn = pygame.Rect(150, 450, 200, 60)
    quit_btn = pygame.Rect(150, 540, 200, 60)

    while True:
        clock.tick(30)
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if left_btn.collidepoint(event.pos):
                    index = max(0, index - 1)
                elif right_btn.collidepoint(event.pos):
                    index = min(len(options) - 1, index + 1)
                elif start_btn.collidepoint(event.pos):
                    return options[index]
                elif quit_btn.collidepoint(event.pos):
                    return None

        window.blit(backg_img, (0, 0))

        title = stat_font.render("Flappy Bird AI", 1, (255, 255, 255))
        window.blit(title, title.get_rect(center=(WIN_WIDTH // 2, 180)))

        label = small_font.render("Generations", 1, (255, 255, 255))
        window.blit(label, label.get_rect(center=(WIN_WIDTH // 2, 300)))

        value = stat_font.render(str(options[index]), 1, (255, 255, 255))
        window.blit(value, value.get_rect(center=(WIN_WIDTH // 2, 365)))

        draw_button(window, left_btn, "<", mouse_pos)
        draw_button(window, right_btn, ">", mouse_pos)
        draw_button(window, start_btn, "Start", mouse_pos)
        draw_button(window, quit_btn, "Quit", mouse_pos)

        pygame.display.update()



def main(genomes, config):
    global generation, best_score
    generation += 1
    
    nets = []
    gen = []
    birds = []
    
    for _, g in genomes:
        # neural network for genone
        net = neat.nn.FeedForwardNetwork.create(g, config) # knows how to setup properly
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        gen.append(g)


    base = Base(730)
    window = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    pipes = [Pipe(700)]
    score = 0
    game_run = True # detects if game is running
    
    while game_run:
        clock.tick(30) # has bird not fall down immediately, capping it at 30 ticks
        for event in pygame.event.get(): # keeps track of user inputs
            if event.type == pygame.QUIT:
                game_run = False
                pygame.quit()
                quit()
        
        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            game_run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            gen[x].fitness += 0.1 # low number due to 30 tries at once (may lower)

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        remove = []
        for pipe in pipes: # generates pipes
            for x, bird in enumerate(birds):
                if pipe.collide(bird): # checks for collision
                    gen[x].fitness -= 1 # everytime bird hits pipe, fitness minus 1
                    birds.pop(x)
                    nets.pop(x)
                    gen.pop(x)
                
                if not pipe.passed and pipe.x < bird.x: # check if bird has passed pipe
                    pipe.passed = True
                    add_pipe = True
            
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                remove.append(pipe)

            pipe.move()
        if add_pipe:
            score += 1
            if score > best_score:
                best_score = score
            
            for g in gen:
                g.fitness += 5
            pipes.append(Pipe(700))

        for r in remove:
            pipes.remove(r)
        base.move() # spawns base
        draw_window(window, birds, pipes, base, score, generation, best_score) # lets us see our bird

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0: # checks for bird hitting ground
                birds.pop(x)
                nets.pop(x)
                gen.pop(x)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, # defining properties
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, # loads in config file
                                config_path)
    population = neat.Population(config) # generates a population

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats) # gives us output

    winner = population.run(main, generation) # runs generations, calls main times that user inputs

if __name__ == "__main__":
    local_directory = os.path.dirname(os.path.abspath(__file__)) # gives us path to directory name
    config_path = os.path.join(local_directory, "config-feedforward.txt") # accessing file
    generations = show_menu()
    if generations is None:
        pygame.quit()
        quit()
    
    run(config_path)
