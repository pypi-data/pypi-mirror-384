import win32com.client as wc

# 1. 启动 PowerPoint 应用程序并使其可见
def create_ppt_application():
    """
    启动 PowerPoint 应用程序并使其可见。
    """
    try:
        # 获取 PowerPoint 应用程序对象
        ppt_app = wc.Dispatch("PowerPoint.Application")
        # 使 PowerPoint 应用程序可见 (True 可见, False 不可见)
        ppt_app.Visible = True
        print("PowerPoint 应用程序已启动并可见。")
        return ppt_app
    except Exception as e:
        print(f"启动 PowerPoint 应用程序失败: {e}")
        return None

# 2. 创建一个新的演示文稿
def create_new_presentation(ppt_app):
    """
    在给定的 PowerPoint 应用程序中创建一个新的演示文稿。
    """
    if not ppt_app:
        print("PowerPoint 应用程序未启动。")
        return None
    try:
        # 添加一个新的演示文稿
        presentation = ppt_app.Presentations.Add()
        print("已创建一个新的演示文稿。")
        return presentation
    except Exception as e:
        print(f"创建新演示文稿失败: {e}")
        return None

# 3. 打开一个已存在的演示文稿
def open_existing_presentation(ppt_app, file_path):
    """
    在给定的 PowerPoint 应用程序中打开一个已存在的演示文稿。
    :param ppt_app: PowerPoint 应用程序对象
    :param file_path: 演示文稿的完整路径
    """
    if not ppt_app:
        print("PowerPoint 应用程序未启动。")
        return None
    try:
        # 打开一个已存在的演示文稿 (第二个参数是 ReadOnly, True 表示只读)
        presentation = ppt_app.Presentations.Open(file_path, False, False, False)
        print(f"已打开演示文稿: {file_path}")
        return presentation
    except Exception as e:
        print(f"打开演示文稿失败: {e}")
        return None

# 4. 保存演示文稿
def save_presentation(presentation, save_path):
    """
    保存演示文稿到指定路径。
    :param presentation: 演示文稿对象
    :param save_path: 保存的完整路径和文件名
    """
    if not presentation:
        print("演示文稿对象无效。")
        return
    try:
        # 保存演示文稿
        presentation.SaveAs(save_path)
        print(f"演示文稿已保存到: {save_path}")
    except Exception as e:
        print(f"保存演示文稿失败: {e}")

# 5. 关闭演示文稿
def close_presentation(presentation):
    """
    关闭演示文稿。
    :param presentation: 演示文稿对象
    """
    if not presentation:
        print("演示文稿对象无效。")
        return
    try:
        # 关闭演示文稿
        presentation.Close()
        print("演示文稿已关闭。")
    except Exception as e:
        print(f"关闭演示文稿失败: {e}")

# 6. 退出 PowerPoint 应用程序
def quit_ppt_application(ppt_app):
    """
    退出 PowerPoint 应用程序。
    :param ppt_app: PowerPoint 应用程序对象
    """
    if not ppt_app:
        print("PowerPoint 应用程序未启动。")
        return
    try:
        # 退出 PowerPoint 应用程序
        ppt_app.Quit()
        print("PowerPoint 应用程序已退出。")
    except Exception as e:
        print(f"退出 PowerPoint 应用程序失败: {e}")

# 7. 获取当前活动演示文稿
def get_active_presentation(ppt_app):
    """
    获取当前活动演示文稿。
    :param ppt_app: PowerPoint 应用程序对象
    """
    if not ppt_app:
        print("PowerPoint 应用程序未启动。")
        return None
    try:
        # 获取当前活动演示文稿
        active_presentation = ppt_app.ActivePresentation
        if active_presentation:
            print(f"当前活动演示文稿的名称是: {active_presentation.Name}")
            return active_presentation
        else:
            print("当前没有活动演示文稿。")
            return None
    except Exception as e:
        print(f"获取当前活动演示文稿失败: {e}")
        return None

# 8. 添加一张新的幻灯片
def add_new_slide(presentation, layout_index=1):
    """
    在演示文稿中添加一张新的幻灯片。
    :param presentation: 演示文稿对象
    :param layout_index: 幻灯片布局的索引 (例如: 1 表示标题幻灯片, 2 表示标题和内容幻灯片)
                         详见 MSO.MsoSlideLayout 枚举
                         https://learn.microsoft.com/zh-cn/office/vba/api/powerpoint.ppslidelayout
    """
    if not presentation:
        print("演示文稿对象无效。")
        return None
    try:
        # 获取幻灯片集合
        slides = presentation.Slides
        # 添加一张新的幻灯片
        # MsoSlideLayout.ppLayoutTitle (1) - 标题幻灯片
        # MsoSlideLayout.ppLayoutTitleAndContent (2) - 标题和内容幻灯片
        # MsoSlideLayout.ppLayoutBlank (12) - 空白幻灯片
        slide = slides.Add(slides.Count + 1, layout_index)
        print(f"已添加一张新的幻灯片，布局索引为: {layout_index}")
        return slide
    except Exception as e:
        print(f"添加新幻灯片失败: {e}")
        return None

# 9. 获取指定索引的幻灯片
def get_slide_by_index(presentation, index):
    """
    获取演示文稿中指定索引的幻灯片。
    :param presentation: 演示文稿对象
    :param index: 幻灯片索引 (从 1 开始)
    """
    if not presentation:
        print("演示文稿对象无效。")
        return None
    try:
        # 获取指定索引的幻灯片
        slide = presentation.Slides(index)
        print(f"已获取索引为 {index} 的幻灯片。")
        return slide
    except Exception as e:
        print(f"获取索引为 {index} 的幻灯片失败: {e}")
        return None

