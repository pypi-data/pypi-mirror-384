# python
from pathlib import Path
from setuptools import setup, find_packages

ROOT = Path(__file__).parent.resolve()
README_PATH = ROOT / "README.md"
LONG_DESC = README_PATH.read_text(encoding="utf-8") if README_PATH.exists() else ""

# 自动适配是否为 src 布局
SRC_DIR = ROOT / "src"
IS_SRC_LAYOUT = SRC_DIR.exists()

packages = find_packages(where="src") if IS_SRC_LAYOUT else find_packages(include=["tools_collections_python*"])
package_dir = {"": "src"} if IS_SRC_LAYOUT else {}

setup(
    name="tools-collections-python",
    version="0.0.8",  # 递增版本号
    packages=packages,
    package_dir=package_dir,
    include_package_data=True,
    install_requires=[],
    author="pikad",
    author_email="1195628604@qq.com",
    description="tools for some open-source projects",
    long_description=LONG_DESC,
    long_description_content_type="text/markdown",
    url="https://gitee.com/itdqj/tools_collections_python",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
)