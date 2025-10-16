# 导入系统模块
import win32com.client  # 用于操作 PowerPoint 的 COM 接口
import datetime  # 用于生成时间戳
import os  # 用于路径操作
import pythoncom  # 用于 COM 初始化
from typing import Optional  # 类型提示支持


def init_ppt_app(visible: bool = True) -> object:
    """
    初始化 PowerPoint 应用实例
    
    思路:
        1. 首先初始化 COM 库，确保可以调用 COM 对象。
        2. 创建 PowerPoint 应用程序对象。
        3. 设置 PowerPoint 应用程序的可见性，默认是前台显示。
        4. 禁用所有警告弹窗，确保不会出现干扰用户的对话框。

    使用的方法和属性:
        - pythoncom.CoInitialize(): 初始化 COM 库。
        - win32com.client.Dispatch(): 创建 COM 对象。
        - ppt_app.Visible: 控制 PowerPoint 应用的显示状态。
        - ppt_app.DisplayAlerts: 禁用警告弹窗。

    Args:
        visible (bool): 是否前台显示 PowerPoint 窗口，默认为 True。

    Returns:
        object: 返回初始化的 PowerPoint 应用程序对象。
    """
    pythoncom.CoInitialize()  # 初始化 COM 组件
    ppt_app = win32com.client.Dispatch("PowerPoint.Application")  # 创建 PowerPoint 应用对象
    ppt_app.Visible = visible  # 控制 PowerPoint 应用的可见性
    ppt_app.DisplayAlerts = False  # 禁用所有警告弹窗
    return ppt_app  # 返回 PowerPoint 应用对象


def create_presentation(ppt_app: object) -> object:
    """
    创建空白演示文稿
    
    思路:
        1. 调用 PowerPoint 应用程序的 Presentations.Add() 方法。
        2. 创建一个新的空白演示文稿对象。

    使用的方法和属性:
        - ppt_app.Presentations.Add(): 创建新的演示文稿。

    Args:
        ppt_app (object): 已初始化的 PowerPoint 应用程序对象。

    Returns:
        object: 返回创建的演示文稿对象。
    """
    presentation = ppt_app.Presentations.Add()  # 新建演示文稿对象
    return presentation  # 返回演示文稿对象


def add_slide(
    presentation: object,
    title: str,
    content: str,
    layout: int = 5
) -> None:
    """
    添加内容幻灯片
    
    思路:
        1. 使用 Slides.Add 方法在指定位置添加新幻灯片。
        2. 设置幻灯片的标题和内容。
        3. 检查是否存在内容占位符，确保内容框可用。
        4. 如果存在内容框，则设置其文本内容。

    使用的方法和属性:
        - presentation.Slides.Add(): 添加新幻灯片。
        - slide.Shapes.Title.TextFrame.TextRange.Text: 设置标题文字。
        - slide.Shapes(2).TextFrame.TextRange.Text: 设置内容文字。

    Args:
        presentation (object): 演示文稿对象。
        title (str): 幻灯片标题文字。
        content (str): 幻灯片内容文字。
        layout (int): 幻灯片版式，默认为 5（标题 + 内容）。
    """
    slide = presentation.Slides.Add(1, layout)  # 添加新幻灯片
    slide.Shapes.Title.TextFrame.TextRange.Text = title  # 设置标题文字
    if slide.Shapes.Count >= 2:  # 检查内容框是否存在
        content_shape = slide.Shapes(2)  # 获取内容框
        content_shape.TextFrame.TextRange.Text = content  # 设置内容文字


def enable_page_numbers(presentation: object) -> None:
    """
    启用幻灯片页码
    
    思路:
        1. 获取演示文稿的幻灯片母版。
        2. 启用页脚和幻灯片页码的可见性。
        3. 遍历每张幻灯片，确保母版形状元素可见。

    使用的方法和属性:
        - presentation.SlideMaster.HeadersFooters: 获取母版的页眉页脚对象。
        - headers_footers.Footer.Visible: 启用页脚。
        - headers_footers.SlideNumber.Visible: 启用页码。
        - slide.DisplayMasterShapes: 显示母版形状。

    Args:
        presentation (object): 演示文稿对象。
    """
    slide_master = presentation.SlideMaster  # 获取幻灯片母版
    headers_footers = slide_master.HeadersFooters  # 获取页眉页脚设置
    headers_footers.Footer.Visible = True  # 启用页脚
    headers_footers.SlideNumber.Visible = True  # 启用页码
    for slide in presentation.Slides:  # 遍历所有幻灯片
        slide.DisplayMasterShapes = True  # 显示母版形状


