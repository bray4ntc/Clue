import pygame
import os
from z3 import *
import random

# Inicializar Pygame
pygame.init()

# Constantes
WINDOW_SIZE = 600  # Reducido de 800 a 600
BOARD_SIZE = 540   # Reducido proporcionalmente
ROOM_SIZE = BOARD_SIZE // 3
CORRIDOR_SIZE = BOARD_SIZE // 20
BOARD_MARGIN = (WINDOW_SIZE - BOARD_SIZE) // 2

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
GREEN = (0, 100, 0)
BEIGE = (245, 222, 179)
ORANGE = (255, 140, 0)
DARK_RED = (139, 0, 0)
YELLOW = (255, 215, 0)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
BLUE=(0, 0, 139)

# Configuración de la ventana
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 60))
pygame.display.set_caption('Clue - Detective Game')

# Fuentes
FONT_LARGE = pygame.font.Font(None, 28)
FONT_SMALL = pygame.font.Font(None, 20)

class GameState:
    MENU = 0
    PLAYING = 1
    SOLVED = 2

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.is_active = True

    def draw(self, screen):
        if not self.is_active:
            actual_color = GRAY
        else:
            actual_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, actual_color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        font = pygame.font.Font(None, 28)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if not self.is_active:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self.rect.collidepoint(event.pos)
        return False

class GameSymbol:
    def __init__(self, name):
        self.name = name
        self.z3_var = Bool(name)

