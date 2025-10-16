from __future__ import print_function

import logging
import os
import time
import types
from datetime import datetime, timedelta, timezone
from logging.handlers import RotatingFileHandler
from os.path import dirname
from pathlib import Path

from IPython.core.interactiveshell import InteractiveShell

from elastic_notebook.algorithm.baseline import MigrateAllBaseline, RecomputeAllBaseline
from elastic_notebook.algorithm.optimizer_exact import OptimizerExact
from elastic_notebook.algorithm.selector import OptimizerType
from elastic_notebook.core.common.profile_migration_speed import profile_migration_speed
from elastic_notebook.core.graph.graph import DependencyGraph
from elastic_notebook.core.io.filesystem_adapter import FilesystemAdapter
from elastic_notebook.core.io.recover import resume
from elastic_notebook.core.mutation.fingerprint import (
    compare_fingerprint,
    construct_fingerprint,
)
from elastic_notebook.core.mutation.object_hash import UnserializableObj
from elastic_notebook.core.notebook.checkpoint import checkpoint
from elastic_notebook.core.notebook.find_input_vars import find_input_vars
from elastic_notebook.core.notebook.find_output_vars import find_created_deleted_vars
from elastic_notebook.core.notebook.restore_notebook import restore_notebook
from elastic_notebook.core.notebook.update_graph import update_graph


class JSTFormatter(logging.Formatter):
    """日本時間（JST）用のログフォーマッター"""

    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        return dt.astimezone(timezone(timedelta(hours=9)))  # UTC+9

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # マイクロ秒を3桁まで表示


