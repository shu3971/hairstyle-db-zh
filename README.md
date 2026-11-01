# 发型图库 · HAIR-DB-01

中文 AI 发型参考图库 · 男发 15 款 + 女发 15 款 · 纯 AI 生成 · MIT 开源

## 在线浏览

GitHub Pages: https://shu3971.github.io/hairstyle-db-zh/

## 特性

- 🔍 中英文实时检索（背头 / bob / curly …）
- 🚻 性别分类筛选（男发 / 女发）
- 🖼️ 大图灯箱预览 + 下载原图
- ⚡ 零依赖纯静态站点（单 HTML + data.js）
- 🤖 所有图像均为 AI 生成（人物不入镜视角设计），无版权风险

## 数据结构

`data.js` 每条记录：

| 字段 | 说明 |
|---|---|
| `id` | 编号（如 `hair-male-00`） |
| `gender` | male / female |
| `style` / `style_zh` | 发型英文 key / 中文名 |
| `angle` / `angle_zh` | 视角（后侧45° / 正侧面 / 后脑俯拍） |
| `keywords` | 英文描述关键词 |
| `thumb` / `img` | 缩略图 / 原图路径 |

## 持续扩量

发型矩阵在持续扩充中，当前 V1 为 30 张样图。扩量脚本通过 SimpAI Studio 本地引擎（Z-imageT）批量生成。

## License

MIT
