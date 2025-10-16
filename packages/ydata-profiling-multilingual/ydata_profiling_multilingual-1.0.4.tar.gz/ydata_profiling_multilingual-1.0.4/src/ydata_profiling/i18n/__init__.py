"""
Internationalization module for ydata-profiling
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional, List, Union
import threading

class TranslationManager:
    """Manages translations for ydata-profiling with support for external translation files"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.translations: Dict[str, Dict[str, str]] = {}
            self.current_locale = 'en'
            self.fallback_locale = 'en'
            self.external_translation_dirs: List[Path] = []
            self.initialized = True
            self._load_translations()

    def add_translation_directory(self, directory: Union[str, Path]):
        """Add external translation directory

        Args:
            directory: Path to directory containing translation JSON files
        """
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            if dir_path not in self.external_translation_dirs:
                self.external_translation_dirs.append(dir_path)
                self._load_external_translations(dir_path)
        else:
            print(f"Warning: Translation directory {directory} does not exist")

    def load_translation_file(self, file_path: Union[str, Path], locale: Optional[str] = None):
        """Load a specific translation file

        Args:
            file_path: Path to the translation JSON file
            locale: Locale code. If None, will be inferred from filename
        """
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"Warning: Translation file {file_path} does not exist")
            return

        if locale is None:
            locale = file_path.stem

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                external_translations = json.load(f)

            # Merge with existing translations
            if locale in self.translations:
                self.translations[locale] = self._merge_translations(
                    self.translations[locale],
                    external_translations
                )
            else:
                self.translations[locale] = external_translations

            print(f"Successfully loaded translation file for locale '{locale}' from {file_path}")
        except Exception as e:
            print(f"Warning: Failed to load translation file {file_path}: {e}")

    def _merge_translations(self, base: dict, override: dict) -> dict:
        """Recursively merge translation dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_translations(result[key], value)
            else:
                result[key] = value
        return result

    def _load_translations(self):
        """Load built-in translation files"""
        translations_dir = Path(__file__).parent / 'locales'
        if translations_dir.exists():
            self._load_translations_from_directory(translations_dir)

    def _load_external_translations(self, directory: Path):
        """Load translations from external directory"""
        self._load_translations_from_directory(directory)

    def _load_translations_from_directory(self, directory: Path):
        """Load all translation files from a directory"""
        for locale_file in directory.glob('*.json'):
            locale = locale_file.stem
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    translations = json.load(f)

                if locale in self.translations:
                    # Merge with existing translations
                    self.translations[locale] = self._merge_translations(
                        self.translations[locale],
                        translations
                    )
                else:
                    self.translations[locale] = translations

            except Exception as e:
                print(f"Warning: Failed to load translation file {locale_file}: {e}")

    def get_available_locales(self) -> List[str]:
        """Get list of available locales"""
        return list(self.translations.keys())

    def set_locale(self, locale: str):
        """Set the current locale"""
        if locale in self.translations or locale == self.fallback_locale:
            self.current_locale = locale
        else:
            print(f"Warning: Locale '{locale}' not found, using fallback '{self.fallback_locale}'")
            print(f"Available locales: {self.get_available_locales()}")

    def get_translation(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """Get translation for a key"""
        target_locale = locale or self.current_locale

        # Try current locale
        if target_locale in self.translations:
            translation = self._get_nested_value(self.translations[target_locale], key)
            if translation:
                return self._format_translation(translation, **kwargs)

        # Try fallback locale
        if target_locale != self.fallback_locale and self.fallback_locale in self.translations:
            translation = self._get_nested_value(self.translations[self.fallback_locale], key)
            if translation:
                return self._format_translation(translation, **kwargs)

        # Return key if no translation found
        return key

    def _get_nested_value(self, data: dict, key: str) -> Optional[str]:
        """Get nested value from dictionary using dot notation"""
        keys = key.split('.')
        current = data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        return current if isinstance(current, str) else None

    def _format_translation(self, translation: str, **kwargs) -> str:
        """Format translation with parameters"""
        try:
            return translation.format(**kwargs)
        except (KeyError, ValueError):
            return translation

    def export_template(self, locale: str, output_file: Union[str, Path]):
        """Export translation template for a specific locale

        Args:
            locale: Source locale to export (usually 'en')
            output_file: Output file path
        """
        template_data = None

        # 方法1: 尝试从内置文件直接读取（推荐）
        translations_dir = Path(__file__).parent / 'locales'
        locale_file = translations_dir / f"{locale}.json"

        if locale_file.exists():
            try:
                with open(locale_file, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                print(f"Loading template from built-in file: {locale_file}")
            except Exception as e:
                print(f"Warning: Failed to load built-in file {locale_file}: {e}")

        # 方法2: 从已加载的翻译中获取
        if template_data is None:
            self._load_translations()  # 确保翻译已加载
            if locale in self.translations:
                template_data = self.translations[locale]
                print(f"Using loaded translation for locale: {locale}")

        # 方法3: 创建基础模板
        if template_data is None:
            print(f"Warning: Locale '{locale}' not found, creating basic template")
            template_data = self._create_basic_template()

        # 导出模板
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)

        print(f"Translation template exported to {output_path}")

    def _create_basic_template(self) -> dict:
        """Create a basic translation template with essential keys based on actual structure"""
        return {
            "report": {
                "overview": "Overview",
                "variables": "Variables",
                "interactions": "Interactions",
                "missing_values": "Missing values",
                "sample": "Sample",
                "duplicates": "Duplicate rows",
                "footer_text": "Report generated by <a href=\"https://ydata.ai/?utm_source=opensource&utm_medium=pandasprofiling&utm_campaign=report\">YData</a>.",
                "most_frequently_occurring": "Most frequently occurring",
                "columns": "Columns",
                "more_details": "More details"
            },
            "rendering": {
                "generate_structure": "Generate report structure",
                "html_progress": "Render HTML",
                "json_progress": "Render JSON",
                "widgets_progress": "Render widgets",
                "other_values_count": "Other values ({other_count})"
            },
            "core": {
                "unknown": "unknown",
                "alerts": {
                    "title": "Alerts",
                    "alerts_high_correlation_tip": "This variable has a high {corr} correlation with {num} fields: {title}",
                    "correlation_types": {
                        "overall": "overall"
                    }
                },
                "collapse": "Collapse",
                "container": "Container",
                "correlationTable": "CorrelationTable",
                "dropdown": "Dropdown",
                "duplicate": "Duplicate",
                "html": "HTML",
                "image": "Image",
                "sample": "Sample",
                "scores": "Scores",
                "table": "Table",
                "toggle_button": "ToggleButton",
                "variable": "Variable",
                "variable_info": "VariableInfo",
                "model": {
                    "bar_count": "Count",
                    "bar_caption": "A simple visualization of nullity by column.",
                    "matrix": "Matrix",
                    "matrix_caption": "Nullity matrix is a data-dense display which lets you quickly visually pick out patterns in data completion.",
                    "heatmap": "Heatmap",
                    "heatmap_caption": "The correlation heatmap measures nullity correlation: how strongly the presence or absence of one variable affects the presence of another.",
                    "first_rows": "First rows",
                    "last_rows": "Last rows",
                    "random_sample": "Random sample"
                },
                "structure": {
                    "correlations": "Correlations",
                    "heatmap": "Heatmap",
                    "table": "Table",
                    "overview": {
                        "values": "values",
                        "number_variables": "Number of variables",
                        "number_observations": "Number of observations",
                        "number_of_series": "Number of series",
                        "missing_cells": "Missing cells",
                        "missing_cells_percentage": "Missing cells (%)",
                        "duplicate_rows": "Duplicate rows",
                        "duplicate_rows_percentage": "Duplicate rows (%)",
                        "total_size_memory": "Total size in memory",
                        "average_record_memory": "Average record size in memory",
                        "dataset_statistics": "Dataset statistics",
                        "variable_types": "Variable types",
                        "variable_descriptions": "Variable descriptions",
                        "overview": "Overview",
                        "url": "URL",
                        "copyright": "Copyright",
                        "dataset": "Dataset",
                        "analysis_started": "Analysis started",
                        "analysis_finished": "Analysis finished",
                        "duration": "Duration",
                        "software_version": "Software version",
                        "download_configuration": "Download configuration",
                        "reproduction": "Reproduction",
                        "variables": "Variables",
                        "alerts_count": "Alerts ({count})",
                        "timeseries_length": "Time series length",
                        "starting_point": "Starting point",
                        "ending_point": "Ending point",
                        "period": "Period",
                        "timeseries_statistics": "Timeseries statistics",
                        "original": "Original",
                        "scaled": "Scaled",
                        "time_series": "Time Series",
                        "interactions": "Interactions",
                        "distinct": "Distinct",
                        "distinct_percentage": "Distinct (%)",
                        "missing": "Missing",
                        "missing_percentage": "Missing (%)",
                        "memory_size": "Memory size",
                        "file": "File",
                        "size": "Size",
                        "file_size": "File size",
                        "file_size_caption": "Histogram with fixed size bins of file sizes (in bytes)",
                        "unique": "Unique",
                        "unique_help": "The number of unique values (all values that occur exactly once in the dataset).",
                        "unique_percentage": "Unique (%)",
                        "max_length": "Max length",
                        "median_length": "Median length",
                        "mean_length": "Mean length",
                        "min_length": "Min length",
                        "length": "Length",
                        "length_histogram": "length histogram",
                        "histogram_lengths_category": "Histogram of lengths of the category",
                        "most_occurring_categories": "Most occurring categories",
                        "frequency": "Frequency",
                        "most_frequent_character_per_category": "Most frequent character per category",
                        "most_occurring_scripts": "Most occurring scripts",
                        "most_frequent_character_per_script": "Most frequent character per script",
                        "most_occurring_blocks": "Most occurring blocks",
                        "most_frequent_character_per_block": "Most frequent character per block",
                        "imaginary": "Imaginary",
                        "real": "Real",
                        "total_characters": "Total characters",
                        "distinct_characters": "Distinct characters",
                        "distinct_categories": "Distinct categories",
                        "unicode_categories": "Unicode categories (click for more information)",
                        "distinct_scripts": "Distinct scripts",
                        "unicode_scripts": "Unicode scripts (click for more information)",
                        "distinct_blocks": "Distinct blocks",
                        "unicode_blocks": "Unicode blocks (click for more information)",
                        "characters_unicode": "Characters and Unicode",
                        "characters_unicode_caption": "The Unicode Standard assigns character properties to each code point, which can be used to analyse textual variables.",
                        "most_occurring_characters": "Most occurring characters",
                        "characters": "Characters",
                        "categories": "Categories",
                        "scripts": "Scripts",
                        "blocks": "Blocks",
                        "unicode": "Unicode",
                        "common_values": "Common Values",
                        "common_values_table": "Common Values (Table)",
                        "1st_row": "1st row",
                        "2nd_row": "2nd row",
                        "3rd_row": "3rd row",
                        "4th_row": "4th row",
                        "5th_row": "5th row",
                        "categories_passes_threshold ": "Number of variable categories passes threshold (<code>config.plot.cat_freq.max_unique</code>)",
                        "common_values_plot": "Common Values (Plot)",
                        "common_words": "Common words",
                        "wordcloud": "Wordcloud",
                        "words": "Words",
                        "mean": "Mean",
                        "min": "Minimum",
                        "max": "Maximum",
                        "zeros": "Zeros",
                        "zeros_percentage": "Zeros (%)",
                        "scatter": "Scatter",
                        "scatterplot": "Scatterplot",
                        "scatterplot_caption": "Scatterplot in the complex plane",
                        "mini_histogram": "Mini histogram",
                        "histogram": "Histogram",
                        "histogram_caption": "Histogram with fixed size bins",
                        "extreme_values": "Extreme values",
                        "histogram_s": "Histogram(s)",
                        "invalid_dates": "Invalid dates",
                        "invalid_dates_percentage": "Invalid dates (%)",
                        "created": "Created",
                        "accessed": "Accessed",
                        "modified": "Modified",
                        "min_width": "Min width",
                        "median_width": "Median width",
                        "max_width": "Max width",
                        "min_height": "Min height",
                        "median_height": "Median height",
                        "max_height": "Max height",
                        "min_area": "Min area",
                        "median_area": "Median area",
                        "max_area": "Max area",
                        "scatter_plot_image_sizes": "Scatter plot of image sizes",
                        "scatter_plot": "Scatter plot",
                        "dimensions": "Dimensions",
                        "exif_keys": "Exif keys",
                        "exif_data": "Exif data",
                        "image": "Image",
                        "common_prefix": "Common prefix",
                        "unique_stems": "Unique stems",
                        "unique_names": "Unique names",
                        "unique_extensions": "Unique extensions",
                        "unique_directories": "Unique directories",
                        "unique_anchors": "Unique anchors",
                        "full": "Full",
                        "stem": "Stem",
                        "name": "Name",
                        "extension": "Extension",
                        "parent": "Parent",
                        "anchor": "Anchor",
                        "path": "Path",
                        "infinite": "Infinite",
                        "infinite_percentage": "Infinite (%)",
                        "Negative": "Negative",
                        "Negative_percentage": "Negative (%)",
                        "5_th_percentile": "5-th percentile",
                        "q1": "Q1",
                        "median": "median",
                        "q3": "Q3",
                        "95_th_percentile": "95-th percentile",
                        "range": "Range",
                        "iqr": "Interquartile range (IQR)",
                        "quantile_statistics": "Quantile statistics",
                        "standard_deviation": "Standard deviation",
                        "cv": "Coefficient of variation (CV)",
                        "kurtosis": "Kurtosis",
                        "mad": "Median Absolute Deviation (MAD)",
                        "skewness": "Skewness",
                        "sum": "Sum",
                        "variance": "Variance",
                        "monotonicity": "Monotonicity",
                        "descriptive_statistics": "Descriptive statistics",
                        "statistics": "Statistics",
                        "augmented_dickey_fuller_test_value": "Augmented Dickey-Fuller test p-value",
                        "autocorrelation": "Autocorrelation",
                        "autocorrelation_caption": "ACF and PACF",
                        "timeseries": "Time-series",
                        "timeseries_plot": "Time-series plot",
                        "scheme": "Scheme",
                        "netloc": "Netloc",
                        "query": "Query",
                        "fragment": "Fragment",
                        "heatmap": "Heatmap",
                        "pearson's r": "Pearson's r",
                        "spearman's ρ": "Spearman's ρ",
                        "kendall's τ": "Kendall's τ",
                        "phik (φk)": "Phik (φk)",
                        "cramér's V (φc)": "Cramér's V (φc)",
                        "auto": "Auto"
                    }
                }
            },
            "html": {
                "alerts": {
                    "title": "Alerts",
                    "not_present": "Alert not present in this dataset",
                    "has_constant_value": "has constant value",
                    "has_constant_length": "has constant length",
                    "has_dirty_categories": "has dirty categories",
                    "has_high_cardinality": "has a high cardinality",
                    "distinct_values": "distinct values",
                    "dataset_has": "Dataset has",
                    "duplicate_rows": "duplicate rows",
                    "dataset_is_empty": "Dataset is empty",
                    "is_highly": "is highly",
                    "correlated_with": "correlated with",
                    "and": "and",
                    "other_fields": "other fields",
                    "highly_imbalanced": "is highly imbalanced",
                    "has": "has",
                    "infinite_values": "infinite values",
                    "missing_values": "missing values",
                    "near_duplicate_rows": "near duplicate rows",
                    "non_stationary": "is non stationary",
                    "seasonal": "is seasonal",
                    "highly_skewed": "is highly skewed",
                    "truncated_files": "truncated files",
                    "alert_type_date": "only contains datetime values, but is categorical. Consider applying",
                    "uniformly_distributed": "is uniformly distributed",
                    "unique_values": "has unique values",
                    "alert_unsupported": "is an unsupported type, check if it needs cleaning or further analysis",
                    "zeros": "zeros"
                },
                "sequence": {
                    "overview_tabs": {
                        "brought_to_you_by": "Brought to you by <a href=\"https://ydata.ai/?utm_source=opensource&utm_medium=ydataprofiling&utm_campaign=report\">YData</a>"
                    }
                },
                "dropdown": "Select Columns",
                "frequency_table": {
                    "value": "Value",
                    "count": "Count",
                    "frequency_percentage": "Frequency (%)",
                    "redacted_value": "Redacted value",
                    "no_values_found": "No values found"
                },
                "scores": {
                    "overall_data_quality": "Overall Data Quality Score"
                },
                "variable_info": {
                    "no_alerts": "No alerts"
                }
            }
        }

# Global translation manager instance
_translation_manager = TranslationManager()

def set_locale(locale: str):
    """Set the global locale"""
    _translation_manager.set_locale(locale)

def get_locale() -> str:
    """Get the current locale"""
    return _translation_manager.current_locale

def add_translation_directory(directory: Union[str, Path]):
    """Add external translation directory"""
    _translation_manager.add_translation_directory(directory)

def load_translation_file(file_path: Union[str, Path], locale: Optional[str] = None):
    """Load a specific translation file"""
    _translation_manager.load_translation_file(file_path, locale)

def get_available_locales() -> List[str]:
    """Get list of available locales"""
    return _translation_manager.get_available_locales()

def export_translation_template(locale: str = 'en', output_file: Union[str, Path] = 'translation_template.json'):
    """Export translation template for customization"""
    _translation_manager.export_template(locale, output_file)

def _(key: str, default: Optional[str] = None, **kwargs) -> str:
    """Translation function with optional default fallback

    Args:
        key: Translation key in dot notation (e.g., 'report.title')
        default: Default value to return if translation is not found
        **kwargs: Parameters for string formatting

    Returns:
        Translated string, default value, or the key itself if no translation found
    """
    translation = _translation_manager.get_translation(key, **kwargs)

    # If the translation key is not found and a default value is provided, use the default value
    if translation == key and default is not None:
        return default

    return translation

def t(key: str, **kwargs) -> str:
    """Translation function - alias for _()

    Args:
        key: Translation key in dot notation
        **kwargs: Parameters for string formatting

    Returns:
        Translated string
    """
    return _(key, **kwargs)

# Export main functions
__all__ = [
    'set_locale', 'get_locale', '_', 't', 'TranslationManager',
    'add_translation_directory', 'load_translation_file',
    'get_available_locales', 'export_translation_template'
]