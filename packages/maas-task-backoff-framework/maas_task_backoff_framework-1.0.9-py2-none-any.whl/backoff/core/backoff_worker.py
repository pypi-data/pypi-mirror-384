#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
任务工作器模块
"""
import logging
from concurrent.futures import TimeoutError as FutureTimeoutError
from math import log
from typing import Optional, Dict, Any, Callable, Tuple, Union, List
from backoff.common.task_entity import TaskEntity, TaskStatus
from backoff.core.task_repository import TaskRepository
from backoff.models.backoff_threadpool import BackoffThreadPool
from backoff.common.result_entity import ResultEntity
from backoff.common.error_code import ErrorCode
from backoff.utils.gpu_utils import get_gpu_utils
from backoff.utils.serialize_data_utils import dumps_data, load_parse_params
from backoff.common.backoff_config import StorageConfig
from backoff.models.redis_lock import acquire_lock, release_lock, RedisDistributedLock
from concurrent.futures import CancelledError
import traceback

logger = logging.getLogger()


def execute_task(
    task_handler: Optional[Callable], task_entity: "TaskEntity"
) -> ResultEntity:
    """
    统一的任务执行函数，支持线程池和进程池。
    注意：禁止在子进程内访问不可序列化的状态（如锁、连接等）。
    """
    task_id = task_entity.task_id
    try:
        # 执行任务
        if task_handler:
            result_obj = task_handler(task_entity)
            logger.info(f"任务 [{task_id}] 执行, 结果: {result_obj.success}")
            return result_obj

        return ResultEntity.res(
            success=False,
            code=-1,
            result="task_handler未设置",
            task_id=task_id,
            message="",
        )

    except Exception as e:
        error_msg = f"execute_task 任务执行失败: {str(e)}"
        logger.error(
            f"任务 [{task_id}] , {error_msg}, 详细错误信息: {traceback.format_exc()}"
        )
        return ResultEntity.fail(
            ErrorCode.TASK_EXECUTE_FAILURE.code, error_msg, None, task_id
        )


class BackoffWorker:
    """任务工作器，负责执行具体的任务"""

    def __init__(
        self,
        task_repository: TaskRepository,
        backoff_threadpool: Optional[BackoffThreadPool] = None,
        task_handler: Optional[Callable] = None,
        task_exception_handler: Optional[Callable] = None,
        task_timeout: int = 300,
        storageConfig: Optional[StorageConfig] = None,
    ):
        """
        初始化任务工作器

        Args:
            task_repository: 任务管理器
            backoff_threadpool: 线程池管理器
            task_handler: 任务处理函数
            task_timeout: 任务超时时间(秒)
        """
        self.task_repository = task_repository
        self.backoff_threadpool = backoff_threadpool
        self.task_handler = task_handler
        self.task_exception_handler = task_exception_handler
        self.task_timeout = task_timeout
        self.gpu_utils = get_gpu_utils()
        self.storageConfig = storageConfig

        # 添加一个字典来存储任务ID与future的映射
        self.running_futures = {}  # {task_id: future}

    def execute_batch_tasks(self, pending_task_ids: List[str]) -> None:
        """
        批量执行任务

        Args:
            tasks: 任务列表

        Returns:
            list[Dict[str, Any]]: 执行结果列表
        """
        if not self.backoff_threadpool:
            logger.warning("执行任务未初始化线程池")
            return

        futures = []
        locks_by_task_id: dict[str, RedisDistributedLock] = {}

        for task_id in pending_task_ids:

            task_entity = self.task_repository.get_task(task_id)
            if not task_entity:
                # 任务不存在，则从队列中删除
                self.task_repository.delete_task(task_id)
                continue

            can_execute_task = self.can_execute_task(task_entity)
            if can_execute_task == False:
                continue

            lock_key = f"{task_entity.biz_prefix}:lock:{task_id}"

            lock = acquire_lock(
                key=lock_key,
                blocking=False,
                ttl_seconds=self.task_timeout * 2,
                config=self.storageConfig,
            )
            if lock:
                locks_by_task_id[task_id] = lock
                # 统一标记为处理中
                self.task_repository.mark_task_processing(task_id)

                future = self.backoff_threadpool.submit_task(
                    execute_task, self.task_handler, task_entity
                )

                # 将future添加到映射字典中
                self.running_futures[task_id] = future
                logger.debug(f"任务 [{task_id}] 添加 running_futures中")
                futures.append((task_entity, future))

        # 收集结果
        for task_entity, future in futures:

            task_id = task_entity.task_id
            lock = locks_by_task_id.get(task_id)
            try:
                # 进程模型：依赖进程池 schedule 的超时以确保超时后终止子进程
                if self.backoff_threadpool.is_process_model():
                    result = future.result()
                else:
                    # 线程模型：使用本地超时控制
                    result = future.result(timeout=self.task_timeout)
                # 统一处理结果
                if result.success:
                    result_str = dumps_data(result.result)
                    self.task_repository.mark_task_completed(task_id, result_str)
                else:
                    result_str = dumps_data(result.message) + dumps_data(result.result)
                    self.task_repository.mark_task_failed(task_id, result_str)

            except CancelledError as e:
                error_message = f"任务 [{task_id}] 已被取消"
                logger.error(error_message)
                self.task_repository.mark_task_canceled(task_id, error_message)

            except FutureTimeoutError as e:
                error_message = (
                    f"任务 [{task_id}] 执行超时 {self.task_timeout} 秒, 异常: {str(e)}"
                )
                logger.error(error_message)
                self.task_repository.mark_task_failed(task_id, error_message)
                self._cancel_future(task_id, future)

            except Exception as e:
                error_message = f"任务 [{task_id}] 执行异常: {str(e)}，异常类型: {type(e)}, 详细错误信息: {traceback.format_exc()}"
                logger.error(error_message)
                # 异常时标记失败，并触发异常处理器
                self.task_repository.mark_task_failed(task_id, error_message)
                self._cancel_future(task_id, future)

                if self.task_exception_handler:
                    self.execute_exception_handler(task_entity)

            finally:
                if lock:
                    release_lock(lock)
                    locks_by_task_id.pop(task_id, None)

                # 从映射字典中移除已完成的future
                logger.debug(f"任务 [{task_id}] 从 running_futures 中移除")
                self.running_futures.pop(task_id, None)

    def _cancel_future(self, task_id: str, future: object) -> bool:
        """取消future并返回是否成功取消"""
        try:
            if future and not future.done():
                cancel_result = future.cancel()
                if cancel_result:
                    logger.warning(f"任务 [{task_id}] 已被取消")
                    return True
            return False
        except Exception as e:
            logger.warning(
                f"取消任务 [{task_id}] 失败: {e}, 详细错误信息: {traceback.format_exc()}"
            )
            return False

    def can_execute_task(self, task_entity: TaskEntity) -> bool:
        """
        验证任务是否可以执行

        Args:
            task_entity: 任务实体

        Returns:
            bool: 是否可以执行
        """
        task_id = task_entity.task_id

        # 执行任务前先判断显存数和利用率是否满足要求,返回的是True 或者 False
        task_entity_from_repo = self.task_repository.get_task(task_id)
        if task_entity_from_repo is None:
            logger.warning(f"任务 [{task_id}] 不存在于仓库中")
            return False

        check_gpu_status = self.gpu_utils.check_gpu_requirements(
            required_memory=task_entity_from_repo.min_gpu_memory_gb,
            max_utilization=task_entity_from_repo.min_gpu_utilization,
        )
        if check_gpu_status == False:
            logger.info(f"任务 [{task_id}] 跳过执行，显存数和利用率不满足要求")
            return False

        # 如果有下次执行时间则判断是否到了执行时间
        if task_entity.next_execution_time > 0:
            if task_entity.is_ready_for_execution() == False:
                logger.debug(f"任务 [{task_id}] 跳过执行，未到执行时间")
                return False

        return True

    def execute_exception_handler(self, task_entity: TaskEntity) -> Any:
        """使用自定义异常处理器执行任务"""
        try:
            return self.task_exception_handler(task_entity)
        except Exception as e:
            logger.error(
                f"执行任务异常处理器时发生异常: {str(e)}, 详细错误信息: {traceback.format_exc()}"
            )
            raise e

    def set_custom_task_handler(self, handler: Callable):
        """
        设置任务处理器

        Args:
            handler: 任务处理函数
        """
        self.task_handler = handler
        logger.info(f"custom_task_handler: [{handler.__name__}] 任务处理器已设置")

    def set_custom_task_exception_handler(self, handler: Callable):
        """
        设置任务异常处理器

        Args:
            handler: 任务异常处理函数
        """
        self.task_exception_handler = handler
        logger.info(
            f"custom_task_exception_handler: [{handler.__name__}] 任务异常处理器已设置"
        )

    def get_queue_statistics(self) -> Dict[str, int]:
        stats = self.task_repository.get_queue_statistics()
        # 确保返回的是dict[str, int]类型
        if isinstance(stats, dict):
            return {
                k: (
                    int(v)
                    if isinstance(v, (int, float, str)) and str(v).isdigit()
                    else 0
                )
                for k, v in stats.items()
            }
        return {}

    def cancel_task(self, task_id: str) -> Tuple[bool, str]:
        """
        取消正在执行的任务

        Args:
            task_id: 任务ID

        Returns:
            Tuple[bool, str]: (是否成功取消, 取消结果信息)
        """
        # 检查任务是否存在
        task_entity = self.task_repository.get_task(task_id)

        if not task_entity:
            message = f"任务 [{task_id}] 不存在"
            logger.warning(message)
            return False, message

        # 检查任务状态
        if task_entity.status == TaskStatus.COMPLETED.value:
            message = f"任务 [{task_id}] 已完成，无法取消"
            logger.warning(message)
            return False, message

        if task_entity.status == TaskStatus.FAILED.value:
            message = f"任务 [{task_id}] 已失败，无法取消"
            logger.warning(message)
            return False, message

        if task_entity.status == TaskStatus.CANCELED.value:
            message = f"任务 [{task_id}] 已被取消"
            logger.info(message)
            return True, message

        # 检查future是否存在且未执行完成
        future = self.running_futures.get(task_id)

        if future:
            if not future.done():
                try:
                    cancel_result = future.cancel()
                    if cancel_result:
                        self.task_repository.mark_task_canceled(
                            task_id, "任务被用户主动取消"
                        )
                        message = f"任务 [{task_id}] 已成功取消"
                        logger.info(message)

                        # 从映射字典中移除已取消的future
                        self.running_futures.pop(task_id, None)
                        return True, message
                    else:
                        message = f"任务 [{task_id}] 取消失败，任务可能已经开始执行"
                        logger.warning(message)
                        return False, message
                except Exception as e:
                    message = f"取消任务 [{task_id}] 时发生异常: {str(e)}, 详细错误信息: {traceback.format_exc()}"
                    logger.error(message)
                    return False, message
            else:
                message = f"任务 [{task_id}] 已执行完成，无法取消"
                logger.warning(message)
                return False, message
        else:
            # 任务可能在队列中但尚未开始执行
            if task_entity.status == TaskStatus.PENDING.value:
                self.task_repository.mark_task_canceled(task_id, "任务被用户主动取消")
                message = f"任务 [{task_id}] 已成功取消（尚未开始执行）"
                logger.info(message)
                return True, message
