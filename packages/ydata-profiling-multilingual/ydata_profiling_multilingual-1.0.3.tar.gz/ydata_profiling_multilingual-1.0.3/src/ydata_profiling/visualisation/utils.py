"""Plotting utility functions."""
import base64
import uuid
import warnings
from io import BytesIO, StringIO
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import quote

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.artist import Artist

from ydata_profiling.config import Settings

# 添加字体配置导入
try:
    from ydata_profiling.visualisation.font_config import apply_font_config
except ImportError:
    def apply_font_config(config, **kwargs):
        return {}


def hex_to_rgb(hex: str) -> Tuple[float, ...]:
    hex = hex.lstrip("#")
    hlen = len(hex)
    return tuple(
        int(hex[i : i + hlen // 3], 16) / 255 for i in range(0, hlen, hlen // 3)
    )


def base64_image(image: bytes, mime_type: str) -> str:
    base64_data = base64.b64encode(image)
    image_data = quote(base64_data)
    return f"data:{mime_type};base64,{image_data}"


def _suppress_font_warnings():
    """抑制字体相关的警告"""
    warnings.filterwarnings('ignore',
                          message='.*missing from font.*',
                          category=UserWarning,
                          module='matplotlib.*')
    warnings.filterwarnings('ignore',
                          message='.*Glyph.*missing from font.*',
                          category=UserWarning,
                          module='matplotlib.*')


def _ensure_builtin_font_for_save(config: Settings) -> None:
    """确保保存时使用内置字体"""
    try:
        # 检查是否需要中文字体支持
        needs_chinese_support = False

        if hasattr(config.plot, 'font'):
            font_config = config.plot.font
            needs_chinese_support = (
                getattr(font_config, 'chinese_support', False) or
                getattr(font_config, 'auto_detect', False)
            )

        if (hasattr(config.i18n, 'auto_font_config') and
            config.i18n.auto_font_config and
            hasattr(config.i18n, 'locale') and
            config.i18n.locale in ['zh', 'zh-CN', 'zh-TW']):
            needs_chinese_support = True

        if needs_chinese_support:
            # 尝试应用内置字体到当前图表
            try:
                from ydata_profiling.assets.fonts.font_manager import get_font_manager

                font_manager = get_font_manager()
                builtin_prop = font_manager.get_builtin_font_prop()

                if builtin_prop:
                    # 直接设置matplotlib的全局字体
                    builtin_font_name = builtin_prop.get_name()
                    current_fonts = plt.rcParams['font.sans-serif'].copy()

                    # 确保内置字体在第一位
                    if builtin_font_name in current_fonts:
                        current_fonts.remove(builtin_font_name)
                    current_fonts.insert(0, builtin_font_name)

                    plt.rcParams['font.sans-serif'] = current_fonts
                    plt.rcParams['axes.unicode_minus'] = False

                    print(f"✅ 保存前应用内置字体: {builtin_font_name}")

            except Exception as e:
                print(f"⚠️ 应用内置字体失败: {e}")

                # 回退到系统字体
                chinese_fonts = [
                    'SimHei', 'Microsoft YaHei', 'PingFang SC', 'STHeiti',
                    'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans'
                ]

                plt.rcParams['font.sans-serif'] = chinese_fonts
                plt.rcParams['font.family'] = 'sans-serif'
                plt.rcParams['axes.unicode_minus'] = False

    except Exception:
        # 静默处理配置错误
        pass


def _post_process_svg(svg_content: str, config: Settings) -> str:
    """对SVG内容进行后处理，确保中文字符正确显示"""
    try:
        import re

        # 确保SVG包含正确的编码声明
        if 'encoding=' not in svg_content and '<?xml' in svg_content:
            svg_content = svg_content.replace(
                '<?xml version="1.0"?>',
                '<?xml version="1.0" encoding="UTF-8"?>'
            )

        # 替换SVG中的字体族声明
        if 'font-family' in svg_content:
            # 查找所有font-family声明并替换为中文字体
            chinese_font_family = "SimHei, Microsoft YaHei, PingFang SC, sans-serif"

            # 替换style属性中的font-family
            svg_content = re.sub(
                r'font-family:\s*[^;"\'>]+',
                f'font-family: {chinese_font_family}',
                svg_content
            )

            # 替换直接的font-family属性
            svg_content = re.sub(
                r'font-family="[^"]*"',
                f'font-family="{chinese_font_family}"',
                svg_content
            )

        return svg_content

    except Exception:
        return svg_content


def plot_360_n0sc0pe(
    config: Settings,
    image_format: Optional[str] = None,
    bbox_extra_artists: Optional[List[Artist]] = None,
    bbox_inches: Optional[str] = None,
) -> str:
    # 抑制字体警告
    _suppress_font_warnings()

    # 确保内置字体在保存前生效
    _ensure_builtin_font_for_save(config)

    if image_format is None:
        image_format = config.plot.image_format.value

    mime_types = {"png": "image/png", "svg": "image/svg+xml"}
    if image_format not in mime_types:
        raise ValueError('Can only 360 n0sc0pe "png" or "svg" format.')

    # 准备保存参数
    save_kwargs = {
        "format": image_format,
        "bbox_extra_artists": bbox_extra_artists,
        "bbox_inches": bbox_inches,
    }

    # 对SVG格式添加特殊设置
    if image_format == "svg":
        save_kwargs.update({
            "facecolor": 'white',
            "edgecolor": 'none',
        })

    if config.html.inline:
        if image_format == "svg":
            image_str = StringIO()

            # 🆕 使用上下文管理器确保字体设置在保存时生效
            with plt.rc_context({
                'font.sans-serif': plt.rcParams['font.sans-serif'],
                'font.family': 'sans-serif',
                'axes.unicode_minus': False
            }):
                plt.savefig(image_str, **save_kwargs)

            plt.close()
            result_string = image_str.getvalue()

            # 对SVG内容进行后处理
            result_string = _post_process_svg(result_string, config)
        else:
            image_bytes = BytesIO()
            save_kwargs["dpi"] = config.plot.dpi

            # 使用上下文管理器确保字体设置在保存时生效
            with plt.rc_context({
                'font.sans-serif': plt.rcParams['font.sans-serif'],
                'font.family': 'sans-serif',
                'axes.unicode_minus': False
            }):
                plt.savefig(image_bytes, **save_kwargs)

            plt.close()
            result_string = base64_image(
                image_bytes.getvalue(), mime_types[image_format]
            )
    else:
        if config.html.assets_path is None:
            raise ValueError("config.html.assets_path may not be none")

        file_path = Path(config.html.assets_path)
        suffix = f"{config.html.assets_prefix}/images/{uuid.uuid4().hex}.{image_format}"

        save_kwargs["fname"] = file_path / suffix
        if image_format == "png":
            save_kwargs["dpi"] = config.plot.dpi

        # 使用上下文管理器确保字体设置在保存时生效
        with plt.rc_context({
            'font.sans-serif': plt.rcParams['font.sans-serif'],
            'font.family': 'sans-serif',
            'axes.unicode_minus': False
        }):
            plt.savefig(**save_kwargs)

        plt.close()
        result_string = suffix

    return result_string