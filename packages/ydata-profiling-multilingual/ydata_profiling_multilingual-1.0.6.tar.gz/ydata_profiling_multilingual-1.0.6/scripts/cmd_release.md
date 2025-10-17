## 方法1: 使用批处理脚本
```bash
scripts\release.bat
```

## 方法2: 使用PowerShell脚本（推荐）
```bash
PowerShell -ExecutionPolicy Bypass -File scripts\release.ps1
```

## 方法3: PowerShell带参数
```bash
PowerShell -ExecutionPolicy Bypass -File scripts\release.ps1 -Version "1.0.0" -Target "test"
```

## 方法4: 手动发布（Windows CMD）
```bash
rmdir /s /q build dist
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
```

## 方法5: 手动发布（PowerShell）

### 1. 打包
```bash
Remove-Item build, dist -Recurse -Force -ErrorAction SilentlyContinue

python -m build

python -m twine check dist/*

```

### 2. 上传至pypi
```bash

python -m twine upload dist/*

```
### 3. 上传至testpypip
```bash

python -m twine upload --repository testpypi dist/*

```