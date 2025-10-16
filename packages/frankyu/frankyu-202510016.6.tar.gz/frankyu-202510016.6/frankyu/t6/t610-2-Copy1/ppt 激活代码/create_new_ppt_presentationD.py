import win32com.client
import os
import time
import subprocess
import datetime
from typing import Optional, Tuple, Any

# 获取 PowerPoint 的常量，例如幻灯片版式、保存格式等
# 如果直接使用数字，可能可读性差，推荐使用常量
try:
    constants = win32com.client.constants
    # 定义常用的PowerPoint常量，方便使用
    ppLayoutBlank = constants.ppLayoutBlank  # 空白幻灯片布局
    ppLayoutTitle = constants.ppLayoutTitle  # 标题幻灯片布局
    ppLayoutTitleAndContent = constants.ppLayoutTitleAndContent # 标题和内容布局
    ppSaveAsPresentation = constants.ppSaveAsPresentation # 保存为PPTX格式
    msoTextOrientationHorizontal = constants.msoTextOrientationHorizontal # 文本框水平方向
    msoTrue = constants.msoTrue # True
    msoFalse = constants.msoFalse # False
except AttributeError:
    # 如果无法导入常量，则使用硬编码的数字值（不推荐，但作为备用）
    print("警告: 无法加载 PowerPoint COM 常量。将使用硬编码的数字值。")
    ppLayoutBlank = 12
    ppLayoutTitle = 1
    ppLayoutTitleAndContent = 2
    ppSaveAsPresentation = 1
    msoTextOrientationHorizontal = 1
    msoTrue = -1 # 这些值是COM对象的内部表示
    msoFalse = 0 # 同样是COM对象的内部表示


