from __future__ import annotations

from typing import Iterable

import pygame


class Field:
    """Official World Boccia court geometry, proportionally scaled."""

    COURT_WIDTH_M = 6.0
    COURT_LENGTH_M = 12.5
    THROWING_AREA_DEPTH_M = 2.5
    PLAY_AREA_LENGTH_M = 10.0
    V_SIDE_HEIGHT_M = 3.0
    V_APEX_HEIGHT_M = 1.5
    CROSS_FROM_BACK_M = 5.0
    CROSS_SIZE_M = 0.25
    TARGET_BOX_M = 0.35

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self.px_per_meter_x = rect.width / self.COURT_WIDTH_M
        self.px_per_meter_y = rect.height / self.COURT_LENGTH_M
        self.throwing_line_y = self._y_from_top(self.PLAY_AREA_LENGTH_M)
        self.launch_line_y = self.throwing_line_y
        self.red_launch_point = self._box_center(3)
        self.blue_launch_point = self._box_center(4)
        self.launch_point = self.red_launch_point.copy()
        self.cross_position = pygame.Vector2(
            self._x_from_left(3.0),
            self._y_from_top(self.CROSS_FROM_BACK_M),
        )
        self.jack_default_position = self.cross_position.copy()
        self.box_font = pygame.font.SysFont("arial", 18, bold=True)

    @property
    def playable_bounds(self) -> pygame.Rect:
        return self.rect.copy()

    @property
    def playing_area_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.rect.left,
            self.rect.top,
            self.rect.width,
            self.throwing_line_y - self.rect.top,
        )

    @property
    def target_box_rect(self) -> pygame.Rect:
        width = self._meters_x(self.TARGET_BOX_M)
        height = self._meters_y(self.TARGET_BOX_M)
        return pygame.Rect(
            round(self.cross_position.x - width / 2),
            round(self.cross_position.y - height / 2),
            round(width),
            round(height),
        )

    def launch_point_for(self, player_key: str) -> pygame.Vector2:
        return (
            self.blue_launch_point.copy()
            if player_key == "blue"
            else self.red_launch_point.copy()
        )

    def box_center(self, box_number: int) -> pygame.Vector2:
        return self._box_center(box_number)

    def has_entered_playing_area(self, body: object) -> bool:
        return (
            float(body.position.y) + float(body.radius)
            < self.throwing_line_y
        )

    def touches_exterior_boundary(self, body: object) -> bool:
        x = float(body.position.x)
        y = float(body.position.y)
        radius = float(body.radius)
        return (
            x - radius <= self.rect.left
            or x + radius >= self.rect.right
            or y - radius <= self.rect.top
            or y + radius >= self.rect.bottom
        )

    def v_line_y_at_x(self, x: float) -> float:
        left_y = self.throwing_line_y - self._meters_y(
            self.V_SIDE_HEIGHT_M
        )
        apex_y = self.throwing_line_y - self._meters_y(
            self.V_APEX_HEIGHT_M
        )
        if x <= self.rect.centerx:
            ratio = (
                (x - self.rect.left)
                / max(1.0, self.rect.centerx - self.rect.left)
            )
            return left_y + (apex_y - left_y) * ratio
        ratio = (
            (x - self.rect.centerx)
            / max(1.0, self.rect.right - self.rect.centerx)
        )
        return apex_y + (left_y - apex_y) * ratio

    def is_valid_jack_position(self, jack: object) -> bool:
        if self.touches_exterior_boundary(jack):
            return False
        if not self.has_entered_playing_area(jack):
            return False
        v_y = self.v_line_y_at_x(float(jack.position.x))
        return float(jack.position.y) + float(jack.radius) < v_y

    def jack_is_in_non_valid_area(self, jack: object) -> bool:
        if self.touches_exterior_boundary(jack):
            return True
        if not self.has_entered_playing_area(jack):
            return True
        v_y = self.v_line_y_at_x(float(jack.position.x))
        return float(jack.position.y) + float(jack.radius) >= v_y

    def replacement_jack_position(
        self,
        balls: Iterable[object],
        jack_radius: float,
    ) -> pygame.Vector2:
        position = self.cross_position.copy()
        if not self._position_overlaps_balls(
            position,
            jack_radius,
            balls,
        ):
            return position

        y = self.cross_position.y + 1.0
        while y < self.throwing_line_y - jack_radius:
            candidate = pygame.Vector2(self.cross_position.x, y)
            if not self._position_overlaps_balls(
                candidate,
                jack_radius,
                balls,
            ):
                return candidate
            y += 1.0
        return position

    def ball_scores_penalty(self, ball: object) -> bool:
        box = self.target_box_rect
        x = float(ball.position.x)
        y = float(ball.position.y)
        radius = float(ball.radius)
        return (
            x - radius > box.left
            and x + radius < box.right
            and y - radius > box.top
            and y + radius < box.bottom
        )

    def draw(self, surface: pygame.Surface) -> None:
        shadow_rect = self.rect.move(6, 7)
        pygame.draw.rect(surface, (18, 23, 28), shadow_rect)
        pygame.draw.rect(surface, (55, 153, 101), self.rect)

        line_color = (245, 247, 245)
        line_width = max(2, round(self.px_per_meter_x * 0.04))
        narrow_width = max(1, round(line_width * 0.65))

        pygame.draw.rect(surface, line_color, self.rect, line_width)
        pygame.draw.line(
            surface,
            line_color,
            (self.rect.left, self.throwing_line_y),
            (self.rect.right, self.throwing_line_y),
            line_width,
        )

        for box_index in range(1, 6):
            x = self._x_from_left(float(box_index))
            pygame.draw.line(
                surface,
                line_color,
                (x, self.throwing_line_y),
                (x, self.rect.bottom),
                narrow_width,
            )

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
                    round(
                        self.throwing_line_y
                        + (self.rect.bottom - self.throwing_line_y) * 0.53
                    ),
                )
            )
            surface.blit(text, text_rect)

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

        target = self.target_box_rect
        pygame.draw.rect(surface, line_color, target, narrow_width)

        half_cross_x = self._meters_x(self.CROSS_SIZE_M) / 2.0
        half_cross_y = self._meters_y(self.CROSS_SIZE_M) / 2.0
        cx, cy = self.cross_position
        pygame.draw.line(
            surface,
            line_color,
            (cx - half_cross_x, cy),
            (cx + half_cross_x, cy),
            narrow_width,
        )
        pygame.draw.line(
            surface,
            line_color,
            (cx, cy - half_cross_y),
            (cx, cy + half_cross_y),
            narrow_width,
        )

    def _position_overlaps_balls(
        self,
        position: pygame.Vector2,
        radius: float,
        balls: Iterable[object],
    ) -> bool:
        for ball in balls:
            minimum = radius + float(ball.radius)
            if position.distance_to(ball.position) < minimum:
                return True
        return False

    def _box_center(self, box_number: int) -> pygame.Vector2:
        box = max(1, min(6, int(box_number)))
        return pygame.Vector2(
            self._x_from_left(box - 0.5),
            self.throwing_line_y
            + self._meters_y(self.THROWING_AREA_DEPTH_M / 2.0),
        )

    def _x_from_left(self, meters: float) -> float:
        return self.rect.left + self._meters_x(meters)

    def _y_from_top(self, meters: float) -> float:
        return self.rect.top + self._meters_y(meters)

    def _meters_x(self, meters: float) -> float:
        return meters * self.px_per_meter_x

    def _meters_y(self, meters: float) -> float:
        return meters * self.px_per_meter_y
