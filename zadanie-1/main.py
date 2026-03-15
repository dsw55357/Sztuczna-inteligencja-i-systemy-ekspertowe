
"""

Na przydzielonej mapie pokazać działanie algorytmu do wyszukiwania najkrótszej ścieżki zaczynając od przydzielonego punktu startowego. Zakładamy, że istnieje możliwość przemieszczania się w obie strony między dowolnymi punktami na mapie a koszt przejścia to odległość w układzie współrzędnych.

- startujemy z punktu F,
- przechodzi przez wszystkie punkty,
- na każdym kroku pokazuje pełne obliczenia,
- wybiera następny punkt metodą ruletki,
- na końcu wypisuje kolejność odwiedzin i długość ścieżki.

"""
import pygame
import math
import random
import sys

from ant_simulation import build_probability_table, distance, roulette_select
from simulation_state import StepState, ProbabilityRow

pygame.init()

# =========================
# Dane wejściowe
# =========================
# mapa punktów
points = {
    "A": (1, 1),
    "B": (5, 8),
    "C": (7, 12),
    "D": (2, 9),
    "E": (7, 2),
    "F": (1, 12),
    "G": (4, 2),
}

# ---------------------------------
# Ustawienia okna
# ---------------------------------
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Algorytm mrówkowy - mapa punktów")

clock = pygame.time.Clock()

# ---------------------------------
# Kolory
# ---------------------------------

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (180, 180, 180)
LIGHT_GRAY = (230, 230, 230)
BLUE = (70, 130, 255)
RED = (220, 70, 70)
GREEN = (60, 180, 75)
ORANGE = (255, 165, 0)
PURPLE = (150, 80, 200)

# Menu
MENU_BG = (0, 0, 0)
MENU_TEXT = (0, 255, 120)
MENU_BORDER = (0, 180, 90)

# ---------------------------------
# Parametry rysowania
# ---------------------------------
MARGIN = 80
POINT_RADIUS = 8

font = pygame.font.SysFont("arial", 22)
small_font = pygame.font.SysFont("arial", 18)
tiny_font = pygame.font.SysFont("consolas", 16)

# Menu
menu_font = pygame.font.SysFont("consolas", 18)
menu_title_font = pygame.font.SysFont("consolas", 22, bold=True)


def transform_points(points_dict, width, height, margin):
    """
    Przekształca współrzędne z układu zadania do współrzędnych ekranu.
    Zachowujemy proporcje i odwracamy oś Y, żeby 'góra mapy' była u góry okna.
    """
    xs = [p[0] for p in points_dict.values()]
    ys = [p[1] for p in points_dict.values()]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    map_width = max_x - min_x
    map_height = max_y - min_y

    drawable_width = width - 2 * margin
    drawable_height = height - 2 * margin

    scale_x = drawable_width / map_width if map_width != 0 else 1
    scale_y = drawable_height / map_height if map_height != 0 else 1
    scale = min(scale_x, scale_y)

    screen_points = {}
    for name, (x, y) in points_dict.items():
        screen_x = margin + (x - min_x) * scale
        screen_y = height - margin - (y - min_y) * scale
        screen_points[name] = (int(screen_x), int(screen_y))

    return screen_points

screen_points = transform_points(points, WIDTH, HEIGHT, MARGIN)


def transform_points(points_dict, width, height, margin):
    """
    Przekształca współrzędne z układu zadania do współrzędnych ekranu.
    Zachowujemy proporcje i odwracamy oś Y, żeby 'góra mapy' była u góry okna.
    """
    xs = [p[0] for p in points_dict.values()]
    ys = [p[1] for p in points_dict.values()]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    map_width = max_x - min_x
    map_height = max_y - min_y

    drawable_width = width - 2 * margin
    drawable_height = height - 2 * margin

    scale_x = drawable_width / map_width if map_width != 0 else 1
    scale_y = drawable_height / map_height if map_height != 0 else 1
    scale = min(scale_x, scale_y)

    screen_points = {}
    for name, (x, y) in points_dict.items():
        screen_x = margin + (x - min_x) * scale
        screen_y = height - margin - (y - min_y) * scale
        screen_points[name] = (int(screen_x), int(screen_y))

    return screen_points

screen_points = transform_points(points, WIDTH, HEIGHT, MARGIN)

# punkt startowy
start = "F"
# parametry algorytmu mrówkowego
alpha = 2 # wpływ feromonu
beta = 3 # wpływ heurystyki (1/d)
initial_pheromone = 1.0

# Dla powtarzalności wyników
random.seed(42)

