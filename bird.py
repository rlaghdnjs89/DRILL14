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
