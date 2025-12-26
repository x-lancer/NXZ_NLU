# Git 中文编码配置说明

## 问题说明

在 Windows 系统中，Git 的 commit 信息可能会出现中文乱码问题。这是因为 Git 和 PowerShell 的编码设置不匹配导致的。

## 解决方案

### 1. 配置 Git 全局编码设置

在 PowerShell 中运行以下命令：

```powershell
# 设置 Git 提交信息使用 UTF-8 编码
git config --global i18n.commitencoding utf-8

# 设置 Git 日志输出使用 UTF-8 编码
git config --global i18n.logoutputencoding utf-8

# 设置不转义路径中的特殊字符
git config --global core.quotepath false
```

### 2. 设置 PowerShell 编码（临时）

在每次使用 Git 前，在 PowerShell 中运行：

```powershell
chcp 65001
```

这会临时将代码页设置为 UTF-8。

### 3. 设置 PowerShell 编码（永久）

在 PowerShell 配置文件中添加编码设置：

1. 打开 PowerShell 配置文件：
   ```powershell
   notepad $PROFILE
   ```

2. 如果文件不存在，先创建：
   ```powershell
   New-Item -Path $PROFILE -Type File -Force
   ```

3. 在配置文件中添加：
   ```powershell
   chcp 65001 | Out-Null
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   ```

4. 重新加载配置：
   ```powershell
   . $PROFILE
   ```

### 4. 验证配置

运行以下命令查看当前配置：

```powershell
git config --global --list | Select-String encoding
```

应该看到：
```
i18n.commitencoding=utf-8
i18n.logoutputencoding=utf-8
```

## 注意事项

- 如果之前的 commit 已经有乱码，需要修改 commit 信息后才能解决
- 修改已推送的 commit 需要使用 `git commit --amend` 和 `git push -f`
- 强制推送会覆盖远程历史，请确保没有其他人基于旧历史进行开发

