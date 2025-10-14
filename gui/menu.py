import pygame
import os

pygame.init()

LIGHT_GREY = (127, 127, 127)
GRAY = (59, 59, 59)
BLUE = (40, 100, 200)
LIGHT_BLUE = (7, 225, 255)
WHITE = (255, 255, 255)

screen_width = 480
screen_height = 480
button_width = 100
button_height = 100

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Chess Timer GUI')
clock = pygame.time.Clock()

IMG_PATH = os.path.join(os.path.dirname(__file__), "img")
bullet_img = pygame.image.load(os.path.join(IMG_PATH, "bullet.png"))
blitz_img = pygame.image.load(os.path.join(IMG_PATH, "blitz.png"))
rapid_img = pygame.image.load(os.path.join(IMG_PATH, "rapid.png"))

bullet_img = pygame.transform.scale(bullet_img, (100, 100))
blitz_img = pygame.transform.scale(blitz_img, (100, 100))
rapid_img = pygame.transform.scale(rapid_img, (100, 100))

options = [
    ("Bullet (1 min)", 60),
    ("Blitz (3 min)", 180),
    ("Rapid (10 min)", 600)
]

mode_images = [bullet_img, blitz_img, rapid_img]

try:
    FONT_PATH = os.path.join(os.path.dirname(__file__), "font", "Orbitron-Bold.ttf")
    font = pygame.font.Font(FONT_PATH, 70)  
    small_font = pygame.font.Font(FONT_PATH, 40)  
except FileNotFoundError:
    font = pygame.font.SysFont('Arial', 70)
    small_font = pygame.font.SysFont('Arial', 40)

def show_menu(screen):
    button_rects = []
    selected_option = 0
    running = True

    icon_positions = [
        (30, 200),
        (30, 325),
        (30, 450), 
    ]

    text_positions = [
        (170, 220),
        (170, 345),
        (170, 470),
    ]

    while running:
        screen.fill(GRAY)
        title_font = pygame.font.Font(FONT_PATH, 70)
        title_text = title_font.render("IntelliChess", True, WHITE)
        screen.blit(title_text, (15, 20))
        button_rects.clear()

        for i, ((label, _), icon) in enumerate(zip(options, mode_images)):
            color = LIGHT_BLUE if i == selected_option else BLUE
            text = small_font.render(label, True, color)

            icon_x, icon_y = icon_positions[i]
            icon_rect = icon.get_rect(topleft=(icon_x, icon_y))

            text_x, text_y = text_positions[i]
            text_rect = text.get_rect(topleft=(text_x, text_y))

            screen.blit(icon, icon_rect)
            screen.blit(text, text_rect)
            button_rects.append((text_rect, i))

        pygame.display.flip()
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_option = (selected_option - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_option = (selected_option + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return options[selected_option][1]  # return time in seconds

            elif event.type == pygame.MOUSEMOTION:
                # Highlight the option under the mouse
                for rect, idx in button_rects:
                    if rect.collidepoint(event.pos):
                        selected_option = idx

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left-click selects the option
                for rect, idx in button_rects:
                    if rect.collidepoint(event.pos):
                        return options[idx][1]  # return time in seconds
