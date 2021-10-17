import time
import queue

import pygame
import copy
from pygame import mixer

# Init 4 hướng
U = (0, -1, "u")
D = (0, 1, "d")
L = (-1, 0, "l")
R = (1, 0, "r")
direction = [U, D, L, R]
# -------------


# Object Matrix Sokoban
class Game:
    DIRECTION_LIST = {'l': (-1, 0), 'r': (1, 0), 'u': (0, -1),
                      'd': (0, 1), 'L': (-1, 0), 'R': (1, 0), 'U': (0, -1), 'D': (0, 1)}

    # Init và nhập vào các biến hỗ trợ giải thuật từ input
    def __init__(self, filename, level_game):
        # Init các biến hỗ trợ giải thuật
        self.deadlock_table = []  # Lưu các dead lock của level
        self.listgoal = []  # Lưu các goal của level
        self.goaldistance = []  # Lưu các matrix chứa goal pull distance của các vị trí của level
        self.stack_move = queue.LifoQueue()
        self.matrix = []
        # --------------------------------

        # Đọc file input, lưu input vào các biến hỗ trợ
        file = open(filename, 'r')
        level_found = False
        for line in file:
            # Lưu matrix
            if not level_found:
                if "Level " + str(level_game) == line.strip():
                    level_found = True
            else:
                if line.strip() != "":
                    row = []
                    for c in line:
                        if c != '\n':
                            row.append(c)
                        elif c == '\n':  
                            continue
                    self.matrix.append(row)
                else:
                    break
       
        x = 0
        y = 0
        for row in self.matrix:
            for pos in row:
                if pos == '@' or pos == '+':
                    # Lấy tọa độ của worker
                    self.worker_x = x
                    self.worker_y = y
                if pos == '.' or pos == '+' or pos == '*':
                    # Lấy tọa độ các goal
                    self.listgoal.append((x, y))
                x = x + 1
            y = y + 1
            x = 0

        x = 0
        y = 0
        for k in range(len(self.listgoal)):
            mymatrix = []
            for i in self.matrix:
                row = []
                for j in i:
                    a = (x, y)