def print_step(step_no, current, rows, rand_value, chosen):
    print("=" * 90)
    print(f"KROK {step_no}")
    print(f"Aktualny punkt: {current}")
    print("-" * 90)
    print(f"{'Miasto':<8}{'d':>12}{'eta=1/d':>14}{'tau^alpha':>14}{'eta^beta':>14}{'waga':>14}{'p':>12}{'P_kum':>12}")
    print("-" * 90)

    for r in rows:
        print(
            f"{r['city']:<8}"
            f"{r['d']:>12.6f}"
            f"{r['eta']:>14.6f}"
            f"{r['tau_alpha']:>14.6f}"
            f"{r['eta_beta']:>14.6f}"
            f"{r['weight']:>14.6f}"
            f"{r['p']:>12.6f}"
            f"{r['cumulative']:>12.6f}"
        )

    print("-" * 90)
    print(f"Wylosowane r = {rand_value:.6f}")
    print(f"Wybrano następny punkt: {chosen}")
    print()

current = start
visited = [start] # lista odwiedzonych punktów
unvisited = set(points.keys()) # zbiór nieodwiedzonych punktów
unvisited.remove(start) # usuwamy punkt startowy z nieodwiedzonych

path = [start]
total_length = 0.0
step_no = 1

current_rows = []
last_random_value = None
last_choice = None
finished = False

history = []

AUTO_STEP_MS = 1800
last_step_time = pygame.time.get_ticks()

# =========================================================
# FUNKCJE GRAFICZNE
# =========================================================
MAP_AREA = pygame.Rect(40, 40, 650, 700)
INFO_AREA = pygame.Rect(720, 40, 440, 700)
POINT_RADIUS = 10

def draw_layout():
    screen.fill(WHITE)
    pygame.draw.rect(screen, LIGHT_GRAY, MAP_AREA, border_radius=8)
    pygame.draw.rect(screen, LIGHT_GRAY, INFO_AREA, border_radius=8)
    pygame.draw.rect(screen, BLACK, MAP_AREA, 2, border_radius=8)
    pygame.draw.rect(screen, BLACK, INFO_AREA, 2, border_radius=8)

def draw_grid():
    step = 50
    for x in range(MAP_AREA.left, MAP_AREA.right, step):
        pygame.draw.line(screen, (111, 235, 111), (x, MAP_AREA.top), (x, MAP_AREA.bottom), 1)
    for y in range(MAP_AREA.top, MAP_AREA.bottom, step):
        pygame.draw.line(screen, (111, 235, 111), (MAP_AREA.left, y), (MAP_AREA.right, y), 1)


def perform_one_step():
    global current, visited, unvisited, path, total_length
    global step_no, current_rows, last_random_value, last_choice, finished

    global history

    if finished:
        return

    current_before = current
    visited_before = visited.copy()
    path_before = path.copy()
    total_length_before = total_length
    unvisited_before = sorted(list(unvisited))

    # Jeżeli zostały jeszcze punkty do odwiedzenia
    if unvisited:
        candidates = sorted(list(unvisited))
        current_rows = build_probability_table(points, current, candidates, alpha, beta, pheromone=initial_pheromone)
        chosen, rand_value = roulette_select(current_rows)

        step_distance = distance(points, current, chosen)
        total_length += distance(points, current, chosen)
        #total_length += step_distance
        visited.append(chosen)
        unvisited.remove(chosen)
        path.append(chosen)

        current = chosen
        last_random_value = rand_value
        last_choice = chosen
        step_no += 1

        history.append(
            StepState(
                step_no=step_no,
                current_before=current_before,
                current_after=current,
                visited_before=visited_before,
                visited_after=visited.copy(),
                unvisited_before=unvisited_before,
                rows=[...],
                rand_value=rand_value,
                chosen=chosen,
                path_before=path_before,
                path_after=path.copy(),
                total_length_before=total_length_before,
                total_length_after=total_length,
                step_distance=step_distance,
            )
        )

    # Jeśli odwiedziliśmy już wszystkie, wracamy do startu
    if not unvisited and not finished:
        if current != start:
            total_length += distance(points, current, start)
            path.append(start)
            last_choice = start
            last_random_value = None
            current = start
            current_rows = []
        finished = True

def draw_path(path):
    if len(path) < 2:
        return

    for i in range(len(path) - 1):
        p1 = screen_points[path[i]]
        p2 = screen_points[path[i + 1]]
        pygame.draw.line(screen, GREEN, p1, p2, 4)

def draw_candidate_edges(current, rows):
    if not rows:
        return

    p1 = screen_points[current]
    for row in rows:
        p2 = screen_points[row["city"]]
        pygame.draw.line(screen, GRAY, p1, p2, 1)

        mx = (p1[0] + p2[0]) // 2
        my = (p1[1] + p2[1]) // 2
        prob_text = tiny_font.render(f"p={row['p']:.3f}", True, BLACK)
        screen.blit(prob_text, (mx + 5, my + 5))


