"""
事件系统
"""

import json
import random

class EventSystem:
    def __init__(self):
        self.events = self.load_events()
    
    def load_events(self):
        """加载事件数据"""
        try:
            with open('data/events.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("警告：未找到事件数据文件")
            return {"random_events": []}
    
    def check_random_event(self, player):
        """检查是否触发随机事件"""
        for event in self.events["random_events"]:
            if random.random() < event["probability"]:
                self.trigger_event(player, event)
                return event
        return None
    
    def trigger_event(self, player, event):
        """触发事件"""
        print("\n" + "=" * 50)
        print(f"【{event['name']}】")
        print(event['description'])
        print("=" * 50)
        
        if "effects" in event:
            for effect, amount in event["effects"].items():
                if effect in player.stats:
                    player.stats[effect] += amount
                elif effect in player.resources:
                    player.update_resource(effect, amount)
        
        input("\n按回车键继续...")
