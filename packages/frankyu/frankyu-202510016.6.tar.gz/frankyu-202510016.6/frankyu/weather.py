import requests  # 导入requests库，用于发送HTTP请求
import pandas as pd  # 导入pandas库，用于数据处理
import os  # 导入os库，用于操作系统接口
from datetime import datetime  # 导入datetime库中的datetime模块，用于处理日期和时间

def get_guangzhou_weather():
    """
    获取广州天气信息
    Get Guangzhou weather information
    
    返回:
    Return:
    dict: 广州的天气信息
          Guangzhou's weather information
    """
    city = "Guangzhou"  # 定义城市名称为广州
    url = f"http://wttr.in/{city}?format=j1"  # 构建请求URL

    response = requests.get(url)  # 发送GET请求
    if response.status_code == 200:  # 如果响应状态码为200（请求成功）
        weather_data = response.json()  # 将响应内容解析为JSON格式
        current_condition = weather_data["current_condition"][0]  # 获取当前天气状况
        return {
            "city": city,  # 返回城市名称
            "temperature": current_condition["temp_C"],  # 返回温度（摄氏度）
            "description": current_condition["weatherDesc"][0]["value"],  # 返回天气描述
            "humidity": current_condition["humidity"],  # 返回湿度
            "wind_speed": current_condition["windspeedKmph"]  # 返回风速（公里/小时）
        }
    else:  # 如果响应状态码不是200
        return {"error": "无法获取天气信息"}  # 返回错误信息

def write_to_excel(weather_info):
    """
    将天气信息写入Excel文件
    Write weather information to Excel file

    参数:
    Parameter:
    weather_info (dict): 天气信息
                         Weather information
    """
    if "error" in weather_info:  # 如果天气信息中包含错误信息
        print(weather_info["error"])  # 打印错误信息
        return

    # 创建DataFrame
    # Create DataFrame
    df = pd.DataFrame([weather_info])

    # 获取当前时间并格式化
    # Get the current time and format it
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_name = f"guangzhou_weather_{current_time}.xlsx"  # 构建包含时间戳的文件名

    # 写入Excel文件
    # Write to Excel file
    with pd.ExcelWriter(file_name, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Weather')  # 将DataFrame写入Excel文件

        # 获取工作表和工作簿对象
        # Get worksheet and workbook objects
        workbook  = writer.book
        worksheet = writer.sheets['Weather']

        # 设置列宽和格式
        # Set column width and format
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column))  # 计算列宽
            col_idx = df.columns.get_loc(column)  # 获取列索引
            worksheet.set_column(col_idx, col_idx, column_width + 5)  # 设置列宽，增加更多宽度

        # 设置单元格格式，包括标题行
        # Set cell format, including header row
        cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, cell_format)  # 设置标题行格式

        worksheet.set_column('A:Z', None, cell_format)  # 应用居中和自动换行格式
    
    print(f"天气信息已写入 {file_name}")  # 打印写入成功信息
    # Print success message

    # 打开Excel文件
    # Open Excel file
    #os.system(f"start EXCEL.EXE {file_name}")  # 在Windows系统上打开Excel文件
    # Open Excel file on Windows system

def weather_get_guangzhou_write_to_excel():    

#if __name__ == "__main__":
    weather_info = get_guangzhou_weather()  # 获取广州天气信息
    write_to_excel(weather_info)  # 将天气信息写入Excel文件