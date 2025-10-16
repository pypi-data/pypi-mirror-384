"""
Font configuration for ydata-profiling visualizations
字体配置模块
"""
import warnings
import re
from typing import Any, Optional, Dict, Union
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


def configure_fonts_for_data(config, data: Any) -> bool:
    """根据配置和数据设置字体"""
    try:
        # 抑制字体警告
        if (hasattr(config.plot, 'font') and
                hasattr(config.plot.font, 'suppress_warnings') and
                config.plot.font.suppress_warnings):
            warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
            warnings.filterwarnings('ignore', message='.*missing from font.*')
            warnings.filterwarnings('ignore', message='.*Glyph.*missing from font.*')

        # 1. 检查自定义字体路径
        if (hasattr(config.plot, 'font') and
                hasattr(config.plot.font, 'custom_font_path') and
                config.plot.font.custom_font_path):
            custom_path = Path(config.plot.font.custom_font_path)
            if custom_path.exists():
                return _setup_custom_font(custom_path)

        # 2. 使用内置字体
        try:
            from ydata_profiling.assets.fonts.font_manager import setup_chinese_fonts
            return setup_chinese_fonts(True)
        except ImportError:
            pass

        # 3. 使用系统字体
        if (hasattr(config.plot, 'font') and
                hasattr(config.plot.font, 'fallback_to_system') and
                config.plot.font.fallback_to_system):
            return _setup_system_chinese_fonts()

        return False

    except Exception as e:
        warnings.warn(f"字体配置失败: {e}")
        return False


def _setup_custom_font(font_path: Path) -> bool:
    """设置自定义字体"""
    try:
        # 强制注册字体
        fm.fontManager.addfont(str(font_path))

        # 获取字体名称
        font_prop = fm.FontProperties(fname=str(font_path))
        font_name = font_prop.get_name()

        # 强制设置为第一优先级
        current_fonts = plt.rcParams['font.sans-serif'].copy()
        if font_name not in current_fonts:
            current_fonts.insert(0, font_name)
        else:
            current_fonts.remove(font_name)
            current_fonts.insert(0, font_name)

        plt.rcParams['font.sans-serif'] = current_fonts
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False

        # 清除字体缓存
        try:
            fm._rebuild()
        except:
            pass

        return True
    except Exception:
        return False


def _setup_system_chinese_fonts() -> bool:
    """设置系统中文字体"""
    try:
        chinese_fonts = [
            'SimHei', 'Microsoft YaHei', 'SimSun',  # Windows
            'PingFang SC', 'STHeiti', 'Heiti SC',  # macOS
            'WenQuanYi Micro Hei', 'Noto Sans CJK SC',  # Linux
            'DejaVu Sans'  # 备用
        ]

        # 强制设置字体优先级
        plt.rcParams['font.sans-serif'] = chinese_fonts
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False

        # 清除字体缓存
        try:
            fm._rebuild()
        except:
            pass

        return True
    except Exception:
        return False


def detect_chinese_content(data: Any) -> bool:
    """检测数据中是否包含中文字符"""
    if data is None:
        return False

    try:
        # 检查列名
        if hasattr(data, 'columns'):
            for col in data.columns:
                if re.search(r'[\u4e00-\u9fa5]', str(col)):
                    return True

        # 检查数据内容（采样检测，避免性能问题）
        if hasattr(data, 'head'):
            sample_data = data.head(10)  # 只检查前10行
            for col in sample_data.columns:
                if sample_data[col].dtype == 'object':  # 只检查字符串类型列
                    sample_values = sample_data[col].dropna().astype(str).head(5)
                    for value in sample_values:
                        if re.search(r'[\u4e00-\u9fa5]', str(value)):
                            return True

        return False

    except Exception:
        # 检测失败时保守返回False
        return False


def apply_font_config(config, **kwargs) -> Dict[str, Any]:
    """应用字体配置到matplotlib参数"""
    plot_params = {}

    if not hasattr(config, 'plot'):
        return plot_params

    font_config = config.plot.font if hasattr(config.plot, 'font') else {}

    # 自定义字体路径
    if font_config.get('custom_font_path'):
        plot_params['font_path'] = font_config['custom_font_path']

    # 中文字体支持
    elif font_config.get('chinese_support', False):
        try:
            from ydata_profiling.assets.fonts.font_manager import get_font_manager
            font_manager = get_font_manager()
            chinese_font = font_manager.get_chinese_font_path()
            if chinese_font:
                plot_params['font_path'] = str(chinese_font)
        except ImportError:
            pass

    return plot_params