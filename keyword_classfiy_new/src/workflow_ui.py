import os
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import pandas as pd
import time
import threading
from typing import List, Dict, Any, Optional

from workflow_processor import WorkflowProcessor
from keyword_classifier import KeywordClassifier

class WorkflowUI(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding="10")
        self.parent = parent
        
        # 初始化工作流处理器
        self.classifier = KeywordClassifier()
        self.workflow_processor = WorkflowProcessor(classifier=self.classifier)
        
        # 初始化文件路径变量
        self.rules_file_path = ""
        self.classification_file_path = ""
        self.output_dir = "./工作流结果"
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        # 文件选择区域
        file_select_frame = ttk.LabelFrame(self, text="工作流文件选择:")
        file_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮区域
        buttons_frame = ttk.Frame(file_select_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 选择工作流规则文件按钮
        self.select_rules_btn = ttk.Button(buttons_frame, text="选择工作流规则文件", command=self.select_rules_file)
        self.select_rules_btn.pack(side=tk.LEFT, padx=5)
        
        # 选择待分类文件按钮
        self.select_classification_btn = ttk.Button(buttons_frame, text="选择待分类文件", command=self.select_classification_file)
        self.select_classification_btn.pack(side=tk.LEFT, padx=5)
        
        # 开始处理按钮
        self.process_workflow_btn = ttk.Button(buttons_frame, text="开始处理", command=self.process_workflow)
        self.process_workflow_btn.pack(side=tk.LEFT, padx=5)
        
        # 文件信息显示区域
        info_frame = ttk.Frame(file_select_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 工作流规则文件信息
        self.rules_file_label = ttk.Label(info_frame, text="工作流规则文件: 未选择")
        self.rules_file_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # 待分类文件信息
        self.classification_file_label = ttk.Label(info_frame, text="待分类文件: 未选择")
        self.classification_file_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # 工作流说明区域
        help_frame = ttk.LabelFrame(self, text="工作流说明:")
        help_frame.pack(fill=tk.X, padx=5, pady=5)
        
        help_text = """工作流处理说明:
1. 工作流规则文件必须是Excel文件，文件名以'工作流规则_'开头
2. 待分类文件必须是Excel文件，文件名以'待分类_'开头
3. 工作流规则文件必须包含Sheet1，可选包含Sheet2、Sheet3等
4. Sheet1必须包含'分类规则'和'结果文件名称'列
5. Sheet2及以上必须包含'分类规则'、'结果文件名称'和'分类sheet名称'列
6. Sheet4及以上必须包含'上层分类规则'列
7. 待分类文件必须包含'关键词'列
8. 输出结果保存在./工作流结果目录下
9. 特殊规则值'全'表示匹配所有关键词
10. 特殊字符替换规则: <>替换为《》, |替换为~, []替换为【】"""
        
        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT, wraplength=800)
        help_label.pack(anchor=tk.W, padx=5, pady=5)
        
        # 进度区域
        progress_frame = ttk.Frame(self)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(anchor=tk.W)
        
        # 状态区域
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(anchor=tk.W)
        
        # 处理信息显示区域
        info_frame = ttk.LabelFrame(self, text="处理信息:")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=15, wrap=tk.WORD)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.info_text.config(state=tk.DISABLED)  # 初始状态为禁用，防止用户编辑
    
    def select_rules_file(self):
        """选择工作流规则文件"""
        file_path = filedialog.askopenfilename(
            title="选择工作流规则Excel文件", 
            filetypes=[("Excel Files", "*.xlsx")])
        
        if file_path:
            # 检查文件名是否以'工作流规则_'开头
            file_name = os.path.basename(file_path)
            if not file_name.startswith("工作流规则_"):
                messagebox.showwarning("警告", "工作流规则文件名必须以'工作流规则_'开头")
                return
            
            self.rules_file_path = file_path
            self.rules_file_label.config(text=f"工作流规则文件: {file_name}")
            self.add_info(f"已选择工作流规则文件: {file_name}")
            self.status_label.config(text="已选择工作流规则文件")
    
    def select_classification_file(self):
        """选择待分类文件"""
        file_path = filedialog.askopenfilename(
            title="选择待分类Excel文件", 
            filetypes=[("Excel Files", "*.xlsx")])
        
        if file_path:
            # 检查文件名是否以'待分类_'开头
            file_name = os.path.basename(file_path)
            if not file_name.startswith("待分类_"):
                messagebox.showwarning("警告", "待分类文件名必须以'待分类_'开头")
                return
            
            self.classification_file_path = file_path
            self.classification_file_label.config(text=f"待分类文件: {file_name}")
            self.add_info(f"已选择待分类文件: {file_name}")
            self.status_label.config(text="已选择待分类文件")
    
    def add_info(self, message):
        """添加处理信息"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"{message}\n")
        self.info_text.see(tk.END)  # 自动滚动到最新消息
        self.info_text.config(state=tk.DISABLED)
    
    def clear_info(self):
        """清空处理信息"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def update_progress(self, current, total, message=""):
        """更新进度条和进度信息"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar["value"] = progress
        
        if message:
            self.progress_label.config(text=f"{message} - {progress}%")
        else:
            self.progress_label.config(text=f"进度: {current}/{total} ({progress}%)")
        
        # 更新UI
        self.update()
    
    def process_workflow(self):
        """处理工作流"""
        # 检查是否选择了工作流规则文件和待分类文件
        if not self.rules_file_path:
            messagebox.showwarning("警告", "请先选择工作流规则文件")
            return
        
        if not self.classification_file_path:
            messagebox.showwarning("警告", "请先选择待分类文件")
            return
        
        # 清空处理信息
        self.clear_info()
        
        # 更新状态
        self.status_label.config(text="正在处理工作流...")
        self.update()  # 更新UI
        
        # 添加处理信息
        self.add_info("开始处理工作流...")
        
        # 重置进度条
        self.progress_bar["value"] = 0
        self.progress_label.config(text="")
        
        # 创建错误回调函数
        def error_callback(error_msg):
            self.add_info(f"错误: {error_msg}")
        
        # 创建进度回调函数
        def progress_callback(stage, current, total, message):
            self.update_progress(current, total, f"{stage}: {message}")
        
        # 使用线程处理工作流，避免UI卡顿
        def process_thread():
            try:
                # 记录开始时间
                start_time = time.time()
                
                # 调用WorkflowProcessor的process_workflow方法处理工作流
                self.add_info("正在读取工作流规则文件...")
                self.update_progress(1, 4, "读取工作流规则文件")
                
                # 处理工作流
                final_files = self.workflow_processor.process_workflow(
                    self.rules_file_path, 
                    self.classification_file_path,
                    error_callback
                )
                
                # 计算总耗时
                end_time = time.time()
                total_time = end_time - start_time
                
                # 更新状态信息
                self.status_label.config(text=f"工作流处理完成，结果已保存至 {os.path.abspath(self.output_dir)}")
                self.add_info(f"工作流处理完成，总耗时: {total_time:.2f}秒")
                self.add_info(f"结果已保存至: {os.path.abspath(self.output_dir)}")
                
                # 显示生成的文件列表
                self.add_info("\n生成的文件列表:")
                for output_name, file_path in final_files.items():
                    self.add_info(f"- {output_name}: {os.path.basename(file_path)}")
                
                # 更新进度条为100%
                self.update_progress(100, 100, "处理完成")
                
                # 显示完成消息
                messagebox.showinfo("完成", f"工作流处理完成，结果已保存至:\n{os.path.abspath(self.output_dir)}")
                
            except Exception as e:
                error_msg = f"工作流处理失败: {str(e)}"
                self.add_info(f"错误: {error_msg}")
                messagebox.showerror("错误", error_msg)
                self.status_label.config(text="处理失败")
                self.progress_bar["value"] = 0
                self.progress_label.config(text="")
        
        # 启动处理线程
        threading.Thread(target=process_thread, daemon=True).start()

# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    root.title("工作流处理测试")
    root.geometry("900x700")
    
    app = WorkflowUI(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
