import win32com.client
import datetime
import os

def start_powerpoint():
    """启动 PowerPoint 应用程序并返回应用程序对象。"""
    try:
        Application = win32com.client.Dispatch("PowerPoint.Application")
        # Application.DisplayAlerts = False  # 移除尝试设置 DisplayAlerts 的行
        return Application
    except Exception as e:
        print(f"启动 PowerPoint 失败: {e}")
        return None

def create_new_presentation(app):
    """创建一个新的 PowerPoint 演示文稿并返回演示文稿对象。"""
    if app:
        try:
            Presentation = app.Presentations.Add()
            return Presentation
        except Exception as e:
            print(f"创建新的演示文稿失败: {e}")
            return None
    return None

def add_slide_content(presentation, title_text, content_text):
    """向演示文稿添加一张幻灯片并设置标题和内容。"""
    if presentation:
        try:
            Slide = presentation.Slides.Add(1, 12)  # 使用标题和内容版式
            for shape in Slide.Shapes:
                if shape.Type == 1:  # msoPlaceholderTitle
                    shape.TextFrame.Text = title_text
                elif shape.Type == 2:  # msoPlaceholderBody
                    shape.TextFrame.Text = content_text
            return True
        except Exception as e:
            print(f"添加幻灯片内容失败: {e}")
            return False
    return False

def add_page_numbers(presentation):
    """向演示文稿的所有幻灯片添加页码。"""
    if presentation:
        try:
            for i in range(1, presentation.Slides.Count + 1):
                slide = presentation.Slides(i)
                headers_footers = slide.HeadersFooters
                headers_footers.SlideNumber.Visible = True
            return True
        except Exception as e:
            print(f"添加页码失败: {e}")
            return False
    return False

def show_presentation(app):
    """在前台显示 PowerPoint 应用程序。"""
    if app:
        try:
            app.Visible = True
            return True
        except Exception as e:
            print(f"显示 PowerPoint 失败: {e}")
            return False
    return False

def generate_filename(save_path):
    """生成带有时间戳的文件名。"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ppt_{timestamp}.pptx"
    full_path = os.path.join(save_path, filename)
    return full_path

def save_presentation(presentation, save_path):
    """保存演示文稿到指定路径，文件名包含时间戳。"""
    if presentation:
        try:
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            full_path = generate_filename(save_path)
            presentation.SaveAs(full_path)
            print(f"演示文稿已保存到: {full_path}")
            return True
        except Exception as e:
            print(f"保存演示文稿失败: {e}")
            return False
    return False

def close_powerpoint(app, presentation=None):
    """关闭演示文稿并退出 PowerPoint 应用程序。"""
    if presentation:
        try:
            presentation.Close()
        except Exception as e:
            print(f"关闭演示文稿失败: {e}")
    if app:
        try:
            app.Quit()
        except Exception as e:
            print(f"退出 PowerPoint 失败: {e}")

def main():
    """主函数，协调各个模块完成创建和保存 PowerPoint 演示文稿的操作。"""
    save_path = r"T:\ppt"
    title = "12345"
    content = "45678"

    app = start_powerpoint()
    if not app:
        return

    presentation = create_new_presentation(app)
    if not presentation:
        close_powerpoint(app)
        return

    if not add_slide_content(presentation, title, content):
        close_powerpoint(app, presentation)
        return

    if not add_page_numbers(presentation):
        close_powerpoint(app, presentation)
        return

    if not show_presentation(app):
        close_powerpoint(app, presentation)
        return

    if not save_presentation(presentation, save_path):
        close_powerpoint(app, presentation)
        return

    #close_powerpoint(app, presentation)

if __name__ == "__main__":
    main()