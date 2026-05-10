# -*- coding: utf-8 -*-
"""
地球online - 主程序入口
作者：Zmccyy
版本：0.1
"""

import json
import os
import sys
from player import Player
from ui import UI
from tasks import TaskSystem
from events import EventSystem

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class Game:
    def __init__(self):
        self.player = None
        self.ui = UI()
        self.task_system = TaskSystem()
        self.event_system = EventSystem()
        self.running = True
    
    def start(self):
        """游戏启动"""
        self.ui.show_welcome()
        
        while self.running:
            choice = self.ui.show_main_menu()
            
            if choice == "1":
                self.new_game()
            elif choice == "2":
                self.load_game()
            elif choice == "3":
                self.show_help()
            elif choice == "4":
                self.quit_game()
    
    def new_game(self):
        """开始新游戏"""
        self.ui.clear_screen()
        print("=== 创建角色 ===")
        name = input("请输入你的名字：")
        
        print("\n请选择你的身份：")
        print("1. 学生 - 智力+5，擅长学习")
        print("2. 上班族 - 财富+500，擅长赚钱")
        print("3. 科学家 - 智力+10，擅长研究")
        print("4. 探险家 - 体力+10，擅长探索")
        
        identity_choice = input("请选择（1-4）：")
        identity_map = {
            "1": "student",
            "2": "worker",
            "3": "scientist",
            "4": "explorer"
        }
        
        identity = identity_map.get(identity_choice, "student")
        
        self.player = Player(name, identity)
        self.ui.show_message(f"欢迎来到地球online，{name}！")
        
        self.game_loop()
    
    def game_loop(self):
        """游戏主循环"""
        while self.running:
            self.ui.show_game_status(self.player)
            choice = self.ui.show_game_menu()
            
            if choice == "1":
                self.do_task()
            elif choice == "2":
                self.show_inventory()
            elif choice == "3":
                self.show_skills()
            elif choice == "4":
                self.show_achievements()
            elif choice == "5":
                self.save_game()
            elif choice == "6":
                self.quit_game()
    
    def do_task(self):
        """执行任务"""
        tasks = self.task_system.get_available_tasks(self.player)
        
        print("\n=== 可用任务 ===")
        for i, task in enumerate(tasks, 1):
            print(f"[{i}] {task['name']} - {task['description']}")
        
        choice = input("\n请选择任务（输入数字，0返回）：")
        
        if choice == "0":
            return
        
        try:
            task_index = int(choice) - 1
            if 0 <= task_index < len(tasks):
                task = tasks[task_index]
                success, message = self.task_system.execute_task(self.player, task["id"])
                
                if success:
                    self.ui.show_message(message)
                    
                    event = self.event_system.check_random_event(self.player)
                    if event:
                        pass
                else:
                    self.ui.show_message(message)
        except ValueError:
            self.ui.show_message("无效的选择")
    
    def show_inventory(self):
        """查看背包"""
        self.ui.clear_screen()
        print("=== 背包 ===")
        if not self.player.inventory:
            print("背包是空的")
        else:
            for i, item in enumerate(self.player.inventory, 1):
                print(f"[{i}] {item}")
        input("\n按回车键返回...")
    
    def show_skills(self):
        """查看技能"""
        self.ui.clear_screen()
        print("=== 技能 ===")
        if not self.player.skills:
            print("还没有技能")
        else:
            for skill, level in self.player.skills.items():
                print(f"{skill}: 等级 {level}")
        input("\n按回车键返回...")
    
    def show_achievements(self):
        """查看成就"""
        self.ui.clear_screen()
        print("=== 成就 ===")
        print("暂未实现，敬请期待...")
        input("\n按回车键返回...")
    
    def save_game(self):
        """保存游戏"""
        if self.player:
            save_data = self.player.to_dict()
            
            if not os.path.exists('saves'):
                os.makedirs('saves')
            
            filename = f"saves/{self.player.name}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.ui.show_message("游戏已保存！")
    
    def load_game(self):
        """读取游戏"""
        self.ui.clear_screen()
        print("=== 读取存档 ===")
        
        if not os.path.exists('saves'):
            self.ui.show_message("没有找到存档")
            return
        
        saves = os.listdir('saves')
        if not saves:
            self.ui.show_message("没有找到存档")
            return
        
        print("可用的存档：")
        for i, save_file in enumerate(saves, 1):
            name = save_file.replace('.json', '')
            print(f"[{i}] {name}")
        
        choice = input("\n请选择存档（输入数字，0返回）：")
        
        if choice == "0":
            return
        
        try:
            save_index = int(choice) - 1
            if 0 <= save_index < len(saves):
                save_file = saves[save_index]
                filename = f"saves/{save_file}"
                
                with open(filename, 'r', encoding='utf-8') as f:
                    save_data = json.load(f)
                
                self.player = Player("", "")
                self.player.from_dict(save_data)
                
                self.ui.show_message(f"成功加载存档：{self.player.name}")
                self.game_loop()
        except (ValueError, IndexError):
            self.ui.show_message("无效的选择")
    
    def show_help(self):
        """显示帮助"""
        self.ui.clear_screen()
        print("=== 游戏帮助 ===")
        print("地球online是一款模拟现实生活的文本游戏")
        print("你可以选择不同的身份，完成任务，提升属性")
        print("体验真实的人生模拟！")
        input("\n按回车键返回...")
    
    def quit_game(self):
        """退出游戏"""
        self.ui.show_message("感谢游玩地球online！再见！")
        self.running = False

if __name__ == "__main__":
    game = Game()
    game.start()
