#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务管理器模块
"""
import time
import datetime
import logging
from typing import List, Optional, Dict, Tuple
from backoff.common.task_entity import TaskEntity, TaskStatus
from backoff.common.backoff_config import StorageConfig
from backoff.repository.storage_adapter import StorageAdapterFactory
from backoff.utils.date_utils import DateUtils
import traceback

logger = logging.getLogger()


class TaskRepository:
    """任务管理器，负责任务的CRUD操作"""

    def __init__(self, biz_prefix: str, storage_config: StorageConfig):
        """
        初始化任务管理器

        Args:
            biz_prefix: 业务前缀
            storage_config: Redis配置
        """
        # 创建适配器
        self.biz_prefix = biz_prefix
        self.adapter = StorageAdapterFactory.create_adapter(biz_prefix, storage_config)

    def create_task(
        self, task_entity: TaskEntity, score: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        创建任务

        Args:
            task_entity: 任务实体（必须包含有效的task_id）
            score: 可选的任务分数（用于排序等场景）

        Returns:
            Tuple[bool, str]: 第一个元素表示是否创建成功，第二个元素为状态消息
        """
        # 1. 参数校验：确保task_id有效
        task_id = task_entity.task_id
        if not task_id:
            error_msg = "任务ID不能为空"
            logger.warning(error_msg)
            return False, error_msg

        try:
            current_time = int(time.time())
            task_entity.create_time = current_time
            task_entity.update_time = current_time

            # 检查任务是否已存在
            if self.adapter.exists(task_id):
                error_msg = f"任务已存在: [{task_id}]"
                logger.warning(error_msg)
                return False, error_msg

            # 存储任务到Redis
            task_data = task_entity.to_redis_dict()
            self.adapter.save_task(task_id, task_data, score)
            
            success_msg = f"任务创建成功: [{task_id}]"
            logger.info(success_msg)
            return True, success_msg

        except Exception as e:
            error_msg = f"创建任务失败: [{task_id}], 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    def get_task(self, task_id: str) -> Optional[TaskEntity]:
        try:
            task_data = self.adapter.fetch_task_details(task_id)
            if not task_data:
                # logger.error(f"任务不存在: [{task_id}]")
                return None

            return task_data
        except Exception as e:
            logger.error(f"获取任务失败: [{task_id}], 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return None

    def update_task(self, task_entity: TaskEntity) -> bool:
        """更新任务"""
        try:
            self.adapter.updata_task(task_entity.task_id, task_entity)
            return True
        except Exception as e:
            logger.error(f"更新任务失败: {task_entity.task_id}, 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return False

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否删除成功
        """
        try:
            # 从各个队列中移除任务
            self.adapter.remove_task_from_pending_queue(task_id)
            self.adapter.remove_task_from_processing_queue(task_id)
            # self.adapter.remove_task_from_completed_queue(task_id)
            # self.adapter.remove_task_from_failed_queue(task_id)

            # 删除任务数据
            self.adapter.delete_task(task_id)

            logger.info(f"任务删除成功: [{task_id}]")
            return True

        except Exception as e:
            logger.error(f"删除任务失败: [{task_id}], 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return False

    def get_pending_taskIds(self, batch_size: int) -> List[str]:
        """
        获取待处理任务

        Args:
            batch_size: 获取数量限制
            service_instance_id: 服务实例ID，如果指定则只返回属于该实例的任务

        Returns:
            List[str]: 待处理任务ID列表
        """
        try:
            task_ids_with_scores = self.adapter.batch_fetch_pending_tasks(batch_size)
            task_ids = [task_id for task_id, score in task_ids_with_scores]

            return task_ids
        except Exception as e:
            logger.error(f"获取待处理任务失败: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return []

    def mark_task_processing(self, task_id: str) -> bool:
        """标记任务为处理中"""
        try:
            task = self.get_task(task_id)
            if not task:
                return False

            # 更新任务状态
            task.update_status(TaskStatus.PROCESSING)
            self.update_task(task)

            # 从添加到处理中队列
            self.adapter.add_task_to_processing_queue(task_id)

            return True

        except Exception as e:
            logger.error(f"标记任务处理中失败: [{task_id}], 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return False

    def mark_task_completed(self, task_id: str, result: str = "") -> bool:
        """
        标记任务为已完成

        Args:
            task_id: 任务ID
            result: 任务结果

        Returns:
            bool: 是否标记成功
        """
        try:
            task = self.get_task(task_id)
            if not task:
                return False

            # 更新任务状态和结果
            task.update_status(TaskStatus.COMPLETED)
            task.update_result(result)
            task.process = 100
            self.update_task(task)

            # 从处理中队列移动到已完成队列
            self.adapter.remove_task_from_pending_queue(task_id)
            self.adapter.remove_task_from_processing_queue(task_id)
            self.adapter.add_task_to_completed_queue(task_id)

            return True

        except Exception as e:
            logger.error(f"标记任务已完成失败: [{task_id}], 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return False

    def mark_task_canceled(self, task_id: str, result: str = "") -> bool:
        """
        标记任务为取消

        Args:
            task_id: 任务ID
            result: 取消原因

        Returns:
            bool: 是否标记成功
        """
        try:
            task = self.get_task(task_id)
            if not task:
                return False

            task.update_result(result)

            # 从处理中队列移除
            self.adapter.remove_task_from_processing_queue(task_id)
            self.adapter.remove_task_from_pending_queue(task_id)
            task.update_status(TaskStatus.CANCELED)
            self.update_task(task)
            return True
        except Exception as e:
            logger.error(f"标记任务已取消失败: [{task_id}], 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return False

    def mark_task_failed(self, task_id: str, result: str = "") -> bool:
        """
        标记任务为失败

        Args:
            task_id: 任务ID
            result: 失败原因

        Returns:
            bool: 是否标记成功
        """
        try:
            task = self.get_task(task_id)
            if not task:
                return False

            # 增加重试次数
            task.increment_retry()
            task.update_result(result)

            # 从处理中队列移除
            self.adapter.remove_task_from_processing_queue(task_id)

            if task.can_retry():
                # 计算下次执行时间并重新加入待处理队列
                task.next_execution_time = task.calculate_next_execution_time()
                task.update_status(TaskStatus.PENDING)
                self.update_task(task)
                self.adapter.add_task_to_pending_queue(task_id)

            else:
                # 达到最大重试次数，标记为失败
                task.update_status(TaskStatus.FAILED)
                self.update_task(task)
                self.adapter.add_task_to_failed_queue(task_id)
                self.adapter.remove_task_from_pending_queue(task_id)
                logger.warning(
                    f"任务 [{task_id}] 已达到最大重试次数: {task.retry_count}, result: {result}"
                )

            return True

        except Exception as e:
            logger.error(f"标记任务失败: [{task_id}], 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return False

    def update_task_progress(self, task_id: str, progress: int) -> bool:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度(0-100)

        Returns:
            bool: 是否更新成功
        """
        try:
            task = self.get_task(task_id)
            if not task:
                return False

            task.update_process(progress)
            self.update_task(task)
            logger.info(f"任务 [{task_id}] 进度更新成功: {progress}%")
            return True

        except Exception as e:
            logger.error(f"更新任务进度失败: [{task_id}], 错误: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return False

    def get_queue_statistics(self) -> Dict[str, dict]:
        """
        获取队列统计信息，返回指定格式的JSON结构数据

        Returns:
            Dict[str, dict]: 包含系统状态和任务统计的字典
        """
        current_time = DateUtils.format_timestamp(time.time())
        try:
            pending_queue: List[str] = self.adapter.queue_members(
                self.adapter.pending_queue_key
            )
            processing_queue: List[str] = self.adapter.queue_members(
                self.adapter.processing_queue_key
            )
            # completed_queue: List[str] = self.adapter.queue_members(
            #     self.adapter.completed_queue_key
            # )
            failed_queue: List[str] = self.adapter.queue_members(
                self.adapter.failed_queue_key
            )
            return {
                "system_status": {"update_time": current_time},
                "tasks": {
                    TaskStatus.PENDING.value: {
                        "total": len(pending_queue),
                        "queue": pending_queue,
                    },
                    TaskStatus.PROCESSING.value: {
                        "total": len(processing_queue),
                        "queue": processing_queue,
                    },
                    # TaskStatus.COMPLETED.value: {
                    #     "total": len(completed_queue),
                    #     "queue": completed_queue,
                    # },
                    TaskStatus.FAILED.value: {
                        "total": len(failed_queue),
                        "queue": failed_queue,
                    },
                },
            }
        except Exception as e:
            logger.error(f"获取队列统计失败: {str(e)}, 详细错误信息: {traceback.format_exc()}")
            return {
                "system_status": {"update_time": current_time},
                "tasks": {
                    TaskStatus.PENDING.value: {"total": 0, "queue": []},
                    TaskStatus.PROCESSING.value: {"total": 0, "queue": []},
                     TaskStatus.FAILED.value: {"total": 0, "queue": []},
                },
            }
