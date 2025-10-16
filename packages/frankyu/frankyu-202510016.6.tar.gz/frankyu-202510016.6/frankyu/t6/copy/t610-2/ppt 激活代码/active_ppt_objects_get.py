import win32com.client
import time

def active_ppt_objects_get(ppt_application=None):
    """
    获取或创建PowerPoint应用程序、活动演示文稿、活动幻灯片，并获取或添加一个文本框
    
    Args:
        ppt_application: 可选，已有的PowerPoint应用程序对象
        
    Returns:
        元组 (ppt_app, presentation, slide, textbox)
            ppt_app: PowerPoint应用程序对象
            presentation: 活动演示文稿对象
            slide: 活动幻灯片对象
            textbox: 活动幻灯片上的一个文本框形状对象
            
    Raises:
        Exception: 当无法初始化PowerPoint对象时抛出
    """
    try:
        # 处理PowerPoint应用程序
        if ppt_application is None:
            try:
                ppt_application = win32com.client.GetObject(None, "PowerPoint.Application")
                print("已连接到现有PowerPoint应用程序")
                print(f"当前警告显示状态: {'开启' if ppt_application.DisplayAlerts else '关闭'}")
            except:
                ppt_application = win32com.client.Dispatch("PowerPoint.Application")
                ppt_application.Visible = True
                ppt_application.DisplayAlerts = False
                print("已创建新PowerPoint应用程序")
                print(f"警告显示状态设置为: {'开启' if ppt_application.DisplayAlerts else '关闭'}")
        
        # 确保PowerPoint应用程序有效
        if ppt_application is None:
            raise Exception("无法创建或获取PowerPoint应用程序实例")
            
        # 处理演示文稿
        try:
            # 尝试获取活动演示文稿，如果没有则创建一个
            if ppt_application.Presentations.Count > 0:
                active_presentation = ppt_application.ActivePresentation
                print(f"已获取现有演示文稿: {active_presentation.Name}")
            else:
                active_presentation = ppt_application.Presentations.Add()
                print(f"已创建新演示文稿: {active_presentation.Name}")
        except Exception as e:
            active_presentation = ppt_application.Presentations.Add()
            print(f"异常后创建新演示文稿: {active_presentation.Name}")
            
        # 处理幻灯片
        try:
            # 尝试获取活动幻灯片，如果没有则在第一页添加一个
            if active_presentation.Slides.Count > 0:
                active_slide = active_presentation.Slides(1) # 获取第一张幻灯片
                print(f"已获取现有幻灯片 (第一张): {active_slide.SlideIndex}")
            else:
                # Add(Index, Layout) - Index是幻灯片在演示文稿中的位置，Layout是幻灯片版式
                # 9代表 ppLayoutTitleAndContent (标题和内容)
                active_slide = active_presentation.Slides.Add(1, 12) # ppLayoutBlank (空白)
                print(f"已创建新幻灯片 (第一张): {active_slide.SlideIndex}")
        except Exception as e:
            active_slide = active_presentation.Slides.Add(1, 12) # ppLayoutBlank (空白)
            print(f"异常后创建新幻灯片: {active_slide.SlideIndex}")
            
        # 获取或添加一个文本框
        # 在PowerPoint中，没有像Excel 'Range' 那样直接的“单元格”概念。
        # 你需要添加一个形状 (Shape)，例如一个文本框 (TextBox)
        # 这里我们尝试获取幻灯片上的第一个文本框，如果没有则创建一个
        textbox = None
        for shape in active_slide.Shapes:
            if shape.HasTextFrame and shape.TextFrame.HasText:
                textbox = shape
                print(f"已获取现有文本框: {textbox.TextFrame.TextRange.Text}")
                break
        
        if textbox is None:
            # msoShapeRectangle 代表矩形形状，可以作为文本框使用
            # AddShape(Type, Left, Top, Width, Height)
            textbox = active_slide.Shapes.AddTextbox(1, 100, 100, 300, 50) # 1代表 msoTextOrientationHorizontal
            textbox.TextFrame.TextRange.Text = "这是一个新的文本框"
            print("已创建新的文本框")
            
        # 打印返回值的详细描述
        print("\n返回值描述:")
        print(f"1. PowerPoint应用程序对象: {ppt_application}")
        print(f"   版本: {ppt_application.Version}")
        print(f"   可见性: {'可见' if ppt_application.Visible else '不可见'}")
        print(f"   警告显示状态: {'开启' if ppt_application.DisplayAlerts else '关闭'}")
        
        print(f"\n2. 演示文稿对象: {active_presentation}")
        print(f"   名称: {active_presentation.Name}")
        print(f"   路径: {active_presentation.Path if active_presentation.Path else '未保存'}")
        print(f"   完整名称: {active_presentation.FullName}")
        print(f"   幻灯片数量: {active_presentation.Slides.Count}")
        
        print(f"\n3. 幻灯片对象: {active_slide}")
        print(f"   索引: {active_slide.SlideIndex}")
        print(f"   名称: {active_slide.Name}")
        print(f"   形状数量: {active_slide.Shapes.Count}")
        
        print(f"\n4. 文本框对象: {textbox}")
        if textbox:
            print(f"   文本: {textbox.TextFrame.TextRange.Text if textbox.HasTextFrame else '无文本框'}")
            print(f"   左边距: {textbox.Left}, 顶边距: {textbox.Top}")
            print(f"   宽度: {textbox.Width}, 高度: {textbox.Height}")
        
        return ppt_application, active_presentation, active_slide, textbox
        
    except Exception as e:
        raise Exception(f"PowerPoint对象初始化失败: {str(e)}")

if __name__ == "__main__":
    try:
        ppt_app, presentation, slide, textbox = active_ppt_objects_get()
        
        if textbox:
            new_text = "Hello, pywin32 and PowerPoint!"
            textbox.TextFrame.TextRange.Text = new_text
            print(f"\n操作结果: 已在文本框中设置值: '{new_text}'")
        else:
            print("\n操作结果: 未能找到或创建文本框。")
            
        time.sleep(10) # 保持PowerPoint应用程序打开10秒，以便观察
        
        # 演示文稿保存和关闭（可选）
        # save_path = "C:\\Users\\YourUser\\Documents\\MyPowerPointPresentation.pptx"
        # presentation.SaveAs(save_path)
        # print(f"\n演示文稿已保存到: {save_path}")
        # presentation.Close()
        # print("演示文稿已关闭。")
        # ppt_app.Quit() # 关闭PowerPoint应用程序
        # print("PowerPoint应用程序已关闭。")

    except Exception as e:
        print(f"操作失败: {e}")