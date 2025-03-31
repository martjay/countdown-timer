#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import glob
import threading
import time
from datetime import timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QSpinBox, QComboBox, QFrame, QMessageBox,
    QDialog, QStyleFactory, QGroupBox, QLineEdit, QListWidget, QListWidgetItem,
    QFormLayout, QDialogButtonBox, QCheckBox, QGridLayout, QScrollBar, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize, QPropertyAnimation, Property, QEasingCurve, QPoint, QUuid
from PySide6.QtGui import QIcon, QFont, QColor, QPalette, QLinearGradient, QGradient, QFontDatabase, QPainter, QPen

import pygame

class ConfirmDialog(QDialog):
    def __init__(self, parent=None, reminder_text="倒计时结束了！"):
        super().__init__(parent)
        self.setWindowTitle("倒计时结束")
        self.reminder_text = reminder_text
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D30;
                color: #FFFFFF;
                border-radius: 10px;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
            }
            QPushButton {
                background-color: #007ACC;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0099FF;
            }
            QPushButton:pressed {
                background-color: #005F99;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 用户自定义提醒文字
        user_reminder_label = QLabel(self.reminder_text)
        user_reminder_label.setStyleSheet("font-size: 20px; color: #FFA000; font-weight: bold; padding: 10px;")
        user_reminder_label.setAlignment(Qt.AlignCenter)
        user_reminder_label.setWordWrap(True)
        
        # 按钮部分 - 使用单独的布局并添加顶部间距
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 15, 0, 0)
        
        self.ok_button = QPushButton("确认并停止播放")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setFixedWidth(180)
        self.ok_button.setFixedHeight(45)
        self.ok_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5252;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #FF7070;
            }
            QPushButton:pressed {
                background-color: #CC4040;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addStretch()
        
        # 添加所有元素到主布局
        layout.addWidget(user_reminder_label)
        layout.addLayout(button_layout)
        layout.addStretch(1)  # 底部添加一些空间
        
        layout.setContentsMargins(25, 25, 25, 25)
        
        self.setMinimumSize(350, 200)
        
        # 创建按钮振动动画效果
        self.createButtonAnimation()
        
    def createButtonAnimation(self):
        """创建按钮振动动画效果"""
        self.anim = QPropertyAnimation(self.ok_button, b"pos")
        self.anim.setDuration(80)
        self.anim.setLoopCount(8)  # 振动4次(来回8次)
        
        # 等待按钮完全渲染后再获取位置
        # 使用一个小的延迟来确保位置已正确计算
        QTimer.singleShot(100, self._setupAnimation)
    
    def _setupAnimation(self):
        """设置动画关键帧"""
        pos = self.ok_button.pos()
        
        # 设置振动关键帧
        self.anim.setKeyValueAt(0, pos)
        self.anim.setKeyValueAt(0.1, pos + QPoint(5, 0))
        self.anim.setKeyValueAt(0.2, pos + QPoint(-5, 0))
        self.anim.setKeyValueAt(0.3, pos + QPoint(5, 0))
        self.anim.setKeyValueAt(0.4, pos + QPoint(-5, 0))
        self.anim.setKeyValueAt(0.5, pos + QPoint(5, 0))
        self.anim.setKeyValueAt(0.6, pos + QPoint(-5, 0))
        self.anim.setKeyValueAt(0.7, pos + QPoint(5, 0))
        self.anim.setKeyValueAt(0.8, pos + QPoint(-5, 0))
        self.anim.setKeyValueAt(0.9, pos + QPoint(5, 0))
        self.anim.setKeyValueAt(1, pos)
        
        # 启动动画
        self.anim.start()
        
        # 每1.8秒重复振动一次
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.restartAnimation)
        self.timer.start(1800)
    
    def restartAnimation(self):
        """重新开始振动动画"""
        if not self.anim.state() == QPropertyAnimation.Running:
            self.anim.start()
            
    def closeEvent(self, event):
        """关闭窗口时停止动画和计时器"""
        self.timer.stop()
        self.anim.stop()
        super().closeEvent(event)

