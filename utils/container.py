from statemachine import StateMachine, State
# A State Machine to control the state of App's Container
class ContainerStateMachine(StateMachine):   
        release_state = State('Release',initial=True) # State that the container is neither in prewarm window nor keep alive window and is not executing
        prewarm_state = State('Prewarm-window')
        keep_alive_state = State('Keep-alive-window')
        excution_state = State('Excution')
                
        enter_keep_alive = prewarm_state.to(keep_alive_state)
        warm_start_in_keep_alive = keep_alive_state.to(excution_state)
        cold_start_in_prewarm = prewarm_state.to(excution_state)
        release_after_keep_alive = keep_alive_state.to(release_state)
        cold_start_from_release = release_state.to(excution_state)
        enter_prewarm = excution_state.to(prewarm_state)
    
class Container(object)   
    def __init__(self, app, container_id):
        self.app = app
        self.container_id = container_id
        self.container_memory = app.app_memory
        # self.prewarm_window = prewarm_window
        # self.keep_alive_window = keep_alive_window
        self.container_state = ContainerStateMachine()
        self.clock = 0
        
    def set_keep_alive_window(self, keep_alive_window):
        self.keep_alive_window = keep_alive_window
        
    def set_prewarm_window(self, prewarm_window):
        self.prewarm_window = prewarm_window 
        
    def set_excute_duration(self, excute_duration):
        self.excute_duration = excute_duration
        
    def get_container_state(self):
        state = self.container_state.current_state
        print("current state info: ", state)
        return state
    
    # check whether the container is in busy befor call next invoc
    def is_idle(self):
        if not self.container_state.is_excution_state():
            return True
    # invoc call before tik_tok
    def invoc_event(self, invoc_func_id):
        self.excute_duration = self.app.get_function_duration(invoc_func_id)
        self.trigger_invoc = True
        self.end_idle_time = self.clock
    
    def get_idle_time(self):
        idle_time = self.end_idle_time - self.start_idle_time
        return idle_time
        
    def tik_tok(self):
        if self.container_state.is_release_state():
            if self.trigger_invoc:
                self.container_state.cold_start_from_release()
                print("*"*30)
                print("cold start from release")
                print("start excution")
                print("*"*30)
            
        if self.container_state.is_excution_state():
            if self.excute_duration > 0:
                self.excute_duration -= 1
                print("-"*15)
                print("excuting")
                print("estimated remain time: ", self.excute_duration)
                print("-"*15)
            else:
                self.start_idle_time = self.clock 
                self.container_state.enter_prewarm()
                print("*"*20)
                print("excution finished")
                print("enter prewarm window")
                print("window size: ", self.prewarm_window)
                print("*"*20)
            
        if self.container_state.is_prewarm_state():
            if self.trigger_invoc:
                self.container_state.cold_start_in_prewarm()
                print("*"*30)
                print("cold start in prewarm window")
                print("start excution")
                print("*"*30)
            else:
                if self.prewarm_window > 0:
                    self.prewarm_window -= 1
                    print("-"*15)
                    print("wating in prewarm window")
                    print("estimated remain prwarm window time: ", self.prewarm_window)
                    print("-"*15)
                else:
                    self.container_state.enter_keep_alive()
                    print("*"*20)
                    print("enter keep alive window")
                    print("window size: ", self.keep_alive_window)
                    print("*"*20)

        if self.container_state.is_keep_alive_state():
            if self.trigger_invoc:
                self.container_state.warm_start_in_keep_alive()
                print("*"*30)
                print("warm start in keep alive window")
                print("start excution")
                print("*"*30)
            else:
                if self.keep_alive_window > 0:
                    self.keep_alive_window -= 1
                    print("-"*15)
                    print("wating in keep alive window")
                    print("estimated remain keep alive window time: ", self.keep_alive_window)
                    print("-"*15)
                else:
                    self.container_state.release_after_keep_alive()
                    print("*"*20)
                    print("release!")
                    print("release resources after keep alive window")
                    print("*"*20)
                
        if self.trigger_invoc:
            self.trigger_invoc = False
        
        self.clock += 1