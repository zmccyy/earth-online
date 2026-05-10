# -*- coding: utf-8 -*-
"""
地球online - 自动化测试脚本
"""

import sys
import os
import json
import io

# 设置编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from player import Player
from tasks import TaskSystem
from events import EventSystem
from ui import UI

def test_player_creation():
    """测试玩家创建"""
    print("\n=== 测试1: 玩家创建 ===")
    
    # 测试学生身份
    player1 = Player("测试学生", "student")
    print(f"✓ 学生创建成功: {player1.name}")
    print(f"  智力: {player1.stats['intelligence']} (应为15)")
    assert player1.stats['intelligence'] == 15, "学生智力加成错误"
    
    # 测试上班族身份
    player2 = Player("测试上班族", "worker")
    print(f"✓ 上班族创建成功: {player2.name}")
    print(f"  财富: {player2.stats['wealth']} (应为1500)")
    assert player2.stats['wealth'] == 1500, "上班族财富加成错误"
    
    # 测试科学家身份
    player3 = Player("测试科学家", "scientist")
    print(f"✓ 科学家创建成功: {player3.name}")
    print(f"  智力: {player3.stats['intelligence']} (应为20)")
    assert player3.stats['intelligence'] == 20, "科学家智力加成错误"
    
    # 测试探险家身份
    player4 = Player("测试探险家", "explorer")
    print(f"✓ 探险家创建成功: {player4.name}")
    print(f"  体力: {player4.stats['strength']} (应为20)")
    assert player4.stats['strength'] == 20, "探险家体力加成错误"
    
    print("✓ 所有身份创建测试通过！\n")
    return player1

def test_task_system(player):
    """测试任务系统"""
    print("=== 测试2: 任务系统 ===")
    
    task_system = TaskSystem()
    
    # 测试任务加载
    tasks = task_system.tasks
    print(f"✓ 任务数据加载成功: {len(tasks['daily_tasks'])}个任务")
    
    # 测试获取可用任务
    available_tasks = task_system.get_available_tasks(player)
    print(f"✓ 获取可用任务: {len(available_tasks)}个")
    
    # 测试执行任务
    initial_wealth = player.stats['wealth']
    initial_hunger = player.resources['hunger']
    
    # 先消耗一些饱食度，以便测试恢复
    player.update_resource('hunger', -50)
    initial_hunger = player.resources['hunger']
    
    # 执行吃早餐任务
    success, message = task_system.execute_task(player, "eat_breakfast")
    print(f"✓ 执行任务'吃早餐': {message}")
    assert success, "任务执行失败"
    assert player.stats['wealth'] == initial_wealth - 10, "金钱消耗错误"
    # 饱食度应该增加30，但不超过100
    expected_hunger = min(100, initial_hunger + 30)
    assert player.resources['hunger'] == expected_hunger, f"饱食度恢复错误，应为{expected_hunger}，实际为{player.resources['hunger']}"
    
    # 测试身份专属任务
    player_worker = Player("测试工人", "worker")
    available_worker = task_system.get_available_tasks(player_worker)
    has_work_task = any(task['id'] == 'go_to_work' for task in available_worker)
    print(f"✓ 上班族可执行'上班打卡': {has_work_task}")
    assert has_work_task, "上班族应该能看到上班任务"
    
    # 测试学生专属任务
    player_student = Player("测试学生", "student")
    available_student = task_system.get_available_tasks(player_student)
    has_study_task = any(task['id'] == 'study' for task in available_student)
    print(f"✓ 学生可执行'学习充电': {has_study_task}")
    assert has_study_task, "学生应该能看到学习任务"
    
    print("✓ 任务系统测试通过！\n")

def test_event_system(player):
    """测试事件系统"""
    print("=== 测试3: 事件系统 ===")
    
    event_system = EventSystem()
    
    # 测试事件加载
    events = event_system.events
    print(f"✓ 事件数据加载成功: {len(events['random_events'])}个事件")
    
    # 测试事件触发（模拟多次触发）
    triggered_count = 0
    for i in range(100):
        initial_wealth = player.stats['wealth']
        event = event_system.check_random_event(player)
        if event:
            triggered_count += 1
            print(f"✓ 触发事件: {event['name']}")
    
    print(f"✓ 100次检查中触发了{triggered_count}次事件")
    print("✓ 事件系统测试通过！\n")

def test_resource_management(player):
    """测试资源管理"""
    print("=== 测试4: 资源管理 ===")
    
    # 测试资源更新
    initial_energy = player.resources['energy']
    player.update_resource('energy', -20)
    print(f"✓ 精力消耗: {initial_energy} -> {player.resources['energy']}")
    assert player.resources['energy'] == initial_energy - 20, "精力消耗错误"
    
    # 测试资源上限
    player.update_resource('energy', 200)
    print(f"✓ 精力上限测试: {player.resources['energy']} (应为100)")
    assert player.resources['energy'] == 100, "精力应该有上限100"
    
    # 测试资源下限
    player.update_resource('energy', -200)
    print(f"✓ 精力下限测试: {player.resources['energy']} (应为0)")
    assert player.resources['energy'] == 0, "精力应该有下限0"
    
    # 恢复资源
    player.update_resource('energy', 50)
    
    print("✓ 资源管理测试通过！\n")

