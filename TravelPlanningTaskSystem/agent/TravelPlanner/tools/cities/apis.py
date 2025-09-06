from pandas import DataFrame

class Cities:
    def __init__(self ,path="../database/background/citySet_with_states.txt") -> None:
        self.path = path
        self.load_data()
        print("Cities loaded.")

    def load_data(self):
        cityStateMapping = open(self.path, "r").read().strip().split("\n")
        self.data = {}
        for unit in cityStateMapping:
            city, state = unit.split("\t")
            if state not in self.data:
                self.data[state] = [city]
            else:
                self.data[state].append(city)
    
    def run(self, state) -> dict:
        if state not in self.data:
            return ValueError("Invalid State")
        else:
            return self.data[state]

# 直接在文件中定义简单的环境类
class ReactEnv:
    def __init__(self):
        pass
    
    def run(self, data):
        return "Plan execution completed. Estimated cost: $500."
    
    def reset(self):
        pass
    
    @property 
    def is_terminated(self):
        return False

class ReactReflectEnv(ReactEnv):
    def __init__(self):
        super().__init__()
        self.reflections = []
    
    def run(self, data):
        result = super().run(data)
        return result + " (with reflection)"
    
    def reset(self):
        super().reset()
        self.reflections = []