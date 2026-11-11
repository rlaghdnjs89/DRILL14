import time
running = False
stack = []


def change_mode(mode):
    if stack:
        stack.pop().finish()
    stack.append(mode)
    mode.init()


def push_mode(mode):
    if stack:
        stack[-1].pause()
    stack.append(mode)
    mode.init()


def pop_mode():
    if stack:
        stack.pop().finish()
    if stack:
        stack[-1].resume()
    else:
        quit()


def quit():
    global running
    running = False

frame_time=0.0

def run(start_mode):
    global running, stack
    running = True
    stack = [start_mode]
    try:
        start_mode.init()
        global frame_time
        frame_time=0.0
        current_time = time.time()

        while running:
            # 0.4초 지연(2.5fps)에서는 렌더 한 번 사이에 날갯짓이 약 17프레임(1.2회) 진행되어
            # 화면상 날개가 거의 멈춘 듯 보이는 시간 앨리어싱이 생긴다.
            # 이동/애니메이션은 frame_time 기반이므로 지연을 줄여도 속도는 변하지 않는다.
            time.sleep(0.01)
            stack[-1].handle_events()
            stack[-1].update()
            stack[-1].render()
            frame_time=time.time()-current_time
            frame_rate=1.0/frame_time if frame_time > 0 else 0.0
            current_time+=frame_time
    
    finally:
        while stack:
            stack.pop().finish()
        running = False