# 10. 删除指定索引的幻灯片
def delete_slide_by_index(presentation, index):
    """
    删除演示文稿中指定索引的幻灯片。
    :param presentation: 演示文稿对象
    :param index: 幻灯片索引 (从 1 开始)
    """
    if not presentation:
        print("演示文稿对象无效。")
        return
    try:
        # 删除指定索引的幻灯片
        presentation.Slides(index).Delete()
        print(f"已删除索引为 {index} 的幻灯片。")
    except Exception as e:
        print(f"删除索引为 {index} 的幻灯片失败: {e}")

# 11. 在幻灯片中添加文本框并设置文本
def add_text_box_to_slide(slide, text, left, top, width, height):
    """
    在幻灯片中添加一个文本框并设置其文本。
    :param slide: 幻灯片对象
    :param text: 要设置的文本内容
    :param left: 文本框左上角的 X 坐标
    :param top: 文本框左上角的 Y 坐标
    :param width: 文本框宽度
    :param height: 文本框高度
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 添加一个文本框 (MsoShapeType.msoTextBox)
        # Left, Top, Width, Height 都是以磅为单位
        shape = slide.Shapes.AddTextbox(1, left, top, width, height) # 1 代表 msoTextOrientationHorizontal
        # 获取文本框的文本帧
        text_frame = shape.TextFrame
        # 获取文本帧的文本范围
        text_range = text_frame.TextRange
        # 设置文本内容
        text_range.Text = text
        print(f"已在幻灯片中添加文本框并设置文本: '{text}'")
        return shape
    except Exception as e:
        print(f"添加文本框失败: {e}")
        return None

# 12. 设置文本框字体样式
def set_text_box_font(shape, font_name="微软雅黑", font_size=24, bold=False, italic=False, underline=False):
    """
    设置文本框的字体样式。
    :param shape: 形状对象 (文本框)
    :param font_name: 字体名称
    :param font_size: 字体大小
    :param bold: 是否加粗
    :param italic: 是否斜体
    :param underline: 是否下划线
    """
    if not shape or not hasattr(shape, 'TextFrame'):
        print("形状对象无效或不是文本框。")
        return
    try:
        font = shape.TextFrame.TextRange.Font
        font.Name = font_name
        font.Size = font_size
        font.Bold = bold
        font.Italic = italic
        font.Underline = underline
        print(f"已设置文本框字体: 名称='{font_name}', 大小={font_size}, 加粗={bold}, 斜体={italic}, 下划线={underline}")
    except Exception as e:
        print(f"设置文本框字体失败: {e}")

# 13. 在幻灯片中插入图片
def insert_picture_to_slide(slide, picture_path, left, top, width=-1, height=-1):
    """
    在幻灯片中插入图片。
    :param slide: 幻灯片对象
    :param picture_path: 图片文件的完整路径
    :param left: 图片左上角的 X 坐标
    :param top: 图片左上角的 Y 坐标
    :param width: 图片宽度 (可选, -1 表示自动调整)
    :param height: 图片高度 (可选, -1 表示自动调整)
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 插入图片 (MsoPictureCmd.msoPictureNormal 插入普通图片)
        # Left, Top, Width, Height 都是以磅为单位
        # -1 表示保持原始尺寸比例
        shape = slide.Shapes.AddPicture(picture_path, False, True, left, top, width, height)
        print(f"已在幻灯片中插入图片: {picture_path}")
        return shape
    except Exception as e:
        print(f"插入图片失败: {e}")
        return None

# 14. 获取幻灯片中所有形状的数量
def get_slide_shapes_count(slide):
    """
    获取幻灯片中所有形状的数量。
    :param slide: 幻灯片对象
    """
    if not slide:
        print("幻灯片对象无效。")
        return 0
    try:
        count = slide.Shapes.Count
        print(f"幻灯片中共有 {count} 个形状。")
        return count
    except Exception as e:
        print(f"获取形状数量失败: {e}")
        return 0

