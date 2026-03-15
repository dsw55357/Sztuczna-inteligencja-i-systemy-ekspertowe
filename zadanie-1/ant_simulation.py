import random
import math
from simulation_state import StepState, ProbabilityRow


# =========================
# Funkcje pomocnicze
# Odległość jest:
# kosztem przejścia między punktami,
# podstawą do wyznaczenia heurystyki:
# eta = 1/d,
# Czyli im bliżej punkt leży, tym większa heurystyka i zwykle większe prawdopodobieństwo wyboru.
# =========================
def distance(points, p1, p2):
    x1, y1 = points[p1]
    x2, y2 = points[p2]
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# =========================
# Główna logika mrówki
# Cel funkcji:
# Dla aktualnego miasta i zbioru miast nieodwiedzonych obliczyć:
# odległości,
# heurystyki,
# wagi,
# prawdopodobieństwa wyboru,
# sumy skumulowane do ruletki.
# Parametry:
# current — aktualne położenie mrówki,
# unvisited — zbiór punktów, których mrówka jeszcze nie odwiedziła,
# pheromone=1.0 — przyjęta wartość początkowego feromonu.
# =========================
def build_probability_table(points, current, unvisited, alpha, beta, pheromone=1.0):
    """
    Zwraca listę słowników z obliczeniami dla kandydatów:
    d, eta, tau^alpha, eta^beta, weight, p, cumulative
    """
    # Będzie tu przechowywana tabela kandydatów.
    # Każdy element listy rows to jeden słownik z informacjami o danym mieście.
    rows = []

    # liczenie wag
    # obliczenie parametrów dla każdego kandydata
    for city in unvisited:
        # obliczanie odległości i heurystyki
        # Dla każdego nieodwiedzonego miasta liczymy:
        # odległość d do aktualnego miasta,
        d = distance(points, current, city) # odległość
        # heurystyka eta = 1/d,
        eta = 1.0 / d
        # wpływ feromonu
        tau_alpha = pheromone ** alpha 
        # wpływ heurystyki
        eta_beta = eta ** beta 
        # waga przejścia
        # Ta wartość jeszcze nie jest prawdopodobieństwem, ale mówi, jak atrakcyjny jest ruch do danego miasta.
        weight = tau_alpha * eta_beta # waga kandydata do wyboru

        # zapis wyników do tabeli
        # Każdy kandydat zostaje zapisany jako słownik zawierający:
        # nazwę miasta,
        # odległość,
        # heurystykę,
        # wpływ feromonu,
        # wpływ heurystyki,
        # wagę
        rows.append({
            "city": city,
            "d": d,
            "eta": eta,
            "tau_alpha": tau_alpha,
            "eta_beta": eta_beta,
            "weight": weight
        })

    # sumowanie wag
    # Liczymy mianownik wzoru na prawdopodobieństwo:  Suma wag wszystkich kandydatów, czyli sumę tau^alpha * eta^beta dla wszystkich miast w zbiorze unvisited.
    total_weight = sum(r["weight"] for r in rows)

    cumulative = 0.0
    # obliczanie prawdopodobieństw i sum skumulowanych
    for r in rows:
        # Dla każdego miasta liczymy prawdopodobieństwo wyboru:  p = waga / suma wag.  Następnie tworzymy sumę skumulowaną, która będzie używana do wyboru metodą ruletki.
        r["p"] = r["weight"] / total_weight
        cumulative += r["p"]
        # sumę skumulowaną:  cumulative = poprzednia suma + p dla aktualnego miasta. Ta suma skumulowana pozwala nam łatwo wybrać miasto, losując liczbę r i sprawdzając, do którego przedziału należy.
        r["cumulative"] = cumulative

    return rows


# =========================
# Koło ruletki
# Ta funkcja realizuje ostateczny wybór następnego punktu.
# Losujemy liczbę r∈[0,1) i sprawdzamy, do którego przedziału skumulowanego należy.
# Każde miasto dostaje przedział długości równej swojemu prawdopodobieństwu.
# Losowanie wskazuje jeden z tych przedziałów.
# im większe p,
# tym większy odcinek na ruletce,
# tym większa szansa wyboru.
# Funkcja zwraca:
# nazwę wybranego miasta,
# wartość losowania
# =========================
def roulette_select(rows):
    """
    Wybór miasta metodą koła ruletki.
    """
    r = random.random()
    for row in rows:
        if r <= row["cumulative"]:
            return row["city"], r # zwracamy też wylosowaną liczbę dla celów dokumentacyjnych
    # Teoretycznie suma skumulowana powinna kończyć się dokładnie na 1, ale przez błędy zaokrągleń komputerowych może wyjść np. 0.999999999.
    # Wtedy wybieramy ostatni element.
    return rows[-1]["city"], r  # zabezpieczenie numeryczne


def build_simulation_history(points, start, alpha, beta, pheromone=1.0, seed=42):
    random.seed(seed)

    history = []

    current = start
    visited = [start]
    unvisited = set(points.keys())
    unvisited.remove(start)

    path = [start]
    total_length = 0.0
    step_no = 1

    while unvisited:
        candidates = sorted(list(unvisited))
        rows = build_probability_table(points, current, candidates, alpha, beta, pheromone)
        chosen, rand_value = roulette_select(rows)

        step_distance = distance(points, current, chosen)
        new_total_length = total_length + step_distance
        new_visited = visited + [chosen]
        new_path = path + [chosen]

        history.append(
            StepState(
                step_no=step_no,
                current_before=current,
                current_after=chosen,
                visited_before=visited.copy(),
                visited_after=new_visited.copy(),
                unvisited_before=candidates.copy(),
                rows=rows.copy(),
                rand_value=rand_value,
                chosen=chosen,
                path_before=path.copy(),
                path_after=new_path.copy(),
                total_length_before=total_length,
                total_length_after=new_total_length,
                step_distance=step_distance
            )
        )

        total_length = new_total_length
        visited = new_visited
        path = new_path
        unvisited.remove(chosen)
        current = chosen
        step_no += 1

    # powrót do startu
    return_distance = distance(points, current, start)
    final_path = path + [start]

    history.append(
        StepState(
            step_no=step_no,
            current_before=current,
            current_after=start,
            visited_before=visited.copy(),
            visited_after=visited.copy() + [start],
            unvisited_before=[],
            rows=[],
            rand_value=None,
            chosen=start,
            path_before=path.copy(),
            path_after=final_path,
            total_length_before=total_length,
            total_length_after=total_length + return_distance,
            step_distance=return_distance
        )
    )

    return history