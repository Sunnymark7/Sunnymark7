# Add or organize a repository

GitHub 个人账号没有真正的“仓库文件夹”。这个主页使用 `project-*` Topics 作为项目分组，并由 GitHub Actions 自动生成 Project Atlas。

## 新建仓库并立即归类

```powershell
gh repo create Sunnymark7/REPOSITORY_NAME --private --description "一句话说明它解决什么问题"
gh repo edit Sunnymark7/REPOSITORY_NAME --add-topic project-ehand --add-topic status-active
gh workflow run sync-profile.yml --repo Sunnymark7/Sunnymark7
```

公开仓库把 `--private` 改为 `--public`。同步任务也会每 6 小时自动运行。

## 项目 Topic

| Topic | Project family |
| --- | --- |
| `project-ehand` | eHand 智能触觉手套 |
| `project-neurotech` | EEG、SSVEP 与脑机交互 |
| `project-embedded` | ESP32、STM32、ADC 与设备工具 |
| `project-instrumentation` | 标定、测量与科研仪器软件 |
| `project-simulation` | 动力学与工程仿真 |

也可以直接使用新的 Topic，例如 `project-robotics`。生成器会先创建一个临时的 **Robotics** 项目族；之后再到 `data/projects.json` 补充正式标题、简介和核心技术即可。

每个仓库只应有一个 `project-*` Topic。存在多个时，生成器会给出警告，并按配置顺序选择，避免同一仓库重复出现。

## 排序、状态与隐藏

这些辅助 Topics 可选：

| Topic | Effect |
| --- | --- |
| `portfolio-featured` | 在项目族中优先展示 |
| `portfolio-hide` | 完全排除，不计数、不展示 |
| `status-active` | 标记为 Active |
| `status-research` | 标记为 Research |
| `status-prototype` | 标记为 Prototype |
| `status-maintained` | 标记为 Maintained |
| `status-completed` | 标记为 Completed |

示例：

```powershell
gh repo edit Sunnymark7/REPOSITORY_NAME `
  --add-topic project-neurotech `
  --add-topic portfolio-featured `
  --add-topic status-prototype
```

## 私有仓库与隐私

- 公开仓库：自动显示名称、说明、最多三项技术和最近推送月份。
- 私有仓库：默认只显示 `data/projects.json` 中人工确认过的策展卡片；不生成真实仓库名或链接。
- 带 `portfolio-hide` 的仓库：即使同步任务拥有私有访问权限，也会被完全忽略。
- 新的私有仓库：如果希望自动更新所属项目族的额外数量，可为主页仓库配置只读、最小范围的 fine-grained token。

GitHub 默认 `GITHUB_TOKEN` 无权读取同一账号的其他私有仓库。可选设置方法：

1. 创建 fine-grained personal access token，只选择需要统计的私有仓库。
2. Repository permissions 只授予 `Metadata: Read-only`。
3. 保存为主页仓库的 Actions secret：

```powershell
gh secret set PROFILE_REPO_TOKEN --repo Sunnymark7/Sunnymark7
```

不要直接复用权限较大的日常登录 token。未配置该 secret 时，公开仓库同步和策展私有卡片仍会正常工作；配置后如果私有数据源不可用，任务会停止而不是发布不完整计数。

## 自动路由规则

生成器按以下顺序处理：

1. `portfolio-hide` 直接排除。
2. 显式 `project-*` Topic 优先。
3. 没有项目 Topic 时，使用名称、描述和现有 Topics 的完整关键词匹配。
4. 仍无法判断的公开仓库进入 **Project Inbox**。
5. 项目内先显示 `portfolio-featured`，再按 `pushed_at` 排序。

工作流会先运行单元测试（其中包含幂等性验证），最后只在 `README.md` 真正变化时提交。