class ElasticNotebook:
    def __init__(self, shell: InteractiveShell, log_file_dir: str):
        self.shell = shell

        # Initialize the dependency graph for capturing notebook state.
        self.dependency_graph = DependencyGraph()

        # Migration properties.
        self.migration_speed_bps = 100000
        self.alpha = 1
        self.selector = OptimizerExact(migration_speed_bps=self.migration_speed_bps)

        # Dictionary of object fingerprints. For detecting modified references.
        self.fingerprint_dict = {}

        # Set of user-declared functions.
        self.udfs = set()

        # Flag if migration speed has been manually set. In this case, skip profiling of migration speed at checkpoint
        # time.
        self.manual_migration_speed = False

        # Strings for determining log filename. For experiments only.
        self.optimizer_name = ""
        self.notebook_name = ""

        # Total elapsed time spent inferring cell inputs and outputs.
        # For measuring overhead.
        self.total_recordevent_time = 0

        # Dict for recording overhead of profiling operations.
        self.profile_dict = {"idgraph": 0, "representation": 0}

        # マイグレーションと再計算の変数リスト
        self._vss_to_migrate = []
        self._vss_to_recompute = []

        # ロガーの設定
        self.log_file_path = os.path.join(log_file_dir, "ElasticNotebook.log")
        self.logger: logging.Logger
        self.__setup_logger()

    @property
    def vss_to_migrate(self):
        """マイグレーション対象の変数リストを取得"""
        return self._vss_to_migrate

    @property
    def vss_to_recompute(self):
        """再計算対象の変数リストを取得"""
        return self._vss_to_recompute

    def __setup_logger(self):
        # ロガーの設定
        self.logger = logging.getLogger("ElasticNotebookLogger")

        # 環境変数からログレベルを取得
        log_level_str = os.environ.get("ELASTIC_KERNEL_LOG_LEVEL", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        self.logger.setLevel(log_level)

        formatter = JSTFormatter(
            "[%(asctime)s %(name)s %(filename)s:%(lineno)d %(levelname)s] %(message)s",
            "%Y-%m-%d %H:%M:%S.%f",
        )

        # ローテーティングファイルハンドラー
        rotating_file_handler = RotatingFileHandler(
            self.log_file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,  # 5MBのログサイズでローテーション、5世代保存
        )
        rotating_file_handler.setLevel(log_level)
        rotating_file_handler.setFormatter(formatter)
        self.logger.addHandler(rotating_file_handler)

    def update_migration_lists(self, vss_to_migrate, vss_to_recompute):
        """マイグレーションと再計算の変数リストを更新"""
        self._vss_to_migrate = [vs.name for vs in vss_to_migrate]
        self._vss_to_recompute = [vs.name for vs in vss_to_recompute]

    def __str__(self):
        """文字列表現を定義"""
        return f"マイグレーション対象: {self.vss_to_migrate}，再計算対象: {self.vss_to_recompute}"

    def record_event(self, cell, pre_execution_user_ns, start_time, cell_runtime):
        record_start = time.time()
        self.logger.debug(f"record_event started for cell: {cell[:50]}...")

        # Create id trees for output variables
        fingerprint_start = time.time()
        for var in self.dependency_graph.variable_snapshots.keys():
            if var not in self.fingerprint_dict and var in self.shell.user_ns:
                var_start = time.time()
                self.fingerprint_dict[var] = construct_fingerprint(
                    self.shell.user_ns[var], self.profile_dict
                )
                var_time = time.time() - var_start
                if var_time > 0.1:  # 100ms以上かかった場合のみログ
                    self.logger.info(
                        f"  construct_fingerprint for '{var}' took {var_time:.3f}s"
                    )
        fingerprint_time = time.time() - fingerprint_start
        self.logger.debug(f"Initial fingerprint creation took {fingerprint_time:.3f}s")

        # Find input variables (variables potentially accessed) of the cell.
        input_vars_start = time.time()
        input_variables, function_defs = find_input_vars(
            cell,
            set(self.dependency_graph.variable_snapshots.keys()),
            self.shell,
            self.udfs,
        )
        input_vars_time = time.time() - input_vars_start
        self.logger.debug(f"find_input_vars took {input_vars_time:.3f}s")
        # Union of ID graphs of input variables. For detecting modifications to unserializable variables.
        input_variables_id_graph_union = set()
        for var in input_variables:
            if var in self.fingerprint_dict:
                input_variables_id_graph_union = input_variables_id_graph_union.union(
                    self.fingerprint_dict[var][1]
                )

        post_execution = set(self.shell.user_ns.keys())
        infer_start = time.time()

        # Find created and deleted variables by computing difference between namespace pre and post execution.
        created_variables, deleted_variables = find_created_deleted_vars(
            pre_execution_user_ns, post_execution
        )

        # Remove stored ID graphs for deleted variables.
        for var in deleted_variables:
            del self.fingerprint_dict[var]
            if var in self.udfs:
                self.udfs.remove(var)

        # Find modified variables by comparing ID graphs and object hashes.
        compare_start = time.time()
        modified_variables = set()
        for k, v in self.fingerprint_dict.items():
            var_compare_start = time.time()
            changed, overwritten = compare_fingerprint(
                self.fingerprint_dict[k],
                self.shell.user_ns[k],
                self.profile_dict,
                input_variables_id_graph_union,
            )
            var_compare_time = time.time() - var_compare_start
            if var_compare_time > 0.1:  # 100ms以上かかった場合のみログ
                self.logger.info(
                    f"  compare_fingerprint for '{k}' took {var_compare_time:.3f}s"
                )
            self.logger.debug(f"{k=} {changed=} {overwritten=}")
            if changed:
                modified_variables.add(k)

            # In the case of non-overwrite modification, the variable is additionally considered as accessed.
            if changed and not overwritten:
                input_variables.add(k)

            # A user defined function has been overwritten.
            elif overwritten and k in self.udfs:
                self.udfs.remove(k)

            # Select unserializable variables are assumed to be modified if accessed.
            if (
                not changed
                and not overwritten
                and isinstance(self.fingerprint_dict[k][2], UnserializableObj)
            ):
                if self.fingerprint_dict[k][1].intersection(
                    input_variables_id_graph_union
                ):
                    modified_variables.add(k)

        compare_time = time.time() - compare_start
        self.logger.debug(f"Compare fingerprints took {compare_time:.3f}s")

        # Create ID graphs for output variables
        create_fingerprint_start = time.time()
        for var in created_variables:
            var_start = time.time()
            self.fingerprint_dict[var] = construct_fingerprint(
                self.shell.user_ns[var], self.profile_dict
            )
            var_time = time.time() - var_start
            if var_time > 0.1:  # 100ms以上かかった場合のみログ
                self.logger.info(
                    f"  construct_fingerprint for new var '{var}' took {var_time:.3f}s"
                )
        create_fingerprint_time = time.time() - create_fingerprint_start
        self.logger.debug(
            f"Create fingerprints for new variables took {create_fingerprint_time:.3f}s"
        )

        # Record newly defined UDFs
        for udf in function_defs:
            if udf in self.shell.user_ns and isinstance(
                self.shell.user_ns[udf], types.FunctionType
            ):
                self.udfs.add(udf)

        # Update the dependency graph.
        update_graph_start = time.time()
        update_graph(
            cell,
            cell_runtime,
            start_time,
            input_variables,
            created_variables.union(modified_variables),
            deleted_variables,
            self.dependency_graph,
        )
        update_graph_time = time.time() - update_graph_start
        self.logger.debug(f"update_graph took {update_graph_time:.3f}s")

        # Update total recordevent time tally.
        infer_end = time.time()
        self.total_recordevent_time += infer_end - infer_start

        total_record_time = time.time() - record_start
        self.logger.debug(f"Total record_event took {total_record_time:.3f}s")
        if total_record_time > 0.5:  # 500ms以上かかった場合は警告
            self.logger.warning(
                f"record_event took {total_record_time:.3f}s - performance issue detected"
            )

    def set_migration_speed(self, migration_speed):
        try:
            if float(migration_speed) > 0:
                self.migration_speed_bps = float(migration_speed)
                self.manual_migration_speed = True
        except ValueError:
            pass

        self.selector.migration_speed_bps = self.migration_speed_bps

    def set_optimizer(self, optimizer):
        self.optimizer_name = optimizer

        if optimizer == OptimizerType.EXACT.value:
            self.selector = OptimizerExact(self.migration_speed_bps)
            self.alpha = 1
        elif optimizer == OptimizerType.EXACT_C.value:
            self.selector = OptimizerExact(self.migration_speed_bps)
            self.alpha = 20
        elif optimizer == OptimizerType.EXACT_R.value:
            self.selector = OptimizerExact(self.migration_speed_bps)
            self.alpha = 0.05
        elif optimizer == OptimizerType.MIGRATE_ALL.value:
            self.selector = MigrateAllBaseline(self.migration_speed_bps)
        elif optimizer == OptimizerType.RECOMPUTE_ALL.value:
            self.selector = RecomputeAllBaseline(self.migration_speed_bps)

    def checkpoint(self, filename):
        self.logger.info("Saving checkpoint started.")

        # Profile the migration speed to filename.
        if not self.manual_migration_speed:
            self.migration_speed_bps = profile_migration_speed(
                dirname(filename), alpha=self.alpha
            )
            self.selector.migration_speed_bps = self.migration_speed_bps
        self.logger.info(f"Migration speed: {self.migration_speed_bps} bytes/s")

        # Checkpoint the notebook.
        migrate_success, vss_to_migrate, vss_to_recompute = checkpoint(
            self.dependency_graph,
            self.shell,
            self.fingerprint_dict,
            self.selector,
            self.udfs,
            filename,
            self.profile_dict,
            self.notebook_name,
            self.optimizer_name,
        )

        # マイグレーションが成功した場合のみ、マイグレーションと再計算の変数リストを更新
        if migrate_success:
            self.update_migration_lists(vss_to_migrate, vss_to_recompute)
            self.logger.info(self)

        self.logger.info("Saving checkpoint finished.")

        return migrate_success

    def load_checkpoint(self, filename):
        self.logger.info("Loading checkpoint started")

        (
            self.dependency_graph,
            variables,
            ces_to_recompute,
            self.udfs,
        ) = resume(filename)

        # Recompute missing VSs and redeclare variables into the kernel.
        restore_notebook(
            self.dependency_graph,
            self.shell,
            variables,
            ces_to_recompute,
        )

        # 読み込んだメタデータから、マイグレートされた変数と再計算される変数を取得
        adapter = FilesystemAdapter()
        metadata = adapter.read_all(Path(filename))

        # マイグレートされた変数と再計算される変数のリストを取得
        vss_to_migrate = (
            metadata.get_vss_to_migrate() if metadata.get_vss_to_migrate() else set()
        )
        vss_to_recompute = (
            metadata.get_vss_to_recompute()
            if metadata.get_vss_to_recompute()
            else set()
        )

        # リストを更新して表示
        self.update_migration_lists(vss_to_migrate, vss_to_recompute)
        self.logger.info(self)
        self.logger.info("Loading checkpoint finished.")
