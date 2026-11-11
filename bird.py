import math
import random

from pico2d import *

import game_framework

# ---------------------------------------------------------------------------
# 물리 상수 (실제 단위 → 픽셀 단위 변환)
# ---------------------------------------------------------------------------
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel = 30 cm (ruler.png 기준, boy.py 와 동일)

# 비행 속도: 중대형 조류의 순항 속도(25~50 km/h) 범위
FLY_SPEED_KMPH = 30.0
FLY_SPEED_MPM = (FLY_SPEED_KMPH * 1000.0 / 60.0)
FLY_SPEED_MPS = (FLY_SPEED_MPM / 60.0)
FLY_SPEED_PPS = (FLY_SPEED_MPS * PIXEL_PER_METER)

# 새 크기: 꼬리 끝~부리 끝 몸길이 1.2 m (날개 편 폭은 약 1.5 m)
BIRD_BODY_LENGTH_M = 1.2
BIRD_BODY_LENGTH_PIXEL = BIRD_BODY_LENGTH_M * PIXEL_PER_METER

# 날갯짓: 중대형 조류의 날갯짓 빈도(2~5 Hz) 범위
FLAPS_PER_SECOND = 3.0          # 1초에 날갯짓 3회
FRAMES_PER_FLAP = 14            # 시트의 14프레임이 날갯짓 한 주기
FRAMES_PER_SECOND = FLAPS_PER_SECOND * FRAMES_PER_FLAP

# 날갯짓에 따른 몸의 상하 흔들림
# 시트 프레임 2 -> 5  : 다운스트로크(날개를 위에서 아래로 내려침) -> 위로 향하는 양력 최대
# 시트 프레임 5 -> 11 : 날개를 아래에 둔 채 뒤로 젖힘
# 시트 프레임 11 -> 0 : 업스트로크(날개를 다시 들어 올림)
# 단진동 y = -A cos(φ) 에서 위쪽 가속도가 최대인 순간이 곧 최저점이므로,
# 양력이 가장 큰 다운스트로크 중앙(프레임 3.5)을 최저점, 반 주기 뒤(10.5)를 최고점으로 둔다.
BOB_AMPLITUDE_M = 0.1                       # 위아래 10 cm
BOB_AMPLITUDE_PIXEL = BOB_AMPLITUDE_M * PIXEL_PER_METER
LOWEST_POINT_FRAME = 3.5                    # 다운스트로크 중앙

# 개체별 편차 및 비행 영역
SPEED_VARIATION = 0.2    # 비행 속도 ±20% (24 ~ 36 km/h)
FLAP_VARIATION = 0.15    # 날갯짓 빈도 ±15% (2.55 ~ 3.45 Hz)
SKY_MIN_RATIO = 0.45     # 비행 고도 하한: 화면 높이의 45% (소년/지면과 겹치지 않게)
SKY_MAX_RATIO = 0.92     # 비행 고도 상한: 화면 높이의 92%

# ---------------------------------------------------------------------------
# 스프라이트 시트 (bird_animation.png : 918 x 506, 14프레임)
# ---------------------------------------------------------------------------
# 시트는 겉보기엔 5x3 격자지만 실제로는 균일 격자가 아니다.
# (프레임 4/13 의 날개가 격자선을 넘고, 프레임 6 은 아래 행 영역까지 내려온다)
# 그래서 tools/analyze_bird_sheet.py 로 측정한 프레임별 실제 영역과
# 눈동자 무게중심(몸 기준점)을 그대로 사용한다.
# (left, top, right, bottom, eye_x, eye_y) -- 시트 위쪽 원점, right/bottom 포함
SHEET_HEIGHT = 506
FRAME_DATA = (
    (34, 1, 179, 143, 123.2, 93.3),
    (216, 2, 361, 142, 305.2, 92.5),
    (398, 12, 543, 141, 487.6, 90.6),
    (555, 17, 725, 138, 669.6, 87.6),
    (728, 48, 909, 135, 851.6, 84.6),
    (34, 217, 179, 334, 123.2, 254.3),
    (216, 216, 361, 339, 305.6, 252.6),
    (398, 216, 543, 335, 487.2, 253.5),
    (580, 217, 725, 325, 669.6, 253.6),
    (762, 219, 907, 328, 851.6, 255.6),
    (34, 392, 179, 499, 123.6, 428.6),
    (216, 394, 361, 499, 305.2, 431.5),
    (376, 395, 543, 482, 487.2, 432.5),
    (546, 370, 725, 483, 669.2, 433.3),
)
assert len(FRAME_DATA) == FRAMES_PER_FLAP

# 몸 중심 = 눈동자에서 시트 기준 (-18, +8) px (눈은 머리 앞쪽 위에 있으므로)
BODY_FROM_EYE = (-18.0, 8.0)

# 크기 기준: 날개를 내린 프레임(5)의 꼬리 끝~부리 끝 길이 146 px 를 새의 몸길이로 본다
BODY_LENGTH_SHEET_PX = 146
SCALE = BIRD_BODY_LENGTH_PIXEL / BODY_LENGTH_SHEET_PX
HALF_BODY_PIXEL = BIRD_BODY_LENGTH_PIXEL / 2