def process_ppt(
    presentation_path: Optional[str] = None,
    slide_index: int = 1, # 默认操作第一张幻灯片
    content_to_add: Optional[list] = None, # 例如：[{"type": "text", "text": "Hello", "left": 100, "top": 100, "width": 300, "height": 50}, {"type": "image", "path": "path/to/image.png", "left": 50, "top": 50, "width": 200, "height": 150}]
    ppt_visible: bool = True,
    save_presentation: bool = False,
    save_path: Optional[str] = None,
    close_presentation: bool = False,
    quit_ppt: bool = False,
    kill_existing_ppt: bool = False # 新增参数，默认不终止现有进程
) -> Tuple[Any, Any, Any]:
    """
    使用 pywin32 操作 PowerPoint 演示文稿，添加内容。

    Args:
        presentation_path (str, optional): 要打开的现有 PowerPoint 文件路径。如果为 None，则创建一个新的演示文稿。
        slide_index (int): 要操作的幻灯片索引 (从 1 开始)。如果幻灯片不存在，将添加新幻灯片。
        content_to_add (list, optional): 要添加到幻灯片的内容列表。
                                        每个元素是一个字典，包含 "type" ("text" 或 "image") 和其他相关参数。
        ppt_visible (bool): 控制 PowerPoint 应用程序是否可见。默认为 True。
        save_presentation (bool): 是否保存演示文稿。默认为 False。
        save_path (str, optional): 如果 save_presentation 为 True，指定保存文件的完整路径。
                                    如果 save_presentation 为 True 但 save_path 为 None 且是新创建的演示文稿，
                                    将尝试保存到当前目录下的一个临时文件名。
        close_presentation (bool): 是否在操作完成后关闭演示文稿。默认为 False。
        quit_ppt (bool): 是否在操作完成后退出 PowerPoint 应用程序。默认为 False。
        kill_existing_ppt (bool): 如果为 True，则在开始处理之前强制终止所有正在运行的 POWERPNT.EXE 进程。默认为 False。

    Returns:
        tuple: 包含 PowerPoint 应用程序对象 (ppt_app), 演示文稿对象 (presentation), 幻灯片对象 (slide)。
               如果 quit_ppt 为 True，则返回 (None, None, None)，因为对象已被释放。
    """
    ppt_app = None
    presentation = None
    slide = None

    # --- 新增的逻辑：终止现有 PowerPoint 进程 ---
    if kill_existing_ppt:
        print("尝试终止现有 POWERPNT.EXE 进程...")
        try:
            # 使用 taskkill 命令强制终止所有 POWERPNT.EXE 进程
            result = subprocess.run(['taskkill', '/F', '/IM', 'POWERPNT.EXE'], check=False, capture_output=True, text=True, encoding='gbk')
            print("Taskkill 命令执行完毕。注意：如果没有 PowerPoint 进程运行，可能会显示错误信息，这是正常的。")
            time.sleep(1) # 给系统一点时间来完全终止进程
        except FileNotFoundError:
            print("错误：找不到 taskkill 命令。请确认您是否在 Windows 系统上运行此脚本。")
        except Exception as e:
            print(f"尝试终止 PowerPoint 进程时发生错误: {e}")
    # --- 新增逻辑结束 ---

    try:
        # 创建或获取 PowerPoint 应用程序对象
        ppt_app = win32com.client.Dispatch("PowerPoint.Application")
        ppt_app.Visible = ppt_visible
        ppt_app.DisplayAlerts = msoFalse # 关闭警告提示

        # 打开现有演示文稿或创建新演示文稿
        if presentation_path and os.path.exists(presentation_path):
            print(f"正在打开演示文稿: {presentation_path}")
            presentation = ppt_app.Presentations.Open(presentation_path)
            # 在PowerPoint中，没有Excel ReadOnly的直接属性，但保存时会提示
        else:
            if presentation_path:
                print(f"警告: 演示文稿 '{presentation_path}' 未找到。改为创建一个新的演示文稿。")
            print("正在创建一个新的演示文稿。")
            presentation = ppt_app.Presentations.Add()

        # 获取或添加幻灯片
        if slide_index > presentation.Slides.Count:
            # 如果请求的索引超出当前幻灯片数量，则添加新幻灯片
            print(f"幻灯片索引 {slide_index} 不存在。正在添加新幻灯片...")
            slide = presentation.Slides.Add(slide_index, ppLayoutBlank) # 默认添加空白幻灯片
        else:
            slide = presentation.Slides(slide_index)
            print(f"正在使用幻灯片: {slide_index}")

        # 添加内容到幻灯片
        if content_to_add:
            print("正在添加内容到幻灯片...")
            for item in content_to_add:
                item_type = item.get("type")
                left = item.get("left", 50)
                top = item.get("top", 50)
                width = item.get("width", 400)
                height = item.get("height", 100)

                if item_type == "text":
                    text_content = item.get("text", "")
                    try:
                        textbox = slide.Shapes.AddTextbox(
                            msoTextOrientationHorizontal, # 水平文本框
                            left, top, width, height
                        )
                        textbox.TextFrame.TextRange.Text = text_content
                        print(f"已添加文本框: '{text_content}'")
                    except Exception as e:
                        print(f"添加文本框时出错: {e}")
                elif item_type == "image":
                    image_path = item.get("path")
                    if image_path and os.path.exists(image_path):
                        try:
                            # AddPicture(FileName, LinkToFile, SaveWithDocument, Left, Top, Width, Height)
                            slide.Shapes.AddPicture(
                                FileName=image_path,
                                LinkToFile=msoFalse,        # 不链接到文件
                                SaveWithDocument=msoTrue,   # 嵌入到文档中
                                Left=left, Top=top, Width=width, Height=height
                            )
                            print(f"已添加图片: {image_path}")
                        except Exception as e:
                            print(f"添加图片 '{image_path}' 时出错: {e}")
                    else:
                        print(f"警告: 图片文件 '{image_path}' 不存在，跳过添加。")
                # 可以根据需要添加更多内容类型，例如：
                # elif item_type == "table":
                #     rows = item.get("rows", 2)
                #     cols = item.get("cols", 2)
                #     table = slide.Shapes.AddTable(rows, cols, Left=left, Top=top, Width=width, Height=height)
                #     print("已添加表格")
                else:
                    print(f"警告: 未知内容类型 '{item_type}'，跳过。")

        # 保存演示文稿
        if save_presentation:
            if save_path:
                full_save_path = os.path.abspath(save_path) # 获取绝对路径
            elif presentation_path:
                full_save_path = os.path.abspath(presentation_path) # 如果是打开的现有演示文稿，默认保存回原路径
            else:
                # 如果是新演示文稿且没有指定保存路径，生成一个临时文件名
                temp_dir = os.getcwd() # 保存到当前工作目录
                temp_filename = f"temp_ppt_{int(time.time())}.pptx"
                full_save_path = os.path.join(temp_dir, temp_filename)
                print(f"新演示文稿未指定 save_path。将保存到临时文件: {full_save_path}")

            try:
                # ppSaveAsPresentation = 1 (for .pptx format)
                presentation.SaveAs(full_save_path, ppSaveAsPresentation)
                print(f"演示文稿已保存到: {full_save_path}")
            except Exception as e:
                print(f"保存演示文稿到 '{full_save_path}' 时出错: {e}")

    except Exception as e:
        print(f"在 PowerPoint 处理过程中发生错误: {e}")

    finally:
        # 清理资源
        if presentation is not None:
            if close_presentation:
                try:
                    # SaveChanges=True 强制保存，SaveChanges=False 不保存更改
                    # 如果 save_presentation 已经处理了保存，这里可以设置为 False 或 True
                    presentation.Close() # 关闭前 SaveAs 已经完成保存，所以这里可以不带参数
                    print("演示文稿已关闭。")
                except Exception as e:
                    print(f"关闭演示文稿时出错: {e}")

        if ppt_app is not None:
            if quit_ppt:
                try:
                    ppt_app.Quit()
                    print("PowerPoint 已退出。")
                except Exception as e:
                    print(f"退出 PowerPoint 时出错: {e}")

        # 返回对象，除非已退出 PowerPoint
        if not quit_ppt and ppt_app is not None:
            return ppt_app, presentation, slide
        else:
            # 如果 PowerPoint 已退出或未成功创建，COM 对象可能无效，返回 None
            return None, None, None


