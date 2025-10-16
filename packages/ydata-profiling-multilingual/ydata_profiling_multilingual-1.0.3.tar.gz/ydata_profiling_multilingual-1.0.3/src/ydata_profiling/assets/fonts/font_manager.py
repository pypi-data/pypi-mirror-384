"""
Font management for ydata-profiling
支持中文字体的字体管理器
"""
import os
import warnings
from pathlib import Path
from typing import Optional, List
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm


class FontManager:
    """字体管理器"""

    def __init__(self):
        self.font_dir = Path(__file__).parent
        self.available_fonts = self._get_bundled_fonts()
        self._font_initialized = False
        self._builtin_font_prop = None  # 存储内置字体属性

    def _get_bundled_fonts(self) -> dict:
        """获取内置字体列表"""
        fonts = {}
        font_files = self.font_dir.glob("*.ttf")

        for font_file in font_files:
            font_name = font_file.stem.lower()
            fonts[font_name] = font_file

        return fonts

    def get_chinese_font_path(self) -> Optional[Path]:
        """获取中文字体路径"""
        # 优先级排序
        chinese_fonts = ['simhei', 'simsun', 'microsoftyahei', 'msyh']

        for font_name in chinese_fonts:
            if font_name in self.available_fonts:
                return self.available_fonts[font_name]

        return None

    def setup_chinese_support(self, force: bool = False) -> bool:
        """设置中文字体支持"""
        if self._font_initialized and not force:
            return True

        try:
            # 抑制字体警告
            warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

            # 获取中文字体路径
            chinese_font_path = self.get_chinese_font_path()

            if chinese_font_path and chinese_font_path.exists():
                # 使用字体属性而不是修改字体名称
                return self._setup_builtin_font_with_properties(chinese_font_path)
            else:
                # 回退到系统字体
                self._setup_system_chinese_fonts()
                return False

        except Exception as e:
            warnings.warn(f"Chinese font setup failed: {e}")
            self._setup_system_chinese_fonts()
            return False

    def _setup_builtin_font_with_properties(self, font_path: Path) -> bool:
        """使用字体属性设置内置字体"""
        try:
            # 直接创建字体属性对象
            self._builtin_font_prop = fm.FontProperties(fname=str(font_path))
            builtin_font_name = self._builtin_font_prop.get_name()

            print(f"✅ 内置字体属性创建成功: {builtin_font_name}")
            print(f"   字体文件路径: {font_path}")

            # 强制注册字体到matplotlib
            fm.fontManager.addfont(str(font_path))

            # 重建字体缓存
            try:
                fm._rebuild()
            except:
                pass

            # 设置matplotlib全局配置，确保内置字体优先
            # 移除可能冲突的字体名称
            current_fonts = plt.rcParams['font.sans-serif'].copy()
            filtered_fonts = [f for f in current_fonts if f != builtin_font_name]

            # 将内置字体放在最前面
            new_fonts = [builtin_font_name] + filtered_fonts

            plt.rcParams['font.sans-serif'] = new_fonts
            plt.rcParams['axes.unicode_minus'] = False

            # 额外设置：强制指定默认字体
            plt.rcParams['font.family'] = 'sans-serif'

            self._font_initialized = True

            print(f"✅ 字体配置成功")
            print(f"   当前字体优先级: {new_fonts[:3]}")

            # 验证字体解析
            test_prop = fm.FontProperties(family=builtin_font_name)
            resolved_path = fm.findfont(test_prop)

            if str(font_path) in resolved_path or font_path.name in resolved_path:
                print(f"✅ 字体解析验证成功: {resolved_path}")
                return True
            else:
                print(f"⚠️ 字体解析验证失败:")
                print(f"   期望包含: {font_path}")
                print(f"   实际解析: {resolved_path}")
                # 即使解析不完美，仍然返回True，因为字体已经注册
                return True

        except Exception as e:
            print(f"❌ 内置字体设置失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _setup_system_chinese_fonts(self):
        """设置系统中文字体"""
        system_fonts = [
            'Microsoft YaHei', 'SimSun', 'SimHei',  # Windows
            'PingFang SC', 'STHeiti', 'Heiti SC',   # macOS
            'WenQuanYi Micro Hei', 'Noto Sans CJK SC',  # Linux
            'DejaVu Sans'  # 备用
        ]

        plt.rcParams['font.sans-serif'] = system_fonts
        plt.rcParams['axes.unicode_minus'] = False
        self._font_initialized = True

        print(f"✅ 系统字体配置完成: {system_fonts[:3]}")

    def get_builtin_font_prop(self) -> Optional[fm.FontProperties]:
        """获取内置字体属性对象"""
        return self._builtin_font_prop

    def get_font_info(self) -> dict:
        """获取字体信息"""
        builtin_font_name = None
        if self._builtin_font_prop:
            builtin_font_name = self._builtin_font_prop.get_name()

        return {
            'bundled_fonts': list(self.available_fonts.keys()),
            'chinese_font_available': self.get_chinese_font_path() is not None,
            'font_initialized': self._font_initialized,
            'font_dir': str(self.font_dir),
            'builtin_font_name': builtin_font_name,
            'builtin_font_prop': self._builtin_font_prop is not None,
            'current_font_priority': plt.rcParams['font.sans-serif'][:5]
        }


# 全局字体管理器实例
_font_manager = FontManager()


def setup_chinese_fonts(enable: bool = True) -> bool:
    """设置中文字体支持（公共接口）"""
    if enable:
        return _font_manager.setup_chinese_support(force=True)
    return True


def get_font_manager() -> FontManager:
    """获取字体管理器实例"""
    return _font_manager


def apply_builtin_font_to_plot():
    """将内置字体应用到当前图表"""
    font_manager = get_font_manager()
    builtin_prop = font_manager.get_builtin_font_prop()

    if builtin_prop:
        # 获取当前的matplotlib轴对象
        import matplotlib.pyplot as plt

        # 应用到当前图表的所有文本
        for ax in plt.gcf().get_axes():
            for text in ax.get_children():
                if hasattr(text, 'set_fontproperties'):
                    try:
                        text.set_fontproperties(builtin_prop)
                    except:
                        pass

        return True
    return False