# 15. 按名称查找幻灯片中的形状
def find_shape_by_name(slide, shape_name):
    """
    按名称查找幻灯片中的形状。
    :param slide: 幻灯片对象
    :param shape_name: 形状的名称
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 遍历幻灯片中的所有形状
        for shape in slide.Shapes:
            if shape.Name == shape_name:
                print(f"已找到名称为 '{shape_name}' 的形状。")
                return shape
        print(f"未找到名称为 '{shape_name}' 的形状。")
        return None
    except Exception as e:
        print(f"查找形状失败: {e}")
        return None

# 16. 设置幻灯片背景颜色 (需要使用RGB值)
def set_slide_background_color(slide, r, g, b):
    """
    设置幻灯片背景颜色。
    :param slide: 幻灯片对象
    :param r: 红色分量 (0-255)
    :param g: 绿色分量 (0-255)
    :param b: 蓝色分量 (0-255)
    """
    if not slide:
        print("幻灯片对象无效。")
        return
    try:
        # 获取背景填充对象
        background_fill = slide.Background.Fill
        # 设置填充类型为纯色填充 (msoFillSolid)
        background_fill.PresetGradient(1, 1) # 随便选择一个渐变类型，然后改为纯色
        background_fill.Solid()
        # 获取背景的 ForeColor 对象
        background_color = background_fill.ForeColor
        # 设置 RGB 颜色
        background_color.RGB = r + (g << 8) + (b << 16)
        print(f"已设置幻灯片背景颜色为 RGB({r}, {g}, {b})。")
    except Exception as e:
        print(f"设置幻灯片背景颜色失败: {e}")

# 17. 获取幻灯片中的所有文本框（形状类型为 msoTextBox）
def get_all_text_boxes_on_slide(slide):
    """
    获取幻灯片中所有文本框。
    :param slide: 幻灯片对象
    :return: 文本框形状列表
    """
    if not slide:
        print("幻灯片对象无效。")
        return []
    text_boxes = []
    try:
        # 遍历幻灯片中的所有形状
        for shape in slide.Shapes:
            # 判断形状类型是否为文本框 (msoShapeType.msoTextBox = 17)
            if shape.Type == 17:  # MsoShapeType.msoTextBox
                text_boxes.append(shape)
                print(f"找到文本框: {shape.Name}, 文本: {shape.TextFrame.TextRange.Text.strip()}")
        return text_boxes
    except Exception as e:
        print(f"获取所有文本框失败: {e}")
        return []

# 18. 修改幻灯片标题
def set_slide_title(slide, title_text):
    """
    修改幻灯片标题。
    :param slide: 幻灯片对象
    :param title_text: 新的标题文本
    """
    if not slide:
        print("幻灯片对象无效。")
        return
    try:
        # 标题形状通常是幻灯片中的第一个形状，或者通过 PlaceholderType 识别
        for shape in slide.Shapes:
            if shape.HasTextFrame and shape.TextFrame.HasText:
                # 检查形状是否是标题占位符
                if shape.Type == 14: # msoPlaceholder
                    if shape.PlaceholderFormat.Type == 1: # ppPlaceholderTitle
                        shape.TextFrame.TextRange.Text = title_text
                        print(f"幻灯片标题已修改为: '{title_text}'")
                        return
        print("未找到幻灯片标题形状。")
    except Exception as e:
        print(f"修改幻灯片标题失败: {e}")

# 19. 插入表格到幻灯片
def insert_table_to_slide(slide, rows, columns, left, top, width, height):
    """
    在幻灯片中插入表格。
    :param slide: 幻灯片对象
    :param rows: 行数
    :param columns: 列数
    :param left: 表格左上角的 X 坐标
    :param top: 表格左上角的 Y 坐标
    :param width: 表格宽度
    :param height: 表格高度
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 插入表格
        shape = slide.Shapes.AddTable(rows, columns, left, top, width, height)
        print(f"已在幻灯片中插入一个 {rows} 行 {columns} 列的表格。")
        return shape
    except Exception as e:
        print(f"插入表格失败: {e}")
        return None

# 20. 设置表格单元格文本
def set_table_cell_text(table_shape, row, column, text):
    """
    设置表格指定单元格的文本。
    :param table_shape: 表格形状对象
    :param row: 行索引 (从 1 开始)
    :param column: 列索引 (从 1 开始)
    :param text: 单元格文本
    """
    if not table_shape or not hasattr(table_shape, 'Table'):
        print("表格形状对象无效。")
        return
    try:
        table = table_shape.Table
        cell = table.Cell(row, column)
        cell.Shape.TextFrame.TextRange.Text = text
        print(f"表格 ({row},{column}) 单元格文本已设置为: '{text}'")
    except Exception as e:
        print(f"设置表格单元格文本失败: {e}")

