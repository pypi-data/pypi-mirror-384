"""
跨平台系统音量控制工具(交互式环境友好版)

功能：
- 自动检测是否在交互式环境中运行
- Windows: 使用pycaw库控制音量
- macOS: 使用osascript调用AppleScript控制音量
- Linux: 使用alsamixer/amixer控制音量(PulseAudio/ALSA)
- 提供统一的错误处理和安装指导
"""

import sys
import platform
import subprocess
from typing import Optional, Tuple

# 检测是否在交互式环境中运行(如Jupyter/IPython)
IS_INTERACTIVE = hasattr(sys, 'ps1') or bool(getattr(sys, 'base_prefix', None))

# 全局配置
SUPPORTED_PLATFORMS = ['Windows', 'Darwin', 'Linux']
CURRENT_PLATFORM = platform.system()

class VolumeControlError(Exception):
    """自定义音量控制异常基类"""
    pass

class UnsupportedPlatformError(VolumeControlError):
    """不支持的平台异常"""
    pass

class InvalidVolumeLevelError(VolumeControlError):
    """无效的音量级别异常"""
    pass

class VolumeControl:
    def __init__(self, default_volume: float = 0.5):
        """
        初始化音量控制器
        
        Args:
            default_volume: 默认音量级别(0.0-1.0), 在未设置音量时作为默认值
        """
        self.default_volume = default_volume
        self.initialized = False
        self.platform_specific_init()
    
    def platform_specific_init(self):
        """平台特定的初始化"""
        try:
            if CURRENT_PLATFORM == 'Windows':
                self.init_windows()
            elif CURRENT_PLATFORM == 'Darwin':
                self.init_macos()
            elif CURRENT_PLATFORM == 'Linux':
                self.init_linux()
            else:
                raise UnsupportedPlatformError(f"不支持的平台: {CURRENT_PLATFORM}")
            
            self.initialized = True
        except Exception as e:
            print(f"初始化失败: {str(e)}", file=sys.stderr)
            self.initialized = False
    
    def init_windows(self):
        """Windows平台初始化"""
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
        except ImportError:
            raise ImportError(
                "缺少pycaw库。请使用以下命令安装:\n"
                "pip install pycaw\n"
                "或访问 https://github.com/AndreMiras/pycaw")
        except Exception as e:
            raise VolumeControlError(f"Windows音频接口初始化失败: {str(e)}")
    
    def init_macos(self):
        """macOS平台初始化"""
        try:
            subprocess.run(['which', 'osascript'], check=True, 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise VolumeControlError("macOS: 未找到osascript命令")
    
    def init_linux(self):
        """Linux平台初始化"""
        try:
            subprocess.run(['which', 'amixer'], check=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            raise VolumeControlError(
                "Linux: 未找到amixer命令。请安装alsa-utils:\n"
                "sudo apt-get install alsa-utils  # Debian/Ubuntu\n"
                "sudo yum install alsa-utils      # CentOS/RHEL")
    
    def set_volume(self, volume_level: Optional[float] = None) -> Tuple[bool, float]:
        """
        设置系统主音量
        
        Args:
            volume_level: 音量级别(0.0-1.0), 如果未提供将使用默认值
        
        Returns:
            Tuple[bool, float]: 操作是否成功及设置的音量级别
            
        Raises:
            VolumeControlError: 音量控制失败时抛出
            InvalidVolumeLevelError: 无效音量级别时抛出
        """
        if not self.initialized:
            raise VolumeControlError("音量控制器未正确初始化")
        
        volume_level = volume_level if volume_level is not None else self.default_volume
        
        if not 0.0 <= volume_level <= 1.0:
            raise InvalidVolumeLevelError("音量级别必须在0.0到1.0之间")
        
        try:
            if CURRENT_PLATFORM == 'Windows':
                self._set_volume_windows(volume_level)
            elif CURRENT_PLATFORM == 'Darwin':
                self._set_volume_macos(volume_level)
            elif CURRENT_PLATFORM == 'Linux':
                self._set_volume_linux(volume_level)
            return True, volume_level
        except Exception as e:
            raise VolumeControlError(f"设置音量失败: {str(e)}")
    
    def _set_volume_windows(self, volume_level: float):
        """Windows平台音量设置"""
        self.volume_interface.SetMasterVolumeLevelScalar(volume_level, None)
    
    def _set_volume_macos(self, volume_level: float):
        """macOS平台音量设置"""
        volume_percent = int(volume_level * 100)
        script = f'set volume output volume {volume_percent}'
        
        try:
            subprocess.run(['osascript', '-e', script], check=True)
        except subprocess.CalledProcessError as e:
            raise VolumeControlError(f"AppleScript执行失败: {str(e)}")
    
    def _set_volume_linux(self, volume_level: float):
        """Linux平台音量设置"""
        volume_percent = int(volume_level * 100)
        
        try:
            subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{volume_percent}%'], 
                          check=True)
        except subprocess.CalledProcessError:
            subprocess.run(['amixer', 'sset', 'Master', f'{volume_percent}%'], 
                           check=True)
    
    def get_volume(self) -> Optional[float]:
        """
        获取当前系统音量
        
        Returns:
            float: 当前音量级别(0.0-1.0), 失败时返回None
        """
        if not self.initialized:
            print("音量控制器未正确初始化", file=sys.stderr)
            return None
        
        try:
            if CURRENT_PLATFORM == 'Windows':
                return self._get_volume_windows()
            elif CURRENT_PLATFORM == 'Darwin':
                return self._get_volume_macos()
            elif CURRENT_PLATFORM == 'Linux':
                return self._get_volume_linux()
        except Exception as e:
            print(f"获取音量失败: {str(e)}", file=sys.stderr)
            return None
    
    def _get_volume_windows(self) -> float:
        """Windows平台获取音量"""
        return self.volume_interface.GetMasterVolumeLevelScalar()
    
    def _get_volume_macos(self) -> float:
        """macOS平台获取音量"""
        script = 'get volume settings'
        result = subprocess.run(['osascript', '-e', script], 
                              check=True, capture_output=True, text=True)
        
        output = result.stdout.strip()
        volume_str = output.split(',')[0].split(':')[1]
        return float(volume_str) / 100
    
    def _get_volume_linux(self) -> float:
        """Linux平台获取音量"""
        try:
            result = subprocess.run(['amixer', '-D', 'pulse', 'get', 'Master'], 
                                  check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            result = subprocess.run(['amixer', 'get', 'Master'], 
                                   check=True, capture_output=True, text=True)
        
        lines = result.stdout.splitlines()
        for line in lines:
            if '[' in line and '%]' in line:
                percent_str = line.split('[')[1].split('%]')[0]
                try:
                    return float(percent_str) / 100
                except ValueError:
                    continue
        
        raise VolumeControlError("无法解析音量级别")

def print_usage():
    """打印使用说明"""
    print("""音量控制工具 - 使用说明

用法:
  python volume_control.py [volume_level]

参数:
  volume_level - 设置音量级别(0.0-1.0), 不提供参数则显示当前音量

示例:
  python volume_control.py 0.75   # 设置音量为75%
  python volume_control.py        # 显示当前音量
""")

def main():
    try:
        controller = VolumeControl(default_volume=0.5)
        
        # 在交互式环境中不处理命令行参数
        if not IS_INTERACTIVE and len(sys.argv) > 1:
            try:
                volume_level = float(sys.argv[1])
                success, level = controller.set_volume(volume_level)
                print(f"音量已设置为 {level*100:.0f}%")
            except ValueError:
                print("错误: 音量参数必须是数字", file=sys.stderr)
                print_usage()
                if not IS_INTERACTIVE:
                    sys.exit(1)
            except VolumeControlError as e:
                print(f"错误: {str(e)}", file=sys.stderr)
                if not IS_INTERACTIVE:
                    sys.exit(1)
        else:
            current_volume = controller.get_volume()
            if current_volume is not None:
                print(f"当前音量: {current_volume*100:.0f}%")
            else:
                print("无法获取当前音量", file=sys.stderr)
                if not IS_INTERACTIVE:
                    sys.exit(1)
    
    except UnsupportedPlatformError as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        print("目前支持以下平台:", ", ".join(SUPPORTED_PLATFORMS), file=sys.stderr)
        if not IS_INTERACTIVE:
            sys.exit(1)
    except Exception as e:
        print(f"发生未预期的错误: {str(e)}", file=sys.stderr)
        if not IS_INTERACTIVE:
            sys.exit(1)

if __name__ == "__main__":
    main()