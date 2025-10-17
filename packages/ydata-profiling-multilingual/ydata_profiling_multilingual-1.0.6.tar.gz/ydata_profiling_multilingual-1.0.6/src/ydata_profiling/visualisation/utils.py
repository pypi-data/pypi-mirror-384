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


def _force_apply_chinese_font() -> Optional[str]:
    """强制应用中文字体到matplotlib"""
    try:
        from ydata_profiling.assets.fonts.font_manager import get_font_manager

        font_manager = get_font_manager()
        chinese_font_path = font_manager.get_chinese_font_path()

        if chinese_font_path and chinese_font_path.exists():
            # 强制重新注册字体
            fm.fontManager.addfont(str(chinese_font_path))

            # 获取字体名称
            font_prop = fm.FontProperties(fname=str(chinese_font_path))
            font_name = font_prop.get_name()

            # 强制设置为第一优先级
            plt.rcParams['font.sans-serif'] = [font_name, 'DejaVu Sans', 'Arial']
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['axes.unicode_minus'] = False

            return font_name

    except Exception:
        pass

    # 回退到系统字体
    chinese_fonts = [
        'SimHei', 'Microsoft YaHei', 'PingFang SC', 'STHeiti',
        'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'DejaVu Sans'
    ]
    plt.rcParams['font.sans-serif'] = chinese_fonts
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['axes.unicode_minus'] = False

    return chinese_fonts[0]


def _apply_font_to_current_figure(font_name: str):
    """将字体应用到当前图表的所有元素"""
    try:
        fig = plt.gcf()
        font_prop = fm.FontProperties(family=font_name)

        for ax in fig.get_axes():
            # 轴标签
            if ax.xaxis.label:
                ax.xaxis.label.set_fontproperties(font_prop)
            if ax.yaxis.label:
                ax.yaxis.label.set_fontproperties(font_prop)
            if ax.title:
                ax.title.set_fontproperties(font_prop)

            # 刻度标签
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(font_prop)

            # 图例
            legend = ax.get_legend()
            if legend:
                for text in legend.get_texts():
                    text.set_fontproperties(font_prop)

            # 所有文本对象
            for text in ax.texts:
                text.set_fontproperties(font_prop)

    except Exception as e:
        print(f"应用字体到图表失败: {e}")


def _post_process_svg(svg_content: str) -> str:
    """对SVG内容进行后处理，确保中文字符正确显示"""
    try:
        import re

        # 确保SVG包含正确的编码声明
        if 'encoding=' not in svg_content and '<?xml' in svg_content:
            svg_content = svg_content.replace(
                '<?xml version="1.0"?>',
                '<?xml version="1.0" encoding="UTF-8"?>'
            )

        # 替换SVG中的Arial字体为中文字体
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

    if image_format is None:
        image_format = config.plot.image_format.value

    mime_types = {"png": "image/png", "svg": "image/svg+xml"}
    if image_format not in mime_types:
        raise ValueError('Can only 360 n0sc0pe "png" or "svg" format.')

    # 强制应用中文字体
    font_name = _force_apply_chinese_font()

    # 应用字体到当前图表
    _apply_font_to_current_figure(font_name)

    # 准备保存参数
    save_kwargs = {
        "format": image_format,
        "bbox_extra_artists": bbox_extra_artists,
        "bbox_inches": bbox_inches,
    }

    if image_format == "svg":
        save_kwargs.update({
            "facecolor": 'white',
            "edgecolor": 'none',
        })

    if config.html.inline:
        if image_format == "svg":
            image_str = StringIO()

            # 使用强制字体上下文保存
            with plt.rc_context({
                'font.sans-serif': [font_name, 'DejaVu Sans'],
                'font.family': 'sans-serif',
                'axes.unicode_minus': False
            }):
                plt.savefig(image_str, **save_kwargs)

            plt.close()
            result_string = image_str.getvalue()

            # 对SVG内容进行后处理
            result_string = _post_process_svg(result_string)
        else:
            image_bytes = BytesIO()
            save_kwargs["dpi"] = config.plot.dpi

            with plt.rc_context({
                'font.sans-serif': [font_name, 'DejaVu Sans'],
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

        with plt.rc_context({
            'font.sans-serif': [font_name, 'DejaVu Sans'],
            'font.family': 'sans-serif',
            'axes.unicode_minus': False
        }):
            plt.savefig(**save_kwargs)

        plt.close()
        result_string = suffix

    return result_string