# Set các vị trí không phải goal ban đầu có goal pull distance = 100000, các vị trí là goal có goal pull distance = 0
                    if a != self.listgoal[k]:
                        row.append(100000)
                    else:
                        row.append(0)
                    x = x + 1
                mymatrix.append(row)
                y = y + 1
                x = 0
            self.goaldistance.append(mymatrix)
            y = 0
        # ----------------------------------------------

        # Tính toán giá trị goal pull distance = hàm set_goaldistance
        self.set_goaldistance()
        # ------------------------------------------------------------
    # ----------------------------------------------------

    def set_goaldistance(self):
        # Tính toán khoảng cách các vị trí đang xét tới goal
        #Chúng tôi thực hiện điều này bằng cách sử dụng thuật toán breadth-first search để "kéo" một hộp từ đích, 
        #tức là kiểm tra từng hướng trong bốn hướng chính xem một hộp được đặt trên hình vuông theo hướng đó có thể được đẩy vào mục tiêu hay không
        queue = []
        # Tìm các Goal position và thêm vào queue
        for k in self.goaldistance:
            for i in range(len(k)):
                for j in range(len(k[i])):
                    if k[i][j] == 0:
                        queue.append((j, i))
            #Tính các khoảng cách từ vị trí đến các goal cho đến khi queue trống
            while len(queue):
                position = queue.pop(0)
                for d in direction:
                    boxPosition = (position[0] + d[0], position[1] + d[1])
                    playerPosition = (position[0] + d[0] * 2, position[1] + d[1] * 2)
                    if k[boxPosition[1]][boxPosition[0]] == 100000:
                        if self.matrix[boxPosition[1]][boxPosition[0]] != '#' and self.matrix[playerPosition[1]][
                            playerPosition[0]] != '#':
                            k[boxPosition[1]][boxPosition[0]] = k[position[1]][position[0]] + 1
                            queue.append(boxPosition)

        # Thêm vị trí của deadlock
        x = 0
        y = 0
        for i in self.matrix:
            for j in i:
                check = True
                for k in range(len(self.goaldistance)):
                    if self.goaldistance[k][y][x] != 100000:
                        check = False
                        break
                if check:
                    a = (x, y)
                    if self.matrix[y][x] != '#':
                        self.deadlock_table.append(a)
                x = x + 1
            y = y + 1
            x = 0

    # Trả về kích thước của matrix
    def load_size(self):
        x = 0
        y = len(self.matrix)
        for row in self.matrix:
            if len(row) > x:
                x = len(row)
        return x * 40, y * 40

    # Trả về matrix
    def get_matrix(self):
        return self.matrix

    # Trả về vị trí x, y trong matrix
    def get_content(self, x, y):
        return self.matrix[y][x]

    # Set vị trí x, y trong matrix
    def set_content(self, x, y, content):
        self.matrix[y][x] = content

    # Check xem worker có thể move
    def can_move(self, a, b):
        return self.get_content(self.worker_x + a, self.worker_y + b) not in ['#', '*', '$']

    # Check ô ở trước worker
    def next(self, a, b):
        return self.get_content(self.worker_x + a, self.worker_y + b)

    # Check xem có đẩy gà được không
    def can_push(self, a, b):
        return self.next(a, b) in ['*', '$'] and self.next(a + a, b + b) in [' ', '.']

    def push_box(self, a, b):
        if self.can_push(a, b):
            worker_content = self.get_content(self.worker_x, self.worker_y)
            current_box = self.next(a, b)
            future_box = self.next(2 * a, 2 * b)
            # move box
            if future_box == ' ':
                self.set_content(self.worker_x + 2 * a, self.worker_y + 2 * b, '$')
            else:
                self.set_content(self.worker_x + 2 * a, self.worker_y + 2 * b, '*')
            # move worker
            if current_box == '$':
                self.set_content(self.worker_x + a, self.worker_y + b, '@')
            else:
                self.set_content(self.worker_x + a, self.worker_y + b, '+')
            # release worker content before
            if worker_content == '@':
                self.set_content(self.worker_x, self.worker_y, ' ')
            else:
                self.set_content(self.worker_x, self.worker_y, '.')
            self.worker_x += a
            self.worker_y += b

    # normal worker move
    def worker_move(self, a, b):
        future_worker = self.next(a, b)
        current_worker = self.get_content(self.worker_x, self.worker_y)
        if future_worker in [' ', '.']:
            if future_worker == ' ':
                self.set_content(self.worker_x + a, self.worker_y + b, '@')
            else:
                self.set_content(self.worker_x + a, self.worker_y + b, '+')
            if current_worker == '@':
                self.set_content(self.worker_x, self.worker_y, ' ')
            else:
                self.set_content(self.worker_x, self.worker_y, '.')
            self.worker_x += a
            self.worker_y += b

    # check_move
    def check_move(self, direction_t: str):
        x = self.DIRECTION_LIST[direction_t][0]
        y = self.DIRECTION_LIST[direction_t][1]
        if self.can_move(x, y):
            return 1  # normal move
        elif self.can_push(x, y):
            return 2  # push_box move
        else:
            return 0  # can't_move

    # move in game
    def move(self, direction: str, un_move1=False):
        x = self.DIRECTION_LIST[direction][0]
        y = self.DIRECTION_LIST[direction][1]
        if un_move1:
            x = -x
            y = -y
        if self.can_push(x, y):
            self.push_box(x, y)
            if not un_move1:
                self.stack_move.put(direction.upper())
        elif self.can_move(x, y):
            self.worker_move(x, y)
            if not un_move1:
                self.stack_move.put(direction.lower())

    # un_move wrong step
    def un_move(self, direction: str):
        backward = (self.DIRECTION_LIST[direction][0] * -1, self.DIRECTION_LIST[direction][1] * -1)
        # move worker
        past_worker = self.next(backward[0], backward[1])
        if past_worker == ' ':
            self.set_content(self.worker_x + backward[0], self.worker_y + backward[1], '@')
        elif past_worker == '.':
            self.set_content(self.worker_x + backward[0], self.worker_y + backward[1], '+')
        self.worker_x += backward[0]
        self.worker_y += backward[1]
        # clear content
        cur_worker = self.next(-backward[0], -backward[1])
        if cur_worker == '@':
            self.set_content(self.worker_x - backward[0], self.worker_y - backward[1], ' ')
        elif cur_worker == '+':
            self.set_content(self.worker_x - backward[0], self.worker_y - backward[1], '.')
        if direction in ['L', 'R', 'U', 'D']:
            past_box = self.next(-backward[0], -backward[1])
            # move box
            if past_box == ' ':
                self.set_content(self.worker_x - backward[0], self.worker_y - backward[1], '$')
            elif past_box == '.':
                self.set_content(self.worker_x - backward[0], self.worker_y - backward[1], '*')
            # clear content
            past_box = self.next(-2 * backward[0], -2 * backward[1])
            if past_box == '$':
                self.set_content(self.worker_x - 2 * backward[0], self.worker_y - 2 * backward[1], ' ')
            elif past_box == '*':
                self.set_content(self.worker_x - 2 * backward[0], self.worker_y - 2 * backward[1], '.')

    # Check xem hoàn thành level chưa
    def is_completed(self):
        for row in self.matrix:
            for cell in row:
                if cell == '$':
                    return False
        return True

    # to create key for hash_table
    def hash_func(self):
        x = 0
        y = 0
        temp = ""
        is_complete = True
        for row in self.matrix:
            for pos in row:
                if pos in ['$', '*']:
                    # them hash key
                    if pos in ['$', '+']:
                        is_complete = False
                    temp = temp + str(x) + str(y)
                else:
                    x = x + 1
            y = y + 1
            x = 0
        temp = temp + str(self.worker_x * 2) + str(self.worker_y * 3)
        return int(temp), is_complete

    def check_deadlock(self):
        for pos in self.deadlock_table:
            if self.matrix[pos[1]][pos[0]] == '$':
                return True
        return False

    def move_cost(self, direct):
        cost = 1
        if direct in ['L', 'R', 'U', 'D']:
            a = self.DIRECTION_LIST[direct][0]
            b = self.DIRECTION_LIST[direct][1]
            # neu push box vao 1 vi tri bi chan thi chi phi se tang
            if self.next(a, b-1) in ['#', '$', '*']:
                cost += 3
            if self.next(a, b+1) in ['#', '$', '*']:
                cost += 3
            if self.next(a+1, b) in ['#', '$', '*']:
                cost += 3
            if self.next(a-1, b) in ['#', '$', '*']:
                cost += 3
        return cost * 3

    def heuristic_func(self):
        '''Hàm lượng giá heuristic để đánh giá trạng thái gần trạng thái cần tìm nhất'''
        distance = 0  # heuristic cost.
        list_box = []
        x = 0
        y = 0
        for row in self.matrix:
            for pos in row:
                if pos == '$' or pos == '*':
                    list_box.append((x, y))
                x = x + 1
            y = y + 1
            x = 0
        for i in range(0, len(list_box)):
            distance = (self.listgoal[i][0] - list_box[i][0]) ** 2 + (self.listgoal[i][1] - list_box[i][1]) ** 2
            distance += (self.worker_x - list_box[i][0]) ** 2 + (self.worker_y - list_box[i][1]) ** 2
            distance += (self.listgoal[i][0] - self.worker_x) ** 2 + (self.listgoal[i][1] - self.worker_y) ** 2
        return distance // 4
