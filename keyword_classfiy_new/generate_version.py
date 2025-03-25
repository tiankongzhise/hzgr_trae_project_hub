import toml
import os
from pathlib import Path

# 获取项目根目录路径
project_root = Path(__file__).parent

# 读取pyproject.toml
toml_path = project_root / 'pyproject.toml'
with open(toml_path, 'r', encoding='utf-8') as f:
    data = toml.load(f)

# 获取版本号
version = data['project']['version']

# 生成version.py内容
version_content = f'__version__ = "{version}"'

# 写入src/version.py
version_path = project_root / 'src' / 'version.py'
with open(version_path, 'w', encoding='utf-8') as f:
    f.write(version_content)

print(f'Successfully generated version.py with version {version}')