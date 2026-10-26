---
name: homework-photo-answer
description: 手机拍的练习册/试卷照片，自动识别题目位置并把答案（含脱式分步过程、竖式、简算技巧）用红字直接标注在图上，可裁剪扶正、可合并成 A4 PDF。触发词：练习册标答案、作业拍照写答案、把答案写在图上、口算/脱式/竖式/简算答案生成、试卷答案标注、拍照作业改答案。
---

# 练习册照片自动标答案

把「手机拍的练习册照片」变成「答案已经写在题上的图」。核心思路：**答案落笔位置靠墨迹检测自动定位，不靠目测坐标**，所以照片有透视、倾斜也能对齐。

## 首次使用：环境自检（必须先做，别跳过）

用户第一次让你标答案时，**先跑这段自检**，缺什么就补什么，补完再进入流程。不要假设对方已经装好 Python。

1. 找一个能用的 Python（按顺序试，第一个成功的就是它）：
   - Windows：`py -3`、`python`、`python3`
   - macOS / Linux：`python3`、`python`
   - 本机若已有托管环境（如 WorkBuddy 的 `binaries/python/envs/default`）优先用它
2. 检查依赖，缺了就装：
   ```bash
   <python> -c "import PIL, numpy; print('ok')"
   # 失败则：
   <python> -m pip install pillow numpy
   ```
   pip 装不动（网络/权限）时：改用虚拟环境 `python -m venv .venv` 再装；国内网络可加
   `-i https://pypi.tuna.tsinghua.edu.cn/simple`（个别受限环境只能用默认源，报错就换回来）。
3. 中文字体检查：`render.py` 会按系统自动找（Windows 微软雅黑 / macOS 苹方 / Linux Noto CJK），
   找不到会打印警告。出现警告就把任意中文字体放进 `scripts/assets/`。

**后面所有 `<python>` 都替换成第 1 步得到的命令**，不要写死任何本机绝对路径。

## 准备

在工作区建一个目录（例如 `<workspace>/homework/`），把 `scripts/engine.py` 和 `scripts/render.py` 拷进去。后续所有命令都在这个目录里跑。

## 流程

### 1. 判断朝向
先看图：文字是竖着读的 → 需要旋转 90°。生成两个方向各一张确认，别猜：
```python
from PIL import Image
im = Image.open(SRC)
im.rotate(90,  expand=True).thumbnail((1000,1000))  # 逆时针
im.rotate(-90, expand=True)...                       # 顺时针
```
**旋转必须写 `fillcolor=(255,255,255)`**，否则四角是黑的，出 PDF 会有黑三角。

### 2. 扶正 + 裁掉背景
先肉眼判断照片里除了页面还有什么（墙、桌面、卡片）。若有背景，**倾斜角自动估计会被背景带偏**（行投影方差指标会打到搜索区间边界）。

- 桌面平铺翻拍：通常本来就不歪，跳过扶正。
- 手持斜拍：只在**正文 x 区间内**算角度才准：
```python
for ang in np.arange(-6, 6.01, 0.25):
    a = np.array(im.rotate(float(ang), resample=Image.BILINEAR).convert('L'))
    prof = (a[y0:y1, x0:x1] < 120).sum(axis=1).astype(float)
    score = (prof ** 2).sum()   # 取最大
```
然后裁掉背景：取页面四边（用缩略图 + 网格目测即可），存成 `<page>_dk.jpg`（文件名必须是 `<page>_dk.jpg`，render 靠它找底图）。

### 3. 探测坐标（这一步不能省）
**不要靠缩略图目测换算坐标**——缩放比算错会整体偏移 20~100px。用脚本扫全页：
```python
import sys; sys.path.insert(0,'.')
from engine import row_bands, col_groups
from PIL import Image
import numpy as np
a = np.array(Image.open('p051_dk.jpg').convert('L'))
for r in row_bands(a, 10, a.shape[0]-10, 30, 1230, minv=10):
    if r[1]-r[0] >= 8:
        print(r, 'c=', (r[0]+r[1])//2, col_groups(a, r[0]-1, r[1]+1, 30, 1230, gap=45))
```
得到：每行的 y 中心、每行内各栏的 [x0,x1]。再裁几个高倍放大图核对题目文字（必须逐题读准，别凭印象）。

### 4. 算答案并用 Python 复核
所有得数都跑一遍 `print()` 验证；排列组合/凑 24 点这类"最优"题直接 `itertools.permutations` 暴力枚举。

### 5. 写配置
复制 `scripts/cfg_template.py` → `cfg_<page>.py`，填 5 类标注：

| 类型 | 用途 | 格式 |
|---|---|---|
| `after` | 题目自带 `=` 的口算/写得数 | `(y, 窗x0, 窗x1, 答案[, 字号])` |
| `blocks` | 脱式/简算的分步过程 | `(x, y, [逐行], 字号, 行距)` |
| `fills` | 括号/圆圈/横线内填空，自动缩字号 | `(中心x, 中心y, 文本, 最大宽)` |
| `notes` | 固定坐标左对齐（等号后空间太窄时用） | `(x, y, 文本, 字号)` |
| `verts` | 竖式乘法（含验算） | `(算式行y, x0, x1, 被乘数, 乘数, 竖式顶y, 底y, 验算/None)` |

### 6. 渲染
`python cfg_<page>.py` → 输出 `answer/<page>_ans.jpg`。改坐标只需重跑，秒级。

### 7. 目视核对（必做）
裁成 2~3 张放大图逐块检查：答案有没有压字、有没有串行、有没有顶到下一栏、有没有超出纸面。发现偏移就改配置重跑。

### 8. 交付
拷贝到成果目录并存 JPG（quality=95, dpi=300）；需要打印就跑 `scripts/mkpdf.py` 合 A4 多页 PDF。

## 排版规则

- **字号**：印刷字高约 30px → 答案 40；过程行 38~40、行距 54；窄处降到 34~36。长式子先量宽：
```python
ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 38).getlength('= (90+3)+(90-2)+...')
```
- **栏宽约束**：`(25×4)×(105×6)` 这类长步骤，40 号会顶到下一栏（实测 371px vs 栏宽 386px），降到 38 才留空隙。
- **脱式题目本身没有印 `=`**：不要在其末尾补裸数字，只在下方写 `= 步骤` 链，最后一行就是答案。
- **竖式/验算**：★ 题在竖式右侧写 `验算：<积>÷<乘数>=<被乘数>`。

## 踩过的坑

1. `rotate()` 不写 `fillcolor` → 四角黑块（PDF 里很难看）。
2. `ink_right` 的**搜索窗宽度决定成败**：给窄了会把答案写进算式中间（光标落到算式最后一个字符），给宽了会吃到下一栏/分隔线。**每个窗必须贴着该栏的 col_groups 结果给**。
3. 倾斜角估计被背景污染时，会返回搜索区间边界值（-20 之类），此时**不要用**该角度，改用局部 x 区间重算或直接跳扶正。
4. 缩略图上目测坐标会算错缩放比 —— 一切坐标以脚本探测为准。
5. 括号填空空间常常只有 190px 左右：用**半角括号** `(7-5)×(8+4)=24` 能上 24 号字，全角只能到 20 号，明显偏小。
6. 页面有轻微透视（左右两栏文字 y 相差 20px）是正常版式错位，不是没扶正；`row_center` 会逐行校正，不用管。

## 参考案例

`references/case-log.md` 记录了 034/041/042/043/044/046/047/051/052 各页的题型与处理要点，新页可对照参考。
