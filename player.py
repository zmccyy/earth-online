"""
玩家系统
"""

class Player:
    def __init__(self, name, identity):
        self.name = name
        self.identity = identity
        self.level = 1
        self.experience = 0
        
        self.stats = {
            "intelligence": 10,
            "strength": 10,
            "social": 10,
            "wealth": 1000
        }
        
        self.apply_identity_bonus()
        
        self.resources = {
            "energy": 100,
            "hunger": 100,
            "happiness": 50
        }
        
        self.skills = {}
        
        self.inventory = []
        
        self.completed_tasks = []
    
    def apply_identity_bonus(self):
        """应用身份加成"""
        bonuses = {
            "student": {"intelligence": 5},
            "worker": {"wealth": 500},
            "scientist": {"intelligence": 10},
            "explorer": {"strength": 10}
        }
        
        if self.identity in bonuses:
            for stat, bonus in bonuses[self.identity].items():
                self.stats[stat] += bonus
    
    def update_stat(self, stat_name, amount):
        """更新属性"""
        if stat_name in self.stats:
            self.stats[stat_name] += amount
            return True
        return False
    
    def update_resource(self, resource_name, amount):
        """更新资源"""
        if resource_name in self.resources:
            self.resources[resource_name] += amount
            self.resources[resource_name] = max(0, min(100, self.resources[resource_name]))
            return True
        return False
    
    def add_experience(self, amount):
        """增加经验值"""
        self.experience += amount
        
        exp_needed = self.level * 100
        if self.experience >= exp_needed:
            self.level_up()
    
    def level_up(self):
        """升级"""
        self.level += 1
        self.experience = 0
        print(f"恭喜！你升到了 {self.level} 级！")
    
    def to_dict(self):
        """转换为字典（用于保存）"""
        return {
            "name": self.name,
            "identity": self.identity,
            "level": self.level,
            "experience": self.experience,
            "stats": self.stats,
            "resources": self.resources,
            "skills": self.skills,
            "inventory": self.inventory,
            "completed_tasks": self.completed_tasks
        }
    
    def from_dict(self, data):
        """从字典加载（用于读取存档）"""
        self.name = data["name"]
        self.identity = data["identity"]
        self.level = data["level"]
        self.experience = data["experience"]
        self.stats = data["stats"]
        self.resources = data["resources"]
        self.skills = data["skills"]
        self.inventory = data["inventory"]
        self.completed_tasks = data["completed_tasks"]
