"""
界面系统
"""

import os
import sys

class UI:
    def __init__(self):
        self.width = 50
        self.setup_encoding()
    
    def setup_encoding(self):
        """设置编码"""
        if sys.platform == 'win32':
            os.system('chcp 65001 > nul')
    
    def clear_screen(self):
        """清屏"""
        if sys.platform == 'win32':
            os.system('cls && chcp 65001 > nul')
        else:
            os.system('clear')
    
    def get_display_width(self, text):
        """获取字符串的显示宽度（中文字符占2个宽度）"""
        width = 0
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                width += 2
            else:
                width += 1
        return width
    
    def pad_string(self, text, width, align='left'):
        """填充字符串到指定宽度"""
        current_width = self.get_display_width(text)
        padding = width - current_width
        
        if padding <= 0:
            return text
        
        if align == 'center':
            left_pad = padding // 2
            right_pad = padding - left_pad
            return ' ' * left_pad + text + ' ' * right_pad
        elif align == 'right':
            return ' ' * padding + text
        else:
            return text + ' ' * padding
    
    def show_welcome(self):
        """显示欢迎界面"""
        self.clear_screen()
        print("╔" + "═" * (self.width - 2) + "╗")
        print("║" + self.pad_string("欢迎来到", self.width - 2, 'center') + "║")
        print("║" + self.pad_string("地球online", self.width - 2, 'center') + "║")
        print("║" + self.pad_string("现实生活模拟器", self.width - 2, 'center') + "║")
        print("╚" + "═" * (self.width - 2) + "╝")
        print()
        input("按回车键继续...")
    
    def show_main_menu(self):
        """显示主菜单"""
        self.clear_screen()
        print("╔" + "═" * (self.width - 2) + "╗")
        print("║" + self.pad_string("主菜单", self.width - 2, 'center') + "║")
        print("╠" + "═" * (self.width - 2) + "╣")
        print("║" + " " * (self.width - 2) + "║")
        print("║" + self.pad_string("[1] 开始新游戏", self.width - 2) + "║")
        print("║" + self.pad_string("[2] 读取存档", self.width - 2) + "║")
        print("║" + self.pad_string("[3] 游戏帮助", self.width - 2) + "║")
        print("║" + self.pad_string("[4] 退出游戏", self.width - 2) + "║")
        print("║" + " " * (self.width - 2) + "║")
        print("╚" + "═" * (self.width - 2) + "╝")
        
        return input("请选择：")
    
    def show_game_status(self, player):
        """显示游戏状态"""
        self.clear_screen()
        print("╔" + "═" * (self.width - 2) + "╗")
        
        title = f"{player.name} | {self.get_identity_name(player.identity)} | Lv.{player.level}"
        print("║" + self.pad_string(title, self.width - 2, 'center') + "║")
        
        print("╠" + "─" * (self.width - 2) + "╣")
        
        stats_text = f"智力:{player.stats['intelligence']} 体力:{player.stats['strength']} 社交:{player.stats['social']} 财富:{player.stats['wealth']}"
        print("║" + self.pad_string(stats_text, self.width - 2, 'center') + "║")
        
        resources_text = f"精力:{player.resources['energy']}/100 饱食:{player.resources['hunger']}/100 快乐:{player.resources['happiness']}/100"
        print("║" + self.pad_string(resources_text, self.width - 2, 'center') + "║")
        
        print("╚" + "═" * (self.width - 2) + "╝")
        print()
    
    def show_game_menu(self):
        """显示游戏菜单"""
        print("[1] 执行任务  [2] 查看背包")
        print("[3] 查看技能  [4] 查看成就")
        print("[5] 保存游戏  [6] 退出游戏")
        print()
        return input("请选择：")
    
    def show_message(self, message):
        """显示消息"""
        print()
        msg_width = self.get_display_width(message)
        
        print("┌" + "─" * (msg_width + 2) + "┐")
        print("│ " + message + " │")
        print("└" + "─" * (msg_width + 2) + "┘")
        input("\n按回车键继续...")
    
    def get_identity_name(self, identity):
        """获取身份中文名"""
        names = {
            "student": "学生",
            "worker": "上班族",
            "scientist": "科学家",
            "explorer": "探险家"
        }
        return names.get(identity, "未知")