def draw_points(visited, current):
    for name, (x, y) in screen_points.items():
        if name == current:
            color = RED
        elif name in visited:
            color = ORANGE
        elif name == start:
            color = PURPLE
        else:
            color = BLUE

        pygame.draw.circle(screen, color, (x, y), POINT_RADIUS)
        pygame.draw.circle(screen, BLACK, (x, y), POINT_RADIUS, 2)

        label = small_font.render(f"{name} {points[name]}", True, BLACK)
        screen.blit(label, (x + 12, y - 12))

def draw_ant(current):
    if current is None:
        return
    x, y = screen_points[current]
    pygame.draw.circle(screen, BLACK, (x, y), 5)

def draw_legend():
    lines = [
        "Legenda:",
        "czerwony - aktualny punkt",
        "pomarańczowy - odwiedzony",
        "fioletowy - punkt startowy",
        "zielona linia - zbudowana trasa",
        "szare linie - aktualni kandydaci",
        "ESC - wyjście",
        "SPACJA - wykonaj krok ręcznie",
    ]

    x = MAP_AREA.left + 10
    y = MAP_AREA.top + 10
    for line in lines:
        screen.blit(small_font.render(line, True, BLACK), (x, y))
        y += 22

def draw_menu_():

    panel = pygame.Rect(
        MAP_AREA.left + 20,
        MAP_AREA.top + 20,
        320,
        220
    )

    # tło
    pygame.draw.rect(
        screen,
        MENU_BG,
        panel,
        border_radius=12
    )

    # ramka
    pygame.draw.rect(
        screen,
        MENU_BORDER,
        panel,
        width=2,
        border_radius=12
    )

    x = panel.left + 15
    y = panel.top + 15

    title = menu_title_font.render("POMOC / STEROWANIE", True, MENU_TEXT)
    screen.blit(title, (x, y))
    y += 35

    lines = [
        "F1     - pokaz / ukryj menu",
        "SPACE  - wykonaj krok algorytmu",
        "ESC    - wyjście",
        "",
        "Legenda:",
        "czerwony     - aktualny punkt",
        "pomarańczowy - odwiedzony punkt",
        "fioletowy    - punkt startowy",
        "zielona linia- zbudowana trasa",
        "szare linie  - kandydaci"
    ]

    for line in lines:
        text = menu_font.render(line, True, MENU_TEXT)
        screen.blit(text, (x, y))
        y += 20


def draw_menu():

    lines = [
        "F1     - pokaz / ukryj menu",
        "SPACE  - wykonaj krok",
        "ESC    - wyjście",
        "",
        "Legenda:",
        "czerwony     - aktualny punkt",
        "pomarańczowy - odwiedzony punkt",
        "fioletowy    - punkt startowy",
        "zielona linia- zbudowana trasa",
        "szare linie  - kandydaci"
    ]

    rendered = [menu_font.render(line, True, MENU_TEXT) for line in lines]

    padding_x = 20
    padding_y = 20
    line_spacing = 6

    max_width = max(text.get_width() for text in rendered)
    line_height = rendered[0].get_height()

    panel_width = max_width + padding_x * 2
    panel_height = len(rendered) * (line_height + line_spacing) + padding_y * 2

    panel = pygame.Rect(
        MAP_AREA.left + 20,
        MAP_AREA.top + 20,
        panel_width,
        panel_height
    )

    # tło
    pygame.draw.rect(screen, MENU_BG, panel, border_radius=12)

    # ramka
    pygame.draw.rect(screen, MENU_BORDER, panel, width=2, border_radius=12)

    x = panel.left + padding_x
    y = panel.top + padding_y

    for text in rendered:
        screen.blit(text, (x, y))
        y += line_height + line_spacing