# 21. 插入图表到幻灯片
def insert_chart_to_slide(slide, chart_type, left, top, width, height):
    """
    在幻灯片中插入图表。
    :param slide: 幻灯片对象
    :param chart_type: 图表类型 (例如: -1 代表默认簇状柱形图，更多类型详见 MSO.XlChartType 枚举)
                        https://learn.microsoft.com/zh-cn/office/vba/api/excel.xlcharttype
    :param left: 图表左上角的 X 坐标
    :param top: 图表左上角的 Y 坐标
    :param width: 图表宽度
    :param height: 图表高度
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 插入图表
        # chart_type = -1 # 默认簇状柱形图 (xlColumnClustered)
        # 例如: wc.constants.xlPie (饼图), wc.constants.xlLine (折线图)
        shape = slide.Shapes.AddChart(chart_type, left, top, width, height)
        print(f"已在幻灯片中插入图表，类型为: {chart_type}")
        return shape
    except Exception as e:
        print(f"插入图表失败: {e}")
        return None

# 22. 获取图表数据表并修改数据
def update_chart_data(chart_shape, series_index, new_values):
    """
    更新图表的数据。
    :param chart_shape: 图表形状对象
    :param series_index: 系列索引 (从 1 开始)
    :param new_values: 新的数据列表 (例如: [10, 20, 30])
    """
    if not chart_shape or not hasattr(chart_shape, 'Chart'):
        print("图表形状对象无效。")
        return
    try:
        chart = chart_shape.Chart
        # 获取图表数据
        chart_data = chart.ChartData
        # 激活数据表
        chart_data.Activate()
        # 获取工作簿
        workbook = chart_data.Workbook
        # 获取第一个工作表
        worksheet = workbook.Sheets(1)

        # 清除现有数据 (可选，取决于更新策略)
        # worksheet.Cells.ClearContents()

        # 写入新数据
        for i, value in enumerate(new_values):
            # 假设数据从 B2 开始 (A列通常是类别标签)
            worksheet.Cells(i + 2, series_index + 1).Value = value

        # 重新应用数据源范围 (如果数据量变化需要重新设置)
        # 例如: chart.SetSourceData("Sheet1!$A$1:$B$4")

        # 保存并关闭工作簿
        workbook.Close()
        print(f"图表系列 {series_index} 数据已更新。")
    except Exception as e:
        print(f"更新图表数据失败: {e}")
        # 尝试关闭工作簿以避免悬挂
        if 'workbook' in locals() and workbook:
            workbook.Close(False) # False 表示不保存更改

# 23. 修改图表标题
def set_chart_title(chart_shape, title_text):
    """
    设置图表标题。
    :param chart_shape: 图表形状对象
    :param title_text: 新的图表标题文本
    """
    if not chart_shape or not hasattr(chart_shape, 'Chart'):
        print("图表形状对象无效。")
        return
    try:
        chart = chart_shape.Chart
        chart.HasTitle = True # 确保有标题
        chart.ChartTitle.Text = title_text
        print(f"图表标题已设置为: '{title_text}'")
    except Exception as e:
        print(f"设置图表标题失败: {e}")

# 24. 导出幻灯片为图片
def export_slide_as_image(slide, output_path, image_format="PNG"):
    """
    将幻灯片导出为图片。
    :param slide: 幻灯片对象
    :param output_path: 输出图片文件的完整路径 (例如: "C:\\temp\\slide1.png")
    :param image_format: 图片格式 ("PNG", "JPG", "BMP", "GIF")
    """
    if not slide:
        print("幻灯片对象无效。")
        return
    try:
        # 导出幻灯片
        # image_format 对应 MsoExportType 枚举，但这里通常直接用字符串
        slide.Export(output_path, image_format)
        print(f"幻灯片已导出为图片: {output_path}")
    except Exception as e:
        print(f"导出幻灯片为图片失败: {e}")

# 25. 设置幻灯片切换效果
def set_slide_transition(slide, transition_type=3, speed=1):
    """
    设置幻灯片切换效果。
    :param slide: 幻灯片对象
    :param transition_type: 切换效果类型 (例如: 3 为淡入淡出，更多类型详见 MsoAnimateType 枚举)
                            https://learn.microsoft.com/zh-cn/office/vba/api/powerpoint.ppeffect
    :param speed: 切换速度 (1: 快, 2: 中, 3: 慢)
    """
    if not slide:
        print("幻灯片对象无效。")
        return
    try:
        entry_effect = slide.SlideShowTransition
        entry_effect.EntryEffect = transition_type
        entry_effect.Speed = speed # 1-3
        print(f"幻灯片切换效果已设置为: 类型={transition_type}, 速度={speed}")
    except Exception as e:
        print(f"设置幻灯片切换效果失败: {e}")

# 26. 运行幻灯片放映
def run_slideshow(presentation):
    """
    运行演示文稿的幻灯片放映。
    :param presentation: 演示文稿对象
    """
    if not presentation:
        print("演示文稿对象无效。")
        return
    try:
        # 运行幻灯片放映
        presentation.SlideShowSettings.Run()
        print("幻灯片放映已启动。")
    except Exception as e:
        print(f"启动幻灯片放映失败: {e}")

# 27. 插入音频到幻灯片
def insert_audio_to_slide(slide, audio_file_path, left, top, width, height):
    """
    在幻灯片中插入音频。
    :param slide: 幻灯片对象
    :param audio_file_path: 音频文件的完整路径
    :param left: 音频图标左上角的 X 坐标
    :param top: 音频图标左上角的 Y 坐标
    :param width: 音频图标宽度
    :param height: 音频图标高度
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        shape = slide.Shapes.AddMediaObject2(audio_file_path, left, top, width, height)
        # 可以进一步设置音频的播放属性，例如自动播放
        # shape.MediaFormat.PlayOnEntry = True
        print(f"已在幻灯片中插入音频: {audio_file_path}")
        return shape
    except Exception as e:
        print(f"插入音频失败: {e}")
        return None