def create_new_ppt_presentationD(
    base_name: str = "ppt.ppt",
    cloud_storage_path: str = r'https://d.docs.live.net/9122e41a29eea899/sb_yufengguang/ppt/', # 示例路径，可能需要修改
    local_storage_path: str = "D:\\",
    use_cloud_storage: bool = False,
    content_to_add: Optional[list] = None,
    kill_existing_ppt: bool = False,
    quit_ppt_after_creation: bool = False,
    close_presentation_after_creation: bool = False,
    save_presentation: bool = True,
    ppt_visible: bool = True,
    file_extension: str = ".pptx",
    timestamp_format: str = "%Y%m%d%H%M%S%f",
    overwrite_existing: bool = False
) -> Tuple[Any, Any, Any]:
    """
    创建一个带有时间戳文件名的新PowerPoint演示文稿，并可选择添加内容。
    
    参数:
        base_name (str): 演示文稿基础名称，默认为"presentation"。
        cloud_storage_path (str): 云存储路径，默认为示例OneDrive路径。
        local_storage_path (str): 本地存储路径，默认为"D:\\"。
        use_cloud_storage (bool): 是否使用云存储路径，默认为False(使用本地)。
        content_to_add (list, optional): 要添加到演示文稿的内容列表。
                                        例如：[{"type": "text", "text": "Hello", "left": 100, "top": 100, "width": 300, "height": 50}]
        kill_existing_ppt (bool): 是否终止现有的PowerPoint进程，默认为False。
        quit_ppt_after_creation (bool): 创建后是否退出PowerPoint，默认为False。
        close_presentation_after_creation (bool): 创建后是否关闭演示文稿，默认为False。
        save_presentation (bool): 是否保存演示文稿，默认为True。
        ppt_visible (bool): PowerPoint是否可见，默认为True。
        file_extension (str): 文件扩展名，默认为".pptx"。
        timestamp_format (str): 时间戳格式，默认为"%Y%m%d%H%M%S%f"。
        overwrite_existing (bool): 如果文件存在是否覆盖，默认为False。
            
    返回:
        元组: (PowerPoint应用对象, 演示文稿对象, 幻灯片对象) 如果已退出则返回(None, None, None)。
    """
    try:
        # 生成时间戳
        timestamp = datetime.datetime.now().strftime(timestamp_format)
        
        # 确定存储路径
        storage_path = cloud_storage_path if use_cloud_storage else local_storage_path
        
        # 确保路径以斜杠结尾
        if not storage_path.endswith(os.sep) and not storage_path.endswith('/'):
            storage_path += os.sep

        # 创建完整文件路径
        filename = f"{base_name}_{timestamp}{file_extension}"
        full_path = os.path.join(storage_path, filename) # 使用os.path.join更稳健
        
        print(f"正在创建新演示文稿: {full_path}")
        
        # 检查文件是否存在(如果不允许覆盖)
        if not overwrite_existing and os.path.exists(full_path):
            raise FileExistsError(f"文件已存在: {full_path}")
        
        # 创建演示文稿
        ppt_app, presentation, slide = process_ppt(
            kill_existing_ppt=kill_existing_ppt,
            content_to_add=content_to_add,
            quit_ppt=quit_ppt_after_creation,
            close_presentation=close_presentation_after_creation,
            save_path=full_path,
            save_presentation=save_presentation,
            ppt_visible=ppt_visible
        )
        
        return ppt_app, presentation, slide
        
    except FileExistsError as fee:
        print(f"错误: {fee}")
        return None, None, None
    except Exception as e:
        print(f"创建演示文稿时发生意外错误: {e}")
        return None, None, None

