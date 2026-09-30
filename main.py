import pygame

from game.game_engine import DIFFICULTIES, GameEngine


pygame.init()


WIDTH, HEIGHT = 800, 400

SCREEN = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Endless Runner - Pygame Version"
)


SKY = (200, 220, 240)
BLACK = (20, 20, 20)
WHITE = (255, 255, 255)

clock = pygame.time.Clock()
FPS = 60


class Game:
    """Application-level state machine."""

    START = "start"
    PLAYING = "playing"
    GAME_OVER = "game_over"

    def __init__(self):
        self.engine = GameEngine(
            WIDTH,
            HEIGHT,
            "Medium",
        )

        self.state = self.START

        self.selected_index = 1
        self.difficulties = list(
            DIFFICULTIES.keys()
        )

        self.title_font = pygame.font.SysFont(
            "Arial",
            48,
            bold=True,
        )

        self.font = pygame.font.SysFont(
            "Arial",
            28,
        )

        self.small_font = pygame.font.SysFont(
            "Arial",
            20,
        )

    @property
    def selected_difficulty(self):
        return self.difficulties[
            self.selected_index
        ]

    def start_run(self):
        # Reset every gameplay variable before replaying.
        self.engine.reset(
            self.selected_difficulty
        )

        self.state = self.PLAYING

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return False

        # ---------------------------
        # Difficulty selection state
        # ---------------------------
        if self.state == self.START:

            if event.type == pygame.KEYDOWN:

                if event.key in (
                    pygame.K_UP,
                    pygame.K_w,
                ):
                    self.selected_index = (
                        self.selected_index - 1
                    ) % len(self.difficulties)

                elif event.key in (
                    pygame.K_DOWN,
                    pygame.K_s,
                ):
                    self.selected_index = (
                        self.selected_index + 1
                    ) % len(self.difficulties)

                elif event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                ):
                    self.start_run()

                elif event.key == pygame.K_ESCAPE:
                    return False

        # ---------------------------
        # Active gameplay state
        # ---------------------------
        elif self.state == self.PLAYING:

            self.engine.handle_event(
                event
            )

        # ---------------------------
        # Game-over state
        # ---------------------------
        elif self.state == self.GAME_OVER:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:
                    # Replay same difficulty.
                    self.start_run()

                elif event.key == pygame.K_d:
                    # Return to difficulty selection.
                    self.state = self.START

                elif event.key == pygame.K_ESCAPE:
                    return False

        return True

    def update(self, dt):
        if self.state == self.PLAYING:

            self.engine.update(dt)

            if self.engine.game_over:
                self.state = self.GAME_OVER

    def render_start(self):
        SCREEN.fill(SKY)

        title = self.title_font.render(
            "ENDLESS RUNNER",
            True,
            BLACK,
        )

        subtitle = self.font.render(
            "Select Difficulty",
            True,
            BLACK,
        )

        SCREEN.blit(
            title,
            title.get_rect(
                center=(WIDTH // 2, 70)
            ),
        )

        SCREEN.blit(
            subtitle,
            subtitle.get_rect(
                center=(WIDTH // 2, 125)
            ),
        )

        for index, difficulty in enumerate(
            self.difficulties
        ):
            selected = (
                index == self.selected_index
            )

            text = self.font.render(
                f"{'>' if selected else ' '} {difficulty}",
                True,
                (30, 100, 30)
                if selected
                else BLACK,
            )

            SCREEN.blit(
                text,
                text.get_rect(
                    center=(
                        WIDTH // 2,
                        185 + index * 50,
                    )
                ),
            )

        controls = self.small_font.render(
            "UP/DOWN or W/S: select    "
            "ENTER/SPACE: start    ESC: quit",
            True,
            BLACK,
        )

        SCREEN.blit(
            controls,
            controls.get_rect(
                center=(WIDTH // 2, 360)
            ),
        )

    def render(self):
        if self.state == self.START:
            self.render_start()
            return

        SCREEN.fill(SKY)

        self.engine.render(
            SCREEN
        )

        if self.state == self.GAME_OVER:
            self.engine.render_game_over(
                SCREEN
            )


def main():
    game = Game()

    running = True

    while running:

        # Convert milliseconds to seconds.
        # Cap long pauses to avoid huge physics jumps.
        dt = min(
            clock.tick(FPS) / 1000.0,
            0.05,
        )

        for event in pygame.event.get():

            running = game.handle_event(
                event
            )

            if not running:
                break

        if not running:
            break

        game.update(dt)
        game.render()

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()