# 28. 插入视频到幻灯片
def insert_video_to_slide(slide, video_file_path, left, top, width, height):
    """
    在幻灯片中插入视频。
    :param slide: 幻灯片对象
    :param video_file_path: 视频文件的完整路径
    :param left: 视频左上角的 X 坐标
    :param top: 视频左上角的 Y 坐标
    :param width: 视频宽度
    :param height: 视频高度
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        shape = slide.Shapes.AddMediaObject2(video_file_path, left, top, width, height)
        # 可以进一步设置视频的播放属性，例如自动播放
        # shape.MediaFormat.PlayOnEntry = True
        print(f"已在幻灯片中插入视频: {video_file_path}")
        return shape
    except Exception as e:
        print(f"插入视频失败: {e}")
        return None

# 29. 复制幻灯片
def copy_slide(presentation, source_slide_index, destination_index):
    """
    复制指定索引的幻灯片到新位置。
    :param presentation: 演示文稿对象
    :param source_slide_index: 源幻灯片的索引 (从 1 开始)
    :param destination_index: 目标位置的索引 (从 1 开始)
    """
    if not presentation:
        print("演示文稿对象无效。")
        return
    try:
        # 获取源幻灯片
        source_slide = presentation.Slides(source_slide_index)
        # 复制幻灯片
        source_slide.Copy()
        # 粘贴幻灯片到指定位置
        presentation.Slides.Paste(destination_index)
        print(f"已复制幻灯片 {source_slide_index} 到 {destination_index}。")
    except Exception as e:
        print(f"复制幻灯片失败: {e}")

# 30. 移动幻灯片
def move_slide(presentation, source_index, destination_index):
    """
    移动幻灯片到新位置。
    :param presentation: 演示文稿对象
    :param source_index: 源幻灯片的索引 (从 1 开始)
    :param destination_index: 目标位置的索引 (从 1 开始)
    """
    if not presentation:
        print("演示文稿对象无效。")
        return
    try:
        # 移动幻灯片
        presentation.Slides.Move(source_index, destination_index)
        print(f"已将幻灯片 {source_index} 移动到 {destination_index}。")
    except Exception as e:
        print(f"移动幻灯片失败: {e}")

# 31. 获取幻灯片中所有形状的名称
def get_all_shape_names_on_slide(slide):
    """
    获取幻灯片中所有形状的名称。
    :param slide: 幻灯片对象
    :return: 形状名称列表
    """
    if not slide:
        print("幻灯片对象无效。")
        return []
    shape_names = []
    try:
        for shape in slide.Shapes:
            shape_names.append(shape.Name)
            print(f"形状名称: {shape.Name}")
        return shape_names
    except Exception as e:
        print(f"获取形状名称失败: {e}")
        return []

# 32. 改变形状的位置和大小
def set_shape_position_and_size(shape, left, top, width, height):
    """
    改变形状的位置和大小。
    :param shape: 形状对象
    :param left: 左上角的 X 坐标
    :param top: 左上角的 Y 坐标
    :param width: 宽度
    :param height: 高度
    """
    if not shape:
        print("形状对象无效。")
        return
    try:
        shape.Left = left
        shape.Top = top
        shape.Width = width
        shape.Height = height
        print(f"形状 '{shape.Name}' 位置和大小已调整: Left={left}, Top={top}, Width={width}, Height={height}")
    except Exception as e:
        print(f"设置形状位置和大小失败: {e}")

# 33. 设置形状的填充颜色
def set_shape_fill_color(shape, r, g, b):
    """
    设置形状的填充颜色。
    :param shape: 形状对象
    :param r: 红色分量 (0-255)
    :param g: 绿色分量 (0-255)
    :param b: 蓝色分量 (0-255)
    """
    if not shape:
        print("形状对象无效。")
        return
    try:
        fill = shape.Fill
        fill.ForeColor.RGB = r + (g << 8) + (b << 16)
        fill.Visible = True # 确保填充可见
        print(f"形状 '{shape.Name}' 填充颜色已设置为 RGB({r}, {g}, {b})。")
    except Exception as e:
        print(f"设置形状填充颜色失败: {e}")

# 34. 设置形状的边框颜色和粗细
def set_shape_line_format(shape, r, g, b, weight=1):
    """
    设置形状的边框颜色和粗细。
    :param shape: 形状对象
    :param r: 红色分量 (0-255)
    :param g: 绿色分量 (0-255)
    :param b: 蓝色分量 (0-255)
    :param weight: 边框粗细 (磅)
    """
    if not shape:
        print("形状对象无效。")
        return
    try:
        line = shape.Line
        line.ForeColor.RGB = r + (g << 8) + (b << 16)
        line.Weight = weight
        line.Visible = True # 确保边框可见
        print(f"形状 '{shape.Name}' 边框颜色已设置为 RGB({r}, {g}, {b}), 粗细为 {weight}。")
    except Exception as e:
        print(f"设置形状边框失败: {e}")

# 35. 将形状置于顶层或底层
def bring_shape_to_front_or_back(shape, to_front=True):
    """
    将形状置于顶层或底层。
    :param shape: 形状对象
    :param to_front: True 表示置于顶层, False 表示置于底层
    """
    if not shape:
        print("形状对象无效。")
        return
    try:
        if to_front:
            shape.ZOrder(0) # msoBringToFront
            print(f"形状 '{shape.Name}' 已置于顶层。")
        else:
            shape.ZOrder(4) # msoSendToBack
            print(f"形状 '{shape.Name}' 已置于底层。")
    except Exception as e:
        print(f"设置形状层级失败: {e}")

# 36. 添加一个矩形形状
def add_rectangle_to_slide(slide, left, top, width, height):
    """
    在幻灯片中添加一个矩形形状。
    :param slide: 幻灯片对象
    :param left: 矩形左上角的 X 坐标
    :param top: 矩形左上角的 Y 坐标
    :param width: 矩形宽度
    :param height: 矩形高度
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 添加一个矩形 (MsoShapeType.msoShapeRectangle = 1)
        shape = slide.Shapes.AddShape(1, left, top, width, height)
        print(f"已在幻灯片中添加一个矩形。")
        return shape
    except Exception as e:
        print(f"添加矩形失败: {e}")
        return None

# 37. 添加一个圆形/椭圆形形状
def add_oval_to_slide(slide, left, top, width, height):
    """
    在幻灯片中添加一个圆形/椭圆形形状。
    :param slide: 幻灯片对象
    :param left: 椭圆形左上角的 X 坐标
    :param top: 椭圆形左上角的 Y 坐标
    :param width: 椭圆形宽度
    :param height: 椭圆形高度
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 添加一个椭圆形 (MsoShapeType.msoShapeOval = 9)
        shape = slide.Shapes.AddShape(9, left, top, width, height)
        print(f"已在幻灯片中添加一个椭圆形。")
        return shape
    except Exception as e:
        print(f"添加椭圆形失败: {e}")
        return None

# 38. 添加一个箭头形状
def add_arrow_to_slide(slide, begin_x, begin_y, end_x, end_y):
    """
    在幻灯片中添加一个箭头形状。
    :param slide: 幻灯片对象
    :param begin_x: 箭头的起始 X 坐标
    :param begin_y: 箭头的起始 Y 坐标
    :param end_x: 箭头的结束 X 坐标
    :param end_y: 箭头的结束 Y 坐标
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 添加一条直线 (MsoShapeType.msoLine = 90)
        shape = slide.Shapes.AddConnector(1, begin_x, begin_y, end_x, end_y) # 1 为 msoConnectorStraight
        # 设置箭头类型
        line = shape.Line
        line.EndArrowheadStyle = 3 # msoArrowheadTriangle (三角形箭头)
        line.EndArrowheadLength = 3 # msoArrowheadLengthMedium
        line.EndArrowheadWidth = 3 # msoArrowheadWidthMedium
        print(f"已在幻灯片中添加一个箭头。")
        return shape
    except Exception as e:
        print(f"添加箭头失败: {e}")
        return None

