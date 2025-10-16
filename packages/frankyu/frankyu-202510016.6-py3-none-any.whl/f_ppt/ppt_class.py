import win32com.client
# 导入 win32com.client 模块，用于与 COM 对象交互

import datetime
# 导入 datetime 模块，用于处理日期和时间

import os
# 导入 os 模块，用于操作文件和目录

import pythoncom
# 导入 pythoncom 模块，用于初始化和清理 COM 库

from typing import Optional
# 从 typing 模块导入 Optional，用于类型注释


class PPTCreator:
    """PPT 创建器类，用于自动化创建和操作 PowerPoint 演示文稿"""

    def __init__(
        self, 
        output_dir: str = "T:\\ppt", 
        visible: bool = True
    ):
        """
        初始化 PPT 创建器
        
        思路:
            1. 保存 PPT 保存目录和是否前台显示的参数。
            2. 初始化 PowerPoint 应用程序和演示文稿变量为 None。

        使用的方法和属性:
            - os 模块中的路径方法
            - win32com.client 模块用于与 PowerPoint COM 对象交互

        Args:
            output_dir (str): PPT 保存目录，默认为 "T:\\ppt"。
            visible (bool): 是否前台显示 PowerPoint 应用程序，默认为 True。
        """
        self.output_dir = output_dir
        # 保存 PPT 的输出目录

        self.visible = visible
        # 是否前台显示 PowerPoint 应用

        self.ppt_app = None
        # 初始化 PowerPoint 应用程序变量为 None

        self.presentation = None
        # 初始化演示文稿对象为 None

    def initialize_ppt(self) -> None:
        """初始化 PowerPoint 应用程序
        
        思路:
            1. 使用 pythoncom.CoInitialize 初始化 COM 库。
            2. 创建 PowerPoint.Application COM 对象。
            3. 设置是否前台显示和禁用警告弹窗。

        使用的方法和属性:
            - pythoncom.CoInitialize(): 初始化 COM 库。
            - win32com.client.Dispatch(): 创建 COM 对象。
            - ppt_app.Visible: 设置是否前台显示。
            - ppt_app.DisplayAlerts: 禁用警告弹窗。
        """
        pythoncom.CoInitialize()
        # 初始化 COM 库

        self.ppt_app = win32com.client.Dispatch(
            "PowerPoint.Application"
        )
        # 创建 PowerPoint 应用程序的 COM 对象

        self.ppt_app.Visible = self.visible
        # 设置 PowerPoint 是否前台显示

        self.ppt_app.DisplayAlerts = False
        # 禁用 PowerPoint 的警告弹窗

    def create_new_presentation(self) -> None:
        """创建新的演示文稿
        
        思路:
            1. 使用 PowerPoint 的 Presentations.Add 方法创建新演示文稿。
            2. 将创建的演示文稿对象保存到类变量中。

        使用的方法和属性:
            - ppt_app.Presentations.Add(): 创建新的演示文稿。
        """
        self.presentation = (
            self.ppt_app.Presentations.Add()
        )
        # 添加一个新的演示文稿对象

    def add_slide_with_content(
        self, 
        title: str, 
        content: str, 
        layout: int = 5
    ) -> None:
        """
        添加带内容的幻灯片
        
        思路:
            1. 使用 Slides.Add 方法添加新的幻灯片。
            2. 设置幻灯片标题和内容。
            3. 检查幻灯片形状数量，确保内容形状可用。

        使用的方法和属性:
            - presentation.Slides.Add(): 添加新的幻灯片。
            - slide.Shapes.Title.TextFrame.TextRange.Text: 设置标题文本。
            - slide.Shapes.Count: 检查形状数量确保内容形状存在。
            - slide.Shapes(2).TextFrame.TextRange.Text: 设置内容文本。

        Args:
            title (str): 幻灯片标题。
            content (str): 幻灯片内容。
            layout (int): 幻灯片版式，默认为 5（标题+内容）。
        """
        slide = self.presentation.Slides.Add(1, layout)
        # 添加新的幻灯片并指定版式

        slide.Shapes.Title.TextFrame.TextRange.Text = title
        # 设置幻灯片的标题文本

        if slide.Shapes.Count >= 2:
            # 如果幻灯片的形状数量大于等于 2

            content_shape = slide.Shapes(2)
            # 获取内容形状

            content_shape.TextFrame.TextRange.Text = content
            # 设置内容文本

    def setup_page_numbers(self) -> None:
        """设置幻灯片页码
        
        思路:
            1. 获取幻灯片母版的页眉页脚设置。
            2. 启用页脚和页码。
            3. 为每张幻灯片启用母版形状显示。

        使用的方法和属性:
            - presentation.SlideMaster.HeadersFooters: 获取母版页眉页脚对象。
            - headers_footers.Footer.Visible: 设置页脚可见性。
            - headers_footers.SlideNumber.Visible: 设置页码可见性。
            - slide.DisplayMasterShapes: 启用母版形状显示。
        """
        slide_master = self.presentation.SlideMaster
        # 获取幻灯片母版对象

        headers_footers = slide_master.HeadersFooters
        # 获取母版的页眉页脚设置

        headers_footers.Footer.Visible = True
        # 设置页脚可见

        headers_footers.SlideNumber.Visible = True
        # 设置页码可见

        for slide in self.presentation.Slides:
            # 遍历演示文稿中的每一张幻灯片

            slide.DisplayMasterShapes = True
            # 启用母版形状的显示

    def save_presentation(
        self, 
        filename: Optional[str] = None, 
        timestamp_format: str = "%Y%m%d_%H%M%S"
    ) -> str:
        """
        保存演示文稿
        
        思路:
            1. 检查并创建保存目录。
            2. 如果未提供文件名，则生成基于时间戳的文件名。
            3. 保存演示文稿到指定路径。

        使用的方法和属性:
            - os.makedirs(): 创建目录。
            - datetime.datetime.now().strftime(): 生成时间戳。
            - os.path.join(): 拼接文件路径。
            - presentation.SaveAs(): 保存演示文稿。

        Args:
            filename (Optional[str]): 自定义文件名，默认为 None。
            timestamp_format (str): 时间戳格式，默认为 "%Y%m%d_%H%M%S"。

        Returns:
            str: 保存的文件完整路径。
        """
        os.makedirs(self.output_dir, exist_ok=True)
        # 检查并创建保存目录

        if filename is None:
            # 如果未提供文件名

            timestamp = datetime.datetime.now().strftime(
                timestamp_format
            )
            # 获取当前时间，并根据指定格式生成时间戳

            filename = f"PPT_{timestamp}.pptx"
            # 使用时间戳生成默认文件名

        save_path = os.path.join(self.output_dir, filename)
        # 拼接完整的保存路径

        self.presentation.SaveAs(save_path)
        # 保存演示文稿到指定路径

        return save_path
        # 返回保存的文件路径

    def close(self) -> None:
        """清理资源并关闭 PowerPoint 应用程序
        
        思路:
            1. 检查并关闭演示文稿对象。
            2. 检查并退出 PowerPoint 应用程序。
            3. 使用 pythoncom.CoUninitialize 释放 COM 库。

        使用的方法和属性:
            - presentation.Close(): 关闭演示文稿。
            - ppt_app.Quit(): 退出 PowerPoint 应用程序。
            - pythoncom.CoUninitialize(): 释放 COM 库。
        """
        if self.presentation:
            # 如果演示文稿对象存在

            self.presentation.Close()
            # 关闭演示文稿

        if self.ppt_app:
            # 如果 PowerPoint 应用程序对象存在

            try:
                self.ppt_app.Quit()
                # 尝试退出 PowerPoint 应用程序
            except:
                pass
                # 忽略可能的异常

        pythoncom.CoUninitialize()
        # 释放 COM 库

    def __enter__(self):
        """支持 with 语句，自动初始化
        
        思路:
            1. 初始化 PowerPoint 应用程序。
            2. 创建新的演示文稿。
            3. 返回当前对象实例。

        使用的方法和属性:
            - initialize_ppt(): 初始化 PowerPoint 应用程序。
            - create_new_presentation(): 创建新的演示文稿。
        """
        self.initialize_ppt()
        # 初始化 PowerPoint 应用程序

        self.create_new_presentation()
        # 创建新的演示文稿

        return self
        # 返回当前对象实例

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句，自动清理资源
        
        思路:
            1. 调用 close 方法清理资源。
            2. 确保无论是否发生异常都能正常退出。

        使用的方法和属性:
            - close(): 清理资源。
        """
        self.close()
        # 清理资源


def create_sample_ppt():
    """创建示例 PPT 的完整流程
    
    思路:
        1. 使用 with 语句创建 PPTCreator 对象。
        2. 添加幻灯片内容。
        3. 设置页码。
        4. 保存演示文稿并打印保存路径。

    使用的方法和属性:
        - PPTCreator: PPT 创建器类。
        - add_slide_with_content(): 添加幻灯片内容。
        - setup_page_numbers(): 设置页码。
        - save_presentation(): 保存演示文稿。
    """
    with PPTCreator(output_dir="T:\\ppt", visible=True) as creator:
        # 使用 with 语句创建 PPTCreator 对象

        creator.add_slide_with_content(
            title="12345",
            content="45678"
        )
        # 添加幻灯片内容，设置标题和正文

        creator.setup_page_numbers()
        # 设置幻灯片页码

        saved_path = creator.save_presentation()
        # 保存演示文稿并获取保存路径

        print(f"PPT已保存至: {saved_path}")
        # 打印保存路径


if __name__ == "__main__":
    # 如果当前脚本作为主程序运行

    create_sample_ppt()
    # 调用 create_sample_ppt 函数，创建示例 PPT