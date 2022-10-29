from statemachine import StateMachine, State
from utils.hybrid_histogram_policy_worker import HybridHistogramPolicyWorker
from utils.fix_keep_alive_policy_worker import FixKeepAlivePolicyWorker
# A State Machine maintain the state of App's Container
class ContainerStateMachine(StateMachine):   
        release_state = State('Release',initial=True) # State that the container is neither in prewarm window nor keep alive window and is not executing
        prewarm_state = State('Prewarm-window')
        keep_alive_state = State('Keep-alive-window')
        execution_state = State('Execution')
                
        enter_keep_alive = prewarm_state.to(keep_alive_state)
        warm_start_in_keep_alive = keep_alive_state.to(execution_state)
        cold_start_in_prewarm = prewarm_state.to(execution_state)
        release_after_keep_alive = keep_alive_state.to(release_state)
        cold_start_from_release = release_state.to(execution_state)
        enter_prewarm = execution_state.to(prewarm_state)
        
        #If the container's prewarm window is 0
        execu_to_keep_alive = execution_state.to(keep_alive_state)
    
class Container(object)   
    def __init__(self, app, container_id, policy_worker):
        self.app = app
        self.container_id = container_id
        self.container_memory = app.app_memory
        # self.prewarm_window = prewarm_window
        # self.keep_alive_window = keep_alive_window
        self.container_state = ContainerStateMachine()
        self.clock = 0
        
        self.policy_worker = policy_worker
        
    def set_keep_alive_window(self, keep_alive_window):
        self.keep_alive_window = keep_alive_window
        
    def set_prewarm_window(self, prewarm_window):
        self.prewarm_window = prewarm_window 
        
    def set_execute_duration(self, execute_duration):
        self.execute_duration = execute_duration
        
    def get_container_state(self):
        state = self.container_state.current_state
        print("current state info: ", state)
        return state
    
    # check whether the container is in busy before call next invoc
    def is_idle(self):
        if not self.container_state.is_execution_state():
            return True
    # invoc call before tik_tok
    def invoc_event(self, invoc_func_id):
        self.execute_duration = self.app.get_function_duration(invoc_func_id)
        self.trigger_invoc = True
        self.new_execu_start_time = self.clock
    
    def get_idle_time(self):
        #idle time = last execution end time - new execution start time
        idle_time = self.new_execu_start_time - self.last_execu_end_time
        return idle_time
        
    def tik_tok(self):
        if self.container_state.is_release_state():
            if self.trigger_invoc:
                self.container_state.cold_start_from_release()
                print("*"*30)
                print("cold start from release")
                print("start execution")
                print("*"*30)
            
        if self.container_state.is_execution_state():
            if self.execute_duration > 0:
                self.execute_duration -= 1
                print("-"*15)
                print("executing")
                print("estimated remain time: ", self.execute_duration)
                print("-"*15)
            else:
                self.last_execu_end_time = self.clock 
                # if prewarm window is 0, then the container will enter keep alive window
                if self.prewarm_window > 0:
                    self.container_state.enter_prewarm()
                    print("*"*20)
                    print("execution finished")
                    print("enter prewarm window")
                    print("window size: ", self.prewarm_window)
                    print("*"*20)
                else:
                    self.container_state.execu_to_keep_alive()
                    print("*"*20)
                    print("execution finished")
                    print("enter keep alive window")
                    print("window size: ", self.keep_alive_window)
                    print("*"*20)
            
        if self.container_state.is_prewarm_state():
            if self.trigger_invoc:
                self.container_state.cold_start_in_prewarm()
                print("*"*30)
                print("cold start in prewarm window")
                print("start execution")
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
                print("start execution")
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