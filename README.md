# homework-photo-answer · 练习册照片自动标答案

手机拍一张练习册/试卷照片 → 自动识别每道题的位置 → 把答案（含脱式分步、竖式、简算过程）用红字**直接写在题目上**，可合并成 A4 PDF 打印。

核心思路：**答案落笔位置靠墨迹检测自动定位，不靠目测坐标**。所以照片有倾斜、透视也能对齐，不会把答案写到隔壁题上。

```
原图（手机随手拍，可能歪/有阴影）
   ↓  旋转 + 扶正 + 裁掉背景
   ↓  扫描文字行 → 得到每行 y 与每栏 x 区间
   ↓  逐题算出答案（过程用脚本复核）
   ↓  按坐标渲染红字
答案图 / A4 PDF
```

## 它是怎么工作的

这套东西分成**两半**，理解这一点很重要：

| 部分 | 谁来做 | 说明 |
|---|---|---|
| **脑**：读题、算答案、决定写什么 | AI 助手（读 `SKILL.md`） | 本仓库不含任何"解题模型"，解题由你的 AI 完成 |
| **笔**：定位、排版、把字画到图上 | `scripts/` 里的 Python | 纯几何计算，不联网、不调 API |

所以它是一个 **Agent Skill**：给 AI 装上后，你发张照片说「生成答案」就行。脚本本身只是"笔"，单独跑不会自己解题。

## 一键安装（把这句话发给你的 AI）

`SKILL.md` 是 Anthropic 在 2025 年底开放的 **Agent Skills 标准**，现在 Claude Code、Codex、Cursor 2.4+、Gemini CLI、GitHub Copilot、Trae、WorkBuddy、豆包 等 40+ 家都读同一份文件。**复制下面任意一句发给你的 AI，它会自己判断目录并装好**：

```
帮我安装这个 skill：https://github.com/<你的账号>/homework-photo-answer
装到我的个人技能目录（比如 WorkBuddy 是 ~/.workbuddy/skills/、Claude Code 是 ~/.claude/skills/），
不要装进当前项目文件夹。装完告诉我它叫什么名字、怎么调用。
```

> 「装到个人技能目录」这句**别删**——不说的话 AI 常常就近装进你当前打开的文件夹，换个目录干活就找不到了。

各家的技能目录（手动 clone 时用）：

| 客户端 | 目录 |
|---|---|
| WorkBuddy | `~/.workbuddy/skills/` |
| CodeBuddy | `~/.codebuddy/skills/` |
| Claude Code / Cowork | `~/.claude/skills/` |
| Codex CLI | `~/.agents/skills/`（或 `~/.codex/skills/`） |
| Trae | `~/.trae/skills/` |
| Cursor / Copilot / Gemini CLI / Cline / Roo | `.agents/skills/`（项目级） |

### 其他装法

