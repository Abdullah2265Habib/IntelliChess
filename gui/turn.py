import pygame
import os

def getTurnFromButton():
    pygame.init()
    
    GREY = (232,232,232)
    WHITE = (255,255,255)

    screen = pygame.display.set_mode((1000,1000))
    pygame.display.set_caption("Choose Your Side")
    
    FONT_DIR=os.path.join(os.path.dirname(__file__),"font")
    IMG_PATH=os.path.join(os.path.dirname(__file__),"img")
    
    try:
        title_font=pygame.font.Font(os.path.join(FONT_DIR,'Orbitron-Bold.ttf'),64)
        font=pygame.font.Font(os.path.join(FONT_DIR,'Orbitron-Bold.ttf'), 36)
    except:
        title_font = pygame.font.SysFont('Arial',64)
        font = pygame.font.SysFont('Arial',36)
    
    try:
        title_page=pygame.image.load(os.path.join(IMG_PATH,"title.png"))
        title_page=pygame.transform.scale(title_page,(1000,1000))
    except:
        title_page=pygame.Surface((600,400))
        title_page.fill((40,40,40))
    
    try:
        white_img=pygame.image.load(os.path.join(IMG_PATH,"wR.png"))
        black_img=pygame.image.load(os.path.join(IMG_PATH,"bR.png"))
        white_img=pygame.transform.scale(white_img,(100,100))
        black_img=pygame.transform.scale(black_img,(100,100))
    except:
        white_img=pygame.Surface((100,100))
        white_img.fill((255,255,255))
        black_img=pygame.Surface((100,100))
        black_img.fill((0,0,0))
    
    button_width=400
    button_height=100
    white_rect=pygame.Rect(300,450,button_width,button_height)
    black_rect=pygame.Rect(300,550,button_width,button_height)
    
    selected_turn=None
    running=True
    
    while running and selected_turn is None:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
                selected_turn=True
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                pos=event.pos
                if white_rect.collidepoint(pos):
                    selected_turn=False 
                    running=False
                elif black_rect.collidepoint(pos):
                    selected_turn=True  
                    running=False

        screen.blit(title_page,(0,0))

        title_text=title_font.render("Choose Your Side",True,GREY)
        screen.blit(title_text, (200,380))
        
        translucent_surface=pygame.Surface((button_width,button_height),pygame.SRCALPHA)
        translucent_surface.fill((127,127,127,180))
        
        screen.blit(translucent_surface,(white_rect.x,white_rect.y))
        screen.blit(translucent_surface,(black_rect.x,black_rect.y))
        
        screen.blit(white_img,(white_rect.x+10,white_rect.y))
        screen.blit(black_img,(black_rect.x+10,black_rect.y))
        
        white_text=font.render('Play as White',True,WHITE)
        black_text=font.render('Play as Black',True,WHITE)
        
        screen.blit(white_text,(white_rect.x+100,white_rect.y+25))
        screen.blit(black_text,(black_rect.x+100,black_rect.y+25))
        
        pygame.display.flip()
    
    return selected_turn