# --------------------

# Object Button ở Menu
class Button:
    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

    def pressed(self):
        action = False
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                self.clicked = True
                action = True
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        return action
# -----------------

# Các hàm hỗ trợ giải thuật Blind Search (IDDFS)
def print_resultsB(solution_t, gen, rep, fri, explore, dur):
    print("\n1. Depth-first search")
    print("Solution: ", solution_t)
    # print("Nodes generated: " + str(gen))
    # print("Nodes repeated: " + str(rep))
    # print("Fringe nodes: " + str(fri))
    # print("Explored nodes: " + str(explore))
    print('Duration: ' + str(dur) + ' secs')


def depth_limited_search(game, depth, hashtable):
    direction_list = ['l', 'u', 'r', 'd']     # dict of legal move
    node_depth = 1
    frontier = queue.LifoQueue()    # format [move_direction_list_queue]
    for direct in direction_list:
        type_move = game.check_move(direct)  # check if sokoban move follow a direct so what's its type
        if type_move == 1:
            frontier.put((node_depth, direct))
        elif type_move == 2:
            frontier.put((node_depth, direct.upper()))
    while not frontier.empty():
        next_node = frontier.get()  # get node to traverse
        # back track neu duyet het con cua 1 node
        for i in range(next_node[0], node_depth):
            game.un_move(game.stack_move.get())
        node_depth = next_node[0]
        if node_depth > depth:
            return False, game.stack_move, True
        game.move(next_node[1])  # duyet node
        hash_value, is_complete = game.hash_func()
        if not is_complete:
            if hash_value in hashtable:
                game.un_move(game.stack_move.get())
                continue
            elif game.check_deadlock():
                game.un_move(game.stack_move.get())
                continue
            else:
                hashtable.append(hash_value)
                node_depth += 1
                for direct in direction_list:
                    type_move = game.check_move(direct)  # check if sokoban move follow a direct so what's its type
                    if type_move == 1:
                        frontier.put((node_depth, direct))
                    elif type_move == 2:
                        frontier.put((node_depth, direct.upper()))
        else:
            return is_complete, game.stack_move, True
    return False, game.stack_move, True