**npx（装到 50+ 个 agent，适合开发者）**
```bash
npx skills add <你的账号>/homework-photo-answer -g -y
npx skills update          # 以后升级
```
用的是 Vercel 开源的 [skills CLI](https://github.com/vercel-labs/skills)（MIT），默认用软链接，一次更新所有 agent 生效。

**上传 ZIP（豆包 / WorkBuddy 客户端）**
豆包：左侧「技能·连接器·伙伴」→ 右上角「+ 新建」→ 上传技能，选打包好的 zip。
WorkBuddy：专家·技能·连接器 → 添加技能 → 上传本地技能包。
两者都要求压缩包里有 `SKILL.md` 且带 YAML 名称/描述——本仓库已满足。打包：
```bash
# 仓库根目录执行，产出的 zip 可直接上传
zip -r homework-photo-answer.zip . -x "*.git*" -x "*.venv*" -x "*.jpg" -x "*.pdf"
```
或在 Releases 里下载现成的 `homework-photo-answer.zip`（见下方「发版」）。

> 豆包还支持一种更懒的方式：直接在对话框发
> `帮我创建技能：https://github.com/<账号>/homework-photo-answer/releases/latest/download/homework-photo-answer.zip`
> 它会自己下载、读 SKILL.md、装好并回报。

### 环境（Python）

技能装好之后，**第一次使用时让 AI 帮你把环境装好即可**——`SKILL.md` 里写了自检流程，AI 会自动检测 Python、缺 Pillow/numpy 就 pip 装、缺中文字体就提示。你不需要手动操作。

想自己装：
```bash
cd scripts
setup.bat          # Windows
bash setup.sh      # macOS / Linux
```
依赖只有两个：**Pillow**、**numpy**，需要 Python 3.10+。

### 字体

渲染中文答案需要中文字体。按平台自动查找，顺序如下：

1. 系统字体：Windows 微软雅黑 / macOS 苹方 / Linux Noto CJK
2. `scripts/assets/` 目录下自带的字体（可放思源黑体等开源字体）

找不到时会打印明确警告。**微软雅黑不能随项目分发**，所以仓库里不放字体文件；若要打包发行，请自行放入 OFL 协议的中文字体（如思源黑体）。

## 用法

本仓库设计为给 AI 助手调用（`SKILL.md` 是给 AI 看的操作手册）。想手动用也可以：

```bash
cd 工作目录                      # 把 scripts/engine.py、render.py 拷进来
cp 你的照片.jpg p051_dk.jpg      # 底图命名必须是 <page>_dk.jpg

# 1. 探测坐标
python -c "
import sys; sys.path.insert(0,'.')
from engine import row_bands, col_groups
from PIL import Image; import numpy as np
a = np.array(Image.open('p051_dk.jpg').convert('L'))
for r in row_bands(a, 10, a.shape[0]-10, 30, 1230, minv=10):
    if r[1]-r[0] >= 8:
        print(r, (r[0]+r[1])//2, col_groups(a, r[0]-1, r[1]+1, 30, 1230, gap=45))
"

# 2. 照探测结果写配置（复制 scripts/cfg_template.py）
# 3. 渲染
python cfg_051.py                # → answer/p051_ans.jpg
# 4. 合 PDF
python mkpdf.py 答案.pdf answer/p051_ans.jpg answer/p052_ans.jpg
```

配置支持 5 类标注：

| 类型 | 用途 |
|---|---|
| `after` | 题目自带 `=` 的口算，答案自动接在等号后 |
| `blocks` | 脱式计算 / 简算，向下写多行过程 |
| `fills` | 括号、圆圈、横线内填空，自动缩字号适配宽度 |
| `notes` | 固定坐标落笔（等号后空间太窄时用） |
| `verts` | 竖式乘法，自动排数位对齐 + 验算 |

## 开源注意事项

- 本仓库**只含代码与方法说明**，不含任何教材扫描件、习题照片或答案图片。
- `.gitignore` 已屏蔽所有图片与 PDF，避免误传孩子的作业照片。
- 代码 MIT 协议，但请注意：教材内容受版权保护，请勿提交或分发教材页面。

## 目录结构

```
SKILL.md                 给 AI 看的操作手册（8 步流程 + 踩坑清单）
README.md                本文件
LICENSE                  MIT
scripts/
  engine.py              行/列墨迹检测：row_bands / col_groups / vlines / rings
  render.py              渲染引擎：after / blocks / fills / notes / verts
  cfg_template.py        配置模板
  mkpdf.py               A4 多页 PDF 合成
  setup.bat / setup.sh   一键装环境
  requirements.txt
references/
  case-log.md            各题型处理方式对照表
```

## 常见问题

**Q：必须装 Python 吗？**
A：目前是。已提供一键脚本，装完之后日常只需一条命令。想做到"零安装"，可以再加一个纯浏览器版本（canvas + JS 实现同样的墨迹检测逻辑）——见 Roadmap。

**Q：支持英语/其他语言吗？**
A：渲染层与语言无关，字体换成西文即可。`SKILL.md` 里的题目说明是中文的，需要的话可自行翻译。

**Q：为什么答案会写歪？**
A：99% 是搜索窗宽度不对。请看 `SKILL.md` 的踩坑第 2 条。

## Roadmap

- [ ] 浏览器版（拖图 → 出图，零安装）
- [ ] 自动透视校正（现在只做旋转，强透视下靠逐行补偿）
- [ ] 竖式除法支持（目前只有乘法）
- [ ] 打包成 Windows 免安装 exe（PyInstaller）
