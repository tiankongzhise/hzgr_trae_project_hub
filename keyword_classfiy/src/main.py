import sys
import os
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import pandas as pd
import re
from pathlib import Path

from keyword_classifier import KeywordClassifier
from excel_handler import ExcelHandler

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("关键词分类工具")
        self.geometry("900x700")
        
        self.excel_handler = ExcelHandler()
        self.classifier = KeywordClassifier()
        self.case_sensitive = tk.BooleanVar(value=False)  # 默认为大小写不敏感
        
        # 文件比较功能的变量
        self.compare_files = []  # 存储要比较的文件路径
        
        self.init_ui()
    
    def init_ui(self):
        # 创建一个笔记本控件，用于切换不同功能页面
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 分类功能页面
        classify_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(classify_frame, text="关键词分类")
        
        # 文件比较功能页面
        compare_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(compare_frame, text="文件比较")
        
        # 初始化分类功能UI
        self.init_classify_ui(classify_frame)
        
        # 初始化文件比较功能UI
        self.init_compare_ui(compare_frame)
        
    def init_classify_ui(self, main_frame):
        # 规则输入区域
        rules_frame = ttk.LabelFrame(main_frame, text="分词规则:")
        rules_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加工具提示
        tooltip_text = "规则说明:\n[]内表示精确匹配\n<>表示排除\n|表示或运算\n+表示与运算\n()用于调整优先级\n使用,分隔不同规则"
        tooltip_label = ttk.Label(rules_frame, text="ℹ️", cursor="question_arrow")
        tooltip_label.pack(anchor=tk.NE, padx=5, pady=5)
        
        # 创建工具提示弹出窗口
        def show_tooltip(event):
            tooltip = tk.Toplevel(self)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
            ttk.Label(tooltip, text=tooltip_text, background="#FFFFCC", relief=tk.SOLID, borderwidth=1).pack()
            tooltip.after(5000, tooltip.destroy)  # 5秒后自动关闭
            
        def hide_tooltip(event):
            for widget in self.winfo_children():
                if isinstance(widget, tk.Toplevel) and not widget.wm_title():
                    widget.destroy()
                    
        tooltip_label.bind('<Enter>', show_tooltip)
        tooltip_label.bind('<Leave>', hide_tooltip)
        
        # 规则文本框 - 缩小高度
        self.rules_text = scrolledtext.ScrolledText(rules_frame, height=6)
        self.rules_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.rules_text.insert(tk.END, "输入分词规则，使用逗号分隔不同规则...")
        
        # 按钮区域
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.load_rules_btn = ttk.Button(buttons_frame, text="从Excel加载规则", command=self.load_rules_from_excel)
        self.load_rules_btn.pack(side=tk.LEFT, padx=5)
        
        self.load_keywords_btn = ttk.Button(buttons_frame, text="加载关键词", command=self.load_keywords)
        self.load_keywords_btn.pack(side=tk.LEFT, padx=5)
        
        self.classify_btn = ttk.Button(buttons_frame, text="开始分类", command=self.start_classification)
        self.classify_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加大小写敏感选项
        self.case_sensitive_check = ttk.Checkbutton(
            buttons_frame, 
            text="大小写敏感", 
            variable=self.case_sensitive,
            onvalue=True,
            offvalue=False
        )
        self.case_sensitive_check.pack(side=tk.LEFT, padx=15)
        
        # 格式提示区域
        format_frame = ttk.Frame(main_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        format_text = "Excel格式说明: 规则文件需包含'分词规则'列或使用第一列，关键词文件使用第一列作为关键词列"
        format_label = ttk.Label(format_frame, text=format_text, foreground="blue")
        format_label.pack(anchor=tk.W)
        
        # 状态区域
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.pack(anchor=tk.W)
        
        # 错误信息显示区域
        error_frame = ttk.LabelFrame(main_frame, text="错误信息:")
        error_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.error_text = scrolledtext.ScrolledText(error_frame, height=5, wrap=tk.WORD)
        self.error_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.error_text.config(state=tk.DISABLED)  # 初始状态为禁用，防止用户编辑
        
        # 进度区域
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(anchor=tk.W)
        
        # 初始化数据
        self.keywords = []
        self.rules_file_path = ""
        self.keywords_file_path = ""
        
        # 清空错误信息
        self.clear_error_text()
    
    def init_compare_ui(self, main_frame):
        # 文件选择区域
        file_select_frame = ttk.LabelFrame(main_frame, text="选择要比较的文件:")
        file_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮区域
        buttons_frame = ttk.Frame(file_select_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 添加文件按钮
        self.add_file_btn = ttk.Button(buttons_frame, text="添加文件", command=self.add_files)
        self.add_file_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加文件夹按钮
        self.add_folder_btn = ttk.Button(buttons_frame, text="添加文件夹", command=self.add_folder)
        self.add_folder_btn.pack(side=tk.LEFT, padx=5)
        
        # 清空文件列表按钮
        self.clear_files_btn = ttk.Button(buttons_frame, text="清空列表", command=self.clear_file_list)
        self.clear_files_btn.pack(side=tk.LEFT, padx=5)
        
        # 开始比较按钮
        self.compare_btn = ttk.Button(buttons_frame, text="开始比较", command=self.start_comparison)
        self.compare_btn.pack(side=tk.LEFT, padx=5)
        
        # 文件列表显示区域
        files_frame = ttk.Frame(file_select_frame)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 文件列表标签
        files_label = ttk.Label(files_frame, text="已选择的文件:")
        files_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # 文件列表显示区域
        self.files_text = scrolledtext.ScrolledText(files_frame, height=6, wrap=tk.WORD)
        self.files_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.files_text.config(state=tk.DISABLED)  # 初始状态为禁用，防止用户编辑
        
        # 比较结果显示区域
        result_frame = ttk.LabelFrame(main_frame, text="比较结果:")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=15, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.result_text.config(state=tk.DISABLED)  # 初始状态为禁用，防止用户编辑
        
        # 状态区域
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.compare_status_label = ttk.Label(status_frame, text="就绪")
        self.compare_status_label.pack(anchor=tk.W)
    
    def clear_error_text(self):
        """清空错误信息显示区域"""
        self.error_text.config(state=tk.NORMAL)
        self.error_text.delete(1.0, tk.END)
        self.error_text.config(state=tk.DISABLED)
    
    def add_error_message(self, message):
        """添加错误信息到显示区域"""
        self.error_text.config(state=tk.NORMAL)
        self.error_text.insert(tk.END, f"{message}\n")
        self.error_text.see(tk.END)  # 自动滚动到最新消息
        self.error_text.config(state=tk.DISABLED)
    
    def load_rules_from_excel(self):
        file_path = filedialog.askopenfilename(
            title="选择Excel文件", 
            filetypes=[("Excel Files", "*.xlsx")])
        
        if file_path:
            try:
                self.clear_error_text()  # 清空之前的错误信息
                self.rules_file_path = file_path
                rules = self.excel_handler.read_rules(file_path)
                # 显示去重前后的规则数量
                original_count = len(rules)
                # 规则已在excel_handler.py中去重
                self.rules_text.delete(1.0, tk.END)
                self.rules_text.insert(tk.END, "\n".join(rules))
                self.status_label.config(text=f"已加载 {len(rules)} 条规则 (已自动去重)")
            except Exception as e:
                error_msg = f"加载规则失败: {str(e)}"
                self.add_error_message(error_msg)
                messagebox.showerror("错误", error_msg)
    
    def load_keywords(self):
        file_path = filedialog.askopenfilename(
            title="选择关键词Excel文件", 
            filetypes=[("Excel Files", "*.xlsx")])
        
        if file_path:
            try:
                self.clear_error_text()  # 清空之前的错误信息
                self.keywords_file_path = file_path
                self.keywords = self.excel_handler.read_keywords(file_path)
                self.status_label.config(text=f"已加载 {len(self.keywords)} 个关键词 (已自动去重)")
            except Exception as e:
                error_msg = f"加载关键词失败: {str(e)}"
                self.add_error_message(error_msg)
                messagebox.showerror("错误", error_msg)
    
    def update_progress(self, current, total, start_time):
        """更新进度条和进度信息"""
        progress = int((current / total) * 100)
        self.progress_bar["value"] = progress
        
        elapsed_time = time.time() - start_time
        eta = (elapsed_time / current) * (total - current) if current > 0 else 0
        
        self.progress_label.config(
            text=f"进度: {current}/{total} ({progress}%) | 已用时: {elapsed_time:.2f}秒 | 预计剩余: {eta:.2f}秒")
        self.update()
    
    def start_classification(self):
        # 清空错误信息
        self.clear_error_text()
        
        # 获取规则
        rules_text = self.rules_text.get(1.0, tk.END).strip()
        if not rules_text and not self.rules_file_path:
            error_msg = "请输入分词规则或从Excel加载规则"
            self.add_error_message(error_msg)
            messagebox.showwarning("警告", error_msg)
            return
        
        # 如果没有从文本框获取到规则，但有规则文件路径，则从文件重新读取
        if not rules_text and self.rules_file_path:
            try:
                rules = self.excel_handler.read_rules(self.rules_file_path)
            except Exception as e:
                error_msg = f"重新读取规则文件失败: {str(e)}"
                self.add_error_message(error_msg)
                messagebox.showerror("错误", error_msg)
                return
        else:
            # 从文本框获取规则
            rules = [r.strip() for r in rules_text.split('\n') if r.strip()]
            # 进一步按逗号分隔
            temp_rules = []
            for r in rules:
                temp_rules.extend([tr.strip() for tr in r.split(',') if tr.strip()])
            # 使用集合去重
            original_count = len(temp_rules)
            rules = list(set(temp_rules))
            # 如果有去重，在状态栏显示信息
            if original_count > len(rules):
                self.status_label.config(text=f"规则已自动去重: {original_count} -> {len(rules)}")
                self.update()  # 更新UI
        
        # 检查关键词
        if not self.keywords and not self.keywords_file_path:
            error_msg = "请先加载关键词"
            self.add_error_message(error_msg)
            messagebox.showwarning("警告", error_msg)
            return
        
        # 如果没有关键词但有文件路径，则重新读取
        if not self.keywords and self.keywords_file_path:
            try:
                self.keywords = self.excel_handler.read_keywords(self.keywords_file_path)
            except Exception as e:
                error_msg = f"重新读取关键词文件失败: {str(e)}"
                self.add_error_message(error_msg)
                messagebox.showerror("错误", error_msg)
                return
        
        try:
            # 重置进度条
            self.progress_bar["value"] = 0
            self.progress_label.config(text="")
            
            # 更新分类器的大小写敏感设置
            self.classifier.case_sensitive = self.case_sensitive.get()
            
            # 设置规则，并传递错误回调函数
            parse_errors = self.classifier.set_rules(rules, self.add_error_message)
            
            # 如果有规则解析错误，显示警告
            if parse_errors:
                self.status_label.config(text=f"警告: {len(parse_errors)} 条规则解析失败，详情请查看错误信息区域")
                self.update()  # 更新UI
            
            # 开始分类
            self.status_label.config(text="正在分类...")
            self.update()  # 更新UI
            
            # 记录开始时间
            start_time = time.time()
            
            # 修改classify_keywords方法的调用，添加进度更新
            total_keywords = len(self.keywords)
            results = []
            error_count = 0  # 记录错误数量
            
            for i, keyword in enumerate(self.keywords):
                # 对每个关键词应用所有规则
                matched_rules = []
                keyword_error = False  # 标记当前关键词是否有错误
                
                for rule_text, rule_matcher in self.classifier.parsed_rules:
                    try:
                        if rule_matcher(keyword):
                            matched_rules.append(rule_text)
                    except Exception as e:
                        error_msg = f"应用规则 '{rule_text}' 到关键词 '{keyword}' 时出错: {str(e)}"
                        self.add_error_message(error_msg)
                        error_count += 1
                        keyword_error = True
                
                # 添加结果
                results.append({
                    'keyword': keyword,
                    'matched_rules': '|'.join(matched_rules) if matched_rules else ''
                })
                
                # 更新进度
                if i % 5 == 0 or i == total_keywords - 1:  # 每5个关键词更新一次，或最后一个
                    self.update_progress(i + 1, total_keywords, start_time)
            
            # 计算总耗时
            end_time = time.time()
            total_time = end_time - start_time
            
            # 保存结果
            try:
                output_file = self.excel_handler.save_results(results)
                
                # 更新状态信息
                status_msg = f"分类完成，结果已保存至 {os.path.abspath(output_file)}"
                if error_count > 0:
                    status_msg += f" (处理过程中有 {error_count} 个错误)"
                self.status_label.config(text=status_msg)
                
                self.progress_label.config(text=f"总耗时: {total_time:.2f}秒 | 平均每个关键词: {total_time/total_keywords:.4f}秒")
                messagebox.showinfo("完成", f"分类完成，共处理 {len(results)} 个关键词，总耗时: {total_time:.2f}秒")
                
            except Exception as e:
                error_msg = f"保存结果失败: {str(e)}"
                self.add_error_message(error_msg)
                messagebox.showerror("错误", error_msg)
                self.status_label.config(text="分类完成但保存失败")
            
        except Exception as e:
            error_msg = f"分类过程中出错: {str(e)}"
            self.add_error_message(error_msg)
            messagebox.showerror("错误", error_msg)
            self.status_label.config(text="分类失败")
            self.progress_label.config(text="")
            self.progress_bar["value"] = 0

    def add_files(self):
        """添加文件到比较列表"""
        file_paths = filedialog.askopenfilenames(
            title="选择Excel文件", 
            filetypes=[("Excel Files", "*.xlsx")])
        
        if file_paths:
            # 筛选出以"关键词分类结果_"开头的文件
            valid_files = []
            for path in file_paths:
                filename = os.path.basename(path)
                if filename.startswith("关键词分类结果_"):
                    valid_files.append(path)
                    self.compare_files.append(path)
            
            # 更新文件列表显示
            self.update_file_list_display()
            
            # 显示提示信息
            if len(valid_files) < len(file_paths):
                messagebox.showinfo("提示", f"已添加 {len(valid_files)} 个有效文件，忽略了 {len(file_paths) - len(valid_files)} 个非关键词分类结果文件")
            else:
                self.compare_status_label.config(text=f"已添加 {len(valid_files)} 个文件")
    
    def add_folder(self):
        """添加文件夹下所有符合条件的文件"""
        folder_path = filedialog.askdirectory(title="选择文件夹")
        
        if folder_path:
            # 获取文件夹下所有Excel文件
            excel_files = []
            for file in os.listdir(folder_path):
                if file.endswith(".xlsx") and file.startswith("关键词分类结果_"):
                    full_path = os.path.join(folder_path, file)
                    excel_files.append(full_path)
                    self.compare_files.append(full_path)
            
            # 更新文件列表显示
            self.update_file_list_display()
            
            # 显示提示信息
            if excel_files:
                self.compare_status_label.config(text=f"已从文件夹添加 {len(excel_files)} 个文件")
            else:
                messagebox.showinfo("提示", "所选文件夹中没有找到符合条件的Excel文件")
    
    def clear_file_list(self):
        """清空文件列表"""
        self.compare_files = []
        self.update_file_list_display()
        self.compare_status_label.config(text="文件列表已清空")
        
        # 清空比较结果
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state=tk.DISABLED)
    
    def update_file_list_display(self):
        """更新文件列表显示"""
        self.files_text.config(state=tk.NORMAL)
        self.files_text.delete(1.0, tk.END)
        
        for i, file_path in enumerate(self.compare_files):
            filename = os.path.basename(file_path)
            self.files_text.insert(tk.END, f"{i+1}. {filename}\n")
        
        self.files_text.config(state=tk.DISABLED)
    
    def start_comparison(self):
        """开始比较文件内容"""
        # 检查文件列表
        if len(self.compare_files) < 2:
            messagebox.showwarning("警告", "请至少添加两个文件进行比较")
            return
        
        try:
            # 清空比较结果
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            
            # 更新状态
            self.compare_status_label.config(text="正在比较文件...")
            self.update()  # 更新UI
            
            # 读取第一个文件作为基准
            base_file = self.compare_files[0]
            base_filename = os.path.basename(base_file)
            base_df = pd.read_excel(base_file)
            
            # 显示基准文件信息
            self.result_text.insert(tk.END, f"基准文件: {base_filename}\n")
            self.result_text.insert(tk.END, f"包含 {len(base_df)} 行数据\n\n")
            
            # 存储所有比较结果，用于可能的导出
            all_comparison_results = []
            
            # 逐个比较其他文件
            for i, compare_file in enumerate(self.compare_files[1:], 1):
                compare_filename = os.path.basename(compare_file)
                self.result_text.insert(tk.END, f"比较文件 {i}: {compare_filename}\n")
                
                file_comparison_result = {
                    "file_name": compare_filename,
                    "differences": []
                }
                
                try:
                    compare_df = pd.read_excel(compare_file)
                    
                    # 检查行数是否一致
                    if len(base_df) != len(compare_df):
                        diff_msg = f"行数不一致! 基准: {len(base_df)}行, 比较文件: {len(compare_df)}行"
                        self.result_text.insert(tk.END, f"{diff_msg}\n")
                        file_comparison_result["row_count_diff"] = diff_msg
                    
                    # 检查列是否一致
                    if set(base_df.columns) != set(compare_df.columns):
                        missing_cols = set(base_df.columns) - set(compare_df.columns)
                        extra_cols = set(compare_df.columns) - set(base_df.columns)
                        
                        if missing_cols:
                            missing_msg = f"缺少列: {', '.join(missing_cols)}"
                            self.result_text.insert(tk.END, f"{missing_msg}\n")
                            file_comparison_result["missing_columns"] = list(missing_cols)
                        
                        if extra_cols:
                            extra_msg = f"多余列: {', '.join(extra_cols)}"
                            self.result_text.insert(tk.END, f"{extra_msg}\n")
                            file_comparison_result["extra_columns"] = list(extra_cols)
                    
                    # 检查共有列的内容是否一致
                    common_cols = set(base_df.columns).intersection(set(compare_df.columns))
                    differences = []
                    diff_count = 0
                    
                    # 确定要比较的最小行数
                    min_rows = min(len(base_df), len(compare_df))
                    
                    # 逐行比较共有列的内容
                    for row_idx in range(min_rows):
                        row_diffs = []
                        row_diff_dict = {"row": row_idx + 1, "column_diffs": []}
                        
                        for col in common_cols:
                            # 获取基准值和比较值
                            base_val = base_df.iloc[row_idx][col]
                            compare_val = compare_df.iloc[row_idx][col]
                            
                            # 处理NaN值的比较
                            if pd.isna(base_val) and pd.isna(compare_val):
                                continue  # 两者都是NaN，视为相同
                            elif pd.isna(base_val) or pd.isna(compare_val):
                                diff_text = f"{col}: 基准值为{'空' if pd.isna(base_val) else base_val}, 比较值为{'空' if pd.isna(compare_val) else compare_val}"
                                row_diffs.append(diff_text)
                                row_diff_dict["column_diffs"].append({
                                    "column": col,
                                    "base_value": "空" if pd.isna(base_val) else str(base_val),
                                    "compare_value": "空" if pd.isna(compare_val) else str(compare_val)
                                })
                                diff_count += 1
                            # 处理非NaN值的比较
                            elif base_val != compare_val:
                                diff_text = f"{col}: 基准值为{base_val}, 比较值为{compare_val}"
                                row_diffs.append(diff_text)
                                row_diff_dict["column_diffs"].append({
                                    "column": col,
                                    "base_value": str(base_val),
                                    "compare_value": str(compare_val)
                                })
                                diff_count += 1
                        
                        # 如果当前行有差异，记录下来
                        if row_diffs:
                            differences.append(f"第{row_idx+1}行: {', '.join(row_diffs)}")
                            file_comparison_result["differences"].append(row_diff_dict)
                    
                    # 显示比较结果
                    if differences:
                        self.result_text.insert(tk.END, f"发现 {diff_count} 处差异:\n")
                        for diff in differences[:20]:  # 限制显示前20个差异，避免界面过长
                            self.result_text.insert(tk.END, f"  - {diff}\n")
                        
                        if len(differences) > 20:
                            self.result_text.insert(tk.END, f"  ... 还有 {len(differences) - 20} 处差异未显示\n")
                    else:
                        self.result_text.insert(tk.END, "内容完全一致\n")
                    
                    self.result_text.insert(tk.END, "\n")
                    
                except Exception as e:
                    error_msg = f"比较文件 '{compare_filename}' 时出错: {str(e)}"
                    self.result_text.insert(tk.END, f"错误: {error_msg}\n\n")
                    file_comparison_result["error"] = error_msg
                
                # 添加当前文件的比较结果到总结果列表
                all_comparison_results.append(file_comparison_result)
            
            # 添加导出结果按钮
            # 获取result_frame作为父容器
            result_frame = self.result_text.master
            
            # 创建一个新的Frame作为导出按钮的容器
            export_frame = ttk.Frame(result_frame)
            export_frame.pack(fill=tk.X, padx=5, pady=5)
            
            export_btn = ttk.Button(
                export_frame, 
                text="导出比较结果", 
                command=lambda: self.export_comparison_results(all_comparison_results)
            )
            export_btn.pack(side=tk.LEFT, padx=5)
            
            # 更新状态
            self.compare_status_label.config(text="比较完成")
            self.result_text.see(1.0)  # 滚动到顶部
            
        except Exception as e:
            error_msg = f"比较过程中出错: {str(e)}"
            self.result_text.config(state=tk.NORMAL)
            self.result_text.insert(tk.END, f"错误: {error_msg}\n")
            self.compare_status_label.config(text="比较失败")
        
        # 确保结果文本框为只读状态
        self.result_text.config(state=tk.DISABLED)
    
    def export_comparison_results(self, comparison_results):
        """导出比较结果到Excel文件"""
        if not comparison_results:
            messagebox.showwarning("警告", "没有比较结果可导出")
            return
        
        try:
            # 获取保存文件路径
            current_time = time.strftime("%Y%m%d_%H%M%S")
            default_filename = f"文件比较结果_{current_time}.xlsx"
            
            file_path = filedialog.asksaveasfilename(
                title="保存比较结果",
                initialfile=default_filename,
                defaultextension=".xlsx",
                filetypes=[("Excel Files", "*.xlsx")]
            )
            
            if not file_path:
                return  # 用户取消了保存操作
            
            # 创建一个Excel写入器
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 创建一个总览表
                overview_data = []
                for i, result in enumerate(comparison_results):
                    file_name = result.get("file_name", f"文件{i+1}")
                    diff_count = len(result.get("differences", []))
                    row_count_diff = result.get("row_count_diff", "行数一致")
                    missing_cols = ", ".join(result.get("missing_columns", [])) or "无"
                    extra_cols = ", ".join(result.get("extra_columns", [])) or "无"
                    error = result.get("error", "无")
                    
                    overview_data.append({
                        "文件名": file_name,
                        "差异数量": diff_count,
                        "行数差异": row_count_diff if "行数不一致" in row_count_diff else "行数一致",
                        "缺少列": missing_cols,
                        "多余列": extra_cols,
                        "错误信息": error
                    })
                
                # 写入总览表
                overview_df = pd.DataFrame(overview_data)
                overview_df.to_excel(writer, sheet_name="比较总览", index=False)
                
                # 为每个文件创建详细差异表
                for i, result in enumerate(comparison_results):
                    file_name = result.get("file_name", f"文件{i+1}")
                    differences = result.get("differences", [])
                    
                    if differences:
                        # 创建详细差异数据
                        detail_data = []
                        for diff in differences:
                            row_num = diff.get("row", "")
                            for col_diff in diff.get("column_diffs", []):
                                detail_data.append({
                                    "行号": row_num,
                                    "列名": col_diff.get("column", ""),
                                    "基准值": col_diff.get("base_value", ""),
                                    "比较值": col_diff.get("compare_value", "")
                                })
                        
                        # 写入详细差异表
                        if detail_data:
                            detail_df = pd.DataFrame(detail_data)
                            sheet_name = f"差异详情_{i+1}"
                            detail_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            messagebox.showinfo("成功", f"比较结果已导出到: {file_path}")
            self.compare_status_label.config(text=f"比较结果已导出到: {os.path.basename(file_path)}")
            
        except Exception as e:
            error_msg = f"导出比较结果失败: {str(e)}"
            messagebox.showerror("错误", error_msg)
            self.compare_status_label.config(text="导出失败")

def main():
    window = MainWindow()
    window.mainloop()

if __name__ == "__main__":
    main()