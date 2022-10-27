from statemachine import StateMachine, State
# A State Machine to control the state of App's Container
class ContainerStateMachine(StateMachine):
    def __init__(self, container_id, container_memory, container_start_time, container_duration, app_list):
        dead = State('dead', initial=True)
        alive = State('alive')
        
        cold_start = dead.to(alive)
        warm_start = alive.to(alive)
        close = alive.to(dead)
        
    
        