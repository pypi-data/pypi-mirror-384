# YData Profiling Multilingual
 
> **Note**: This is a fork of [ydataai/ydata-profiling](https://github.com/ydataai/ydata-profiling) with added international multilingual functionality. I only implemented multilingual language support - all core profiling features remain unchanged from the original project.

[![Build Status](https://github.com/ydataai/pandas-profiling/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/ydataai/pandas-profiling/actions/workflows/tests.yml)
[![PyPI download month](https://img.shields.io/pypi/dm/ydata-profiling.svg)](https://pypi.python.org/pypi/ydata-profiling/)
[![](https://pepy.tech/badge/pandas-profiling)](https://pypi.org/project/ydata-profiling/)
[![Code Coverage](https://codecov.io/gh/ydataai/pandas-profiling/branch/master/graph/badge.svg?token=gMptB4YUnF)](https://codecov.io/gh/ydataai/pandas-profiling)
[![Release Version](https://img.shields.io/github/release/ydataai/pandas-profiling.svg)](https://github.com/ydataai/pandas-profiling/releases)
[![Python Version](https://img.shields.io/pypi/pyversions/ydata-profiling)](https://pypi.org/project/ydata-profiling/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
 
## 🌍 What I Added
 
This fork adds comprehensive internationalization (i18n) support to the original ydata-profiling:
 
- **🔤 Multi-language Support**: Built-in English, Chinese, and framework for custom languages
- **🛠️ Custom Translations**: Users can create and load their own translation files
- **📊 Localized Reports**: All UI elements, labels, and messages are translatable
- **⚙️ Translation Tools**: Command-line utilities for creating and validating translations
- **🔄 100% Backward Compatibility**: Works exactly like original ydata-profiling
 
## 🙏 Credits
 
- **Original Project**: [ydata-profiling](https://github.com/ydataai/ydata-profiling) by YData team
- **Multilingual Enhancement**: Added by [Landon Zeng](https://github.com/landonzeng)
- **What I Did**: Only implemented i18n functionality - all core features are from the original project
 
## 🚀 Quick Start
 
### Installation
 
```bash
pip install ydata-profiling-multilingual
```

### Basic Usage (Same as Original + Language Support)

```python
import pandas as pd
from ydata_profiling import ProfileReport
 
# Create sample data
df = pd.DataFrame({
    'numeric': [1, 2, 3, 4, 5],
    'categorical': ['A', 'B', 'A', 'C', 'B'],
})
 
# Generate report in Chinese (NEW FEATURE)
profile = ProfileReport(df, title="数据分析报告", locale='zh')
profile.to_file("chinese_report.html")
 
# Generate report in English (same as original)
profile = ProfileReport(df, title="Data Analysis Report")
profile.to_file("english_report.html")
```
## 🌐 Supported Languages
- English (en) - Default
- Chinese Simplified (zh) - 简体中文
- Custom Languages - Add your own!

## 🔧 New Multilingual Features
### Export Translation Template

```bash
# Use new command line tool
ydata-profiling-translate create-template -l en -o ./my_template.json
```
### Create Custom Translation
```python
from ydata_profiling.i18n import load_translation_file, set_locale
 
# Load your custom translation file
load_translation_file('my_french.json', 'fr')
 
# Generate French report
profile = ProfileReport(df, title="Rapport d'Analyse", locale='fr')
```

### Load Translation Directory
```python
from ydata_profiling.i18n import add_translation_directory
 
# Load all translations from a directory
add_translation_directory('./my_translations/')
```

## 📚 Examples
Check the examples/ folder for complete workflows:
```python
# Run the complete example
python examples/translation_workflow_example.py
```

## 🔄 Migration from Original
If you're using the original ydata-profiling, migration is seamless:
```python
# Your existing code works unchanged
from ydata_profiling import ProfileReport
profile = ProfileReport(df)  # Still works!
 
# Just add locale for multilingual support
profile = ProfileReport(df, locale='zh')  # Now with Chinese!
```

## 🤝 Contributing
This project focuses only on multilingual functionality. For core profiling features:
- Core Issues: Please report to original ydata-profiling
- Translation Issues: Report here at ydata-profiling-multilingual

### Adding New Languages
1. Export English template: ydata-profiling-translate create-template
2. Translate the JSON file
3. Submit PR with your translation

## 📄 License
Same as original project: MIT License

## 🔗 Links
- Original Project: [ydata-profiling](https://github.com/ydataai/ydata-profiling)
- This Fork: [ydata-profiling-multilingual](https://github.com/landonzeng/ydata-profiling-multilingual)
- My GitHub: [landonzeng](https://github.com/landonzeng)

## ⚠️ Disclaimer
I am not affiliated with YData. This is an independent fork that adds multilingual support. All core profiling algorithms and features are from the original ydata-profiling project. I only implemented the internationalization layer.

## 🌟 If this multilingual version helps you, please star both repositories:
- ⭐ Original ydata-profiling
- ⭐ This multilingual fork