# 方法1: 使用批处理脚本
scripts\release.bat

# 方法2: 使用PowerShell脚本（推荐）
PowerShell -ExecutionPolicy Bypass -File scripts\release.ps1

# 方法3: PowerShell带参数
PowerShell -ExecutionPolicy Bypass -File scripts\release.ps1 -Version "1.0.0" -Target "test"

# 方法4: 手动发布（Windows CMD）
rmdir /s /q build dist
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*

# 方法5: 手动发布（PowerShell）
Remove-Item build, dist -Recurse -Force -ErrorAction SilentlyContinue
python -m build
python -m twine check dist/*

# 上传至pypi和testpypip
python -m twine upload dist/*
python -m twine upload --repository testpypi dist/*