class Room:
    def __init__(self, name, x, y, color):
        self.name = name
        self.rect = pygame.Rect(x, y, ROOM_SIZE - 10, ROOM_SIZE - 10)
        self.color = color
        self.symbol = GameSymbol(name)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(screen, DARK_RED, self.rect, 3)
        
        corner_size = 8
        corners = [
            (self.rect.topleft, (self.rect.left + corner_size, self.rect.top), (self.rect.left, self.rect.top + corner_size)),
            (self.rect.topright, (self.rect.right - corner_size, self.rect.top), (self.rect.right, self.rect.top + corner_size)),
            (self.rect.bottomleft, (self.rect.left + corner_size, self.rect.bottom), (self.rect.left, self.rect.bottom - corner_size)),
            (self.rect.bottomright, (self.rect.right - corner_size, self.rect.bottom), (self.rect.right, self.rect.bottom - corner_size))
        ]
        
        for corner in corners:
            pygame.draw.circle(screen, RED, corner[0], 4)
        
        text = FONT_SMALL.render(self.name, True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

class ClueBoard:
    def __init__(self):
        self.rooms = [
            Room("KITCHEN", BOARD_MARGIN + 2 * ROOM_SIZE, BOARD_MARGIN, BEIGE),
            Room("BALL ROOM", BOARD_MARGIN + ROOM_SIZE, BOARD_MARGIN, RED),
            Room("CONSERVATORY", BOARD_MARGIN, BOARD_MARGIN, GREEN),
            Room("DINING ROOM", BOARD_MARGIN + 2 * ROOM_SIZE, BOARD_MARGIN + ROOM_SIZE, BROWN),
            Room("BILLIARD ROOM", BOARD_MARGIN, BOARD_MARGIN + ROOM_SIZE, PURPLE),
            Room("LIBRARY", BOARD_MARGIN, BOARD_MARGIN + 2 * ROOM_SIZE, BROWN),
            Room("HALL", BOARD_MARGIN + ROOM_SIZE, BOARD_MARGIN + 2 * ROOM_SIZE, YELLOW),
            Room("LOUNGE", BOARD_MARGIN + 2 * ROOM_SIZE, BOARD_MARGIN + 2 * ROOM_SIZE, GREEN),
            Room("STUDY", BOARD_MARGIN, BOARD_MARGIN + 2 * ROOM_SIZE, BROWN)
        ]
        
    def draw(self, screen):
        board_rect = pygame.Rect(BOARD_MARGIN, BOARD_MARGIN, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(screen, BEIGE, board_rect)
        
        for x in range(BOARD_MARGIN, BOARD_MARGIN + BOARD_SIZE + 1, BOARD_SIZE // 24):
            for y in range(BOARD_MARGIN, BOARD_MARGIN + BOARD_SIZE + 1, BOARD_SIZE // 24):
                pygame.draw.rect(screen, (218, 165, 32), (x, y, BOARD_SIZE // 24, BOARD_SIZE // 24), 1)
        
        for room in self.rooms:
            room.draw(screen)
        
        logo_size = BOARD_SIZE // 4
        logo_rect = pygame.Rect(WINDOW_SIZE//2 - logo_size//2, WINDOW_SIZE//2 - logo_size//2, 
                               logo_size, logo_size)
        pygame.draw.rect(screen, ORANGE, logo_rect)
        logo_text = FONT_LARGE.render("CLUE", True, BLACK)
        logo_text_rect = logo_text.get_rect(center=logo_rect.center)
        screen.blit(logo_text, logo_text_rect)

class ClueGame:
    def __init__(self):
        self.board = ClueBoard()
        self.kb = KnowledgeBase()
        self.suspects = [GameSymbol(name) for name in ["Miss Scarlet", "Colonel Mustard", "Mrs White"]]
        self.weapons = [GameSymbol(name) for name in ["Cuchillo", "Revolver", "Veneno"]]
        
        button_y = WINDOW_SIZE + 15
        self.solve_button = Button(WINDOW_SIZE//4 - 50, button_y, 100, 30, "Solve", RED, DARK_RED)
        self.play_button = Button(WINDOW_SIZE//2 - 50, button_y, 100, 30, "Play", GREEN, (0, 100, 0))
        self.menu_button = Button(WINDOW_SIZE*3//4 - 50, button_y, 100, 30, "Menu", BLUE, (0, 0, 139))
        
        self.init_knowledge_base()
        
        self.running = True
        self.game_state = GameState.MENU
        self.solution = None
        self.player_guesses = []
        self.attempts_left = 3

    def init_knowledge_base(self):
        self.kb.add(exactly_one([s.z3_var for s in self.suspects]))
        self.kb.add(exactly_one([w.z3_var for w in self.weapons]))
        self.kb.add(exactly_one([r.symbol.z3_var for r in self.board.rooms]))

    def solve(self):
        if self.kb.evaluate():
            model = self.kb.model()
            return {
                'suspect': next(s for s in self.suspects if model[s.z3_var]),
                'weapon': next(w for w in self.weapons if model[w.z3_var]),
                'room': next(r for r in self.board.rooms if model[r.symbol.z3_var])
            }
        return None

    def make_guess(self):
        suspect = random.choice(self.suspects)
        weapon = random.choice(self.weapons)
        room = random.choice(self.board.rooms)
        return {'suspect': suspect, 'weapon': weapon, 'room': room}

    def check_guess(self, guess):
        if not self.solution:
            self.solution = self.solve()
        
        correct = (guess['suspect'].name == self.solution['suspect'].name and
                  guess['weapon'].name == self.solution['weapon'].name and
                  guess['room'].name == self.solution['room'].name)
        return correct

    def draw(self, screen):
        screen.fill(WHITE)
        self.board.draw(screen)
        
        self.solve_button.draw(screen)
        self.play_button.draw(screen)
        self.menu_button.draw(screen)
        
        if self.game_state == GameState.PLAYING:
            text = f"Attempts left: {self.attempts_left}"
            text_surface = FONT_SMALL.render(text, True, BLACK)
            screen.blit(text_surface, (10, 10))
            
            for i, guess in enumerate(self.player_guesses):
                y_pos = 30 + i * 20
                guess_text = f"Guess {i+1}: {guess['suspect'].name} with {guess['weapon'].name} in {guess['room'].name}"
                text_surface = FONT_SMALL.render(guess_text, True, BLACK)
                screen.blit(text_surface, (10, y_pos))
        
        elif self.game_state == GameState.SOLVED:
            y_pos = 10
            texts = [
                f"Murderer: {self.solution['suspect'].name}",
                f"Weapon: {self.solution['weapon'].name}",
                f"Room: {self.solution['room'].name}"
            ]
            for text in texts:
                text_surface = FONT_SMALL.render(text, True, BLACK)
                screen.blit(text_surface, (10, y_pos))
                y_pos += 20

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEMOTION:
                    for button in [self.solve_button, self.play_button, self.menu_button]:
                        button.handle_event(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.solve_button.handle_event(event):
                        self.solution = self.solve()
                        self.game_state = GameState.SOLVED
                    elif self.play_button.handle_event(event):
                        if self.game_state != GameState.PLAYING:
                            self.game_state = GameState.PLAYING
                            self.attempts_left = 3
                            self.player_guesses = []
                            self.solution = self.solve()
                        else:
                            guess = self.make_guess()
                            self.player_guesses.append(guess)
                            self.attempts_left -= 1
                            
                            if self.check_guess(guess) or self.attempts_left == 0:
                                self.game_state = GameState.SOLVED
                    elif self.menu_button.handle_event(event):
                        self.game_state = GameState.MENU
                        self.solution = None
                        self.player_guesses = []

            self.draw(screen)
            pygame.display.flip()

class KnowledgeBase:
    def __init__(self):
        self.solver = Solver()

    def add(self, rule):
        self.solver.add(rule)

    def evaluate(self):
        return self.solver.check() == sat

    def model(self):
        if self.evaluate():
            return self.solver.model()
        return None

def exactly_one(variables):
    return And(Or(variables), 
               *[Not(And(v1, v2)) for i, v1 in enumerate(variables) 
                 for v2 in variables[i+1:]])

if __name__ == "__main__":
    game = ClueGame()
    game.run()
    pygame.quit()