def iterative_deepening_search(game):
    depth = 1000
    init_matrix = copy.deepcopy(game.get_matrix())
    init_x, init_y = game.worker_x, game.worker_y
    start = time.time()
    while True:
        hashtable = []
        # thu tung do sau toi khi tim thay ket qua
        found, stack_move, remaining = depth_limited_search(game, depth, hashtable)
        if found:
            end = time.time()
            solution = []
            while not stack_move.empty():
                solution.insert(0,stack_move.get())
            print_resultsB(solution, 1, 0, 0, 1, end - start)
            return solution
        elif not remaining:
            end = time.time()
            print_resultsB(game.stack_move, 1, 0, 0, 1, end - start)
            return []
        else:
            depth += 1000
            game.matrix.clear()
            game.matrix = copy.deepcopy(init_matrix)
            game.stack_move.queue.clear()
            game.stack_move = queue.LifoQueue()
            game.worker_x, game.worker_y = init_x, init_y
# -------------------------------------------

# Các hàm hỗ trợ giải thuật Heuristic
def print_results(solution_t, gen, rep, fri, explore, dur):
    print("\n2. Iterative deepening A star search")
    print("Solution: ", solution_t)
    # print("Nodes generated: " + str(gen))
    # print("Nodes repeated: " + str(rep))
    # print("Fringe nodes: " + str(fri))
    # print("Explored nodes: " + str(explore))
    print('Duration: ' + str(dur) + ' secs')

def ida_star_limited_cost_search(game, real_cost, estimated_cost, hashtable):
    direction_list = ['l', 'u', 'r', 'd']     # dict of legal move
    # nodes_generated = 0
    # nodes_repeated = 0
    node_depth = 1
    new_estimated_cost = real_cost + game.heuristic_func()
    frontier = queue.LifoQueue()    # format [move_direction_list_queue]
    for direct in direction_list:
        type_move = game.check_move(direct)  # check if sokoban move follow a direct so what's its type
        if type_move == 1:
            frontier.put((node_depth, new_estimated_cost + game.move_cost(direct), direct))
        elif type_move == 2:
            frontier.put((node_depth, new_estimated_cost + game.move_cost(direct), direct.upper()))
    # duyet lan luot cac node con cua node cha
    min_cost = float("inf")
    while not frontier.empty():
        next_node = frontier.get()  # get node to traverse
        # back track neu duyet het con cua 1 node
        for i in range(next_node[0], node_depth):
            game.un_move(game.stack_move.get())
        node_depth = next_node[0]
        new_estimated_cost = next_node[1]
        if new_estimated_cost < min_cost:
            min_cost = new_estimated_cost
        if min_cost > estimated_cost:
            return min_cost
        game.move(next_node[2])  # duyet node
        # demo_ui(game)
        hash_value, is_complete = game.hash_func()
        if not is_complete:
            if hash_value in hashtable:
                game.un_move(game.stack_move.get())
                # demo_ui(game)
                continue
            elif game.check_deadlock():
                game.un_move(game.stack_move.get())
                # demo_ui(game)
                continue
            else:
                hashtable.append(hash_value)
                node_depth += 1
                for direct in direction_list:
                    type_move = game.check_move(direct)  # check if sokoban move follow a direct so what's its type
                    if type_move == 1:
                        frontier.put((node_depth, new_estimated_cost + game.move_cost(direct), direct))
                    elif type_move == 2:
                        frontier.put((node_depth, new_estimated_cost + game.move_cost(direct), direct.upper()))
        else:
            return -min_cost
    return min_cost

