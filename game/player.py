import pygame


class Player:
    """Player movement and physics. Motion is time-based for FPS independence."""

    def __init__(self, x, ground_y, width=30, height=40):
        self.x = float(x)
        self.ground_y = float(ground_y)
        self.width = width
        self.height = height

        # Physics values are expressed per second / per second squared.
        self.gravity = 2200.0
        self.jump_strength = -750.0

        self.y = self.ground_y - self.height
        self.vy = 0.0
        self.on_ground = True

    def reset(self):
        """Return the player to its initial state."""
        self.y = self.ground_y - self.height
        self.vy = 0.0
        self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.vy = self.jump_strength
            self.on_ground = False
            return True

        return False

    def update(self, dt):
        """Advance vertical physics using elapsed time."""
        self.vy += self.gravity * dt
        self.y += self.vy * dt

        ground_level = self.ground_y - self.height

        if self.y >= ground_level:
            self.y = ground_level
            self.vy = 0.0
            self.on_ground = True

    def rect(self):
        return pygame.Rect(
            round(self.x),
            round(self.y),
            self.width,
            self.height,
        )