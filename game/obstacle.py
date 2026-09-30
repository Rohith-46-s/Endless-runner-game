import pygame


class Obstacle:
    """A horizontally scrolling obstacle."""

    def __init__(self, x, ground_y, speed, width=25, height=40):
        self.x = float(x)
        self.width = width
        self.height = height
        self.y = float(ground_y - height)
        self.speed = float(speed)
        self.scored = False

    def move(self, dt):
        """Move using speed in pixels/second."""
        self.x -= self.speed * dt

    def off_screen(self):
        return self.x + self.width < 0

    def rect(self):
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )