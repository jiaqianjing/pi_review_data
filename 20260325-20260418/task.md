# 任务描述
帮我分析 ./reviewed_clips_2026-04-18.csv 仔细分析这个数据的 meta 信息，我要用于碰撞检测模型的任务，现在需要专门提取一个 eval 数据，用于评估模型效果.

# meta 字段
1. #: 序号
2. Clip ID: 视频片段ID
3. Camera SN: 摄像头序列号
4. Env: 记录视频存放 aws s3 的 region，目前：api => us-east-1, gpst => us-east-2
5. Region: aws s3 的 region
6. S3 URL: 存放在 aws s3 的视频 url
7. Reviewer: 标注人员
8. Review Time: 标注时间
9. Label ID: 标注 ID，唯一标识样本的标签;例如：`event_collision_02_004` 指的是这是 event_collision 标注任务，Label L1=02, Label L2=004;
10. Label L1: 标注的一级标签
11. Label L2: 标注的二级标签
12. Label L3: 标注的三级标签
13. Label L4: 标注的四级标签


# 基础视频数据信息
1. 数据格式 .mp4
2. fps=15
3. duration=10s 左右
4. 视频生成的方式，一般是事件触发时，会保存事件发生前后 5s 的视频（不一定准确，大致是这样）。事件一般指的的 dashcamera 捕捉到的 G值猛烈变化定义的事件；

# 首要任务 eval set 划分
1. 提取样本数：5050 个；
2. 正样本：50 个，label 为 collision；
3. 负样本：5000 个，label 为 no_collision；
4. 按子标签的比例分层抽取，保证数据多样性，保证数据集涵盖每一个子类；

# 次要任务 train set 划分
1. 保证 eval set 划分后的剩余的数据，全部划分给 train set；

# 输出文件
1. eval set 结果存放文件：waylens-eval-collision-v2.csv
2. eval set 说明文件：waylens-eval-collision-v2.md
3. train set 结果存放文件：waylens-train-collision.csv
4. train set 说明文件：waylens-train-collision.md


# 备注
1. 除了 Label L1 ，可以将其与层级标签都当作场景标签或者 tag 理解；
2. 数据集说明文件主要用于下游训练任务理解数据，尽可能描述的简洁、准确、不遗漏重点，便于 LLM 快速理解数据。
3. 剩余的数据全部划分给 train set。

# 补充说明（2026-04-18 确认）
1. "Indeterminate Collision Detection"（共 9 条）直接忽略，不参与 eval / train 划分；
2. 优先保证 eval set 的数量和质量，train set 是增量的，后续还有其他样本补充；
3. 正样本（Collision Detected）按 L2+L3 组合做分层抽样，保证每种碰撞子类型都被覆盖；
4. 负样本（Non-Collision Detected）按 L2 级别做分层抽样；
