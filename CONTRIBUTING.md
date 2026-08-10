# Add or organize a repository

GitHub 个人账号不能创建真正的“仓库文件夹”。本主页使用统一的 `project-*` Topics 作为项目分组，并由 GitHub Actions 自动生成项目索引。

## 新建并归类仓库

```powershell
gh repo create Sunnymark7/REPOSITORY_NAME --public --description "一句话说明项目目标"
gh repo edit Sunnymark7/REPOSITORY_NAME --add-topic project-ehand
gh workflow run sync-profile.yml --repo Sunnymark7/Sunnymark7
```

私有仓库将 `--public` 改成 `--private`。可用项目 Topic：

| Topic | Project group |
| --- | --- |
| `project-ehand` | eHand 智能触觉手套 |
| `project-neurotech` | SSVEP、EEG 与脑机交互 |
| `project-embedded` | ESP32、固件、ADC 与嵌入式工具 |
| `project-instrumentation` | 标定、测量与科研仪器 |
| `project-simulation` | 动力学与工程仿真 |
| `project-experiments` | Web 实验与快速原型 |

## 整理已有仓库

```powershell
gh repo edit Sunnymark7/REPOSITORY_NAME --add-topic project-neurotech
gh workflow run sync-profile.yml --repo Sunnymark7/Sunnymark7
```

同步任务也会每天自动执行。没有 `project-*` Topic 的公开仓库会先按名称、描述和现有 Topics 自动推断；无法推断时会显示在“待整理”区。

## 让自动任务读取私有仓库数量

GitHub 默认的 `GITHUB_TOKEN` 只能访问当前主页仓库。若希望同步任务自动统计新增的私有仓库，需要创建最小权限的 fine-grained personal access token：

1. Repository access 只选择需要统计的私有仓库。
2. Repository permissions 仅需 `Metadata: Read-only`。
3. 将 token 保存为主页仓库的 Actions secret：

```powershell
gh secret set PROFILE_REPO_TOKEN --repo Sunnymark7/Sunnymark7
```

不配置该 secret 也能正常同步公开仓库；私有项目将使用 `data/projects.json` 中的安全基线数量，且永远不会公开私有仓库名称或链接。
