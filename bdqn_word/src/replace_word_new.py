import os
import win32com.client as win32
from win32com.client import constants
from main import get_user_name
from tqdm import tqdm

def get_templite_file(target_path):
    # 存储符合条件的文件列表
    doc_files = []

    # 获取当前目录下所有文件和文件夹名称
    all_items = os.listdir(target_path)

    # # 遍历目录及子目录
    # for root, dirs, files in os.walk(target_path):
    #     for file in files:
    #         # 检查文件扩展名
    #         if file.lower().endswith(('.doc', '.docx')):
    #             # 拼接完整路径并添加到列表
    #             full_path = os.path.join(root, file)
    #             doc_files.append(full_path)
    # 筛选符合条件的文件（仅当前目录）
    for item in all_items:
        # 拼接完整路径
        full_path = os.path.join(target_path, item)
        # 检查是否为文件且扩展名为.doc或.docx
        if os.path.isfile(full_path) and item.lower().endswith(('.doc', '.docx')):
            doc_files.append(full_path)

    # 打印结果
    if not doc_files:
        print("未找到 .doc 或 .docx 文件。")
    return doc_files


def generate_authorization(template_path, user_name,output_dir):
    # 初始化Word应用
    word = win32.gencache.EnsureDispatch('Word.Application')
    word.Visible = False  # 隐藏Word界面
    
    try:
        # 解析模板路径
        template_dir = os.path.dirname(template_path)
        template_name = os.path.splitext(os.path.basename(template_path))[0]
        template_ext = os.path.splitext(template_path)[1].lower()
        
        # 打开模板文件（兼容.doc/.docx）
        doc = word.Documents.Open(template_path)
        
        # 执行全局替换（保留格式）
        word.Selection.Find.Execute(
            FindText="{账号}",
            ReplaceWith=user_name,
            Replace=constants.wdReplaceAll,
            MatchCase=False
        )

        # 生成输出路径
        os.makedirs(output_dir, exist_ok=True)
        new_filename = f"{template_name}_{user_name}{template_ext}"
        output_path = os.path.join(output_dir, new_filename)

        # 保存文件（保留原格式）
        doc.SaveAs(output_path, FileFormat=doc.SaveFormat)
        doc.Close()
        return output_path

    except Exception as e:
        raise RuntimeError(f"文档生成失败: {str(e)}")
    finally:
        word.Quit()  # 强制关闭进程

# 使用示例
if __name__ == "__main__":
    template_path = r"C:\Users\tiank\OneDrive\2025年项目\教育类\嘉华\北大青鸟总部授权"
    output_dir = r'C:\Users\tiank\OneDrive\2025年项目\教育类\嘉华\北大青鸟总部授权\授权书生成'
    user_name_list = get_user_name()
    templite_file_list = get_templite_file(template_path)
    for user_name in tqdm(user_name_list,desc='生成授权书'):
        for template_path in templite_file_list:
            saved_path = generate_authorization(template_path, user_name,output_dir)
            print(f"已生成授权书：{saved_path}")