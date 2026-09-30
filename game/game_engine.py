import math
import pygame
from array import array

from .player import Player
from .obstacle import Obstacle


WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
BROWN = (120, 80, 40)
DARK_GREEN = (30, 100, 30)
RED = (190, 50, 50)


# Speed is pixels/second.
# Maximum speed prevents the game from becoming physically unsolvable.
DIFFICULTIES = {
    "Easy": {
        "initial_speed": 300.0,
        "acceleration": 7.0,
        "max_speed": 440.0,
        "spawn_interval": 1.35,
    },
    "Medium": {
        "initial_speed": 360.0,
        "acceleration": 11.0,
        "max_speed": 540.0,
        "spawn_interval": 1.15,
    },
    "Hard": {
        "initial_speed": 430.0,
        "acceleration": 18.0,
        "max_speed": 660.0,
        "spawn_interval": 0.95,
    },
}


class _SoundManager:
    """Non-blocking sound effects with generated fallbacks."""

    def __init__(self):
        self.jump = None
        self.score = None
        self.game_over = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            # No external audio files are required.
            self.jump = self._tone(620, 0.08)
            self.score = self._tone(900, 0.07)
            self.game_over = self._tone(180, 0.22)

        except (pygame.error, ValueError, TypeError):
            # Audio failure must never stop gameplay.
            self.jump = None
            self.score = None
            self.game_over = None

    @staticmethod
    def _tone(frequency, duration, volume=0.18):
        mixer_info = pygame.mixer.get_init()

        if not mixer_info:
            return None

        sample_rate = mixer_info[0]
        sample_count = max(1, int(sample_rate * duration))
        amplitude = int(32767 * volume)

        samples = array("h")

        for i in range(sample_count):
            envelope = 1.0 - (i / sample_count)

            value = int(
                amplitude
                * envelope
                * math.sin(
                    2.0 * math.pi * frequency * i / sample_rate
                )
            )

            samples.append(value)

        return pygame.mixer.Sound(buffer=samples.tobytes())

    @staticmethod
    def play(sound):
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass


class GameEngine:
    """Core simulation for one endless-runner session."""

    def __init__(self, width, height, difficulty="Medium"):
        self.width = width
        self.height = height
        self.ground_y = height - 40

        self.font = pygame.font.SysFont("Arial", 30)
        self.large_font = pygame.font.SysFont(
            "Arial",
            54,
            bold=True,
        )
        self.small_font = pygame.font.SysFont("Arial", 22)

        self.sounds = _SoundManager()
        self.difficulty = difficulty

        self.reset(difficulty)

    def reset(self, difficulty=None):
        """Completely reset one gameplay session."""

        if difficulty is not None:
            self.difficulty = difficulty

        settings = DIFFICULTIES[self.difficulty]

        # Player state.
        self.player = Player(80, self.ground_y)

        # Difficulty state.
        self.speed = settings["initial_speed"]
        self.acceleration = settings["acceleration"]
        self.max_speed = settings["max_speed"]
        self.spawn_interval = settings["spawn_interval"]

        # Run state.
        self._spawn_timer = 0.0
        self.obstacles = []
        self.distance = 0.0
        self.score = 0
        self.game_over = False

    def handle_event(self, event):
        """Handle gameplay-specific input."""

        if (
            event.type == pygame.KEYDOWN
            and event.key
            in (
                pygame.K_SPACE,
                pygame.K_UP,
                pygame.K_w,
            )
            and not self.game_over
        ):
            if self.player.jump():
                self.sounds.play(self.sounds.jump)

    def handle_input(self):
        # Kept for compatibility with the original architecture.
        pass

    @staticmethod
    def _swept_aabb(
        player_old,
        player_new,
        obstacle_old,
        obstacle_new,
    ):
        """
        Continuous collision detection.

        Treat the player's top-left point as moving relative to an expanded
        obstacle. This detects a collision anywhere during the frame instead
        of checking only the final rectangles.
        """

        # Already overlapping at the beginning of the frame.
        if player_old.colliderect(obstacle_old):
            return True

        # Player movement relative to obstacle movement.
        dx = (
            (player_new.x - player_old.x)
            - (obstacle_new.x - obstacle_old.x)
        )

        dy = (
            (player_new.y - player_old.y)
            - (obstacle_new.y - obstacle_old.y)
        )

        # Expand obstacle by the player's width/height.
        expanded_left = obstacle_old.x - player_old.width
        expanded_right = obstacle_old.x + obstacle_old.width

        expanded_top = obstacle_old.y - player_old.height
        expanded_bottom = obstacle_old.y + obstacle_old.height

        # Player's starting top-left point.
        px = player_old.x
        py = player_old.y

        def axis_entry_exit(
            position,
            delta,
            low,
            high,
        ):
            if delta == 0:
                if low <= position <= high:
                    return -math.inf, math.inf

                return math.inf, -math.inf

            t1 = (low - position) / delta
            t2 = (high - position) / delta

            return min(t1, t2), max(t1, t2)

        x_entry, x_exit = axis_entry_exit(
            px,
            dx,
            expanded_left,
            expanded_right,
        )

        y_entry, y_exit = axis_entry_exit(
            py,
            dy,
            expanded_top,
            expanded_bottom,
        )

        entry = max(
            x_entry,
            y_entry,
            0.0,
        )

        exit_ = min(
            x_exit,
            y_exit,
            1.0,
        )

        return entry <= exit_

    def update(self, dt):
        if self.game_over:
            return

        # Smooth acceleration with a hard upper limit.
        self.speed = min(
            self.max_speed,
            self.speed + self.acceleration * dt,
        )

        # Save old player rectangle for continuous collision detection.
        previous_player_rect = self.player.rect()

        self.player.update(dt)

        current_player_rect = self.player.rect()

        # Time-based obstacle spawning.
        self._spawn_timer += dt

        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer -= self.spawn_interval

            self.obstacles.append(
                Obstacle(
                    self.width,
                    self.ground_y,
                    self.speed,
                )
            )

        # Move obstacles and test the complete movement path.
        for obstacle in self.obstacles:
            previous_obstacle_rect = obstacle.rect()

            obstacle.speed = self.speed
            obstacle.move(dt)

            current_obstacle_rect = obstacle.rect()

            if self._swept_aabb(
                previous_player_rect,
                current_player_rect,
                previous_obstacle_rect,
                current_obstacle_rect,
            ):
                self.game_over = True
                self.sounds.play(self.sounds.game_over)
                return

        # Award one point for every successfully cleared obstacle.
        for obstacle in self.obstacles:
            if (
                not obstacle.scored
                and obstacle.x + obstacle.width < self.player.x
            ):
                obstacle.scored = True
                self.score += 1

                self.sounds.play(self.sounds.score)

        # Remove obstacles that have completely left the screen.
        self.obstacles = [
            obstacle
            for obstacle in self.obstacles
            if not obstacle.off_screen()
        ]

        self.distance += self.speed * dt

    def render(self, screen):
        pygame.draw.line(
            screen,
            BROWN,
            (0, self.ground_y),
            (self.width, self.ground_y),
            4,
        )

        pygame.draw.rect(
            screen,
            WHITE,
            self.player.rect(),
        )

        for obstacle in self.obstacles:
            pygame.draw.rect(
                screen,
                DARK_GREEN,
                obstacle.rect(),
            )

        score_text = self.font.render(
            f"Score: {self.score}   Speed: {self.speed:.0f}",
            True,
            BLACK,
        )

        screen.blit(
            score_text,
            (10, 10),
        )

        difficulty_text = self.small_font.render(
            f"Difficulty: {self.difficulty}",
            True,
            BLACK,
        )

        screen.blit(
            difficulty_text,
            (10, 45),
        )

    def render_game_over(self, screen):
        """Render the dedicated game-over screen."""

        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )

        overlay.fill(
            (0, 0, 0, 165)
        )

        screen.blit(
            overlay,
            (0, 0),
        )

        title = self.large_font.render(
            "GAME OVER",
            True,
            RED,
        )

        score = self.font.render(
            f"Final Score: {self.score}",
            True,
            WHITE,
        )

        prompt = self.small_font.render(
            "Press R to replay  |  Press D for difficulty menu  |  ESC to quit",
            True,
            WHITE,
        )

        screen.blit(
            title,
            title.get_rect(
                center=(self.width // 2, 130)
            ),
        )

        screen.blit(
            score,
            score.get_rect(
                center=(self.width // 2, 205)
            ),
        )

        screen.blit(
            prompt,
            prompt.get_rect(
                center=(self.width // 2, 270)
            ),
        )