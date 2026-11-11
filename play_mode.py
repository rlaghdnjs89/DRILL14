from pico2d import *
import game_world
import game_framework
from boy import Boy
from grass import Grass
from bird import Bird

BIRD_COUNT = 10

boy = None


def handle_events():


    event_list = get_events()
    for event in event_list:
        if event.type == SDL_QUIT:
            game_framework.quit()
            return
        elif event.type == SDL_KEYDOWN and event.key == SDLK_ESCAPE:
            game_framework.quit()
        else:
            boy.handle_event(event)


def init():
    global boy

    boy = Boy()
    game_world.add_oject(boy)

    grass = Grass()
    game_world.add_oject(grass, 0)

    # 새떼: 10마리를 오브젝트 레이어에 등록 (game_world.update/render 가 일괄 처리)
    for _ in range(BIRD_COUNT):
        game_world.add_oject(Bird(), 1)


def pause():
    boy.pause()


def resume():
    pass


def finish():
    global boy
    game_world.clear()
    boy = None


def update():
    game_world.update()

def render():
    clear_canvas()
    game_world.render()
    update_canvas()









