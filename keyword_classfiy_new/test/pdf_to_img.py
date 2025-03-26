from pathlib import Path
# from PyPDF2 import PdfReader
# from PIL import Image
import fitz  # PyMuPDF

def convert_pdf_to_images(pdf_path: Path, output_folder: Path):
    if not output_folder.exists():
        output_folder.mkdir(parents=True, exist_ok=True)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF文件路径或文件不存在: {pdf_path}")
    
    if pdf_path.is_file():
        pdf_file_list = [pdf_path]
    else:
        pdf_file_list = [f for f in pdf_path.iterdir() if f.suffix.lower() == ".pdf"]
    
    for pdf_file in pdf_file_list:
        print(f"正在处理文件: {pdf_file}")
        # 打开PDF文件
        doc = fitz.open(pdf_file)
        
        # 遍历每一页
        for page_num in range(len(doc)):
            # 获取页面
            page = doc[page_num]
            # 将页面转换为图片
            pix = page.get_pixmap(matrix=fitz.Matrix(200/72, 200/72))  # 300 DPI
            # 保存图片
            output_path = output_folder / f"{pdf_file.stem}_page_{page_num + 1}.jpg"
            pix.save(str(output_path))
        
        # 关闭PDF文件
        doc.close()

if __name__ == "__main__":
    pdf_path = Path(r"E:\OneDrive\2025年项目\教育类\嘉华\北大青鸟总部授权\授权文件")
    output_folder = Path(r"E:\OneDrive\2025年项目\教育类\嘉华\北大青鸟总部授权\授权文件\img")
    convert_pdf_to_images(pdf_path, output_folder)
    

