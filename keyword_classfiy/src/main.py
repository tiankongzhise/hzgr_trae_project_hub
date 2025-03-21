import sys
import os
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

from keyword_classifier import KeywordClassifier
from excel_handler import ExcelHandler

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("关键词分类工具")
        self.geometry("800x600")
        
        self.excel_handler = ExcelHandler()
        self.classifier = KeywordClassifier()
        
        self.init_ui()
    
    def init_ui(self):
        # 主框架
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
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
                self.rules_text.delete(1.0, tk.END)
                self.rules_text.insert(tk.END, "\n".join(rules))
                self.status_label.config(text=f"已加载 {len(rules)} 条规则")
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
                self.status_label.config(text=f"已加载 {len(self.keywords)} 个关键词")
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
            rules = temp_rules
        
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
                    'matched_rules': '|'.join(matched_rules) if matched_rules else '',
                    'error': '是' if keyword_error else '否'  # 添加错误标记
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

def main():
    window = MainWindow()
    window.mainloop()

if __name__ == "__main__":
    main()