# --- 使用示例 ---
if __name__ == "__main__":
    # 创建一个用于测试的图片文件（如果没有真实图片）
    dummy_image_path = "D:\\test_image.png"
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 50), color = 'red')
        img.save(dummy_image_path)
        print(f"已创建虚拟图片文件: {dummy_image_path}")
    except ImportError:
        print("警告: PIL (Pillow) 库未安装。无法创建虚拟图片文件。图片添加功能可能无法测试。请安装 'pip install Pillow'。")
        dummy_image_path = None # 将图片路径设为None，避免后续出错

    try:
        # 示例 1: 创建一个新的演示文稿，添加标题和内容
        print("\n--- 示例 1: 创建新演示文稿并添加文本 ---")
        ppt_app_1, presentation_1, slide_1 = create_new_ppt_presentationD(
            base_name="MyNewPPT_Text",
            local_storage_path="D:\\",
            content_to_add=[
                {"type": "text", "text": "Hello Pywin32 PowerPoint!", "left": 100, "top": 50, "width": 800, "height": 100},
                {"type": "text", "text": "这是一个自动生成的演示文稿。", "left": 100, "top": 150, "width": 800, "height": 50}
            ],
            kill_existing_ppt=False, # 第一次运行时可以设置为True，确保清理环境
            quit_ppt_after_creation=False,
            close_presentation_after_creation=False,
            save_presentation=True,
            ppt_visible=True
        )
        if ppt_app_1:
            print(f"示例 1 成功创建演示文稿: {presentation_1.FullName if presentation_1 else 'N/A'}")
            time.sleep(5) # 保持打开5秒以便观察
            # 可以在这里对 ppt_app_1, presentation_1, slide_1 进行更多操作
            # 例如，添加新幻灯片
            # new_slide = presentation_1.Slides.Add(presentation_1.Slides.Count + 1, ppLayoutTitle)
            # new_slide.Shapes.AddTextbox(msoTextOrientationHorizontal, 100, 100, 500, 50).TextFrame.TextRange.Text = "新幻灯片标题"
            
            # 操作完成后，如果之前没有设置 quit_ppt_after_creation=True，则手动退出
            if ppt_app_1: # 再次检查对象是否有效
                if presentation_1:
                    presentation_1.Close()
                ppt_app_1.Quit()
                print("示例 1 PowerPoint 应用程序已关闭。")


        # 示例 2: 创建一个新的演示文稿，并尝试添加图片和多行文本
        print("\n--- 示例 2: 创建新演示文稿并添加图片和多行文本 ---")
        if dummy_image_path:
            ppt_app_2, presentation_2, slide_2 = create_new_ppt_presentation(
                base_name="MyNewPPT_ImageText",
                local_storage_path="D:\\",
                content_to_add=[
                    {"type": "text", "text": "这张幻灯片包含一张图片和一些文本！", "left": 50, "top": 30, "width": 700, "height": 60},
                    {"type": "image", "path": dummy_image_path, "left": 100, "top": 100, "width": 200, "height": 100},
                    {"type": "text", "text": "左边是图片。", "left": 350, "top": 120, "width": 400, "height": 50}
                ],
                quit_ppt_after_creation=True, # 创建后自动退出 PowerPoint
                save_presentation=True,
                ppt_visible=True
            )
            if ppt_app_2 is None:
                print("示例 2 PowerPoint 应用程序已自动退出。")
            else:
                print("示例 2 成功创建演示文稿。")
        else:
            print("跳过示例 2: 未能创建虚拟图片文件，无法测试图片添加功能。")


    except Exception as e:
        print(f"主程序执行过程中发生错误: {e}")

    finally:
        # 清理可能残留的虚拟图片文件
        if dummy_image_path and os.path.exists(dummy_image_path):
            try:
                os.remove(dummy_image_path)
                print(f"已删除虚拟图片文件: {dummy_image_path}")
            except Exception as e:
                print(f"删除虚拟图片文件时出错: {e}")