def test_level_system(player):
    """测试升级系统"""
    print("=== 测试5: 升级系统 ===")
    
    initial_level = player.level
    initial_exp = player.experience
    
    # 添加经验值
    player.add_experience(100)
    print(f"✓ 获得100经验值")
    print(f"  等级: {initial_level} -> {player.level}")
    print(f"  经验: {initial_exp} -> {player.experience}")
    
    assert player.level == initial_level + 1, "应该升级了"
    assert player.experience == 0, "升级后经验应该清零"
    
    print("✓ 升级系统测试通过！\n")

def test_save_load(player):
    """测试存档系统"""
    print("=== 测试6: 存档系统 ===")
    
    # 保存游戏
    save_data = player.to_dict()
    print(f"✓ 存档数据生成成功")
    print(f"  玩家名: {save_data['name']}")
    print(f"  身份: {save_data['identity']}")
    print(f"  等级: {save_data['level']}")
    
    # 创建新玩家并加载数据
    new_player = Player("", "")
    new_player.from_dict(save_data)
    print(f"✓ 存档数据加载成功")
    
    # 验证数据一致性
    assert new_player.name == player.name, "名字不一致"
    assert new_player.identity == player.identity, "身份不一致"
    assert new_player.level == player.level, "等级不一致"
    assert new_player.stats == player.stats, "属性不一致"
    
    print("✓ 存档系统测试通过！\n")

def test_ui_system():
    """测试UI系统"""
    print("=== 测试7: UI系统 ===")
    
    ui = UI()
    
    # 测试宽度计算
    test_str = "测试中文"
    width = ui.get_display_width(test_str)
    print(f"✓ 字符串'{test_str}'显示宽度: {width} (应为8)")
    assert width == 8, "中文宽度计算错误"
    
    test_str2 = "test123"
    width2 = ui.get_display_width(test_str2)
    print(f"✓ 字符串'{test_str2}'显示宽度: {width2} (应为7)")
    assert width2 == 7, "英文宽度计算错误"
    
    # 测试字符串填充
    padded = ui.pad_string("测试", 10, 'center')
    print(f"✓ 居中填充: '{padded}' (宽度应为10)")
    assert ui.get_display_width(padded) == 10, "填充宽度错误"
    
    print("✓ UI系统测试通过！\n")

def test_complete_gameplay():
    """测试完整游戏流程"""
    print("=== 测试8: 完整游戏流程 ===")
    
    # 创建玩家
    player = Player("完整测试玩家", "worker")
    print(f"✓ 创建玩家: {player.name} (上班族)")
    
    # 初始化系统
    task_system = TaskSystem()
    event_system = EventSystem()
    
    # 模拟一天的游戏
    print("\n模拟一天的游戏流程:")
    
    # 早上：吃早餐
    print("\n1. 早上：吃早餐")
    success, msg = task_system.execute_task(player, "eat_breakfast")
    print(f"   {msg}")
    print(f"   状态: 精力={player.resources['energy']}, 饱食={player.resources['hunger']}, 快乐={player.resources['happiness']}")
    
    # 上午：上班
    print("\n2. 上午：上班打卡")
    success, msg = task_system.execute_task(player, "go_to_work")
    print(f"   {msg}")
    print(f"   状态: 精力={player.resources['energy']}, 饱食={player.resources['hunger']}, 财富={player.stats['wealth']}")
    
    # 中午：吃午餐
    print("\n3. 中午：吃午餐")
    success, msg = task_system.execute_task(player, "eat_lunch")
    print(f"   {msg}")
    print(f"   状态: 精力={player.resources['energy']}, 饱食={player.resources['hunger']}")
    
    # 下午：继续工作或休息
    print("\n4. 下午：休息放松")
    success, msg = task_system.execute_task(player, "rest")
    print(f"   {msg}")
    print(f"   状态: 精力={player.resources['energy']}, 快乐={player.resources['happiness']}")
    
    # 晚上：社交
    print("\n5. 晚上：社交活动")
    success, msg = task_system.execute_task(player, "socialize")
    print(f"   {msg}")
    print(f"   状态: 社交={player.stats['social']}, 快乐={player.resources['happiness']}")
    
    # 睡觉
    print("\n6. 深夜：睡觉")
    success, msg = task_system.execute_task(player, "sleep")
    print(f"   {msg}")
    print(f"   状态: 精力={player.resources['energy']}, 饱食={player.resources['hunger']}")
    
    # 检查随机事件
    print("\n7. 检查随机事件")
    event = event_system.check_random_event(player)
    if event:
        print(f"   触发事件: {event['name']}")
    else:
        print("   未触发事件")
    
    # 最终状态
    print("\n=== 最终状态 ===")
    print(f"玩家: {player.name}")
    print(f"等级: Lv.{player.level}")
    print(f"经验: {player.experience}/{player.level * 100}")
    print(f"属性: 智力={player.stats['intelligence']}, 体力={player.stats['strength']}, 社交={player.stats['social']}, 财富={player.stats['wealth']}")
    print(f"资源: 精力={player.resources['energy']}, 饱食={player.resources['hunger']}, 快乐={player.resources['happiness']}")
    print(f"完成任务数: {len(player.completed_tasks)}")
    
    print("\n✓ 完整游戏流程测试通过！\n")

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("地球online - 自动化测试")
    print("="*60)
    
    try:
        # 运行所有测试
        player = test_player_creation()
        test_task_system(player)
        test_event_system(player)
        test_resource_management(player)
        test_level_system(player)
        test_save_load(player)
        test_ui_system()
        test_complete_gameplay()
        
        print("\n" + "="*60)
        print("✓ 所有测试通过！游戏功能正常！")
        print("="*60 + "\n")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