def draw_info_panel(step_no, current, visited, total_length, rows, rand_value, chosen, finished):
    x = INFO_AREA.left + 15
    y = INFO_AREA.top + 15

    title = font.render("Stan symulacji", True, BLACK)
    screen.blit(title, (x, y))
    y += 35

    lines = [
        f"Krok: {step_no}",
        f"Aktualny punkt: {current}",
        f"Odwiedzone: {' -> '.join(visited)}",
        f"Długość trasy: {total_length:.3f}",
    ]

    if rand_value is not None:
        lines.append(f"Los ruletki r = {rand_value:.6f}")
    if chosen is not None:
        lines.append(f"Wybrano: {chosen}")
    if finished:
        lines.append("Status: zakończono cykl")

    for line in lines:
        txt = small_font.render(line, True, BLACK)
        screen.blit(txt, (x, y))
        y += 26

    y += 10
    subtitle = font.render("Tabela prawdopodobieństw", True, BLACK)
    screen.blit(subtitle, (x, y))
    y += 30

    header = "Miasto   d     eta    waga     p    P_kum"
    screen.blit(tiny_font.render(header, True, BLACK), (x, y))
    y += 22

    for row in rows:
        line = (
            f"{row['city']:<5}"
            f"{row['d']:>6.3f}"
            f"{row['eta']:>7.3f}"
            f"{row['weight']:>8.4f}"
            f"{row['p']:>7.3f}"
            f"{row['cumulative']:>7.3f}"
        )
        screen.blit(tiny_font.render(line, True, BLACK), (x, y))
        y += 20



def main():
    print("Hello, World!")  
    # =========================
    # Główna logika mrówki
    # =========================
    global current
    global total_length
    step = 1
    history_index = 0 # do przeglądania historii kroków
    show_help = False
    running = True
    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    perform_one_step()
                    last_step_time = now
                elif event.key == pygame.K_F1:
                    show_help = not show_help
                # Przegląd stanów algorytmu
                elif event.key == pygame.K_RIGHT:
                    history_index = min(history_index + 1, len(history)-1)
                elif event.key == pygame.K_LEFT:
                    history_index = max(history_index - 1, 0)



        draw_layout()
        draw_grid()
        draw_path(path)
        draw_candidate_edges(current, current_rows)
        draw_points(visited, current)
        draw_ant(current)

        if show_help:
            #draw_legend()
            draw_menu()
        
        draw_info_panel(
            step_no=step_no,
            current=current,
            visited=visited,
            total_length=total_length,
            rows=current_rows,
            rand_value=last_random_value,
            chosen=last_choice,
            finished=finished
        )

        pygame.display.flip()
        clock.tick(60)

    # Pętla działa tak długo, jak długo istnieją jeszcze nieodwiedzone punkty.
    while unvisited:
        # przygotowanie kandydatów
        # zamieniamy zbiór na posortowaną listę
        candidates = sorted(list(unvisited))  # dla czytelnej kolejności w tabeli
        # obliczenie tabeli decyzji
        # Dla aktualnego punktu i listy kandydatów liczymy:
        # odległości,
        # heurystyki,
        # wagi,
        # prawdopodobieństwa,
        # sumy skumulowane
        rows = build_probability_table(points, current, candidates, alpha, beta, pheromone=1.0) #
        # wybór metodą ruletki
        # Mrówka podejmuje decyzję na podstawie:
        # tabeli prawdopodobieństw,
        # wylosowanej liczby.
        chosen, rand_value = roulette_select(rows)

        # drukowanie kroków - pokazanie wyników
        print_step(step, current, rows, rand_value, chosen)

        # aktualizacja długości trasy
        # Do sumy dokładamy długość nowo przebytego odcinka
        total_length += distance(current, chosen)
        # aktualizacja list odwiedzin
        # nowy punkt trafia do listy odwiedzonych,
        # znika ze zbioru nieodwiedzonych.   
        visited.append(chosen)
        unvisited.remove(chosen)
        # przesunięcie mrówki
        # Nowo wybrane miasto staje się aktualnym położeniem mrówki
        current = chosen
        # zwiększenie numeru kroku
        step += 1

    # Powrót do startu
    # liczona jest odległość z ostatniego punktu do startu,
    return_distance = distance(points, current, start)
    # odległość ta jest dodawana do całkowitej długości trasy,
    total_length += return_distance
    # start dopisywany jest na końcu listy visited, aby powstał pełny cykl.
    visited.append(start)

    print("=" * 90)
    print("PODSUMOWANIE")
    print("=" * 90)
    print("Kolejność odwiedzonych punktów:")
    print(" -> ".join(visited))
    print(f"Długość ścieżki: {total_length:.6f}")
    print(f"Ostatni odcinek powrotu {current} -> {start}: {return_distance:.6f}")

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()

"""

W praktyce można to zrobić tak, żeby program pełnił jednocześnie rolę obliczeniową i dokumentacyjną.

2. Liczenie odległości

Koszt przejścia to odległość euklidesowa:

3. Prawdopodobieństwo wyboru kolejnego punktu

Dla pojedynczej mrówki, jeśli nie masz podanych różnych feromonów początkowych, najczęściej przyjmuje się:

4. Koło ruletki

Po obliczeniu prawdopodobieństw robisz sumy skumulowane i losujesz liczbę r∈[0,1).
Pierwszy przedział, do którego wpada r, wskazuje kolejny punkt.

"""