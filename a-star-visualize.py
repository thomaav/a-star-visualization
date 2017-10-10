import heapq
import os, shutil, subprocess
from itertools import product
from math import sqrt, inf, floor
from random import shuffle
from PIL import Image, ImageDraw, ImageColor

IMAGE_DIR = "./astar_images/"
GIF_DIR = "./astar_gifs/"

def euclidean_h(c1, c2):
    """
    Suggested function for heuristic h(n).
    """
    x = c1[0] - c2[0]
    y = c1[1] - c2[1]
    return sqrt(x**2 + y**2)

def random_color():
    rgb = [255, 0, 0]
    shuffle(rgb)
    return tuple(rgb)

def darken_color(rgb, multiplier):
    if not 0 <= multiplier <= 1:
        print("[WARN]: darken_color called with invalid multiplier {val}.".format(val=multiplier))
        return rgb
    return tuple([floor(color * (1 - multiplier)) for color in rgb])

class Board(object):
    def __init__(self, fname):
        with open(fname, "r") as f:
            self.board = f.read().splitlines()
            start_line = [line for line in self.board if "A" in line][0]
            end_line = [line for line in self.board if "B" in line][0]
            self.start_index = (self.board.index(start_line), start_line.index("A"))
            self.end_index = (self.board.index(end_line), end_line.index("B"))
            self.length = len(self.board[0])
            self.height = len(self.board)
            self.costs = {
                "w": 100,
                "m": 50,
                "f": 10,
                "g": 5,
                "r": 1,
                ".": 1,
                "A": 0,
                "B": 0
            }
            self.colors = {
                ".": "white",
                "#": "black",
                "A": "#00FF00",
                "B": "red",
                "w": "#4C4CFF",
                "m": "#A5A5A5",
                "f": "#007F00",
                "g": "#7FFF7F",
                "r": "#BF7F3F",
                "O": "yellow"
            }

    def show(self):
        print(*self.board, sep="\n")

    def draw_image(self, board=None, closed_cells=[], square_side=25):
        """
        Return an Image of the board that is colored according to
        self.colors, and has darkened colors for given closed cells.
        """
        # should anyone want to pass another board, then sure
        board = board if board is not None else self.board
        img_squares = []
        colors = []
        chars = []
        img_length = self.length * square_side
        img_height = self.height * square_side

        # create squares, colors and chars for ImageDraw
        for i in range(self.height):
            for j in range(self.length):
                # x and y is opposite here than what is in the list
                # that represents the board
                upper_left = (j * square_side, i * square_side)
                lower_right = ((upper_left[0]) + 25, (upper_left)[1] + 25)
                img_squares.append((upper_left, lower_right))
                chars.append(board[i][j])
                colors.append(self.colors[board[i][j]])

        # darken colors of given closed cells
        for cell in closed_cells:
            index = cell[0] * self.length + cell[1]
            color_as_rgb = ImageColor.getrgb(colors[index])
            colors[index] = darken_color(color_as_rgb, 0.4)
            chars[index] = "x"

        # draw the actual image
        image = Image.new("RGB", (img_length, img_height))
        draw = ImageDraw.Draw(image)
        for i, square in enumerate(img_squares):
            char = chars[i]
            color = colors[i]
            draw.rectangle((square[0], square[1]), fill=color)
            draw.text((square[0]), char, fill="black")

        return image

    def get_adjacent_cells(self, index):
        """
        Returns all adjacent, legal cells as a list.
        """
        adjacent_cells = []
        for direction in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
            cell = (index[0] + direction[0], index[1] + direction[1])
            # skip squares not on the board
            if (
                    0 <= cell[0] < self.height and
                    0 <= cell[1] < self.length and
                    self.board[cell[0]][cell[1]] != "#"
                ):
                adjacent_cells.append(cell)
        return adjacent_cells

    def get_all_cells(self):
        """
        Cartesian product of board's height and length (0-indexed).
        """
        return list(product(range(self.height), range(self.length)))

    def bfs(self, start=None, end=None):
        """
        BFS that keeps the track of previous cell taken to all
        discovered cells.
        """
        # there is no way to use self.* as default params
        start = self.start_index if start is None else start
        end = self.end_index if end is None else end
        queue = [start]
        prev_cell = {}
        closed_cells = []
        while queue:
            cell = queue.pop(0)
            closed_cells.append(cell)
            # if we have found the end cell, we are done, so recreate
            # the path to it
            if cell == end:
                path = []
                tmp_cell = end
                while tmp_cell != start:
                    path.insert(0, tmp_cell)
                    tmp_cell = prev_cell[tmp_cell]
                return path, queue, closed_cells
            for adjacent_cell in self.get_adjacent_cells(cell):
                # if already evaluated, skip
                if adjacent_cell in prev_cell:
                    continue
                prev_cell[adjacent_cell] = cell
                queue.append(adjacent_cell)

        # return empty path if there exists none
        return []

    def a_star(self, h_function, start=None, end=None, visualize_fname=None):
        """
        A*-algorithm that uses f(n) = g(n) + h(n), where g is the
        shortest path found from start to current cell, and h is the
        heuristic for the remaining length to the end.

        h_function is the heuristic function that is to be used, to
        allow for different ones. It should be on the form h(cell1,
        cell2).
        """
        # there is no way to use self.* as default params
        start = self.start_index if start is None else start
        end = self.end_index if end is None else end
        # priority queue for cells, f(n)
        fringe = []
        # score for g(n) in f(n) = g(n) + h(n), default infinity
        non_h_score = {key:inf for key in self.get_all_cells()}
        # where fastest path came from to a given cell
        prev_cell = {}
        closed_cells = []

        # if we want to visualize, we need to collect images
        images = []

        # start at the given start cell
        heapq.heappush(fringe, (0, start))
        non_h_score[start] = 0

        while fringe:
            cell_score, cell_index = heapq.heappop(fringe)
            closed_cells.append(cell_index)

            if visualize_fname:
                images.append(self.draw_image(closed_cells=closed_cells))

            # we found the end, reconstruct the path
            if cell_index == end:
                path = []
                tmp_cell = end
                while tmp_cell != start:
                    path.insert(0, tmp_cell)
                    tmp_cell = prev_cell[tmp_cell]
                open_cells = [element[1] for element in fringe]

                # if gif is wanted, save images and call convert, then
                # delete images
                if visualize_fname:
                    img_num_length = len(str(len(images)))
                    print("[INFO]: Saving {num_images} images.".format(num_images=len(images)))
                    for i, image in enumerate(images):
                        padding_num = img_num_length - len(str(i))
                        # left pad 0s for proper sorting with imagemagick convert
                        image.save(IMAGE_DIR + "image" + "0" * padding_num + str(i) + ".png", "PNG")

                    print("[INFO]: Converting to gif: {gif_dir}{name}.".format(gif_dir=GIF_DIR, name=visualize_fname))
                    convert_command = "convert -delay 1 -loop 0 " + IMAGE_DIR + "*png " + GIF_DIR + visualize_fname
                    subprocess.call(convert_command, shell=True)

                    print("[INFO]: Cleaning up images in {img_dir}.".format(img_dir=IMAGE_DIR))
                    for f in os.listdir(IMAGE_DIR):
                        f_path = os.path.join(IMAGE_DIR, f)
                        try:
                            if os.path.isfile(f_path):
                                os.unlink(f_path)
                        except Exception as e:
                            print(e)

                return path, open_cells, closed_cells

            for adjacent_cell in self.get_adjacent_cells(cell_index):
                if adjacent_cell in prev_cell:
                    continue

                adjacent_cell_cost = self.costs[self.board[adjacent_cell[0]][adjacent_cell[1]]]

                # not a shorter path to adjacent cell; skip
                if non_h_score[cell_index] + adjacent_cell_cost >= non_h_score[adjacent_cell]:
                    continue

                # best current path to adjacent cell
                prev_cell[adjacent_cell] = cell_index
                non_h_score[adjacent_cell] = non_h_score[cell_index] + adjacent_cell_cost
                heapq.heappush(fringe, (non_h_score[adjacent_cell] + h_function(adjacent_cell, end), adjacent_cell))

        # return empty path if there exists none
        return []

    def get_solution_board(self):
        # unimmutify strings
        solution_board = [list(line) for line in self.board[:]]
        solution_path = self.a_star(euclidean_h)[0]
        for cell in solution_path:
            if solution_board[cell[0]][cell[1]] not in ["A", "B"]:
                solution_board[cell[0]][cell[1]] = "O"
        solution_board = ["".join(line) for line in solution_board]
        return solution_board

def main():
    main_board = Board("boards/board-1-2.txt")
    main_board.a_star(euclidean_h, visualize_fname="test.gif")

if __name__ == "__main__":
    main()
