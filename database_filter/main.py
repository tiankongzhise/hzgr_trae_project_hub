import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import pymysql
from dotenv import load_dotenv
from openpyxl import Workbook

# 加载环境变量
# import sys
# dotenv_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), '.env')
# load_dotenv(dotenv_path)
load_dotenv()

class DatabaseFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("数据库查询工具")
        
        # 数据库连接配置
        self.db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT',3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME')
        }
        # 初始化UI
        self.setup_ui()
    
    def setup_ui(self):
        # 数据库选择
        tk.Label(self.root, text="选择数据库:").grid(row=0, column=0, padx=5, pady=5)
        self.db_combobox = ttk.Combobox(self.root, state="readonly")
        self.db_combobox.grid(row=0, column=1, padx=5, pady=5)
        
        # 表格选择
        tk.Label(self.root, text="选择表格:").grid(row=1, column=0, padx=5, pady=5)
        self.table_combobox = ttk.Combobox(self.root, state="readonly")
        self.table_combobox.grid(row=1, column=1, padx=5, pady=5)
        
        # 维度选择
        tk.Label(self.root, text="筛选维度:").grid(row=2, column=0, padx=5, pady=5)
        self.column_combobox = ttk.Combobox(self.root, state="readonly")
        self.column_combobox.grid(row=2, column=1, padx=5, pady=5)
        
        # 关键词输入
        tk.Label(self.root, text="关键词(多个关键词可用逗号或换行分隔):").grid(row=3, column=0, padx=5, pady=5)
        self.keyword_entry = tk.Text(self.root, height=3, width=30)
        self.keyword_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # 查询按钮
        self.query_btn = tk.Button(self.root, text="查询", command=self.execute_query)
        self.query_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        # 导出按钮
        self.export_btn = tk.Button(self.root, text="导出为Excel", command=self.export_to_excel)
        self.export_btn.grid(row=5, column=0, columnspan=2, pady=10)
        
        # 结果展示
        self.result_text = tk.Text(self.root, height=10, width=50)
        self.result_text.grid(row=6, column=0, columnspan=2, padx=5, pady=5)
        
        # 初始化数据库连接
        self.connect_to_db()
    
    def connect_to_db(self):
        try:
            self.conn = pymysql.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            
            # 获取数据库列表
            self.cursor.execute("SHOW DATABASES")
            databases = [db[0] for db in self.cursor.fetchall()]
            self.db_combobox['values'] = databases
            
            # 绑定事件
            self.db_combobox.bind("<<ComboboxSelected>>", self.on_db_selected)
            
        except Exception as e:
            print(f"环境变量文件路径: {dotenv_path}")
            print(f"实际加载的数据库配置: {self.db_config}")
            
            # 详细的错误诊断信息
            error_details = f"数据库连接失败: {str(e)}\n"
            error_details += f"可能原因:\n"
            error_details += f"1. 数据库服务未运行: 请检查MySQL服务是否启动\n"
            error_details += f"2. 网络连接问题: 尝试ping {self.db_config['host']}\n"
            error_details += f"3. 权限问题: 用户'{self.db_config['user']}'是否有访问权限\n"
            error_details += f"4. 端口问题: 端口{self.db_config['port']}是否开放\n"
            error_details += f"5. 数据库不存在: 数据库'{self.db_config['database']}'是否存在"
            
            print(error_details)
            messagebox.showerror("错误", error_details)
    
    def on_db_selected(self, event):
        selected_db = self.db_combobox.get()
        self.cursor.execute(f"USE {selected_db}")
        
        # 获取表格列表
        self.cursor.execute("SHOW TABLES")
        tables = [table[0] for table in self.cursor.fetchall()]
        self.table_combobox['values'] = tables
        
        # 绑定事件
        self.table_combobox.bind("<<ComboboxSelected>>", self.on_table_selected)
    
    def on_table_selected(self, event):
        selected_table = self.table_combobox.get()
        
        # 获取列名
        self.cursor.execute(f"DESCRIBE {selected_table}")
        columns = [column[0] for column in self.cursor.fetchall()]
        self.column_combobox['values'] = columns
    
    def execute_query(self):
        try:
            table = self.table_combobox.get()
            column = self.column_combobox.get()
            keyword_text = self.keyword_entry.get("1.0", tk.END).strip()
            
            if not all([table, column, keyword_text]):
                messagebox.showwarning("警告", "请选择表格、维度和输入关键词")
                return
            
            # 解析关键词，支持逗号或换行分隔
            keywords = []
            for line in keyword_text.split('\n'):
                keywords.extend([k.strip() for k in line.split(',') if k.strip()])
            
            if not keywords:
                messagebox.showwarning("警告", "请输入有效的关键词")
                return
            
            # 构建多条件查询
            query = f"SELECT * FROM {table} WHERE "
            query += " OR ".join([f"{column} LIKE %s" for _ in keywords])
            params = [f"%{k}%" for k in keywords]
            self.cursor.execute(query, params)
            
            # 获取结果
            results = self.cursor.fetchall()
            
            # 显示结果
            self.result_text.delete(1.0, tk.END)
            for row in results:
                self.result_text.insert(tk.END, str(row) + "\n")
            
            # 保存结果用于导出
            self.query_results = results
            self.query_columns = [desc[0] for desc in self.cursor.description]
            
        except Exception as e:
            messagebox.showerror("错误", f"查询失败: {str(e)}")
    
    def export_to_excel(self):
        if not hasattr(self, 'query_results') or not self.query_results:
            messagebox.showwarning("警告", "没有可导出的查询结果")
            return
        
        try:
            # 创建DataFrame
            df = pd.DataFrame(self.query_results, columns=self.query_columns)
            
            # 保存为Excel
            file_path = "query_results.xlsx"
            df.to_excel(file_path, index=False)
            
            messagebox.showinfo("成功", f"数据已导出到 {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseFilterApp(root)
    root.mainloop()