# 39. 获取幻灯片中所有形状的类型
def get_all_shape_types_on_slide(slide):
    """
    获取幻灯片中所有形状的类型。
    :param slide: 幻灯片对象
    :return: 形状类型列表
    """
    if not slide:
        print("幻灯片对象无效。")
        return []
    shape_types = []
    try:
        for shape in slide.Shapes:
            shape_types.append(shape.Type)
            # 常见的类型值:
            # 1 (msoShapeRectangle)
            # 9 (msoShapeOval)
            # 17 (msoTextBox)
            # 13 (msoPicture)
            # 14 (msoPlaceholder)
            # 90 (msoLine)
            # 16 (msoTable)
            # 17 (msoChart)
            print(f"形状名称: {shape.Name}, 类型: {shape.Type}")
        return shape_types
    except Exception as e:
        print(f"获取形状类型失败: {e}")
        return []

# 40. 将幻灯片中的文本框文字替换
def replace_text_in_text_boxes(slide, old_text, new_text):
    """
    将幻灯片中所有文本框内的指定文字进行替换。
    :param slide: 幻灯片对象
    :param old_text: 要被替换的旧文本
    :param new_text: 替换成的新文本
    """
    if not slide:
        print("幻灯片对象无效。")
        return
    try:
        for shape in slide.Shapes:
            if shape.HasTextFrame and shape.TextFrame.HasText:
                text_range = shape.TextFrame.TextRange
                if old_text in text_range.Text:
                    text_range.Text = text_range.Text.replace(old_text, new_text)
                    print(f"在形状 '{shape.Name}' 中替换了文本: '{old_text}' -> '{new_text}'")
    except Exception as e:
        print(f"替换文本失败: {e}")

# 41. 获取演示文稿中所有幻灯片的数量
def get_presentation_slide_count(presentation):
    """
    获取演示文稿中所有幻灯片的数量。
    :param presentation: 演示文稿对象
    """
    if not presentation:
        print("演示文稿对象无效。")
        return 0
    try:
        count = presentation.Slides.Count
        print(f"演示文稿中共有 {count} 张幻灯片。")
        return count
    except Exception as e:
        print(f"获取幻灯片数量失败: {e}")
        return 0

# 42. 设置演示文稿的作者信息
def set_presentation_author(presentation, author_name):
    """
    设置演示文稿的作者信息。
    :param presentation: 演示文稿对象
    :param author_name: 作者姓名
    """
    if not presentation:
        print("演示文稿对象无效。")
        return
    try:
        presentation.BuiltInDocumentProperties("Author").Value = author_name
        print(f"演示文稿作者已设置为: '{author_name}'")
    except Exception as e:
        print(f"设置演示文稿作者失败: {e}")

# 43. 获取演示文稿的作者信息
def get_presentation_author(presentation):
    """
    获取演示文稿的作者信息。
    :param presentation: 演示文稿对象
    :return: 作者姓名
    """
    if not presentation:
        print("演示文稿对象无效。")
        return ""
    try:
        author = presentation.BuiltInDocumentProperties("Author").Value
        print(f"演示文稿作者是: '{author}'")
        return author
    except Exception as e:
        print(f"获取演示文稿作者失败: {e}")
        return ""

# 44. 复制幻灯片中的形状
def copy_shape_on_slide(slide, shape_name):
    """
    复制幻灯片中的指定形状。
    :param slide: 幻灯片对象
    :param shape_name: 要复制的形状名称
    """
    if not slide:
        print("幻灯片对象无效。")
        return
    try:
        shape_to_copy = find_shape_by_name(slide, shape_name)
        if shape_to_copy:
            shape_to_copy.Copy()
            print(f"已复制形状 '{shape_name}'。")
        else:
            print(f"未找到要复制的形状 '{shape_name}'。")
    except Exception as e:
        print(f"复制形状失败: {e}")

# 45. 粘贴形状到幻灯片
def paste_shape_to_slide(slide, left, top):
    """
    粘贴形状到幻灯片。
    :param slide: 幻灯片对象
    :param left: 粘贴位置的 X 坐标
    :param top: 粘贴位置的 Y 坐标
    """
    if not slide:
        print("幻灯片对象无效。")
        return None
    try:
        # 粘贴形状，并获取新粘贴的形状
        pasted_shape = slide.Shapes.Paste()
        # 设置粘贴位置
        pasted_shape.Left = left
        pasted_shape.Top = top
        print(f"形状已粘贴到幻灯片，位置: Left={left}, Top={top}。")
        return pasted_shape
    except Exception as e:
        print(f"粘贴形状失败: {e}")
        return None

# 46. 设置幻灯片视图模式
def set_slide_view_mode(ppt_app, view_type=1):
    """
    设置 PowerPoint 应用程序的幻灯片视图模式。
    :param ppt_app: PowerPoint 应用程序对象
    :param view_type: 视图类型 (例如: 1 为普通视图，更多类型详见 MSO.PpViewType 枚举)
                      ppViewNormal = 1
                      ppViewSlideSorter = 2
                      ppViewNotesPage = 3
                      ppViewOutline = 4
                      ppViewSlide = 5
                      ppViewHandoutMaster = 6
                      ppViewNotesMaster = 7
                      ppViewOutlineBrowse = 8
                      ppViewMasterThumbnails = 9
                      ppViewPrintPreview = 10
                      ppViewNormalView = 11 (Office 2013 及更高版本)
    """
    if not ppt_app:
        print("PowerPoint 应用程序未启动。")
        return
    try:
        ppt_app.ActiveWindow.View.Type = view_type
        print(f"PowerPoint 视图模式已设置为: {view_type}")
    except Exception as e:
        print(f"设置视图模式失败: {e}")

