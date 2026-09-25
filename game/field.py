from __future__ import annotations

import pygame


class Field:
    """Campo regolamentare World Boccia, scalato in modo proporzionale."""

    COURT_WIDTH_M = 6.0
    COURT_LENGTH_M = 12.5
    THROWING_AREA_DEPTH_M = 2.5
    PLAY_AREA_LENGTH_M = 10.0
    V_SIDE_HEIGHT_M = 3.0
    V_APEX_HEIGHT_M = 1.5
    CROSS_FROM_BACK_M = 5.0
    CROSS_SIZE_M = 0.25

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect

        self.px_per_meter_x = rect.width / self.COURT_WIDTH_M
        self.px_per_meter_y = rect.height / self.COURT_LENGTH_M

        self.throwing_line_y = self._y_from_top(self.PLAY_AREA_LENGTH_M)
        self.launch_line_y = self.throwing_line_y

        # Nella prova individuale il rosso occupa il box 3 e il blu il box 4.
        self.red_launch_point = self._box_center(3)
        self.blue_launch_point = self._box_center(4)

        # Compatibilità con la modalità Allenamento: usa il box 3.
        self.launch_point = self.red_launch_point.copy()

        # La croce è a 3 m dai lati e a 5 m dal fondo opposto.
        self.cross_position = pygame.Vector2(
            self._x_from_left(3.0),
            self._y_from_top(self.CROSS_FROM_BACK_M),
        )

        # Finché non aggiungiamo la fase separata di lancio del jack,
        # il jack iniziale viene posizionato sulla croce regolamentare.
        self.jack_default_position = self.cross_position.copy()

        self.box_font = pygame.font.SysFont("arial", 18, bold=True)

    @property
    def playable_bounds(self) -> pygame.Rect:
        # Il motore attuale usa ancora il perimetro completo come limite fisico.
        # Le linee regolamentari vengono comunque disegnate in scala corretta.
        return self.rect.copy()

    def launch_point_for(self, player_key: str) -> pygame.Vector2:
        if player_key == "blue":
            return self.blue_launch_point.copy()
        return self.red_launch_point.copy()

    def draw(self, surface: pygame.Surface) -> None:
        shadow_rect = self.rect.move(6, 7)
        pygame.draw.rect(surface, (18, 23, 28), shadow_rect)

        pygame.draw.rect(surface, (55, 153, 101), self.rect)

        line_color = (245, 247, 245)
        line_width = max(2, round(self.px_per_meter_x * 0.04))

        # Perimetro 6 m x 12,5 m.
        pygame.draw.rect(surface, line_color, self.rect, line_width)

        # Linea di lancio: separa i 10 m di campo dai 2,5 m dei box.
        pygame.draw.line(
            surface,
            line_color,
            (self.rect.left, self.throwing_line_y),
            (self.rect.right, self.throwing_line_y),
            line_width,
        )

        # Sei box da 1 m x 2,5 m.
        for box_index in range(1, 6):
            x = self._x_from_left(float(box_index))
            pygame.draw.line(
                surface,
                line_color,
                (x, self.throwing_line_y),
                (x, self.rect.bottom),
                line_width,
            )

        # Numerazione dei box 1-6.
        for box_number in range(1, 7):
            center = self._box_center(box_number)
            text = self.box_font.render(
                str(box_number),
                True,
                (20, 24, 28),
            )
            text_rect = text.get_rect(
                center=(
                    round(center.x),
                    round(self.throwing_line_y + (
                        self.rect.bottom - self.throwing_line_y
                    ) * 0.53),
                )
            )
            surface.blit(text, text_rect)

        # V-line: ai lati 3 m sopra la linea di lancio,
        # vertice centrale 1,5 m sopra la linea di lancio.
        side_y = self.throwing_line_y - self._meters_y(
            self.V_SIDE_HEIGHT_M
        )
        apex_y = self.throwing_line_y - self._meters_y(
            self.V_APEX_HEIGHT_M
        )
        apex_x = self.rect.centerx

        pygame.draw.line(
            surface,
            line_color,
            (self.rect.left, side_y),
            (apex_x, apex_y),
            line_width,
        )
        pygame.draw.line(
            surface,
            line_color,
            (apex_x, apex_y),
            (self.rect.right, side_y),
            line_width,
        )

        # Croce regolamentare da 25 cm.
        half_cross_x = self._meters_x(self.CROSS_SIZE_M) / 2.0
        half_cross_y = self._meters_y(self.CROSS_SIZE_M) / 2.0
        cx, cy = self.cross_position
        pygame.draw.line(
            surface,
            line_color,
            (cx - half_cross_x, cy),
            (cx + half_cross_x, cy),
            line_width,
        )
        pygame.draw.line(
            surface,
            line_color,
            (cx, cy - half_cross_y),
            (cx, cy + half_cross_y),
            line_width,
        )

    def _box_center(self, box_number: int) -> pygame.Vector2:
        box = max(1, min(6, int(box_number)))
        x = self._x_from_left((box - 0.5))
        y = self.throwing_line_y + self._meters_y(
            self.THROWING_AREA_DEPTH_M / 2.0
        )
        return pygame.Vector2(x, y)

    def _x_from_left(self, meters: float) -> float:
        return self.rect.left + self._meters_x(meters)

    def _y_from_top(self, meters: float) -> float:
        return self.rect.top + self._meters_y(meters)

    def _meters_x(self, meters: float) -> float:
        return meters * self.px_per_meter_x

    def _meters_y(self, meters: float) -> float:
        return meters * self.px_per_meter_y