def iterative_deepening_a_star_search(game):
    init_matrix = copy.deepcopy(game.get_matrix())
    init_x, init_y = game.worker_x, game.worker_y
    start = time.time()
    # gioi han cost from node init
    estimated_cost = game.heuristic_func()
    while True:
        hashtable = []  # tranh lap cac node da duyet qua
        # thu tung do sau toi khi tim thay ket qua
        new_estimated_cost = ida_star_limited_cost_search(game, 0, estimated_cost, hashtable)
        hashtable.clear()
        # quy uoc neu new_estimated_cost ma < 0 la goal
        if new_estimated_cost < 0:
            end = time.time()
            solution = []
            while not game.stack_move.empty():
                solution.insert(0, game.stack_move.get())
            print_results(solution, 1, 0, 0, 1, end - start)
            return solution
        #   neu new_estimated_cost ma = vo cung thi ko giai dc
        elif new_estimated_cost == float("inf"):
            # can't find solution
            print("not found")
            return []
        else:
            estimated_cost = new_estimated_cost
            game.matrix.clear()
            game.matrix = copy.deepcopy(init_matrix)
            game.stack_move.queue.clear()
            game.stack_move = queue.LifoQueue()
            game.worker_x, game.worker_y = init_x, init_y
# -----------------------------------