# 47. 隐藏或显示幻灯片
def hide_or_show_slide(slide, hide=True):
    """
    隐藏或显示幻灯片。
    :param slide: 幻灯片对象
    :param hide: True 表示隐藏, False 表示显示
    """
    if not slide:
        print("幻灯片对象无效。")
        return
    try:
        slide.SlideShowTransition.Hidden = hide
        status = "隐藏" if hide else "显示"
        print(f"幻灯片 '{slide.SlideIndex}' 已设置为 {status}。")
    except Exception as e:
        print(f"隐藏/显示幻灯片失败: {e}")

# 48. 添加超链接到文本框
def add_hyperlink_to_text_box(text_box_shape, address, text_to_display=None):
    """
    给文本框添加超链接。
    :param text_box_shape: 文本框形状对象
    :param address: 超链接地址 (例如: "http://www.google.com" 或 "C:\\temp\\document.pdf")
    :param text_to_display: 要显示的文本 (可选, 如果不提供则使用文本框现有文本)
    """
    if not text_box_shape or not hasattr(text_box_shape, 'TextFrame'):
        print("形状对象无效或不是文本框。")
        return
    try:
        text_range = text_box_shape.TextFrame.TextRange
        if text_to_display:
            text_range.Text = text_to_display
        
        # 添加超链接
        text_range.ActionSettings[1].Hyperlink.Address = address # 1 for msoActionClick
        text_range.ActionSettings[1].Action = 1 # msoActionHyperlink
        
        print(f"已为文本框 '{text_box_shape.Name}' 添加超链接: {address}")
    except Exception as e:
        print(f"添加超链接失败: {e}")

# 49. 在幻灯片中添加备注
def add_notes_to_slide(slide, notes_text):
    """
    在幻灯片中添加备注。
    :param slide: 幻灯片对象
    :param notes_text: 备注内容
    """
    if not slide:
        print("幻灯片对象无效。")
        return
    try:
        # 获取备注页面
        notes_page = slide.NotesPage
        # 获取备注文本框 (通常是 NotesPage 中的一个文本框)
        for shape in notes_page.Shapes:
            if shape.HasTextFrame and shape.TextFrame.HasText:
                # 假设第一个文本框是备注文本框
                shape.TextFrame.TextRange.Text = notes_text
                print(f"已为幻灯片 {slide.SlideIndex} 添加备注。")
                return
        print(f"未找到幻灯片 {slide.SlideIndex} 的备注文本框。")
    except Exception as e:
        print(f"添加备注失败: {e}")

# 50. 检查演示文稿是否已保存
def check_presentation_saved_status(presentation):
    """
    检查演示文稿是否已保存。
    :param presentation: 演示文稿对象
    :return: True 如果已保存, False 如果未保存
    """
    if not presentation:
        print("演示文稿对象无效。")
        return False
    try:
        saved = presentation.Saved
        if saved:
            print("演示文稿已保存。")
        else:
            print("演示文稿未保存 (有未保存的更改)。")
        return saved
    except Exception as e:
        print(f"检查保存状态失败: {e}")
        return False


