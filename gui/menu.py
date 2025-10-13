import pygame
import os    #Used to handle file paths, like locating your font file safely across different operating systems.

def show_menu(screen):  #A function that displays a menu on the screen.
    # === Load images ===
    IMG_PATH = os.path.join(os.path.dirname(__file__), "img")

    bullet_img = pygame.image.load(os.path.join(IMG_PATH, "bullet.png"))
    blitz_img = pygame.image.load(os.path.join(IMG_PATH, "blitz.png"))
    rapid_img = pygame.image.load(os.path.join(IMG_PATH, "rapid.png"))

    # resize them so they fit beside the text
    bullet_img = pygame.transform.scale(bullet_img, (60, 60))
    blitz_img = pygame.transform.scale(blitz_img, (60, 60))
    rapid_img = pygame.transform.scale(rapid_img, (60, 60))

    mode_images = [bullet_img, blitz_img, rapid_img]

    #==== set font for menu ====
    pygame.font.init()  # initializes the font module in pygame so you can use custom fonts.

    # Correct path to Orbitron font
    FONT_PATH = os.path.join(os.path.dirname(__file__), "Orbitron", "Orbitron-Regular.ttf")

    if not os.path.exists(FONT_PATH):
        raise FileNotFoundError(f"Font file not found at: {FONT_PATH}")

    font = pygame.font.Font(FONT_PATH, 70)
    small_font = pygame.font.Font(FONT_PATH, 40)

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BLUE = (40, 100, 200)
    LIGHT_BLUE = (100, 180, 255)
    GRAY = (30, 30, 30)

    clock = pygame.time.Clock()
    running = True

    # Options with (label, seconds)
    options = [
        ("Bullet   (1  min)", 60),
        ("Blitz   (5  min)", 300),
        ("Rapid (15 min)", 900)
    ]
    selected_option = 0

    # Store button rects for mouse detection
    button_rects = []

    while running:
        screen.fill(GRAY)
        title_text = font.render("IntelliChess", True, WHITE)
        screen.blit(title_text, (screen.get_width() // 2 - title_text.get_width() // 2, 80))

        button_rects.clear()
        for i, ((label, _), icon) in enumerate(zip(options, mode_images)):
            color = LIGHT_BLUE if i == selected_option else BLUE
            text = small_font.render(label, True, color)

            group_y = 250 + i * 100
            group_padding = 20

            # Measure widths
            icon_width = icon.get_width()
            text_width = text.get_width()

            total_width = icon_width + group_padding + text_width

            # Center the group horizontally
            group_x = (screen.get_width() - total_width) // 2
            icon_rect = icon.get_rect(topleft=(group_x, group_y - icon.get_height() // 2))
            text_rect = text.get_rect(topleft=(icon_rect.right + group_padding, group_y - text.get_height() // 2))

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