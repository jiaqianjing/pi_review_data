## 任务描述
读取 ./reviewed_clips_2026-04-20.csv 分析并按照如下处理：

# 字段说明
1. #: 序号
2. Clip ID: 视频片段ID
3. Camera SN: 摄像头序列号
4. Env: 表示视频片段存放的来源在不同 aws 的部署环境；
5. Region: aws s3 的 region
6. S3 URL: 存放在 aws s3 的视频 url
7. Reviewer: 标注人员
8. Review Time: 标注时间
9. Label ID: 标注 ID，唯一标识样本的标签;例如：`event_collision_02_004` 指的是这是 event_collision 标注任务，Label L1=02, Label L2=004;
10. Label L1: 标注的一级标签，其中 "Non-Collision Detected" 表示 no_collision, "Collision Detected" 表示 collision;
11. Label L2: 标注的二级标签;
12. Label L3: 标注的三级标签;
13. Label L4: 标注的四级标签;

## 其他说明
1. 数据上游来源：api 和 gpst 环境的 pi，fcw，severe brake 事件;
2. Clip ID,Camera SN,Env 唯一确定一个视频; 
3. 视频存放在 aws  s3 上；
4. api 环境对应 aws region：us-east-1,  gpst 环境对应 aws region: us-east-2;
5. 当前机器已经赋予 IAM Role 可以通过 aws sdk 或 aws cli 访问 aws s3;

# 基础视频数据信息
1. 数据格式 .mp4
2. fps=15
3. duration=10s～16s 左右
4. 视频生成的方式，一般是事件触发时，会保存事件发生前后 5s 或者 前 7s 后 8s 的视频（不一定准确，大致是这样）。事件一般指的的 dashcamera 捕捉到的 G 值猛烈变化定义的事件；

## 任务
1. 跳过 "Label L1" == "Indeterminate Collision Detection" 的所有记录；
2. 下载视频到本地的命名格式：{env}-{sn}-{clipid}.mp4;
###  输出文件
1. train set 结果存放文件：waylens-train-collision-v3/meta.csv
2. train set video 存放目录：waylens-train-collision-v3/videos/
3. train set 说明文件：waylens-train-collision-v3/README.md