# --- 使用示例 ---
if __name__ == "__main__":
    ppt_app = None
    presentation = None
    try:
        # 1. 启动 PowerPoint 应用程序
        ppt_app = create_ppt_application()
        if not ppt_app:
            exit()

        # 2. 创建一个新的演示文稿
        presentation = create_new_presentation(ppt_app)
        if not presentation:
            quit_ppt_application(ppt_app)
            exit()

        # 8. 添加一张新的幻灯片 (标题幻灯片)
        slide1 = add_new_slide(presentation, 1)
        if slide1:
            # 18. 修改幻灯片标题
            set_slide_title(slide1, "Pywin32 操作 PPT 示例")
            # 11. 在幻灯片中添加文本框
            subtitle_shape = add_text_box_to_slide(slide1, "用 Python 自动化您的演示文稿！", 100, 200, 600, 50)
            if subtitle_shape:
                # 12. 设置文本框字体样式
                set_text_box_font(subtitle_shape, font_name="Arial", font_size=36, bold=True, italic=True)

        # 8. 添加一张新的幻灯片 (标题和内容幻灯片)
        slide2 = add_new_slide(presentation, 2)
        if slide2:
            set_slide_title(slide2, "插入图片和形状")
            # 11. 添加内容文本框
            content_shape = add_text_box_to_slide(slide2, "这张幻灯片演示了如何插入图片和自定义形状。", 50, 100, 600, 50)
            # 13. 在幻灯片中插入图片
            # 假设你有一个图片文件在当前目录下
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            picture_path = os.path.join(current_dir, "example_image.png") # 请确保存在此图片文件
            # 为了演示，创建一个虚拟图片文件
            from PIL import Image
            img = Image.new('RGB', (60, 30), color = 'red')
            img.save(picture_path)

            if os.path.exists(picture_path):
                insert_picture_to_slide(slide2, picture_path, 50, 150, 300, 200)
            else:
                print(f"图片文件 {picture_path} 不存在，跳过插入图片。")

            # 36. 添加一个矩形形状
            rect_shape = add_rectangle_to_slide(slide2, 400, 150, 150, 100)
            if rect_shape:
                # 33. 设置形状的填充颜色 (蓝色)
                set_shape_fill_color(rect_shape, 0, 0, 255)
                # 34. 设置形状的边框颜色和粗细 (红色边框，粗细 3 磅)
                set_shape_line_format(rect_shape, 255, 0, 0, 3)

            # 37. 添加一个圆形/椭圆形形状
            oval_shape = add_oval_to_slide(slide2, 450, 300, 100, 100)
            if oval_shape:
                # 33. 设置形状的填充颜色 (绿色)
                set_shape_fill_color(oval_shape, 0, 255, 0)
                # 35. 将形状置于顶层
                bring_shape_to_front_or_back(oval_shape, True)

            # 38. 添加一个箭头形状
            arrow_shape = add_arrow_to_slide(slide2, 300, 250, 450, 300)
            if arrow_shape:
                # 34. 设置箭头颜色 (黑色)
                set_shape_line_format(arrow_shape, 0, 0, 0, 2)


        # 8. 添加一张新的幻灯片 (空白幻灯片)
        slide3 = add_new_slide(presentation, 12) # ppLayoutBlank
        if slide3:
            set_slide_title(slide3, "表格和图表示例") # 空白幻灯片可能没有标题占位符
            # 11. 手动添加一个标题文本框
            title_shape_3 = add_text_box_to_slide(slide3, "表格和图表示例", 50, 50, 600, 50)
            if title_shape_3:
                set_text_box_font(title_shape_3, font_size=40, bold=True)


            # 19. 插入表格到幻灯片
            table_shape = insert_table_to_slide(slide3, 3, 3, 50, 150, 300, 150)
            if table_shape:
                # 20. 设置表格单元格文本
                set_table_cell_text(table_shape, 1, 1, "姓名")
                set_table_cell_text(table_shape, 1, 2, "年龄")
                set_table_cell_text(table_shape, 1, 3, "城市")
                set_table_cell_text(table_shape, 2, 1, "张三")
                set_table_cell_text(table_shape, 2, 2, "30")
                set_table_cell_text(table_shape, 2, 3, "北京")
                set_table_cell_text(table_shape, 3, 1, "李四")
                set_table_cell_text(table_shape, 3, 2, "25")
                set_table_cell_text(table_shape, 3, 3, "上海")

            # 21. 插入图表到幻灯片 (簇状柱形图)
            # 使用 wc.constants 获取 Office 常量
            chart_shape = insert_chart_to_slide(slide3, wc.constants.xlColumnClustered, 400, 150, 400, 300)
            if chart_shape:
                # 22. 更新图表数据
                update_chart_data(chart_shape, 1, [100, 200, 150, 250])
                # 23. 修改图表标题
                set_chart_title(chart_shape, "销售额图表")

        # 8. 添加一张新的幻灯片 (标题和内容)
        slide4 = add_new_slide(presentation, 2)
        if slide4:
            set_slide_title(slide4, "高级操作")
            # 25. 设置幻灯片切换效果 (淡入淡出，中速)
            set_slide_transition(slide4, 3, 2) # ppEffectFade, ppTransitionMedium

            # 40. 将幻灯片中的文本框文字替换
            # 先添加一个文本框
            replace_text_box = add_text_box_to_slide(slide4, "原始文本包含'旧'文字。", 50, 150, 400, 50)
            if replace_text_box:
                replace_text_in_text_boxes(slide4, "旧", "新")

            # 48. 添加超链接到文本框
            hyperlink_text_box = add_text_box_to_slide(slide4, "点击访问 Google", 50, 250, 200, 30)
            if hyperlink_text_box:
                add_hyperlink_to_text_box(hyperlink_text_box, "http://www.google.com")

            # 49. 在幻灯片中添加备注
            add_notes_to_slide(slide4, "这是第四张幻灯片的备注，用于演示添加备注功能。")

        # 29. 复制幻灯片 (复制第一张到末尾)
        copy_slide(presentation, 1, presentation.Slides.Count + 1)
        print(f"当前幻灯片总数: {get_presentation_slide_count(presentation)}")

        # 30. 移动幻灯片 (将复制的幻灯片移动到第二张)
        move_slide(presentation, presentation.Slides.Count, 2)
        print(f"移动幻灯片后，当前幻灯片总数: {get_presentation_slide_count(presentation)}")

        # 7. 获取当前活动演示文稿
        get_active_presentation(ppt_app)

        # 42. 设置演示文稿的作者信息
        set_presentation_author(presentation, "Pywin32 自动化演示")
        # 43. 获取演示文稿的作者信息
        get_presentation_author(presentation)

        # 46. 设置幻灯片视图模式
        set_slide_view_mode(ppt_app, 2) # ppViewSlideSorter

        # 47. 隐藏幻灯片 (隐藏第三张)
        hide_or_show_slide(presentation.Slides(3), True)

        # 41. 获取演示文稿中所有幻灯片的数量
        get_presentation_slide_count(presentation)

        # 4. 保存演示文稿
        save_path = os.path.join(current_dir, "MyAutomatedPresentation.pptx")
        save_presentation(presentation, save_path)

        # 50. 检查演示文稿是否已保存
        check_presentation_saved_status(presentation)

        # 26. 运行幻灯片放映 (可选，会启动放映模式)
        # run_slideshow(presentation)

        # 稍作等待，以便观察效果
        # import time
        # time.sleep(5)

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 5. 关闭演示文稿
        if presentation:
            close_presentation(presentation)
        # 6. 退出 PowerPoint 应用程序
        if ppt_app:
            quit_ppt_application(ppt_app)