# Các hàm hỗ trợ nhập input lựa chọn level, giải thuật
def display_box(screen, message):
    fontobject = pygame.font.Font(None, 18)
    pygame.draw.rect(screen, (0, 0, 0),
                     ((screen.get_width() / 2) - 100,
                      (screen.get_height() / 2) - 10,
                      200, 20), 0)
    pygame.draw.rect(screen, (255, 255, 255),
                     ((screen.get_width() / 2) - 102,
                      (screen.get_height() / 2) - 12,
                      204, 24), 1)
    if len(message) != 0:
        screen.blit(fontobject.render(message, True, (255, 255, 255)),
                    ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
    pygame.display.flip()

def get_key():
    while True:
        event = pygame.event.poll()
        if event.type == pygame.KEYDOWN:
            return event.key
        else:
            pass

def ask(screen_game, question):
    pygame.font.init()
    current_string = []
    display_box(screen_game, question + ": " + "".join(current_string))
    while 1:
        inkey = get_key()
        if inkey == pygame.K_BACKSPACE:
            current_string = current_string[0:-1]
        elif inkey == pygame.K_RETURN:
            break
        elif inkey == pygame.K_MINUS:
            current_string.append("_")
        elif inkey <= 127:
            current_string.append(chr(inkey))
        display_box(screen_game, question + ": " + "".join(current_string))
    return "".join(current_string)
# ----------------------------------------------------

# Các hàm hỗ trợ vẽ output giải thuật + Thông báo hoàn thành level
def print_game(game_t: Game, screen_game):
    size_x, size_y = game_t.load_size()
    screen_game.fill(background)
    x = SCREEN_WIDTH / 2 - size_x / 2
    y = SCREEN_HEIGHT / 2 - size_y / 2
    matrix = game_t.get_matrix()
    for row in matrix:
        out_matrix = True
        for char in row:
            if char == ' ':  # đất
                if out_matrix:
                    screen_game.blit(back_ground_tile, (x, y))
                else:
                    screen_game.blit(floor, (x, y))
            elif char == '#':  # bụi cỏ
                out_matrix = False
                screen_game.blit(wall, (x, y))
            elif char == '@':  # nông dân
                screen_game.blit(worker, (x, y))
            elif char == '.':  # bếp
                screen_game.blit(docker, (x, y))
            elif char == '*':  # gà đã nấu
                screen_game.blit(box_docked, (x, y))
            elif char == '$':  # gà
                screen_game.blit(box, (x, y))
            elif char == '+':  # nông dân nấu ăn
                screen_game.blit(worker_docked, (x, y))
            x = x + 40
        x = SCREEN_WIDTH / 2 - size_x / 2
        y = y + 40

def display_end(screen):
    message = "              Level Completed"
    fontobject = pygame.font.Font(None, 18)
    pygame.draw.rect(screen, (0, 0, 0),
                     ((screen.get_width() / 2) - 100,
                      (screen.get_height() / 2) - 10,
                      200, 20), 0)
    pygame.draw.rect(screen, (255, 255, 255),
                     ((screen.get_width() / 2) - 102,
                      (screen.get_height() / 2) - 12,
                      204, 24), 1)
    screen.blit(fontobject.render(message, True, (255, 255, 255)),
                ((screen.get_width() / 2) - 100, (screen.get_height() / 2) - 10))
    pygame.display.flip()
# ----------------------------------------------------------------

# Hàm menu game + Hàm bổ trợ vẽ lại menu mặc định
def draw_menu(a, b, c, bg):
    screen.blit(bg, (0, 0))
    a.draw(screen)
    b.draw(screen)
    c.draw(screen)

def menu():
    mixer.music.load('background.mp3')
    mixer.music.play(-1)
    mixer.music.set_volume(0.08)
    bg = pygame.image.load('images/menu.png').convert_alpha()
    bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(bg, (0, 0))
    credit_text = pygame.transform.scale(pygame.image.load('images/credit_text.png'), (SCREEN_WIDTH, SCREEN_HEIGHT))
    start_button = Button(100, 200, pygame.image.load('images/start_button.png'), 0.8)
    exit_button = Button(100, 320, pygame.image.load('images/exit_button.png'), 0.8)
    credit_button = Button(100, 440, pygame.image.load('images/credit_button.png'), 0.8)
    minicosmos = Button(500, 250, pygame.image.load('images/minicosmos.png'), 0.4)
    microcosmos = Button(500, 400, pygame.image.load('images/microcosmos.png'), 0.4)
    draw_menu(start_button, exit_button, credit_button, bg)

    while True:
        if start_button.pressed():
            draw_menu(start_button, exit_button, credit_button, bg)
            minicosmos.draw(screen)
            microcosmos.draw(screen)
        if minicosmos.pressed():
            draw_menu(start_button, exit_button, credit_button, bg)
            level = int(ask(screen, "Select Level"))
            while level < 1 or level > 40:
                pygame.display.update()
                level = int(ask(screen, "Press again"))
            pygame.display.update()
            algo = int(ask(screen, "Press 0:IDDFS, 1:IDA*"))
            while algo != 0 and algo != 1:
                pygame.display.update()
                algo = int(ask(screen, "Press again"))
            select = 'levels - Mini'
            return level, select, algo
        if microcosmos.pressed():
            draw_menu(start_button, exit_button, credit_button, bg)
            level = int(ask(screen, "Select Level"))
            while level < 1 or level > 40:
                pygame.display.update()
                level = int(ask(screen, "Press again"))
            pygame.display.update()
            algo = int(ask(screen, "Press 0:IDDFS, Press 1:IDA*"))
            while algo != 0 and algo != 1:
                pygame.display.update()
                algo = int(ask(screen, "Press again"))
            select = 'levels - Micro'
            return level, select, algo
        if credit_button.pressed():
            draw_menu(start_button, exit_button, credit_button, bg)
            screen.blit(credit_text, (0, 0))
        if exit_button.pressed():
            return -1, 0, 0
        # Xử lý QUIT game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
        pygame.display.update()
# ------------------------------------------------

# Main loop
while True:
    # Init Đồ họa game
    pygame.init()
    pygame.display.set_caption('Chicken Sokoban')
    wall = pygame.image.load('images/wall.png')
    floor = pygame.image.load('images/floor.png')
    box = pygame.image.load('images/box.png')
    box_docked = pygame.image.load('images/box_docked.png')
    worker = pygame.image.load('images/worker.png')
    worker_docked = pygame.image.load('images/worker_dock.png')
    docker = pygame.image.load('images/dock.png')
    back_ground_tile = pygame.image.load('images/backgroundtile.png')
    background = 255, 226, 191
    SCREEN_WIDTH, SCREEN_HEIGHT = 1080, 720
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    # -----------------------------

    # Vẽ menu và lấy input
    menuT = menu()
    mixer.music.stop()
    level_g = menuT[0]
    if level_g == -1:
        pygame.quit()
        break
    select_g = menuT[1]
    aglo = menuT[2]
    game = Game(select_g, level_g)
    # -----------------------------

    # Chạy giải thuật tìm đường
    solution =[]
    if aglo == 0:
        solution = iterative_deepening_search(game)
    elif aglo == 1:
        solution = iterative_deepening_a_star_search(game)
    game = Game(select_g, level_g)
    # --------------------------

    # Demo giải thuật
    for event in solution:
        game.move(event)
        print_game(game, screen)
        pygame.display.update()
        time.sleep(0.02)
        if pygame.event.get() == pygame.mouse.get_pressed()[0]:
            print("")
        if game.is_completed():
            display_end(screen)
            time.sleep(3)
    # -----------------------
# ---------