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

# 새 크기: 스프라이트 한 프레임의 폭을 1.5 m 로 본다
BIRD_SIZE_M = 1.5
BIRD_SIZE_PIXEL = BIRD_SIZE_M * PIXEL_PER_METER

# 날갯짓: 중대형 조류의 날갯짓 빈도(2~5 Hz) 범위
FLAPS_PER_SECOND = 3.0          # 1초에 날갯짓 3회
FRAMES_PER_FLAP = 14            # 시트의 14프레임이 날갯짓 한 주기
FRAMES_PER_SECOND = FLAPS_PER_SECOND * FRAMES_PER_FLAP

# ---------------------------------------------------------------------------
# 스프라이트 시트 (bird_animation.png : 918 x 506, 5열 x 3행, 14프레임)
# ---------------------------------------------------------------------------
SHEET_WIDTH, SHEET_HEIGHT = 918, 506
SHEET_COLS, SHEET_ROWS = 5, 3
CELL_WIDTH = SHEET_WIDTH / SHEET_COLS    # 183.6 (정수로 나누어 떨어지지 않음)
CELL_HEIGHT = SHEET_HEIGHT / SHEET_ROWS  # 168.67
FRAME_W, FRAME_H = 183, 168              # 실제로 잘라낼 크기


def _build_frame_rects():
    """프레임 번호 -> (left, bottom, width, height) 클리핑 사각형 목록.

    시트는 위 행부터 왼쪽→오른쪽으로 재생되지만 pico2d 의 clip_draw 는
    좌하단 원점이므로 bottom = 시트높이 - top - 높이 로 변환한다.
    셀 폭이 183.6 px 이므로 left 는 누적 오차가 없도록 col * 183.6 을 내림한다.
    (알파 채널 분석으로 14프레임 모두 잘림/이웃 프레임 섞임이 없음을 확인)
    """
    rects = []
    for i in range(FRAMES_PER_FLAP):
        row, col = divmod(i, SHEET_COLS)
        left = int(col * CELL_WIDTH)
        top = int(row * CELL_HEIGHT)
        bottom = SHEET_HEIGHT - top - FRAME_H
        rects.append((left, bottom, FRAME_W, FRAME_H))
    return rects


FRAME_RECTS = _build_frame_rects()


# 화면에 그릴 크기: 프레임 폭을 BIRD_SIZE_PIXEL 로 맞추고 세로는 원본 비율 유지
DRAW_W = BIRD_SIZE_PIXEL
DRAW_H = BIRD_SIZE_PIXEL * FRAME_H / FRAME_W


class Bird:
    image = None  # 10마리가 하나의 텍스처를 공유 (한 번만 로딩)

    def __init__(self, x=400, y=400):
        if Bird.image is None:
            Bird.image = load_image('bird_animation.png')
        self.x, self.y = x, y
        self.frame = 0.0
        self.dir = 1                 # 1: 오른쪽, -1: 왼쪽
        self.speed = FLY_SPEED_PPS   # px/s

    def update(self):
        dt = game_framework.frame_time
        # 날갯짓: 초당 FRAMES_PER_SECOND 프레임만큼 진행 (FPS 와 무관하게 3 Hz 유지)
        self.frame = (self.frame + FRAMES_PER_SECOND * dt) % FRAMES_PER_FLAP
        # 비행: 거리 = 속도 x 시간 (등속 운동)
        self.x += self.dir * self.speed * dt

    def draw(self):
        left, bottom, w, h = FRAME_RECTS[int(self.frame)]
        Bird.image.clip_draw(left, bottom, w, h, self.x, self.y, DRAW_W, DRAW_H)
