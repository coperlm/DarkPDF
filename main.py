#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BlackPDF - PDF阅读器（颜色翻转版）
可以将PDF的颜色反转显示，实现暗黑模式阅读效果
PySide6版本 - 适用于Arch Linux
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QScrollArea, QSpinBox, QMessageBox)
from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QImage, QPixmap, QPainter, QKeyEvent, QWheelEvent
import fitz  # PyMuPDF


class PDFViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pdf_document = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.invert_colors = True  # 默认开启颜色翻转
        self.page_images = []  # 存储所有页面的图像
        
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('BlackPDF - 颜色翻转PDF阅读器')
        self.setGeometry(100, 100, 1000, 800)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # 工具栏
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)
        
        # PDF显示区域 - 使用垂直布局容器来放置所有页面
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建容器widget来存放所有页面
        self.pages_container = QWidget()
        self.pages_layout = QVBoxLayout(self.pages_container)
        self.pages_layout.setSpacing(10)  # 页面之间的间距
        self.pages_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.pages_container)
        self.scroll_area.setStyleSheet("background-color: #2b2b2b;")
        main_layout.addWidget(self.scroll_area)
        
        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # 状态栏
        self.status_label = QLabel('请打开PDF文件')
        main_layout.addWidget(self.status_label)
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar_layout = QHBoxLayout()
        
        # 打开文件按钮
        open_btn = QPushButton('📁 打开PDF')
        open_btn.clicked.connect(self.open_file)
        toolbar_layout.addWidget(open_btn)
        
        toolbar_layout.addStretch()
        
        # 上一页按钮
        prev_btn = QPushButton('⬅️ 上一页')
        prev_btn.clicked.connect(self.prev_page)
        toolbar_layout.addWidget(prev_btn)
        
        # 页码显示和跳转
        toolbar_layout.addWidget(QLabel('页码:'))
        self.page_spinbox = QSpinBox()
        self.page_spinbox.setMinimum(1)
        self.page_spinbox.valueChanged.connect(self.jump_to_page)
        toolbar_layout.addWidget(self.page_spinbox)
        
        self.page_count_label = QLabel('/ 0')
        toolbar_layout.addWidget(self.page_count_label)
        
        # 下一页按钮
        next_btn = QPushButton('下一页 ➡️')
        next_btn.clicked.connect(self.next_page)
        toolbar_layout.addWidget(next_btn)
        
        toolbar_layout.addStretch()
        
        # 缩放控制
        toolbar_layout.addWidget(QLabel('缩放:'))
        
        zoom_out_btn = QPushButton('🔍-')
        zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar_layout.addWidget(zoom_out_btn)
        
        self.zoom_label = QLabel('100%')
        toolbar_layout.addWidget(self.zoom_label)
        
        zoom_in_btn = QPushButton('🔍+')
        zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(zoom_in_btn)
        
        toolbar_layout.addStretch()
        
        # 颜色翻转开关
        self.color_toggle_btn = QPushButton('🌙 暗黑模式: 开')
        self.color_toggle_btn.clicked.connect(self.toggle_color_invert)
        toolbar_layout.addWidget(self.color_toggle_btn)
        
        return toolbar_layout
        
    def open_file(self):
        """打开PDF文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择PDF文件', '', 'PDF文件 (*.pdf)'
        )
        
        if file_path:
            try:
                if self.pdf_document:
                    self.pdf_document.close()
                
                self.pdf_document = fitz.open(file_path)
                self.current_page = 0
                
                # 更新页码控制
                page_count = len(self.pdf_document)
                self.page_spinbox.setMaximum(page_count)
                self.page_count_label.setText(f'/ {page_count}')
                self.page_spinbox.setValue(1)
                
                self.render_all_pages()
                self.status_label.setText(f'已打开: {file_path}')
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'无法打开PDF文件:\n{str(e)}')
                
    def render_all_pages(self):
        """渲染所有页面并连续显示"""
        if not self.pdf_document:
            return
        
        # 清空之前的页面
        while self.pages_layout.count():
            item = self.pages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.page_images = []
        
        try:
            # 渲染所有页面
            for page_num in range(len(self.pdf_document)):
                page = self.pdf_document[page_num]
                
                # 设置缩放矩阵
                mat = fitz.Matrix(self.zoom_level, self.zoom_level)
                
                # 渲染为图像
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # 转换为QImage
                img_format = QImage.Format.Format_RGB888
                img = QImage(pix.samples, pix.width, pix.height, 
                            pix.stride, img_format)
                
                # 颜色翻转
                if self.invert_colors:
                    img.invertPixels()
                
                # 创建pixmap并添加到列表
                pixmap = QPixmap.fromImage(img)
                self.page_images.append(pixmap)
                
                # 创建label显示这一页
                page_label = QLabel()
                page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                page_label.setPixmap(pixmap)
                
                # 添加到布局
                self.pages_layout.addWidget(page_label)
            
            # 添加弹性空间，使页面靠上对齐
            self.pages_layout.addStretch()
            
        except Exception as e:
            QMessageBox.warning(self, '警告', f'渲染页面时出错:\n{str(e)}')
    
    def render_page(self):
        """重新渲染所有页面（当缩放或颜色模式改变时）"""
        self.render_all_pages()
            
    def prev_page(self):
        """上一页 - 滚动到上一页位置"""
        if self.pdf_document and self.current_page > 0:
            self.current_page -= 1
            self.scroll_to_page(self.current_page)
            
    def next_page(self):
        """下一页 - 滚动到下一页位置"""
        if self.pdf_document and self.current_page < len(self.pdf_document) - 1:
            self.current_page += 1
            self.scroll_to_page(self.current_page)
    
    def scroll_to_page(self, page_num):
        """滚动到指定页面"""
        if page_num < 0 or page_num >= len(self.page_images):
            return
        
        # 计算滚动位置
        scroll_position = 0
        for i in range(page_num):
            if i < self.pages_layout.count():
                widget = self.pages_layout.itemAt(i).widget()
                if widget:
                    scroll_position += widget.height() + self.pages_layout.spacing()
        
        # 滚动到指定位置
        self.scroll_area.verticalScrollBar().setValue(scroll_position)
        
        # 更新页码显示
        self.page_spinbox.blockSignals(True)
        self.page_spinbox.setValue(page_num + 1)
        self.page_spinbox.blockSignals(False)
            
    def jump_to_page(self, page_num):
        """跳转到指定页"""
        if self.pdf_document:
            self.current_page = page_num - 1
            self.scroll_to_page(self.current_page)
            
    def zoom_in(self):
        """放大"""
        self.zoom_level = min(self.zoom_level + 0.2, 5.0)
        self.zoom_label.setText(f'{int(self.zoom_level * 100)}%')
        self.render_page()
        
    def zoom_out(self):
        """缩小"""
        self.zoom_level = max(self.zoom_level - 0.2, 0.2)
        self.zoom_label.setText(f'{int(self.zoom_level * 100)}%')
        self.render_page()
        
    def toggle_color_invert(self):
        """切换颜色翻转"""
        self.invert_colors = not self.invert_colors
        
        if self.invert_colors:
            self.color_toggle_btn.setText('🌙 暗黑模式: 开')
            self.scroll_area.setStyleSheet("background-color: #2b2b2b;")
        else:
            self.color_toggle_btn.setText('☀️ 正常模式')
            self.scroll_area.setStyleSheet("background-color: #ffffff;")
            
        self.render_page()
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        if not self.pdf_document:
            return
            
        key = event.key()
        
        # 方向键和常用快捷键
        if key in (Qt.Key.Key_Right, Qt.Key.Key_Down, Qt.Key.Key_PageDown, Qt.Key.Key_Space):
            self.next_page()
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Up, Qt.Key.Key_PageUp):
            self.prev_page()
        elif key == Qt.Key.Key_Home:
            # 跳转到第一页
            self.current_page = 0
            self.render_page()
        elif key == Qt.Key.Key_End:
            # 跳转到最后一页
            self.current_page = len(self.pdf_document) - 1
            self.render_page()
        elif key == Qt.Key.Key_Plus or key == Qt.Key.Key_Equal:
            # 放大
            self.zoom_in()
        elif key == Qt.Key.Key_Minus:
            # 缩小
            self.zoom_out()
        elif key == Qt.Key.Key_I:
            # I键切换颜色翻转
            self.toggle_color_invert()
        elif key == Qt.Key.Key_P:
            # P键切换自动播放
            self.toggle_auto_play()
        else:
            super().keyPressEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮事件处理 - 缩放控制"""
        if not self.pdf_document:
            return
        
        # Ctrl + 滚轮：缩放
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            # 普通滚轮：自然滚动（由QScrollArea处理）
            super().wheelEvent(event)
        
    def closeEvent(self, event):
        """关闭事件"""
        if self.pdf_document:
            self.pdf_document.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    viewer = PDFViewer()
    viewer.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
