import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QTextEdit, 
                             QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt

from keyword_classifier import KeywordClassifier
from excel_handler import ExcelHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("关键词分类工具")
        self.setGeometry(100, 100, 800, 600)
        
        self.excel_handler = ExcelHandler()
        self.classifier = KeywordClassifier()
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 规则输入区域
        rules_layout = QVBoxLayout()
        rules_label = QLabel("分词规则:")
        rules_label.setToolTip("规则说明:\n[]内表示精确匹配\n<>表示排除\n|表示或运算\n+表示与运算\n()用于调整优先级\n使用,分隔不同规则")
        self.rules_text = QTextEdit()
        self.rules_text.setPlaceholderText("输入分词规则，使用逗号分隔不同规则...")
        
        rules_layout.addWidget(rules_label)
        rules_layout.addWidget(self.rules_text)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        
        self.load_rules_btn = QPushButton("从Excel加载规则")
        self.load_rules_btn.clicked.connect(self.load_rules_from_excel)
        
        self.load_keywords_btn = QPushButton("加载关键词")
        self.load_keywords_btn.clicked.connect(self.load_keywords)
        
        self.classify_btn = QPushButton("开始分类")
        self.classify_btn.clicked.connect(self.start_classification)
        
        buttons_layout.addWidget(self.load_rules_btn)
        buttons_layout.addWidget(self.load_keywords_btn)
        buttons_layout.addWidget(self.classify_btn)
        
        # 状态区域
        status_layout = QVBoxLayout()
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        # 添加所有布局
        main_layout.addLayout(rules_layout)
        main_layout.addLayout(buttons_layout)
        main_layout.addLayout(status_layout)
        
        # 初始化数据
        self.keywords = []
        self.rules_file_path = ""
        self.keywords_file_path = ""
    
    def load_rules_from_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel Files (*.xlsx)")
        
        if file_path:
            try:
                self.rules_file_path = file_path
                rules = self.excel_handler.read_rules(file_path)
                self.rules_text.setText("\n".join(rules))
                self.status_label.setText(f"已加载 {len(rules)} 条规则")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载规则失败: {str(e)}")
    
    def load_keywords(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择关键词Excel文件", "", "Excel Files (*.xlsx)")
        
        if file_path:
            try:
                self.keywords_file_path = file_path
                self.keywords = self.excel_handler.read_keywords(file_path)
                self.status_label.setText(f"已加载 {len(self.keywords)} 个关键词")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载关键词失败: {str(e)}")
    
    def start_classification(self):
        # 获取规则
        rules_text = self.rules_text.toPlainText()
        if not rules_text.strip() and not self.rules_file_path:
            QMessageBox.warning(self, "警告", "请输入分词规则或从Excel加载规则")
            return
        
        # 如果没有从文本框获取到规则，但有规则文件路径，则从文件重新读取
        if not rules_text.strip() and self.rules_file_path:
            rules = self.excel_handler.read_rules(self.rules_file_path)
        else:
            # 从文本框获取规则
            rules = [r.strip() for r in rules_text.split('\n') if r.strip()]
            # 进一步按逗号分隔
            temp_rules = []
            for r in rules:
                temp_rules.extend([tr.strip() for tr in r.split(',') if tr.strip()])
            rules = temp_rules
        
        # 检查关键词
        if not self.keywords and not self.keywords_file_path:
            QMessageBox.warning(self, "警告", "请先加载关键词")
            return
        
        # 如果没有关键词但有文件路径，则重新读取
        if not self.keywords and self.keywords_file_path:
            self.keywords = self.excel_handler.read_keywords(self.keywords_file_path)
        
        try:
            # 设置规则
            self.classifier.set_rules(rules)
            
            # 开始分类
            self.status_label.setText("正在分类...")
            QApplication.processEvents()  # 更新UI
            
            results = self.classifier.classify_keywords(self.keywords)
            
            # 保存结果
            if not os.path.exists('./data'):
                os.makedirs('./data')
                
            output_file = './data/classification_results.xlsx'
            self.excel_handler.save_results(results, output_file)
            
            self.status_label.setText(f"分类完成，结果已保存至 {os.path.abspath(output_file)}")
            QMessageBox.information(self, "完成", f"分类完成，共处理 {len(results)} 个关键词")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"分类过程中出错: {str(e)}")
            self.status_label.setText("分类失败")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()