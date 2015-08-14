import Tkinter
import sys
import os
import stat
import random
from tkFileDialog import askdirectory
import pygame
pygame.init()
pygame.font.init()


class Tile(object):
    '''A single rectangle in treemap'''

    def __init__(self, path, size, children, colour=(255, 255, 255)):
        '''(Tile, str, float, list, tuple(int,int,int)) -> NoneType'''

        self.path = path
        self.size = size
        self.children = children  # List of Tiles
        self.colour = colour
        self.colour_hlt = (255, 255, 0)  # yellow (for highlight)
        self.content = None
        self.mouseover = False  # Hovering over a treemap Tile
        self.mouseover_menu = False  # Hovering over a menu Tile
        self.font = pygame.font.Font(None, 21)
        self.buttondown = False

    def draw(self, surface, mouse_xy, thickness):
        '''(Tile, Surface, tuple(int,int), int) -> NoneType
        Draw a Tile on this surface'''

        pygame.draw.rect(surface, self.colour, self.rect, thickness)
        # Draw another rectangle as highlight
        if self.mouseover:
            pygame.draw.rect(surface, self.colour_hlt, \
                             self.rect.inflate(-3, -3), 3)

    def blit(self, surface, mouse_xy, *args):
        '''(Tile, Surface, tuple(int,int), args) -> NoneType
        Blit the contents for the Tile currently pointed at by the mouse'''

        # Blit the menu
        px, py, w, h = self.rect
        if px >= game.width:
            content = self.font.render(self.path, 1, (0, 200, 0))
            surface.blit(content, (px + 20, py + 20))

        # Blit the folder path
        if mouse_xy:
            x, y = mouse_xy
            self.content = self.font.render(self.path, 1, (255, 255, 255))
            self.mouseover = False  # Reset flag
            self.mouseover_menu = False  # Reset flag

            # Figure out if mouse is within the boundaries of this Tile
            if x > px and x < px + w:
                if y > py and y < py + h:
                    self.mouseover = True
                    if x > game.width:
                        self.mouseover_menu = True
                    surface.blit(self.content, (270, 570))  # blit folderpath

        if not self.mouseover_menu:
            self.buttondown = False  # Ignore clicks when mouse isn't over menu

    def mousedown(self, *args):
        '''(Tile, args) -> NoneType
        Set flag to acknowledge mouseclick'''

        # Acknowledge clicks only when mouse is over the menu
        # Note: Clicks aren't processed until mouse button is up
        if self.mouseover_menu:
            self.buttondown = True

    def leftclick(self):
        '''(Tile) -> str
        Return folder path for the currently selected menu item'''

        if self.path == game.history[-1]:  # We're already at this path
            return
        game.history.append(self.path)
        return game.history[-1]

    def rightclick(self):
        '''(Tile) -> str
        Return folder path of the last visited directory'''

        if len(game.history) == 1:  # No previous entries available
            return
        game.history.pop()
        return game.history[-1]

    def select(self):
        '''(Tile) -> str
        Ask user to choose a new directory and return its path
        Return None if action was cancelled'''

        userinput = game.ask_directory()
        if not userinput:  # User cancelled the action
            return
        game.running = False
        del game.history[:]
        game.history.append(userinput)
        return game.history[-1]

    def onclick(self, *args):
        '''(Tile, args) -> NoneType
        Process type of event triggered by the user'''

        newpath = None
        if game.button == 3:
            newpath = self.rightclick()
        elif self.buttondown and self.mouseover_menu:
            self.buttondown = False
            if self.path == '<Select New..>':
                newpath = self.select()
            elif self.path == '<Home>':
                if len(game.history) == 1:  # Already at root
                    return
                game.history = game.history[:1]
                newpath = game.history[-1]
            elif self.path == '<Back>':
                newpath = self.rightclick()
            elif game.button == 1:
                newpath = self.leftclick()

        if newpath:
            game.path = newpath  # Set new root path
            game.run()  # Draw new treemap