def save_ppt(
    presentation: object,
    output_dir: str,
    filename: Optional[str] = None,
    timestamp_format: str = "%Y%m%d_%H%M%S"
) -> str:
    """
    保存演示文稿文件
    
    思路:
        1. 检查并创建保存目录。
        2. 如果未指定文件名，则生成基于时间戳的默认文件名。
        3. 将演示文稿保存到指定路径。

    使用的方法和属性:
        - os.makedirs(): 创建目录。
        - datetime.datetime.now().strftime(): 生成时间戳。
        - os.path.join(): 拼接文件路径。
        - presentation.SaveAs(): 保存演示文稿。

    Args:
        presentation (object): 演示文稿对象。
        output_dir (str): 文件保存目录。
        filename (Optional[str]): 自定义文件名，默认为 None。
        timestamp_format (str): 时间戳格式，默认为 "%Y%m%d_%H%M%S"。

    Returns:
        str: 保存的文件完整路径。
    """
    os.makedirs(output_dir, exist_ok=True)  # 创建输出目录（如果不存在）
    if not filename:  # 如果未指定文件名
        timestamp = datetime.datetime.now().strftime(timestamp_format)  # 获取时间戳
        filename = f"PPT_{timestamp}.pptx"  # 生成默认文件名
    save_path = os.path.join(output_dir, filename)  # 拼接完整文件路径
    presentation.SaveAs(save_path)  # 保存演示文稿
    return save_path  # 返回保存路径


def close_ppt(
    ppt_app: object,
    presentation: object
) -> None:
    """
    安全关闭 PPT 资源
    
    思路:
        1. 如果演示文稿对象存在，则关闭它。
        2. 如果 PowerPoint 应用程序对象存在，则退出它。
        3. 调用 pythoncom.CoUninitialize() 释放 COM 库。

    使用的方法和属性:
        - presentation.Close(): 关闭演示文稿。
        - ppt_app.Quit(): 退出 PowerPoint 应用程序。
        - pythoncom.CoUninitialize(): 释放 COM 库。

    Args:
        ppt_app (object): PowerPoint 应用程序对象。
        presentation (object): 演示文稿对象。
    """
    if presentation:  # 如果演示文稿对象存在
        presentation.Close()  # 关闭演示文稿
    if ppt_app:  # 如果 PowerPoint 应用程序对象存在
        try:
            ppt_app.Quit()  # 尝试退出 PowerPoint 应用程序
        except:
            pass  # 忽略异常
    pythoncom.CoUninitialize()  # 释放 COM 库


def create_sample_ppt():
    """
    完整的 PPT 创建示例
    
    思路:
        1. 初始化 PowerPoint 应用程序并创建空白演示文稿。
        2. 添加首页幻灯片并设置内容。
        3. 启用页码功能。
        4. 保存演示文稿到指定目录。
        5. 确保资源在操作完成后被安全释放。

    使用的方法和属性:
        - init_ppt_app(): 初始化 PowerPoint 应用程序。
        - create_presentation(): 创建空白演示文稿。
        - add_slide(): 添加内容幻灯片。
        - enable_page_numbers(): 启用页码。
        - save_ppt(): 保存演示文稿。
        - close_ppt(): 安全关闭资源。
    """
    ppt_app = None  # 初始化 PowerPoint 应用程序变量
    presentation = None  # 初始化演示文稿变量
    try:
        ppt_app = init_ppt_app(visible=True)  # 初始化 PowerPoint 应用程序
        presentation = create_presentation(ppt_app)  # 创建空白演示文稿
        add_slide(  # 添加内容幻灯片
            presentation,
            title="项目汇报",
            content="2023年度总结",
            layout=5
        )
        enable_page_numbers(presentation)  # 启用页码
        saved_path = save_ppt(  # 保存演示文稿
            presentation,
            output_dir="T:\\ppt",
            filename=None
        )
        print(f"文件已保存到：{saved_path}")  # 打印保存路径
    finally:
        close_ppt(ppt_app, presentation)  # 确保资源被安全释放


if __name__ == "__main__":
    create_sample_ppt()  # 程序入口，创建示例 PPT