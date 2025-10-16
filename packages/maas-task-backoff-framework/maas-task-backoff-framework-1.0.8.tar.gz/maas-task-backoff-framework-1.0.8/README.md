# 任务退避重试、调度框架

[![Python](https://img.shields.io/badge/Python-3-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个基于Redis的分布式任务退避重试、调度框架，支持多种退避策略和并发执行。

## ✨ 核心特性

- 🔄 **多种退避策略**: 固定间隔、指数退避、线性退避
- 🚀 **高并发执行**: 支持线程池/进程池并发处理
- 📊 **任务优先级**: 支持任务优先级管理
- ⏱️ **超时控制**: 任务执行超时和失败处理
- 📈 **状态监控**: 完整的任务状态管理和监控
- 🎯 **灵活调度**: 可配置的定时调度间隔
- 🔒 **分布式锁**: 基于Redis的分布式任务队列
- 💾 **存储方式**: 目前只支持 Redis，后续会增加MySQL、达梦数据库等支持

## 📚设计思路


### 业务架构设计

![](http://fire-blog.oss-cn-beijing.aliyuncs.com//images/20250909113017.png)

### 退避工具内部组件设计


![](http://fire-blog.oss-cn-beijing.aliyuncs.com//images/20250909113043.png)

### 设计类图

![](http://fire-blog.oss-cn-beijing.aliyuncs.com//images/20250909113102.png)

### 调用时序图

用户提交task

![](http://fire-blog.oss-cn-beijing.aliyuncs.com//images/20250909113117.png)

调度执行task

![](http://fire-blog.oss-cn-beijing.aliyuncs.com//images/20250909113543.png)

## 📦 安装

```bash
pip install maas-task-backoff-framework
```

## 🚀 快速开始

### 使用示例

```python
from backoff.scheduler.backoff_scheduler import (
    TaskBackoffScheduler,
    TaskBackoffConfig,
    TaskEntity,
    TaskConfig,
    StorageConfig,
    ThreadPoolConfig,
    SchedulerConfig,
    ResultEntity,
)

# 1. 创建配置
config = TaskBackoffConfig()

# Redis存储配置
config.storage = StorageConfig(
    type="redis", 
    host="localhost", 
    port=6379, 
    database=0, 
    password=""
)

# 任务配置
config.task = TaskConfig(
    biz_prefix="my_service",
    batch_size=10,
    max_retry_count=3,
    backoff_strategy="exponential",
    backoff_interval=30,
    backoff_multiplier=2.0,
    min_gpu_memory_gb=0.5,
    min_gpu_utilization=10
)

# 线程池配置
config.threadpool = ThreadPoolConfig(
    concurrency=5, 
    exec_timeout=300, 
    proc_mode="process"
)

# 调度器配置
config.scheduler = SchedulerConfig(interval=10)

# 2. 创建调度器
scheduler = TaskBackoffScheduler(config)

# 3. 定义任务处理器
def task_handler(task: TaskEntity):
    # 您的业务逻辑
    print(f"处理任务: {task.task_id}")
    return ResultEntity.ok(
        result={"status": "success", "data": "处理完成"},
        task_id=task.task_id,
    )

def exception_handler(task: TaskEntity):
    # 异常处理逻辑
    return ResultEntity.fail(
        code=-1,
        message="任务执行失败",
        task_id=task.task_id,
    )

# 4. 注册处理器
scheduler.set_custom_task_handler(task_handler)

scheduler.set_custom_task_exception_handler(exception_handler)

# 5. 启动调度器（如果不需要启动调度器，请忽略此步骤，只提供基础的Task API操作）
scheduler.start()
```

## 💻 Task任务数据结构

```python
{
    "task_id": "task_5775520148",
    "process": 0,
    "status": "pending",
    "result": "",
    "param": "{\"index\": 111, \"data\": \"test_data\"}",
    "retry_count": 0,
    "next_execution_time": 0,
    "create_time": 1756695076,
    "update_time": 1756695076,
    "max_retry_count": 5,
    "backoff_strategy": "fixed",
    "backoff_interval": 60,
    "backoff_multiplier": 2.0,
    "min_gpu_memory_gb": 0,
    "min_gpu_utilization": 0.0,
    "biz_prefix": "custom_scheduling_example"
}
```

结果字段说明

|字段     | 类型   |  说明           |
|----------|--------|----------------|
| task_id     | string |  任务唯一id     |
| biz_prefix     | string |  任务的业务前缀    |
| process     | int |  任务进度  |
| status     | string    |  任务状态      |
| result | string    | 任务的执行结果    |
| param | string |   任务的参数      |
| retry_count | int |   重试次数      |
| next_execution_time | int |   下次执行时间 |
| create_time | int |   创建时间      |
| update_time | int |   更新时间      |
| max_retry_count | int |   最大重试次数      |
| backoff_strategy | string |   退避类型      |
| backoff_interval | int |   退避间隔      |
| backoff_multiplier | int |      退避倍数   |
| min_gpu_memory_gb | int |      需要的最小GPU内存   |
| min_gpu_utilization | int |      需要的最小GPU使用率   |


## 📚 API 参考

### 任务管理

#### 1.创建任务

创建任务可选权重值 `score` , 不传默认会以为当前时间为权重值先进先出；`score` 越小越先执行

```python
scheduler.create_task(
    task_params={"key": "value"},
    task_id="unique_task_id",
    score=100
) -> Tuple[bool, message: str]
```

参数字段说明
| 字段     | 类型 | 必填   |  说明           |
|----------|--------|--------|----------------|
| task_params     |是| dict |  任务的业务参数     |
| task_id     | 是 |string |  自定义的任务id    |
| score     |否| int |  权重值（不传默认会以为当前时间为权重值先进先出；越小越先执行）  |


#### 2.查询任务

```python
scheduler.get_task(task_id) -> TaskEntity
```

#### 3.撤销任务

- 线程模式下撤销任务仅会变更任务状态为 `canceled`，等待任务执行完成

- 进程模式下会直接取消正在运行中的任务并变更任务状态

```python
scheduler.cancel_task(task_id) -> Tuple[bool, str]:
```

#### 4.获取队列统计

```python
scheduler.get_queue_statistics() -> Dict[str, int]:
```

队列统计结构返回结果示例

```python
{
    "system_status": {
        "update_time": "2025-09-01 15:30:13"
    },
    "tasks": {
        "PENDING": {
            "total": 34,
            "queue": [
                "task_2728059290",
                "task_2829088805"
            ]
        },
        "DOING": {
            "total": 0,
            "queue": []
        },
        "DONE": {
            "total": 0,
            "queue": []
        },
        "FAILED": {
            "total": 0,
            "queue": []
        }
    }
}
```

字段说明
| 字段     | 类型   |  说明           |
|----------|--------|----------------|
| update_time     | string |  请求时间    |
| tasks     | object |  任务队列统计      |
| PENDING     | object |  等待队列      |
| DOING     | object |  处理中队列      |
| DONE     | object |  已完成队列      |
| FAILED     | object |  失败队列      |
| total     | int  |  任务队列成员总数      | 
| queue     | list |  任务成员列表      |


### 5.更任务状态

```python
# 标记任务完成
scheduler.mark_task_completed(task_id, "执行结果") -> bool

# 标记任务失败
scheduler.mark_task_failed(task_id, "失败原因") -> bool

# 标记任务处理中
scheduler.mark_task_processing(task_id) -> bool
```

### 6.更新任务进度

```python
# 更新任务进度
scheduler.update_task_progress(task_id, 75) -> bool # 75%
```

### 7.调度器控制

如果不显示执行 `scheduler.start()` 则不会启动定时调度，只提供 Task API 的基础操作

```python
# 启动调度器
scheduler.start()

# 关闭调度器
scheduler.shutdown()
```

### 8.处理器管理

- 任务处理器 ( `set_custom_task_handler` ): 可选设置，处理正常的业务逻辑
  
- 异常处理器 ( `set_custom_task_exception_handler` ): 可选设置，处理任务执行过程中的异常情况

```python
# 注册任务处理器（可选）
scheduler.set_custom_task_handler(task_handler)

# 注册异常处理器（可选）
scheduler.set_custom_task_exception_handler(exception_handler)
```

**处理器函数签名**

处理器参数必须为 `TaskEntity` ，响应类型必须为 `ResultEntity`

```python
from backoff.scheduler.backoff_scheduler import (
    TaskEntity,
    ResultEntity,
)
def task_handler(task: TaskEntity) -> ResultEntity:
    # 您的业务逻辑
    pass

def exception_handler(task: TaskEntity) -> ResultEntity:
    # 异常处理逻辑
    pass
```

#### 返回值示例

**成功处理:**

```python
return ResultEntity.ok(
    result={"status": "success", "data": "处理结果"},
    task_id=task.task_id,
)
```

**失败处理:**
```python
return ResultEntity.fail(
    code=-1,
    message="任务执行失败",
    result={"error": "具体错误信息"},
    task_id=task.task_id,
)
```


## ⚙️ 配置详解

### StorageConfig (存储配置)

| 参数     | 类型   | 必填 | 默认值    | 说明           |
|----------|--------|------|-----------|----------------|
| type     | string | 是   | redis     | 存储类型，目前仅支持Redis      |
| host     | string | 是   |  localhost| Redis主机地址  |
| port     | int    | 是   | 6379      | Redis端口      |
| database | int    | 否   | 0         | Redis数据库    |
| password | string | 否   | ""        | Redis密码      |

**type 存储类型:**

- `redis` : 默认
- `mysql` : 暂未支持
- `达梦` : 暂未支持

### TaskConfig (任务配置)

| 参数                | 类型   | 必填 | 默认值        | 说明                    |
|---------------------|--------|------|---------------|-------------------------|
| biz_prefix          | string | **是**   | -         | 业务唯一标识               |
| max_retry_count     | int    | 否   | 3             | 最大重试次数            |
| backoff_strategy    | string | 否   | exponential   | 退避策略                |
| backoff_interval    | int    | 否   | 30            | 初始退避间隔(秒)        |
| backoff_multiplier  | float  | 否   | 2.0           | 退避倍数                |
| batch_size          | int    | 否   | 100           | 批次大小                |
| min_gpu_memory_gb   | float  | 否   | 0             | 最小GPU内存(GB)         |
| min_gpu_utilization | int    | 否   | 0             | 最小GPU利用率(%)        |

**backoff_strategy 退避策略说明:**

- `exponential` : 指数退避 (默认)
- `fixed` : 固定间隔重试
- `linear` : 线性退避

### ThreadPoolConfig (线程池配置)

| 参数          | 类型   | 必填 | 默认值 | 说明                    |
|---------------|--------|------|--------|-------------------------|
| concurrency   | int    | 否   | 10     | 并发线程/进程数         |
| proc_mode     | string | 否   | process | 执行模式                |
| exec_timeout  | int    | 否   | 300    | 任务超时时间(秒)        |

**proc_mode 执行模式说明:**

- `thread` : 线程池模式
- `process` : 进程池模式 (默认)

线程池模式，一旦线程启动后，线程将会持续运行，直到执行完毕，线程将被回收。

进程池模式，如果进程内业务异常或者超时等待，进程将被收回。

### SchedulerConfig (调度器配置)

| 参数     | 类型 | 必填 | 默认值 | 说明           |
|----------|------|------|--------|----------------|
| interval | int  | 否   | 10     | 轮询间隔(秒)   |



