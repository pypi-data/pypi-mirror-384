import selenium.webdriver
import time
import os
import sys
import platform
import datetime

def executeSeleniumAutomation(
    chromedriver_path,
    chrome_browser_path,
    username,
    password,
    login_url,
    wait_time_after_navigation=3,
    wait_time_after_input=1,
    wait_time_after_checkbox=0.5,
    wait_time_after_click=1,
    wait_time_for_login_completion=5,
    observe_time_before_closing=15
):
    """
    执行完整的 Selenium 自动化流程，包括：
    1. 获取并记录 Python 环境信息到文件。
    2. 初始化 WebDriver 并导航到登录页面。
    3. 输入用户名和密码，勾选相关复选框。
    4. 点击登录按钮并等待登录完成。
    5. 保持浏览器打开一段时间供观察，最后关闭浏览器。

    参数:
        chromedriver_path (str): ChromeDriver 可执行文件的路径。
        chrome_browser_path (str): Chrome 浏览器可执行文件的路径。
        username (str): 登录的用户名。
        password (str): 登录的密码。
        login_url (str): 登录页面的 URL。
        wait_time_after_navigation (int/float): 导航到登录页面后等待的时间。
        wait_time_after_input (int/float): 输入用户名/密码后等待的时间。
        wait_time_after_checkbox (int/float): 点击勾选框后等待的时间。
        wait_time_after_click (int/float): 点击登录按钮后等待的时间。
        wait_time_for_login_completion (int/float): 等待登录重定向/响应的时间。
        observe_time_before_closing (int/float): 在关闭浏览器前保持打开的观察时间。
    """
    # --- 获取并打印 Python 环境信息，并写入文件 ---
    # 获取当前时间并格式化为时间戳
    current_time = datetime.datetime.now()
    timestamp_str = current_time.strftime("%Y%m%d_%H%M%S")
    # 生成文件名称，包含时间戳
    file_name = f"environment_info_{timestamp_str}.txt"
    
    # 准备要写入文件和打印到控制台的内容列表
    output_lines = []
    output_lines.append(f"--- Python 环境信息 ---")
    output_lines.append(f"记录时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}") # 写入完整时间
    output_lines.append(f"Python 环境路径: {sys.executable}")
    output_lines.append(f"Python 版本: {sys.version}")

    try:
        selenium_version = selenium.webdriver.__version__
        output_lines.append(f"Selenium WebDriver 版本: {selenium_version}")
    except AttributeError:
        output_lines.append("无法获取 Selenium WebDriver 版本。请确保 'selenium.webdriver' 已正确安装。")

    output_lines.append(f"平台: {platform.platform()}")
    output_lines.append(f"操作系统名称: {os.name}")
    output_lines.append(f"系统架构: {platform.machine()}")
    output_lines.append(f"处理器信息: {platform.processor()}")
    output_lines.append("\n此脚本已在上述 Python 环境下成功运行。")
    output_lines.append("-" * 30) # 添加分隔线

    # 将信息打印到控制台
    for line in output_lines:
        print(line)

    # 将信息写入文件
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")
        print(f"\n环境信息已成功写入文件: {file_name}")
    except IOError as e:
        print(f"写入文件失败: {e}")

    # --- Selenium 自动化部分 ---
    driver = None  # 初始化 driver 变量为 None
    try:
        print(f"正在使用 ChromeDriver 初始化 Chrome WebDriver，路径为：{chromedriver_path}")
        print(f"正在尝试启动 Chrome 浏览器，路径为：{chrome_browser_path}")
        
        # 设置 WebDriver 服务
        service = selenium.webdriver.chrome.service.Service(executable_path=chromedriver_path)
        chrome_options = selenium.webdriver.chrome.options.Options()
        # 添加启动参数，使浏览器最大化显示
        chrome_options.add_argument("--start-maximized")
        # 指定 Chrome 浏览器可执行文件的路径
        chrome_options.binary_location = chrome_browser_path

        # 初始化 Chrome WebDriver 实例
        driver = selenium.webdriver.Chrome(service=service, options=chrome_options)
        print("WebDriver 初始化成功！")

        # --- 导航到登录页面 ---
        print(f"正在导航到登录页面：{login_url}")
        driver.get(login_url)
        time.sleep(wait_time_after_navigation) # 给页面更多时间加载

        # --- 查找用户名和密码输入框并输入凭据 ---
        print("正在输入用户名和密码...")
        username_field = driver.find_element("id", "password_name")
        username_field.send_keys(username)

        password_field = driver.find_element("id", "password_pwd")
        password_field.send_keys(password)

        time.sleep(wait_time_after_input) # 短暂等待，等待输入完成

        # --- 勾选“记住登录状态”框 ---
        print("正在勾选‘记住登录状态’...")
        remember_checkbox = driver.find_element("id", "rememberPwd")
        # 检查是否未被勾选，如果没有则点击
        if not remember_checkbox.is_selected():
            remember_checkbox.click()
        else:
            print("‘记住登录状态’已是勾选状态。")

        time.sleep(wait_time_after_checkbox) # 短暂等待

        # --- 勾选“我已阅读并同意免责声明条款”框 ---
        print("正在勾选‘我已阅读并同意免责声明条款’...")
        disclaimer_checkbox = driver.find_element("id", "password_disclaimer")
        # 检查是否未被勾选，如果没有则点击
        if not disclaimer_checkbox.is_selected():
            disclaimer_checkbox.click()
        else:
            print("‘我已阅读并同意免责声明条款’已是勾选状态。")

        time.sleep(wait_time_after_click) # 短暂等待，确保勾选操作完成

        # --- 查找并点击登录按钮 ---
        print("正在点击登录按钮...")
        login_button = driver.find_element("id", "password_submitBtn")
        login_button.click()

        # --- 等待登录完成并验证 ---
        print("等待登录完成...")
        time.sleep(wait_time_for_login_completion) # 给足够的时间让登录请求处理和页面跳转

        current_page_url = driver.current_url
        print("当前页面标题:", driver.title)
        print("当前页面 URL:", current_page_url)

        # 改进的登录成功判断逻辑：如果URL不再是原始登录页面，则认为成功跳转
        if current_page_url != login_url:
            print("登录成功！页面已跳转。")
        else:
            print("登录可能失败：页面未跳转。")
            print("请手动检查浏览器页面，看是否有其他提示或错误信息。")

        # --- 保持浏览器打开一段时间以便观察 ---
        print(f"保持浏览器打开 {observe_time_before_closing} 秒钟以便观察最终状态...")
        time.sleep(observe_time_before_closing)

    except Exception as e:
        print(f"发生错误：{e}")

    finally:
        # 确保在任何情况下都关闭浏览器
        if 'driver' in locals() and driver:
            print("关闭浏览器。")
            driver.quit()
            print("浏览器已成功关闭。")

# --- 调用函数示例 ---
if __name__ == "__main__":
    # --- 配置项 ---
    # ChromeDriver 可执行文件的路径
    CHROMEDRIVER_PATH = r"C:\Users\Public\Chrome\chromedriver.exe"
    # Chrome 浏览器可执行文件的路径
    CHROME_BROWSER_PATH = r"C:\Users\Public\Chrome\Application\chrome.exe"

    # --- 账号凭据（⚠️ 不推荐直接硬编码，请考虑更安全的加载方式！） ---
    USERNAME = "frank_yu"
    PASSWORD = "a@123456"

    # --- 登录页面的 URL ---
    LOGIN_URL = "http://ac.prime3c.com/ac_portal/disclaimer/pc.html?template=disclaimer&tabs=pwd&vlanid=0&_ID_=0&switch_url=&url=http://ac.prime3c.com/homepage/index.html&controller_type=&mac=04-d9-c8-bd-58-48"

    # 调用主自动化函数，传入所有配置参数
    executeSeleniumAutomation(
        chromedriver_path=CHROMEDRIVER_PATH,
        chrome_browser_path=CHROME_BROWSER_PATH,
        username=USERNAME,
        password=PASSWORD,
        login_url=LOGIN_URL
    )