"""
任务系统
"""

import json

class TaskSystem:
    def __init__(self):
        self.tasks = self.load_tasks()
    
    def load_tasks(self):
        """加载任务数据"""
        try:
            with open('data/tasks.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("警告：未找到任务数据文件")
            return {"daily_tasks": []}
    
    def get_available_tasks(self, player):
        """获取可用任务"""
        available = []
        
        for task in self.tasks["daily_tasks"]:
            if "requirements" in task:
                if "identity" in task["requirements"]:
                    if player.identity != task["requirements"]["identity"]:
                        continue
            
            available.append(task)
        
        return available
    
    def execute_task(self, player, task_id):
        """执行任务"""
        task = self.find_task(task_id)
        
        if not task:
            return False, "任务不存在"
        
        if not self.check_resources(player, task):
            return False, "资源不足，无法执行任务"
        
        self.consume_resources(player, task)
        
        self.give_rewards(player, task)
        
        player.completed_tasks.append(task_id)
        
        return True, f"完成任务：{task['name']}"
    
    def find_task(self, task_id):
        """查找任务"""
        for task in self.tasks["daily_tasks"]:
            if task["id"] == task_id:
                return task
        return None
    
    def check_resources(self, player, task):
        """检查资源是否足够"""
        if "costs" in task:
            for resource, amount in task["costs"].items():
                if resource in player.stats:
                    if player.stats[resource] < amount:
                        return False
                elif resource in player.resources:
                    if player.resources[resource] < amount:
                        return False
        return True
    
    def consume_resources(self, player, task):
        """消耗资源"""
        if "costs" in task:
            for resource, amount in task["costs"].items():
                if resource in player.stats:
                    player.stats[resource] -= amount
                elif resource in player.resources:
                    player.update_resource(resource, -amount)
    
    def give_rewards(self, player, task):
        """给予奖励"""
        if "rewards" in task:
            for reward, amount in task["rewards"].items():
                if reward in player.stats:
                    player.stats[reward] += amount
                elif reward in player.resources:
                    player.update_resource(reward, amount)
                elif reward == "experience":
                    player.add_experience(amount)
