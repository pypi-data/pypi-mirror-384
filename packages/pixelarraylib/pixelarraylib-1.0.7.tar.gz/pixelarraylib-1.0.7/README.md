# PixelArrayLib - PixelArray Python开发工具库

PixelArrayLib是一个功能丰富的Python开发工具库，包含阿里云服务、数据库工具、装饰器、监控等功能，同时提供便捷的命令行工具。

## 安装

```bash
pip install pixelarraylib
```

## 使用方法

### 1. Python程序中使用

```python
# 导入pixelarraylib模块
import pixelarraylib

# 使用各种功能模块
from pixelarraylib.aliyun import some_service
from pixelarraylib.db_utils import database_tools
from pixelarraylib.decorators import useful_decorators
```

### 2. 命令行工具使用

安装后，你可以在命令行中直接使用 `pixelarraylib` 命令：

#### 创建测试用例文件
```bash
# 一键创建所有测试用例文件
pixelarraylib create_test_case_files
```

## 功能特性

- **阿里云服务集成**: 包含CMS、Green、DM、FC、SMS、STS等服务
- **数据库工具**: MySQL、Redis等数据库操作工具
- **Web框架**: FastAPI集成
- **实用工具**: 二维码生成、加密解密、XML处理等
- **命令行工具**: 测试用例生成、代码统计等实用脚本

## 开发

### 本地开发安装

```bash
# 克隆仓库
git clone https://gitlab.com/pixelarrayai/general_pythondevutils_lib.git
cd general_pythondevutils_lib

# 安装开发依赖
pip install -e .

# 测试命令行工具
pixelarraylib --help
```

### 添加新的命令行工具

1. 在 `pixelarraylib/scripts/` 目录下创建新的脚本文件
2. 在 `pixelarraylib/__main__.py` 中添加新的命令选项
3. 更新 `pixelarraylib/scripts/__init__.py` 导出新功能

## 许可证

MIT License

## 作者

Lu qi (qi.lu@pixelarrayai.com) 