def _build_frames():
    """프레임별 (clip_left, clip_bottom, clip_w, clip_h, dx, dy, draw_w, draw_h).

    - clip_* : 측정한 실제 영역 그대로 자르므로 잘림도, 이웃 프레임 침범도 없다.
               pico2d clip_draw 는 좌하단 원점이므로 bottom = 시트높이 - 1 - 아래쪽 행.
    - dx, dy : 몸 중심에서 잘라낸 사각형 중심까지의 화면 오프셋(px, y 위쪽 +).
               이 오프셋만큼 옮겨 그리면 프레임마다 사각형 크기/위치가 달라도
               몸통은 화면상 한 점에 고정되어 떨리지 않는다.
    """
    frames = []
    for left, top, right, bottom, eye_x, eye_y in FRAME_DATA:
        w, h = right - left + 1, bottom - top + 1
        body_x, body_y = eye_x + BODY_FROM_EYE[0], eye_y + BODY_FROM_EYE[1]
        center_x, center_y = left + w / 2, top + h / 2
        dx = (center_x - body_x) * SCALE
        dy = -(center_y - body_y) * SCALE  # 시트는 y 아래쪽 +, 화면은 y 위쪽 +
        frames.append((left, SHEET_HEIGHT - 1 - bottom, w, h, dx, dy, w * SCALE, h * SCALE))
    return frames


FRAMES = _build_frames()


class Bird:
    image = None  # 10마리가 하나의 텍스처를 공유 (한 번만 로딩)

    def __init__(self, x=None, y=None):
        if Bird.image is None:
            Bird.image = load_image('bird_animation.png')

        canvas_w, canvas_h = get_canvas_width(), get_canvas_height()
        # 위치: 지정하지 않으면 하늘 영역(화면 높이 45%~92%) 안에서 무작위
        self.x = x if x is not None else random.uniform(HALF_BODY_PIXEL,
                                                        canvas_w - HALF_BODY_PIXEL)
        self.y = y if y is not None else random.uniform(canvas_h * SKY_MIN_RATIO,
                                                        canvas_h * SKY_MAX_RATIO)
        self.dir = random.choice((-1, 1))  # 1: 오른쪽, -1: 왼쪽

        # 개체별 편차: 같은 종이라도 속도와 날갯짓 빈도가 조금씩 다르다
        self.speed = FLY_SPEED_PPS * random.uniform(1 - SPEED_VARIATION, 1 + SPEED_VARIATION)
        self.frames_per_second = FRAMES_PER_SECOND * random.uniform(1 - FLAP_VARIATION,
                                                                    1 + FLAP_VARIATION)
        # 시작 위상을 흩뜨려 10마리가 동시에 똑같이 날갯짓하지 않게 한다
        self.frame = random.uniform(0, FRAMES_PER_FLAP)

    def update(self):
        dt = game_framework.frame_time
        # 날갯짓: 초당 frames_per_second 프레임만큼 진행 (FPS 와 무관하게 약 3 Hz 유지)
        self.frame = (self.frame + self.frames_per_second * dt) % FRAMES_PER_FLAP
        # 비행: 거리 = 속도 x 시간 (등속 운동)
        self.x += self.dir * self.speed * dt
        self.turn_at_edge()

    def turn_at_edge(self):
        """화면 끝에 닿으면 반대로 방향을 바꾼다.

        경계를 넘어간 만큼을 반대쪽으로 반사(x = 2*경계 - x)시켜
        frame_time 이 큰 프레임에서도 이동 거리 손실 없이 정확히 되돌아온다.
        """
        min_x = HALF_BODY_PIXEL
        max_x = get_canvas_width() - HALF_BODY_PIXEL
        if self.x > max_x:
            self.x = 2 * max_x - self.x
            self.dir = -1
        elif self.x < min_x:
            self.x = 2 * min_x - self.x
            self.dir = 1

    def draw(self):
        left, bottom, w, h, dx, dy, draw_w, draw_h = FRAMES[int(self.frame)]
        y = self.y + dy + self.bob_offset()
        if self.dir == 1:
            Bird.image.clip_draw(left, bottom, w, h, self.x + dx, y, draw_w, draw_h)
        else:
            # 원본은 오른쪽을 바라보므로, 왼쪽으로 날 때는 좌우 반전.
            # 그림이 뒤집히므로 몸 중심 기준 x 오프셋도 부호를 바꾼다.
            Bird.image.clip_composite_draw(left, bottom, w, h, 0, 'h',
                                           self.x - dx, y, draw_w, draw_h)

    def bob_offset(self):
        """날갯짓 위상에 맞춘 몸의 상하 오프셋(px).

        위상 = 2π * (frame - 3.5) / 14
        -cos 를 쓰면 다운스트로크 중앙(3.5)에서 최저이면서 위로 가속이 가장 크고,
        이후 상승해 7프레임 뒤(10.5)에서 최고가 된다. 즉 '내려치면 떠오르고,
        들어 올리면 가라앉는' 실제 날갯짓 양력 변화와 위상이 일치한다.
        실수 frame 을 그대로 쓰므로 프레임 사이에서도 부드럽게 보간된다.
        """
        phase = 2 * math.pi * (self.frame - LOWEST_POINT_FRAME) / FRAMES_PER_FLAP
        return -BOB_AMPLITUDE_PIXEL * math.cos(phase)