class Map(object):
    '''A treemap of the contents of a directory
    Directories with no contents inside are treated as empty'''

    def __init__(self, dirpath):
        '''(Map, str) -> NoneType'''

        treemap = self.build_tree(dirpath)  # Root node for treemap
        menu = self.build_menu(dirpath, treemap.size)  # Root node for menu
        self.root = Tile(None, treemap.size, [treemap, menu])  # Root node
        self.allocate_size(self.root)

    def build_tree(self, dirpath):
        '''(Map, str) -> Tile
        Return the root node of a tree representation of the directory
        structure at dirpath'''

        children = []  # Nested list of Tiles
        dirpaths = []  # List of subdirectory paths

        for f in os.listdir(dirpath):
            absolute = os.path.join(dirpath, f)
            colour = (random.randrange(0, 160, 10), \
                      random.randrange(0, 160, 10), \
                      random.randrange(0, 160, 10))

            if os.path.isfile(absolute):
                children.append(Tile(absolute, os.stat(absolute).st_size, \
                                     [], colour))
            elif os.path.isdir(absolute):
                children.append(self.build_tree(absolute))

        if not children:  # Empty directory
            return Tile(None, 0.0001, [])  # Return blank Tile
        return Tile(None, sum([x.size for x in children]), children)

    def build_menu(self, rootpath, totalsize):
        '''(Map, str, float) -> Tile
        Return the root node of a tree representing the menu'''

        dirs = os.listdir(rootpath)
        menuitems = []
        size = totalsize * 0.4 * 1 / 14  # max of 14 items in the menu

        # Add default items to the menu first
        base_items = ('<Select New..>', '<Home>', '<Back>')
        for item in base_items:
            menuitems.append(Tile(item, size, [], (0, 0, 0)))

        # Add sub-directories to the menu
        for f in dirs:
            p = os.path.join(rootpath, f)
            if os.path.isdir(p):
                menuitems.append(Tile(p, size, [], (0, 0, 0)))

        return Tile(None, totalsize * 0.4, menuitems)

    def allocate_size(self, node, x=0, y=0, w=1, h=1, width=1, height=1):
        '''(Map, Tile, int, int, int, int, int, int) -> NoneType
        Calculate the relative width and height of each Tile in the treemap'''

        node.pos = (x * game.width, y * game.height)
        node.dimensions = (w * game.width, h * game.height)
        node.rect = pygame.Rect(node.pos, node.dimensions)
        totalsize = node.size

        if w >= h:
            width = w
            for child in node.children:
                w = (child.size * width) / float(totalsize)
                self.allocate_size(child, x, y, w, h, width, height)
                x += w
        else:
            height = h
            for child in node.children:
                h = (child.size * height) / float(totalsize)
                self.allocate_size(child, x, y, w, h, width, height)
                y += h

    def update(self, surface, func, mouse_xy=None, node=None):
        '''(Map, Surface, function, tuple(int,int), Tile) -> NoneType
        Update the treemap'''

        if not node:
            node = self.root
        if not node.children:
            func(node, surface, mouse_xy, 0)  # Draw items inside the directory
            return
        for child in node.children:
            self.update(surface, func, mouse_xy, child)
            if func != Tile.blit:
                func(node, surface, mouse_xy, 2)  # Draw the directory itself


class Main(object):
    '''A controller class'''

    def __init__(self, screen_size):
        '''(Main, tuple(int,int)) -> NoneType'''

        self.path = self.ask_directory()
        self.history = [self.path]  # history of paths traversed by user
        self.surface = pygame.display.set_mode(screen_size)
        self.menu_width = 300   # 800px to 1100px -> menu
        self.width = screen_size[0] - self.menu_width  # 0 to 800px -> treemap
        self.height = screen_size[1]
        self.button = None  # Mouse button

    def ask_directory(self):
        '''(Main) -> str
        Ask user to choose a directory and return its path'''

        files = {}
        root = Tkinter.Tk()
        root.wm_withdraw()
        path = askdirectory()
        root.destroy()
        return path

    def flip(self):
        '''(Main) -> NoneType
        Listen for PyGame events and update surface in a loop'''

        self.running = True
        mouse_xy = None  # current co-ordinates of mouse
        while self.running:
            event = pygame.event.poll()
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEMOTION:
                mouse_xy = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:  # Click started
                self.treemap.update(self.surface, Tile.mousedown)
                self.button = event.button   # 1=left, 3=right
            elif event.type == pygame.MOUSEBUTTONUP:   # Click completed
                self.treemap.update(self.surface, Tile.onclick)
                self.button = None

            self.surface.fill((0, 0, 0))
            self.treemap.update(self.surface, Tile.draw)
            self.treemap.update(self.surface, Tile.blit, mouse_xy)
            pygame.display.flip()

    def run(self):
        '''(Main) -> NoneType
        Draw a new treemap'''

        self.running = False
        if self.path:
            self.treemap = Map(self.path)
            self.flip()


if __name__ == '__main__':
    game = Main((1100, 600))
    game.run()
    pygame.quit()