class TimeDisplay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = "00:00:00"
        self._color = QColor("#FF5252")
        self.setFixedHeight(100)
        self.setStyleSheet("background-color: transparent;")
        
    def setText(self, text):
        self.value = text
        self.update()
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        font = QFont("Arial", 46, QFont.Bold)
        painter.setFont(font)
        
        # 绘制阴影
        shadow_color = QColor(0, 0, 0, 100)
        painter.setPen(shadow_color)
        painter.drawText(self.rect().adjusted(3, 3, 3, 3), Qt.AlignCenter, self.value)
        
        # 绘制渐变文本
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self._color)
        gradient.setColorAt(1, QColor("#007ACC"))
        
        painter.setPen(QPen(gradient, 1))
        painter.drawText(self.rect(), Qt.AlignCenter, self.value)
    
    def setColor(self, color):
        self._color = color
        self.update()

class CountdownButton(QPushButton):
    def __init__(self, text, color, parent=None):
        super().__init__(text, parent)
        self.default_color = color
        self.setFixedHeight(38)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 5px 12px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {self._lightenColor(color, 20)};
            }}
            QPushButton:pressed {{
                background-color: {self._darkenColor(color, 20)};
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #888888;
            }}
        """)
    
    def _lightenColor(self, color, amount=20):
        c = QColor(color)
        h, s, l, a = c.getHsl()
        l = min(l + amount, 255)
        c.setHsl(h, s, l, a)
        return c.name()
    
    def _darkenColor(self, color, amount=20):
        c = QColor(color)
        h, s, l, a = c.getHsl()
        l = max(l - amount, 0)
        c.setHsl(h, s, l, a)
        return c.name()

class CountdownTimer(QMainWindow):
    def __init__(self):
        """初始化应用"""
        super().__init__()
        
        # 设置窗口标题和大小
        self.setWindowTitle("倒计时器")
        # 移除固定大小限制，允许窗口自由调整大小
        self.setMinimumSize(500, 400)
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 初始化pygame mixer用于音频播放
        pygame.mixer.init()
        
        # 配置和音频文件目录
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_dir = os.path.join(os.path.expanduser("~"), ".countdown_timer")
        self.audio_dir = os.path.join(self.base_dir, "audio")  # 使用项目目录下的audio文件夹
        self.config_file = os.path.join(self.config_dir, "settings.json")
        
        # 确保目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.audio_dir, exist_ok=True)
        
        # 初始化变量
        self.audio_files = {}  # 存储音频文件映射
        self.tasks = []  # 存储任务列表
        self.task_items = {}  # 存储任务和对应的UI项
        
        # 创建定时器，每秒更新一次
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_all_tasks)
        self.timer.start(1000)  # 1000毫秒 = 1秒
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 创建UI并添加到主布局
        self.task_group = self._create_ui()
        main_layout.addWidget(self.task_group)
        
        # 设置黑暗主题
        self._set_dark_theme()
        
        # 刷新音频文件列表
        self._refresh_audio_files()
        
        # 加载配置
        self._load_config()
        
        # 初始化任务列表
        self._init_task_list()

    def _set_dark_theme(self):
        """设置暗黑主题"""
        dark_palette = QPalette()
        
        # 设置颜色
        dark_palette.setColor(QPalette.Window, QColor(45, 45, 48))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(37, 37, 38))
        dark_palette.setColor(QPalette.AlternateBase, QColor(50, 50, 52))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(60, 60, 62))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 82, 82))
        dark_palette.setColor(QPalette.Link, QColor(0, 122, 204))
        dark_palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
        dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # 设置禁用状态的颜色
        dark_palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(128, 128, 128))
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(128, 128, 128))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(128, 128, 128))
        
        self.setPalette(dark_palette)
        
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D30;
            }
            QWidget {
                background-color: #2D2D30;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QSpinBox {
                background-color: #333337;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                min-height: 25px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #444444;
                width: 16px;
                border-radius: 2px;
            }
            QComboBox {
                background-color: #333337;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
                min-height: 25px;
            }
            QComboBox::drop-down {
                background-color: #444444;
                width: 20px;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QComboBox QAbstractItemView {
                background-color: #333337;
                color: #FFFFFF;
                selection-background-color: #007ACC;
            }
            QGroupBox {
                border: 1px solid #3C3C3C;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                color: #CCCCCC;
            }
        """)
    
    def _create_ui(self):
        """创建用户界面"""
        # 任务列表
        task_group = QGroupBox("任务列表")
        task_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #3C3C3C;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        task_layout = QVBoxLayout(task_group)
        task_layout.setContentsMargins(10, 15, 10, 10)
        task_layout.setSpacing(10)

        # 任务列表控件
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                border: 1px solid #3C3C3C;
                border-radius: 6px;
                outline: none;
                padding: 5px;
            }
            QListWidget::item {
                border: none;
                padding-top: 3px;
                padding-bottom: 3px;
            }
            QListWidget::item:selected {
                background: transparent;
                color: inherit;
                border: none;
                outline: none;
            }
        """)
        # 完全禁用垂直和水平滚动条
        self.task_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.task_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.task_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.task_list.setIconSize(QSize(0, 0))  # 避免图标带来的额外边距
        self.task_list.setSpacing(3)
        self.task_list.itemDoubleClicked.connect(self._edit_task)
        task_layout.addWidget(self.task_list)

        # 添加任务按钮 - 靠右排列
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        add_task_button = QPushButton("添加新任务")
        add_task_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1C95EA;
            }
        """)
        add_task_button.setCursor(Qt.PointingHandCursor)
        add_task_button.clicked.connect(self._add_task)
        button_layout.addWidget(add_task_button)
        
        task_layout.addLayout(button_layout)
        
        # 预先刷新音频文件
        self._refresh_audio_files()
        
        return task_group
    
    def resizeEvent(self, event):
        """窗口大小变化时更新所有列表项尺寸"""
        super().resizeEvent(event)
        self._update_list_items_width()
    
    def _update_list_items_width(self):
        """更新所有列表项的宽度"""
        width = self.task_list.viewport().width()
        for task_id, (item, _) in self.task_items.items():
            current_height = item.sizeHint().height()
            item.setSizeHint(QSize(width, current_height))
    
    def _handle_list_resize(self, event):
        """处理列表尺寸变化事件"""
        # 已删除，不再使用
        pass
    
    def _update_all_item_widths(self):
        """更新所有列表项的宽度，使其填充列表宽度"""
        # 已删除，不再使用
        pass
    
    def _load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    # 加载任务
                    tasks_data = config.get('tasks', [])
                    self.tasks = [Task.from_dict(task_data) for task_data in tasks_data]
                    
                    # 如果没有任务，添加一个默认任务
                    if not self.tasks:
                        self._create_default_task()
                    
                    # 加载窗口大小和位置
                    if 'window' in config:
                        window_config = config['window']
                        if all(k in window_config for k in ['x', 'y', 'width', 'height']):
                            x = window_config['x']
                            y = window_config['y']
                            width = window_config['width']
                            height = window_config['height']
                            
                            # 确保窗口位置在屏幕内
                            screen = QApplication.primaryScreen().geometry()
                            if (x >= 0 and x < screen.width() - 100 and 
                                y >= 0 and y < screen.height() - 100 and
                                width >= self.minimumWidth() and height >= self.minimumHeight()):
                                self.setGeometry(x, y, width, height)
                                
        except Exception as e:
            QMessageBox.warning(self, "配置加载错误", f"加载配置时出错：{str(e)}")
            self._create_default_task()
        
        # 刷新音频文件列表
        self._refresh_audio_files()
    
    def _save_config(self):
        """保存配置"""
        try:
            # 获取当前窗口的几何信息
            geometry = self.geometry()
            
            config = {
                'tasks': [task.to_dict() for task in self.tasks],
                'window': {
                    'x': geometry.x(),
                    'y': geometry.y(),
                    'width': geometry.width(),
                    'height': geometry.height()
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.warning(self, "配置保存错误", f"保存配置时出错：{str(e)}")
    
    def _create_default_task(self):
        """创建默认任务"""
        default_task = Task(
            name="示例任务",
            hours=0,
            minutes=25,
            seconds=0,
            reminder_text="倒计时结束了！",
            enabled=True
        )
        self.tasks.append(default_task)
    
    def _init_task_list(self):
        """初始化任务列表"""
        self.task_list.clear()
        self.task_items = {}
        
        for task in self.tasks:
            self._add_task_to_list(task)
    
    def _add_task_to_list(self, task):
        """将任务添加到列表"""
        # 创建列表项
        item = QListWidgetItem(self.task_list)
        
        # 创建自定义部件
        widget = TaskListItem(task)
        
        # 设置列表项大小，确保不超出可见区域
        list_width = self.task_list.viewport().width()
        item.setSizeHint(QSize(list_width, widget.sizeHint().height()))
        
        # 设置自定义部件
        self.task_list.setItemWidget(item, widget)
        
        # 绑定开始/停止按钮事件
        widget.toggle_button.clicked.connect(lambda checked, t=task, w=widget: self._toggle_task(t, w))
        
        # 绑定删除按钮事件
        widget.delete_button.clicked.connect(lambda: self._delete_task(task))
        
        # 存储任务项映射
        self.task_items[task.id] = (item, widget)
    
    def _add_task(self):
        """添加新任务"""
        dialog = TaskEditDialog(self, None, self.audio_files)
        
        if dialog.exec() == QDialog.Accepted:
            # 添加任务到列表
            self.tasks.append(dialog.task)
            self._add_task_to_list(dialog.task)
            
            # 保存配置
            self._save_config()
    
    def _edit_task(self, item):
        """编辑任务"""
        # 获取对应的任务
        for task_id, (list_item, widget) in self.task_items.items():
            if list_item == item:
                task = None
                for t in self.tasks:
                    if t.id == task_id:
                        task = t
                        break
                
                if task:
                    dialog = TaskEditDialog(self, task, self.audio_files)
                    
                    # 连接删除按钮信号
                    dialog.delete_button.clicked.connect(lambda: self._delete_task(task))
                    
                    if dialog.exec() == QDialog.Accepted:
                        # 更新UI
                        widget.task = task  # 更新引用
                        widget.update_all()
                        
                        # 保存配置
                        self._save_config()
                break
    
    def _delete_task(self, task):
        """删除任务"""
        # 确认对话框
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除任务 \"{task.name}\" 吗？", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 停止任务
            if task.running:
                self._stop_task(task)
            
            # 从任务列表移除
            self.tasks.remove(task)
            
            # 从UI中移除
            if task.id in self.task_items:
                item, widget = self.task_items[task.id]
                row = self.task_list.row(item)
                self.task_list.takeItem(row)
                del self.task_items[task.id]
            
            # 保存配置
            self._save_config()
    
    def _toggle_task(self, task, widget):
        """切换任务状态"""
        if task.running:
            self._stop_task(task)
        else:
            self._start_task(task)
        
        # 更新UI
        widget.update_all()
    
    def _start_task(self, task):
        """开始任务"""
        if not task.enabled:
            return
        
        # 初始化剩余时间
        task.remaining_seconds = task.total_seconds
        task.running = True
    
    def _stop_task(self, task):
        """停止任务"""
        task.running = False
    
    def _update_all_tasks(self):
        """更新所有任务状态"""
        for task in self.tasks:
            if task.running and task.remaining_seconds > 0:
                # 减少剩余时间
                task.remaining_seconds -= 1
                
                # 更新UI
                if task.id in self.task_items:
                    _, widget = self.task_items[task.id]
                    widget.update_remain_time()
            
            # 检查是否到达零
            if task.running and task.remaining_seconds <= 0:
                self._task_finished(task)
    
    def _task_finished(self, task):
        """任务完成的处理"""
        task.running = False
        
        # 更新UI
        if task.id in self.task_items:
            _, widget = self.task_items[task.id]
            widget.update_all()
        
        # 播放音频循环
        if task.audio_file and os.path.exists(task.audio_file):
            try:
                pygame.mixer.music.load(task.audio_file)
                pygame.mixer.music.play(-1)  # -1表示循环播放
                
                # 让任务栏图标闪烁提醒用户
                QApplication.alert(self, 0)  # 0表示一直闪烁直到用户激活窗口
                
                # 将窗口置于前台并激活
                self.setWindowState((self.windowState() & ~Qt.WindowMinimized) | Qt.WindowActive)
                self.activateWindow()
                self.raise_()
                
                # 显示确认对话框
                dialog = ConfirmDialog(self, task.reminder_text)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)  # 设置对话框置顶
                if dialog.exec() == QDialog.Accepted:
                    pygame.mixer.music.stop()
                    QApplication.alert(self, 0)  # 停止闪烁
            except Exception as e:
                QMessageBox.critical(self, "错误", f"播放音频文件时出错：{str(e)}")
    
    def _refresh_audio_files(self):
        """刷新音频文件列表"""
        # 清空映射
        self.audio_files = {}
        
        # 获取所有音频文件
        audio_files = []
        for ext in ["*.mp3", "*.wav", "*.ogg"]:
            pattern = os.path.join(self.audio_dir, ext)
            found = glob.glob(pattern)
            audio_files.extend(found)
        
        # 获取相对路径作为显示名称
        audio_names = [os.path.basename(f) for f in audio_files]
        self.audio_files = dict(zip(audio_names, audio_files))
        
        if not audio_files:
            print(f"未找到音频文件 - 请将音频放在: {self.audio_dir}")
        else:
            print(f"找到 {len(audio_files)} 个音频文件在 {self.audio_dir}")
            for i, file in enumerate(sorted(audio_files)[:10]):  # 仅显示前10个文件
                print(f"  {i+1}. {os.path.basename(file)}")
            if len(audio_files) > 10:
                print(f"  ... 以及其他 {len(audio_files) - 10} 个文件")
    
    def closeEvent(self, event):
        """窗口关闭事件，保存配置"""
        self._save_config()
        if self.timer.isActive():
            self.timer.stop()
        
        # 停止所有正在播放的音频
        pygame.mixer.stop()
        
        # 关闭窗口
        event.accept()

class Task:
    """任务类，表示一个倒计时任务"""
    def __init__(self, name="", hours=0, minutes=0, seconds=0, reminder_text="", audio_file="", enabled=True):
        self.id = str(QUuid.createUuid())
        self.name = name
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.reminder_text = reminder_text
        self.audio_file = audio_file
        self.enabled = enabled
        self.remaining_seconds = 0
        self.running = False
        self.timer = None
    
    @property
    def total_seconds(self):
        """计算任务总秒数"""
        return self.hours * 3600 + self.minutes * 60 + self.seconds
    
    def to_dict(self):
        """将任务转换为字典，用于保存配置"""
        return {
            "id": self.id,
            "name": self.name,
            "hours": self.hours,
            "minutes": self.minutes,
            "seconds": self.seconds,
            "reminder_text": self.reminder_text,
            "audio_file": self.audio_file,
            "enabled": self.enabled
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建任务，用于加载配置"""
        task = cls(
            name=data.get("name", ""),
            hours=data.get("hours", 0),
            minutes=data.get("minutes", 0),
            seconds=data.get("seconds", 0),
            reminder_text=data.get("reminder_text", ""),
            audio_file=data.get("audio_file", ""),
            enabled=data.get("enabled", True)
        )
        task.id = data.get("id", str(QUuid.createUuid()))
        return task

class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    def __init__(self, parent=None, task=None, audio_files=None):
        super().__init__(parent)
        self.setWindowTitle("编辑任务" if task else "新建任务")
        self.task = task or Task()
        self.audio_files = audio_files or {}
        self.audio_name_to_path = {os.path.basename(path): path for path in self.audio_files.values()}
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2D2D30;
                color: #FFFFFF;
                border-radius: 5px;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit, QSpinBox {
                background-color: #333337;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                min-height: 25px;
            }
            QComboBox {
                background-color: #333337;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                min-height: 25px;
            }
            QCheckBox {
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #007ACC;
                color: white;
                border-radius: 3px;
                padding: 6px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1C97EA;
            }
            QPushButton:pressed {
                background-color: #0062A3;
            }
            QPushButton#delete_button {
                background-color: #E74C3C;
            }
            QPushButton#delete_button:hover {
                background-color: #FF6B5E;
            }
        """)
        
        self.setupUI()
        
    def setupUI(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignRight)
        
        # 时间设置
        time_layout = QHBoxLayout()
        
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 99)
        self.hours_spin.setValue(self.task.hours)
        self.hours_spin.setFixedWidth(70)
        self.hours_spin.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.hours_spin)
        time_layout.addWidget(QLabel("小时"))
        
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setValue(self.task.minutes)
        self.minutes_spin.setFixedWidth(70)
        self.minutes_spin.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.minutes_spin)
        time_layout.addWidget(QLabel("分钟"))
        
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(0, 59)
        self.seconds_spin.setValue(self.task.seconds)
        self.seconds_spin.setFixedWidth(70)
        self.seconds_spin.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.seconds_spin)
        time_layout.addWidget(QLabel("秒"))
        
        time_layout.addStretch()
        form_layout.addRow("倒计时时间:", time_layout)
        
        # 提醒文字
        self.reminder_edit = QLineEdit(self.task.reminder_text)
        self.reminder_edit.setPlaceholderText("输入提醒文字")
        form_layout.addRow("提醒文字:", self.reminder_edit)
        
        # 音频选择
        self.audio_combo = QComboBox()
        audio_names = list(self.audio_name_to_path.keys())
        self.audio_combo.addItems(audio_names)
        
        if self.task.audio_file:
            base_name = os.path.basename(self.task.audio_file)
            if base_name in audio_names:
                self.audio_combo.setCurrentText(base_name)
        
        form_layout.addRow("提醒音频:", self.audio_combo)
        
        # 启用状态
        self.enabled_checkbox = QCheckBox("启用此任务")
        self.enabled_checkbox.setChecked(self.task.enabled)
        form_layout.addRow("", self.enabled_checkbox)
        
        layout.addLayout(form_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.delete_button = QPushButton("删除任务")
        self.delete_button.setObjectName("delete_button")
        if not self.task.id:  # 新任务不显示删除按钮
            self.delete_button.setVisible(False)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
        
        self.setMinimumWidth(400)
        self.setFixedHeight(290)
        
    def accept(self):
        """确认编辑结果"""
        # 验证输入
        total_seconds = (self.hours_spin.value() * 3600 + 
                        self.minutes_spin.value() * 60 + 
                        self.seconds_spin.value())
        
        if total_seconds <= 0:
            QMessageBox.warning(self, "错误", "请设置大于0的倒计时时间")
            return
        
        # 更新任务数据
        # 生成自动任务名：使用时间
        hours = self.hours_spin.value()
        minutes = self.minutes_spin.value()
        seconds = self.seconds_spin.value()
        self.task.name = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        self.task.hours = hours
        self.task.minutes = minutes
        self.task.seconds = seconds
        self.task.reminder_text = self.reminder_edit.text()
        self.task.enabled = self.enabled_checkbox.isChecked()
        
        # 更新音频文件
        audio_name = self.audio_combo.currentText()
        if audio_name and audio_name in self.audio_name_to_path:
            self.task.audio_file = self.audio_name_to_path[audio_name]
        
        super().accept()

class TaskListItem(QWidget):
    """自定义任务列表项，显示任务信息和控制按钮"""
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI布局"""
        # 使用简单的水平布局，确保按钮可见
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        # 设置背景样式
        self.setStyleSheet("""
            background-color: #2D2D30;
            border-radius: 6px;
            border-left: 3px solid #007ACC;
        """)
        
        # 左侧部分：状态指示器和任务信息
        left_widget = QWidget()
        left_widget.setStyleSheet("background-color: transparent; border: none;")
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # 状态指示器
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(12, 12)
        self.update_status_indicator()
        left_layout.addWidget(self.status_indicator)
        
        # 任务信息
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: transparent; border: none;")
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(3)
        
        # 提醒文字显示在上方
        reminder = self.task.reminder_text
        self.name_label = QLabel(reminder)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFFFFF;")
        
        # 时间信息显示在下方
        time_str = f"{self.task.hours:02d}:{self.task.minutes:02d}:{self.task.seconds:02d}"
        details_text = f"时间: {time_str}"
        self.details_label = QLabel(details_text)
        self.details_label.setStyleSheet("color: #B2B2B2; font-size: 12px;")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.details_label)
        left_layout.addWidget(info_widget)
        
        # 添加左侧部分，并设置为可伸展
        main_layout.addWidget(left_widget, 1)
        
        # 占位空间，让按钮靠右
        main_layout.addStretch()
        
        # 剩余时间显示
        remain_widget = QWidget()
        remain_widget.setStyleSheet("background-color: transparent; border: none;")
        remain_layout = QVBoxLayout(remain_widget)
        remain_layout.setContentsMargins(0, 0, 0, 0)
        remain_layout.setAlignment(Qt.AlignCenter)
        
        remain_label = QLabel("剩余时间")
        remain_label.setAlignment(Qt.AlignCenter)
        remain_label.setStyleSheet("color: #888888; font-size: 11px;")
        
        self.remain_label = QLabel()
        self.remain_label.setFixedWidth(80)
        self.remain_label.setAlignment(Qt.AlignCenter)
        self.update_remain_time()
        
        remain_layout.addWidget(remain_label)
        remain_layout.addWidget(self.remain_label)
        main_layout.addWidget(remain_widget)
        
        # 按钮容器 - 固定宽度确保一直可见
        buttons_widget = QWidget()
        buttons_widget.setFixedWidth(110)
        buttons_widget.setStyleSheet("background-color: transparent; border: none;")
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)
        
        # 开始/停止按钮
        self.toggle_button = QPushButton("开始" if not self.task.running else "停止")
        self.toggle_button.setFixedSize(50, 30)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.update_toggle_button()
        
        # 删除按钮
        self.delete_button = QPushButton("删除")
        self.delete_button.setFixedSize(45, 30)
        self.delete_button.setCursor(Qt.PointingHandCursor)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF6B5E;
            }
        """)
        
        buttons_layout.addWidget(self.toggle_button)
        buttons_layout.addWidget(self.delete_button)
        
        # 添加按钮区域到主布局
        main_layout.addWidget(buttons_widget)
        
        # 设置固定高度
        self.setFixedHeight(70)
    
    def update_status_indicator(self):
        """更新状态指示器"""
        color = "#555555"  # 默认灰色（禁用）
        
        if self.task.enabled:
            if self.task.running:
                color = "#00C853"  # 运行中为绿色
            else:
                color = "#007ACC"  # 启用但未运行为蓝色
        
        self.status_indicator.setStyleSheet(f"""
            background-color: {color};
            border-radius: 5px;
        """)
    
    def update_remain_time(self):
        """更新剩余时间显示"""
        if self.task.running:
            hours, remainder = divmod(self.task.remaining_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.remain_label.setText(time_str)
            
            # 根据剩余时间调整颜色
            if self.task.remaining_seconds < 10:
                self.remain_label.setStyleSheet("font-size: 14px; color: #FF5252; font-weight: bold;")
            elif self.task.remaining_seconds < 30:
                self.remain_label.setStyleSheet("font-size: 14px; color: #FFA000; font-weight: bold;")
            else:
                self.remain_label.setStyleSheet("font-size: 14px; color: #00C853; font-weight: bold;")
        else:
            self.remain_label.setText("")
    
    def update_toggle_button(self):
        """更新开始/停止按钮状态"""
        if not self.task.enabled:
            # 任务禁用状态
            self.toggle_button.setText("开始")
            self.toggle_button.setEnabled(False)
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #555555;
                    color: #999999;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
            """)
        elif self.task.running:
            # 任务运行状态
            self.toggle_button.setText("停止")
            self.toggle_button.setEnabled(True)
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF5252;
                    color: white;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FF7373;
                }
            """)
        else:
            # 任务启用但未运行状态
            self.toggle_button.setText("开始")
            self.toggle_button.setEnabled(True)
            self.toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: #00C853;
                    color: white;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #00E676;
                }
            """)
    
    def update_all(self):
        """更新所有显示内容"""
        self.update_status_indicator()
        self.update_remain_time()
        self.update_toggle_button()
        
        # 更新提醒文字和时间信息
        time_str = f"{self.task.hours:02d}:{self.task.minutes:02d}:{self.task.seconds:02d}"
        self.name_label.setText(self.task.reminder_text)
        self.details_label.setText(f"时间: {time_str}")
        
        # 如果任务被禁用，更新文字颜色
        if not self.task.enabled:
            self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #888888;")
            self.details_label.setStyleSheet("color: #666666; font-size: 12px;")
            # 禁用删除按钮
            self.delete_button.setEnabled(self.task.running == False)
        else:
            self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.details_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
            # 启用删除按钮
            self.delete_button.setEnabled(True)

def main():
    # 创建QApplication实例
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 设置应用图标
    icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # 创建并显示主窗口
    window = CountdownTimer()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 