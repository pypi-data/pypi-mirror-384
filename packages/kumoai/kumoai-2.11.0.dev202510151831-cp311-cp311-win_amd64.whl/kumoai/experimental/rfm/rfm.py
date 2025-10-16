import json
import time
import warnings
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from typing import Iterator, List, Literal, Optional, Union, overload

import numpy as np
import pandas as pd
from kumoapi.model_plan import RunMode
from kumoapi.pquery import QueryType
from kumoapi.rfm import Context
from kumoapi.rfm import Explanation as ExplanationConfig
from kumoapi.rfm import (
    PQueryDefinition,
    RFMEvaluateRequest,
    RFMPredictRequest,
    RFMValidateQueryRequest,
)
from kumoapi.task import TaskType

from kumoai import global_state
from kumoai.exceptions import HTTPException
from kumoai.experimental.rfm import LocalGraph
from kumoai.experimental.rfm.local_graph_sampler import LocalGraphSampler
from kumoai.experimental.rfm.local_graph_store import LocalGraphStore
from kumoai.experimental.rfm.local_pquery_driver import (
    LocalPQueryDriver,
    date_offset_to_seconds,
)
from kumoai.utils import InteractiveProgressLogger, ProgressLogger

_RANDOM_SEED = 42

_MAX_PRED_SIZE: dict[TaskType, int] = defaultdict(lambda: 1_000)
_MAX_PRED_SIZE[TaskType.TEMPORAL_LINK_PREDICTION] = 200

_MAX_CONTEXT_SIZE = {
    RunMode.DEBUG: 100,
    RunMode.FAST: 1_000,
    RunMode.NORMAL: 5_000,
    RunMode.BEST: 10_000,
}
_MAX_TEST_SIZE = {  # Share test set size across run modes for fair comparison:
    RunMode.DEBUG: 100,
    RunMode.FAST: 2_000,
    RunMode.NORMAL: 2_000,
    RunMode.BEST: 2_000,
}

_MAX_SIZE = 30 * 1024 * 1024
_SIZE_LIMIT_MSG = ("Context size exceeds the 30MB limit. {stats}\nPlease "
                   "reduce either the number of tables in the graph, their "
                   "number of columns (e.g., large text columns), "
                   "neighborhood configuration, or the run mode. If none of "
                   "this is possible, please create a feature request at "
                   "'https://github.com/kumo-ai/kumo-rfm' if you must go "
                   "beyond this for your use-case.")


@dataclass(repr=False)
class Explanation:
    prediction: pd.DataFrame
    summary: str
    details: ExplanationConfig

    @overload
    def __getitem__(self, index: Literal[0]) -> pd.DataFrame:
        pass

    @overload
    def __getitem__(self, index: Literal[1]) -> str:
        pass

    def __getitem__(self, index: int) -> Union[pd.DataFrame, str]:
        if index == 0:
            return self.prediction
        if index == 1:
            return self.summary
        raise IndexError("Index out of range")

    def __iter__(self) -> Iterator[Union[pd.DataFrame, str]]:
        return iter((self.prediction, self.summary))

    def __repr__(self) -> str:
        return str((self.prediction, self.summary))


class KumoRFM:
    r"""The Kumo Relational Foundation model (RFM) from the `KumoRFM: A
    Foundation Model for In-Context Learning on Relational Data
    <https://kumo.ai/research/kumo_relational_foundation_model.pdf>`_ paper.

    :class:`KumoRFM` is a foundation model to generate predictions for any
    relational dataset without training.
    The model is pre-trained and the class provides an interface to query the
    model from a :class:`LocalGraph` object.

    .. code-block:: python

        from kumoai.experimental.rfm import LocalGraph, KumoRFM

        df_users = pd.DataFrame(...)
        df_items = pd.DataFrame(...)
        df_orders = pd.DataFrame(...)

        graph = LocalGraph.from_data({
            'users': df_users,
            'items': df_items,
            'orders': df_orders,
        })

        rfm = KumoRFM(graph)

        query = ("PREDICT COUNT(transactions.*, 0, 30, days)>0 "
                 "FOR users.user_id=0")
        result = rfm.query(query)

        print(result)  # user_id  COUNT(transactions.*, 0, 30, days) > 0
                       # 1        0.85

    Args:
        graph: The graph.
        preprocess: Whether to pre-process the data in advance during graph
            materialization.
            This is a runtime trade-off between graph materialization and model
            processing speed.
            It can be benefical to preprocess your data once and then run many
            queries on top to achieve maximum model speed.
            However, if activiated, graph materialization can take potentially
            much longer, especially on graphs with many large text columns.
            Best to tune this option manually.
        verbose: Whether to print verbose output.
    """
    def __init__(
        self,
        graph: LocalGraph,
        preprocess: bool = False,
        verbose: Union[bool, ProgressLogger] = True,
    ) -> None:
        graph = graph.validate()
        self._graph_def = graph._to_api_graph_definition()
        self._graph_store = LocalGraphStore(graph, preprocess, verbose)
        self._graph_sampler = LocalGraphSampler(self._graph_store)

        self._batch_size: Optional[int | Literal['max']] = None
        self.num_retries: int = 0

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}()'

    @contextmanager
    def batch_mode(
        self,
        batch_size: Union[int, Literal['max']] = 'max',
        num_retries: int = 1,
    ) -> Generator[None, None, None]:
        """Context manager to predict in batches.

        .. code-block:: python

            with model.batch_mode(batch_size='max', num_retries=1):
                df = model.predict(query, indices=...)

        Args:
            batch_size: The batch size. If set to ``"max"``, will use the
                maximum applicable batch size for the given task.
            num_retries: The maximum number of retries for failed queries due
                to unexpected server issues.
        """
        if batch_size != 'max' and batch_size <= 0:
            raise ValueError(f"'batch_size' must be greater than zero "
                             f"(got {batch_size})")

        if num_retries < 0:
            raise ValueError(f"'num_retries' must be greater than or equal to "
                             f"zero (got {num_retries})")

        self._batch_size = batch_size
        self.num_retries = num_retries
        yield
        self._batch_size = None
        self.num_retries = 0

    @overload
    def predict(
        self,
        query: str,
        indices: Union[List[str], List[float], List[int], None] = None,
        *,
        explain: Literal[False] = False,
        anchor_time: Union[pd.Timestamp, Literal['entity'], None] = None,
        context_anchor_time: Union[pd.Timestamp, None] = None,
        run_mode: Union[RunMode, str] = RunMode.FAST,
        num_neighbors: Optional[List[int]] = None,
        num_hops: int = 2,
        max_pq_iterations: int = 20,
        random_seed: Optional[int] = _RANDOM_SEED,
        verbose: Union[bool, ProgressLogger] = True,
    ) -> pd.DataFrame:
        pass

    @overload
    def predict(
        self,
        query: str,
        indices: Union[List[str], List[float], List[int], None] = None,
        *,
        explain: Literal[True],
        anchor_time: Union[pd.Timestamp, Literal['entity'], None] = None,
        context_anchor_time: Union[pd.Timestamp, None] = None,
        run_mode: Union[RunMode, str] = RunMode.FAST,
        num_neighbors: Optional[List[int]] = None,
        num_hops: int = 2,
        max_pq_iterations: int = 20,
        random_seed: Optional[int] = _RANDOM_SEED,
        verbose: Union[bool, ProgressLogger] = True,
    ) -> Explanation:
        pass

    def predict(
        self,
        query: str,
        indices: Union[List[str], List[float], List[int], None] = None,
        *,
        explain: bool = False,
        anchor_time: Union[pd.Timestamp, Literal['entity'], None] = None,
        context_anchor_time: Union[pd.Timestamp, None] = None,
        run_mode: Union[RunMode, str] = RunMode.FAST,
        num_neighbors: Optional[List[int]] = None,
        num_hops: int = 2,
        max_pq_iterations: int = 20,
        random_seed: Optional[int] = _RANDOM_SEED,
        verbose: Union[bool, ProgressLogger] = True,
    ) -> Union[pd.DataFrame, Explanation]:
        """Returns predictions for a predictive query.

        Args:
            query: The predictive query.
            indices: The entity primary keys to predict for. Will override the
                indices given as part of the predictive query. Predictions will
                be generated for all indices, independent of whether they
                fulfill entity filter constraints. To pre-filter entities, use
                :meth:`~KumoRFM.is_valid_entity`.
            explain: If set to ``True``, will additionally explain the
                prediction. Explainability is currently only supported for
                single entity predictions with ``run_mode="FAST"``.
            anchor_time: The anchor timestamp for the prediction. If set to
                ``None``, will use the maximum timestamp in the data.
                If set to ``"entity"``, will use the timestamp of the entity.
            context_anchor_time: The maximum anchor timestamp for context
                examples. If set to ``None``, ``anchor_time`` will
                determine the anchor time for context examples.
            run_mode: The :class:`RunMode` for the query.
            num_neighbors: The number of neighbors to sample for each hop.
                If specified, the ``num_hops`` option will be ignored.
            num_hops: The number of hops to sample when generating the context.
            max_pq_iterations: The maximum number of iterations to perform to
                collect valid labels. It is advised to increase the number of
                iterations in case the predictive query has strict entity
                filters, in which case, :class:`KumoRFM` needs to sample more
                entities to find valid labels.
            random_seed: A manual seed for generating pseudo-random numbers.
            verbose: Whether to print verbose output.

        Returns:
            The predictions as a :class:`pandas.DataFrame`.
            If ``explain=True``, additionally returns a textual summary that
            explains the prediction.
        """
        query_def = self._parse_query(query)

        if num_hops != 2 and num_neighbors is not None:
            warnings.warn(f"Received custom 'num_neighbors' option; ignoring "
                          f"custom 'num_hops={num_hops}' option")

        if explain and run_mode in {RunMode.NORMAL, RunMode.BEST}:
            warnings.warn(f"Explainability is currently only supported for "
                          f"run mode 'FAST' (got '{run_mode}'). Provided run "
                          f"mode has been reset. Please lower the run mode to "
                          f"suppress this warning.")

        if indices is None:
            if query_def.entity.ids is None:
                raise ValueError("Cannot find entities to predict for. Please "
                                 "pass them via `predict(query, indices=...)`")
            indices = query_def.entity.ids.value
        else:
            query_def = replace(
                query_def,
                entity=replace(query_def.entity, ids=None),
            )

        if len(indices) == 0:
            raise ValueError("At least one entity is required")

        if explain and len(indices) > 1:
            raise ValueError(
                f"Cannot explain predictions for more than a single entity "
                f"(got {len(indices)})")

        query_repr = query_def.to_string(rich=True, exclude_predict=True)
        if explain:
            msg = f'[bold]EXPLAIN[/bold] {query_repr}'
        else:
            msg = f'[bold]PREDICT[/bold] {query_repr}'

        if not isinstance(verbose, ProgressLogger):
            verbose = InteractiveProgressLogger(msg, verbose=verbose)

        with verbose as logger:

            batch_size: Optional[int] = None
            if self._batch_size == 'max':
                task_type = query_def.get_task_type(
                    stypes=self._graph_store.stype_dict,
                    edge_types=self._graph_store.edge_types,
                )
                batch_size = _MAX_PRED_SIZE[task_type]
            else:
                batch_size = self._batch_size

            if batch_size is not None:
                offsets = range(0, len(indices), batch_size)
                batches = [indices[step:step + batch_size] for step in offsets]
            else:
                batches = [indices]

            if len(batches) > 1:
                logger.log(f"Splitting {len(indices):,} entities into "
                           f"{len(batches):,} batches of size {batch_size:,}")

            predictions: List[pd.DataFrame] = []
            summary: Optional[str] = None
            details: Optional[Explanation] = None
            for i, batch in enumerate(batches):
                # TODO Re-use the context for subsequent predictions.
                context = self._get_context(
                    query=query_def,
                    indices=batch,
                    anchor_time=anchor_time,
                    context_anchor_time=context_anchor_time,
                    run_mode=RunMode(run_mode),
                    num_neighbors=num_neighbors,
                    num_hops=num_hops,
                    max_pq_iterations=max_pq_iterations,
                    evaluate=False,
                    random_seed=random_seed,
                    logger=logger if i == 0 else None,
                )
                request = RFMPredictRequest(
                    context=context,
                    run_mode=RunMode(run_mode),
                )
                with warnings.catch_warnings():
                    warnings.filterwarnings('ignore', message='gencode')
                    request_msg = request.to_protobuf()
                    _bytes = request_msg.SerializeToString()
                if i == 0:
                    logger.log(f"Generated context of size "
                               f"{len(_bytes) / (1024*1024):.2f}MB")

                if len(_bytes) > _MAX_SIZE:
                    stats = Context.get_memory_stats(request_msg.context)
                    raise ValueError(_SIZE_LIMIT_MSG.format(stats=stats))

                if (isinstance(verbose, InteractiveProgressLogger) and i == 0
                        and len(batches) > 1):
                    verbose.init_progress(
                        total=len(batches),
                        description='Predicting',
                    )

                for attempt in range(self.num_retries + 1):
                    try:
                        if explain:
                            resp = global_state.client.rfm_api.explain(_bytes)
                            summary = resp.summary
                            details = resp.details
                        else:
                            resp = global_state.client.rfm_api.predict(_bytes)
                        df = pd.DataFrame(**resp.prediction)

                        # Cast 'ENTITY' to correct data type:
                        if 'ENTITY' in df:
                            entity = query_def.entity.pkey.table_name
                            pkey_map = self._graph_store.pkey_map_dict[entity]
                            df['ENTITY'] = df['ENTITY'].astype(
                                type(pkey_map.index[0]))

                        # Cast 'ANCHOR_TIMESTAMP' to correct data type:
                        if 'ANCHOR_TIMESTAMP' in df:
                            ser = df['ANCHOR_TIMESTAMP']
                            if not pd.api.types.is_datetime64_any_dtype(ser):
                                if isinstance(ser.iloc[0], str):
                                    unit = None
                                else:
                                    unit = 'ms'
                                df['ANCHOR_TIMESTAMP'] = pd.to_datetime(
                                    ser, errors='coerce', unit=unit)

                        predictions.append(df)

                        if (isinstance(verbose, InteractiveProgressLogger)
                                and len(batches) > 1):
                            verbose.step()

                        break
                    except HTTPException as e:
                        if attempt == self.num_retries:
                            try:
                                msg = json.loads(e.detail)['detail']
                            except Exception:
                                msg = e.detail
                            raise RuntimeError(
                                f"An unexpected exception occurred. Please "
                                f"create an issue at "
                                f"'https://github.com/kumo-ai/kumo-rfm'. {msg}"
                            ) from None

                        time.sleep(2**attempt)  # 1s, 2s, 4s, 8s, ...

        if len(predictions) == 1:
            prediction = predictions[0]
        else:
            prediction = pd.concat(predictions, ignore_index=True)

        if explain:
            assert len(predictions) == 1
            assert summary is not None
            assert details is not None
            return Explanation(
                prediction=prediction,
                summary=summary,
                details=details,
            )

        return prediction

    def is_valid_entity(
        self,
        query: str,
        indices: Union[List[str], List[float], List[int], None] = None,
        *,
        anchor_time: Union[pd.Timestamp, Literal['entity'], None] = None,
    ) -> np.ndarray:
        r"""Returns a mask that denotes which entities are valid for the
        given predictive query, *i.e.*, which entities fulfill (temporal)
        entity filter constraints.

        Args:
            query: The predictive query.
            indices: The entity primary keys to predict for. Will override the
                indices given as part of the predictive query.
            anchor_time: The anchor timestamp for the prediction. If set to
                ``None``, will use the maximum timestamp in the data.
                If set to ``"entity"``, will use the timestamp of the entity.
        """
        query_def = self._parse_query(query)

        if indices is None:
            if query_def.entity.ids is None:
                raise ValueError("Cannot find entities to predict for. Please "
                                 "pass them via "
                                 "`is_valid_entity(query, indices=...)`")
            indices = query_def.entity.ids.value

        if len(indices) == 0:
            raise ValueError("At least one entity is required")

        if anchor_time is None:
            anchor_time = self._graph_store.max_time

        if isinstance(anchor_time, pd.Timestamp):
            self._validate_time(query_def, anchor_time, None, False)
        else:
            assert anchor_time == 'entity'
            if (query_def.entity.pkey.table_name
                    not in self._graph_store.time_dict):
                raise ValueError(f"Anchor time 'entity' requires the entity "
                                 f"table '{query_def.entity.pkey.table_name}' "
                                 f"to have a time column")

        node = self._graph_store.get_node_id(
            table_name=query_def.entity.pkey.table_name,
            pkey=pd.Series(indices),
        )
        query_driver = LocalPQueryDriver(self._graph_store, query_def)
        return query_driver.is_valid(node, anchor_time)

    def evaluate(
        self,
        query: str,
        *,
        metrics: Optional[List[str]] = None,
        anchor_time: Union[pd.Timestamp, Literal['entity'], None] = None,
        context_anchor_time: Union[pd.Timestamp, None] = None,
        run_mode: Union[RunMode, str] = RunMode.FAST,
        num_neighbors: Optional[List[int]] = None,
        num_hops: int = 2,
        max_pq_iterations: int = 20,
        random_seed: Optional[int] = _RANDOM_SEED,
        verbose: Union[bool, ProgressLogger] = True,
    ) -> pd.DataFrame:
        """Evaluates a predictive query.

        Args:
            query: The predictive query.
            metrics: The metrics to use.
            anchor_time: The anchor timestamp for the prediction. If set to
                ``None``, will use the maximum timestamp in the data.
                If set to ``"entity"``, will use the timestamp of the entity.
            context_anchor_time: The maximum anchor timestamp for context
                examples. If set to ``None``, ``anchor_time`` will
                determine the anchor time for context examples.
            run_mode: The :class:`RunMode` for the query.
            num_neighbors: The number of neighbors to sample for each hop.
                If specified, the ``num_hops`` option will be ignored.
            num_hops: The number of hops to sample when generating the context.
            max_pq_iterations: The maximum number of iterations to perform to
                collect valid labels. It is advised to increase the number of
                iterations in case the predictive query has strict entity
                filters, in which case, :class:`KumoRFM` needs to sample more
                entities to find valid labels.
            random_seed: A manual seed for generating pseudo-random numbers.
            verbose: Whether to print verbose output.

        Returns:
            The metrics as a :class:`pandas.DataFrame`
        """
        query_def = self._parse_query(query)

        if num_hops != 2 and num_neighbors is not None:
            warnings.warn(f"Received custom 'num_neighbors' option; ignoring "
                          f"custom 'num_hops={num_hops}' option")

        if query_def.entity.ids is not None:
            query_def = replace(
                query_def,
                entity=replace(query_def.entity, ids=None),
            )

        query_repr = query_def.to_string(rich=True, exclude_predict=True)
        msg = f'[bold]EVALUATE[/bold] {query_repr}'

        if not isinstance(verbose, ProgressLogger):
            verbose = InteractiveProgressLogger(msg, verbose=verbose)

        with verbose as logger:
            context = self._get_context(
                query=query_def,
                indices=None,
                anchor_time=anchor_time,
                context_anchor_time=context_anchor_time,
                run_mode=RunMode(run_mode),
                num_neighbors=num_neighbors,
                num_hops=num_hops,
                max_pq_iterations=max_pq_iterations,
                evaluate=True,
                random_seed=random_seed,
                logger=logger if verbose else None,
            )
            if metrics is not None and len(metrics) > 0:
                self._validate_metrics(metrics, context.task_type)
                metrics = list(dict.fromkeys(metrics))
            request = RFMEvaluateRequest(
                context=context,
                run_mode=RunMode(run_mode),
                metrics=metrics,
            )
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='Protobuf gencode')
                request_msg = request.to_protobuf()
                request_bytes = request_msg.SerializeToString()
            logger.log(f"Generated context of size "
                       f"{len(request_bytes) / (1024*1024):.2f}MB")

            if len(request_bytes) > _MAX_SIZE:
                stats_msg = Context.get_memory_stats(request_msg.context)
                raise ValueError(_SIZE_LIMIT_MSG.format(stats_msg=stats_msg))

            try:
                resp = global_state.client.rfm_api.evaluate(request_bytes)
            except HTTPException as e:
                try:
                    msg = json.loads(e.detail)['detail']
                except Exception:
                    msg = e.detail
                raise RuntimeError(f"An unexpected exception occurred. "
                                   f"Please create an issue at "
                                   f"'https://github.com/kumo-ai/kumo-rfm'. "
                                   f"{msg}") from None

        return pd.DataFrame.from_dict(
            resp.metrics,
            orient='index',
            columns=['value'],
        ).reset_index(names='metric')

    def get_train_table(
        self,
        query: str,
        size: int,
        *,
        anchor_time: Union[pd.Timestamp, Literal['entity'], None] = None,
        random_seed: Optional[int] = _RANDOM_SEED,
        max_iterations: int = 20,
    ) -> pd.DataFrame:
        """Returns the labels of a predictive query for a specified anchor
        time.

        Args:
            query: The predictive query.
            size: The maximum number of entities to generate labels for.
            anchor_time: The anchor timestamp for the query. If set to
                :obj:`None`, will use the maximum timestamp in the data.
                If set to :`"entity"`, will use the timestamp of the entity.
            random_seed: A manual seed for generating pseudo-random numbers.
            max_iterations: The number of steps to run before aborting.

        Returns:
            The labels as a :class:`pandas.DataFrame`.
        """
        query_def = self._parse_query(query)

        if anchor_time is None:
            anchor_time = self._graph_store.max_time
            anchor_time = anchor_time - (query_def.target.end_offset *
                                         query_def.num_forecasts)

        assert anchor_time is not None
        if isinstance(anchor_time, pd.Timestamp):
            self._validate_time(query_def, anchor_time, None, evaluate=True)
        else:
            assert anchor_time == 'entity'
            if (query_def.entity.pkey.table_name
                    not in self._graph_store.time_dict):
                raise ValueError(f"Anchor time 'entity' requires the entity "
                                 f"table '{query_def.entity.pkey.table_name}' "
                                 f"to have a time column")

        query_driver = LocalPQueryDriver(self._graph_store, query_def,
                                         random_seed)

        node, time, y = query_driver.collect_test(
            size=size,
            anchor_time=anchor_time,
            batch_size=min(10_000, size),
            max_iterations=max_iterations,
            guarantee_train_examples=False,
        )

        entity = self._graph_store.pkey_map_dict[
            query_def.entity.pkey.table_name].index[node]

        return pd.DataFrame({
            'ENTITY': entity,
            'ANCHOR_TIMESTAMP': time,
            'TARGET': y,
        })

    # Helpers #################################################################

    def _parse_query(self, query: str) -> PQueryDefinition:
        if isinstance(query, PQueryDefinition):
            return query

        if isinstance(query, str) and query.strip()[:9].lower() == 'evaluate ':
            raise ValueError("'EVALUATE PREDICT ...' queries are not "
                             "supported in the SDK. Instead, use either "
                             "`predict()` or `evaluate()` methods to perform "
                             "predictions or evaluations.")

        try:
            request = RFMValidateQueryRequest(
                query=query,
                graph_definition=self._graph_def,
            )

            resp = global_state.client.rfm_api.validate_query(request)
            # TODO Expose validation warnings.

            if len(resp.validation_response.warnings) > 0:
                msg = '\n'.join([
                    f'{i+1}. {warning.title}: {warning.message}' for i, warning
                    in enumerate(resp.validation_response.warnings)
                ])
                warnings.warn(f"Encountered the following warnings during "
                              f"parsing:\n{msg}")

            return resp.query_definition
        except HTTPException as e:
            try:
                msg = json.loads(e.detail)['detail']
            except Exception:
                msg = e.detail
            raise ValueError(f"Failed to parse query '{query}'. "
                             f"{msg}") from None

    def _validate_time(
        self,
        query: PQueryDefinition,
        anchor_time: pd.Timestamp,
        context_anchor_time: Union[pd.Timestamp, None],
        evaluate: bool,
    ) -> None:

        if self._graph_store.min_time == pd.Timestamp.max:
            return  # Graph without timestamps

        if anchor_time < self._graph_store.min_time:
            raise ValueError(f"Anchor timestamp '{anchor_time}' is before "
                             f"the earliest timestamp "
                             f"'{self._graph_store.min_time}' in the data.")

        if (context_anchor_time is not None
                and context_anchor_time < self._graph_store.min_time):
            raise ValueError(f"Context anchor timestamp is too early or "
                             f"aggregation time range is too large. To make "
                             f"this prediction, we would need data back to "
                             f"'{context_anchor_time}', however, your data "
                             f"only contains data back to "
                             f"'{self._graph_store.min_time}'.")

        if (context_anchor_time is not None
                and context_anchor_time > anchor_time):
            warnings.warn(f"Context anchor timestamp "
                          f"(got '{context_anchor_time}') is set to a later "
                          f"date than the prediction anchor timestamp "
                          f"(got '{anchor_time}'). Please make sure this is "
                          f"intended.")
        elif (query.query_type == QueryType.TEMPORAL
              and context_anchor_time is not None and context_anchor_time +
              query.target.end_offset * query.num_forecasts > anchor_time):
            warnings.warn(f"Aggregation for context examples at timestamp "
                          f"'{context_anchor_time}' will leak information "
                          f"from the prediction anchor timestamp "
                          f"'{anchor_time}'. Please make sure this is "
                          f"intended.")

        elif (context_anchor_time is not None and context_anchor_time -
              query.target.end_offset * query.num_forecasts
              < self._graph_store.min_time):
            _time = context_anchor_time - (query.target.end_offset *
                                           query.num_forecasts)
            warnings.warn(f"Context anchor timestamp is too early or "
                          f"aggregation time range is too large. To form "
                          f"proper input data, we would need data back to "
                          f"'{_time}', however, your data only contains "
                          f"data back to '{self._graph_store.min_time}'.")

        if (not evaluate and anchor_time
                > self._graph_store.max_time + pd.DateOffset(days=1)):
            warnings.warn(f"Anchor timestamp '{anchor_time}' is after the "
                          f"latest timestamp '{self._graph_store.max_time}' "
                          f"in the data. Please make sure this is intended.")

        max_eval_time = (self._graph_store.max_time -
                         query.target.end_offset * query.num_forecasts)
        if evaluate and anchor_time > max_eval_time:
            raise ValueError(
                f"Anchor timestamp for evaluation is after the latest "
                f"supported timestamp '{max_eval_time}'.")

    def _get_context(
        self,
        query: PQueryDefinition,
        indices: Union[List[str], List[float], List[int], None],
        anchor_time: Union[pd.Timestamp, Literal['entity'], None],
        context_anchor_time: Union[pd.Timestamp, None],
        run_mode: RunMode,
        num_neighbors: Optional[List[int]],
        num_hops: int,
        max_pq_iterations: int,
        evaluate: bool,
        random_seed: Optional[int] = _RANDOM_SEED,
        logger: Optional[ProgressLogger] = None,
    ) -> Context:

        if num_neighbors is not None:
            num_hops = len(num_neighbors)

        if num_hops < 0:
            raise ValueError(f"'num_hops' must be non-negative "
                             f"(got {num_hops})")
        if num_hops > 6:
            raise ValueError(f"Cannot predict on subgraphs with more than 6 "
                             f"hops (got {num_hops}). Please reduce the "
                             f"number of hops and try again. Please create a "
                             f"feature request at "
                             f"'https://github.com/kumo-ai/kumo-rfm' if you "
                             f"must go beyond this for your use-case.")

        query_driver = LocalPQueryDriver(self._graph_store, query, random_seed)
        task_type = query.get_task_type(
            stypes=self._graph_store.stype_dict,
            edge_types=self._graph_store.edge_types,
        )

        if logger is not None:
            if task_type == TaskType.BINARY_CLASSIFICATION:
                task_type_repr = 'binary classification'
            elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
                task_type_repr = 'multi-class classification'
            elif task_type == TaskType.REGRESSION:
                task_type_repr = 'regression'
            elif task_type == TaskType.TEMPORAL_LINK_PREDICTION:
                task_type_repr = 'link prediction'
            else:
                task_type_repr = str(task_type)
            logger.log(f"Identified {query.query_type} {task_type_repr} task")

        if task_type.is_link_pred and num_hops < 2:
            raise ValueError(f"Cannot perform link prediction on subgraphs "
                             f"with less than 2 hops (got {num_hops}) since "
                             f"historical target entities need to be part of "
                             f"the context. Please increase the number of "
                             f"hops and try again.")

        if num_neighbors is None:
            if run_mode == RunMode.DEBUG:
                num_neighbors = [16, 16, 4, 4, 1, 1][:num_hops]
            elif run_mode == RunMode.FAST or task_type.is_link_pred:
                num_neighbors = [32, 32, 8, 8, 4, 4][:num_hops]
            else:
                num_neighbors = [64, 64, 8, 8, 4, 4][:num_hops]

        if anchor_time is None:
            anchor_time = self._graph_store.max_time
            if evaluate:
                anchor_time = anchor_time - (query.target.end_offset *
                                             query.num_forecasts)
            if logger is not None:
                assert isinstance(anchor_time, pd.Timestamp)
                if anchor_time == pd.Timestamp.min:
                    pass  # Static graph
                elif (anchor_time.hour == 0 and anchor_time.minute == 0
                      and anchor_time.second == 0
                      and anchor_time.microsecond == 0):
                    logger.log(f"Derived anchor time {anchor_time.date()}")
                else:
                    logger.log(f"Derived anchor time {anchor_time}")

        assert anchor_time is not None
        if isinstance(anchor_time, pd.Timestamp):
            if context_anchor_time is None:
                context_anchor_time = anchor_time - (query.target.end_offset *
                                                     query.num_forecasts)
            self._validate_time(query, anchor_time, context_anchor_time,
                                evaluate)
        else:
            assert anchor_time == 'entity'
            if query.entity.pkey.table_name not in self._graph_store.time_dict:
                raise ValueError(f"Anchor time 'entity' requires the entity "
                                 f"table '{query.entity.pkey.table_name}' to "
                                 f"have a time column")
            if context_anchor_time is not None:
                warnings.warn("Ignoring option 'context_anchor_time' for "
                              "`anchor_time='entity'`")
            context_anchor_time = None

        y_test: Optional[pd.Series] = None
        if evaluate:
            max_test_size = _MAX_TEST_SIZE[run_mode]
            if task_type.is_link_pred:
                max_test_size = max_test_size // 5

            test_node, test_time, y_test = query_driver.collect_test(
                size=max_test_size,
                anchor_time=anchor_time,
                max_iterations=max_pq_iterations,
                guarantee_train_examples=True,
            )
            if logger is not None:
                if task_type == TaskType.BINARY_CLASSIFICATION:
                    pos = 100 * int((y_test > 0).sum()) / len(y_test)
                    msg = (f"Collected {len(y_test):,} test examples with "
                           f"{pos:.2f}% positive cases")
                elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
                    msg = (f"Collected {len(y_test):,} test examples "
                           f"holding {y_test.nunique()} classes")
                elif task_type == TaskType.REGRESSION:
                    _min, _max = float(y_test.min()), float(y_test.max())
                    msg = (f"Collected {len(y_test):,} test examples with "
                           f"targets between {format_value(_min)} and "
                           f"{format_value(_max)}")
                elif task_type == TaskType.TEMPORAL_LINK_PREDICTION:
                    num_rhs = y_test.explode().nunique()
                    msg = (f"Collected {len(y_test):,} test examples with "
                           f"{num_rhs:,} unique items")
                else:
                    raise NotImplementedError
                logger.log(msg)

        else:
            assert indices is not None

            if len(indices) > _MAX_PRED_SIZE[task_type]:
                raise ValueError(f"Cannot predict for more than "
                                 f"{_MAX_PRED_SIZE[task_type]:,} entities at "
                                 f"once (got {len(indices):,}). Use "
                                 f"`KumoRFM.batch_mode` to process entities "
                                 f"in batches")

            test_node = self._graph_store.get_node_id(
                table_name=query.entity.pkey.table_name,
                pkey=pd.Series(indices),
            )

            if isinstance(anchor_time, pd.Timestamp):
                test_time = pd.Series(anchor_time).repeat(
                    len(test_node)).reset_index(drop=True)
            else:
                time = self._graph_store.time_dict[
                    query.entity.pkey.table_name]
                time = time[test_node] * 1000**3
                test_time = pd.Series(time, dtype='datetime64[ns]')

        train_node, train_time, y_train = query_driver.collect_train(
            size=_MAX_CONTEXT_SIZE[run_mode],
            anchor_time=context_anchor_time or 'entity',
            exclude_node=test_node if (query.query_type == QueryType.STATIC
                                       or anchor_time == 'entity') else None,
            max_iterations=max_pq_iterations,
        )

        if logger is not None:
            if task_type == TaskType.BINARY_CLASSIFICATION:
                pos = 100 * int((y_train > 0).sum()) / len(y_train)
                msg = (f"Collected {len(y_train):,} in-context examples with "
                       f"{pos:.2f}% positive cases")
            elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
                msg = (f"Collected {len(y_train):,} in-context examples "
                       f"holding {y_train.nunique()} classes")
            elif task_type == TaskType.REGRESSION:
                _min, _max = float(y_train.min()), float(y_train.max())
                msg = (f"Collected {len(y_train):,} in-context examples with "
                       f"targets between {format_value(_min)} and "
                       f"{format_value(_max)}")
            elif task_type == TaskType.TEMPORAL_LINK_PREDICTION:
                num_rhs = y_train.explode().nunique()
                msg = (f"Collected {len(y_train):,} in-context examples with "
                       f"{num_rhs:,} unique items")
            else:
                raise NotImplementedError
            logger.log(msg)

        entity_table_names = query.get_entity_table_names(
            self._graph_store.edge_types)

        # Exclude the entity anchor time from the feature set to prevent
        # running out-of-distribution between in-context and test examples:
        exclude_cols_dict = query.exclude_cols_dict
        if anchor_time == 'entity':
            if entity_table_names[0] not in exclude_cols_dict:
                exclude_cols_dict[entity_table_names[0]] = []
            time_column_dict = self._graph_store.time_column_dict
            time_column = time_column_dict[entity_table_names[0]]
            exclude_cols_dict[entity_table_names[0]].append(time_column)

        subgraph = self._graph_sampler(
            entity_table_names=entity_table_names,
            node=np.concatenate([train_node, test_node]),
            time=np.concatenate([
                train_time.astype('datetime64[ns]').astype(int).to_numpy(),
                test_time.astype('datetime64[ns]').astype(int).to_numpy(),
            ]),
            run_mode=run_mode,
            num_neighbors=num_neighbors,
            exclude_cols_dict=exclude_cols_dict,
        )

        if len(subgraph.table_dict) >= 15:
            raise ValueError(f"Cannot query from a graph with more than 15 "
                             f"tables (got {len(subgraph.table_dict)}). "
                             f"Please create a feature request at "
                             f"'https://github.com/kumo-ai/kumo-rfm' if you "
                             f"must go beyond this for your use-case.")

        step_size: Optional[int] = None
        if query.query_type == QueryType.TEMPORAL:
            step_size = date_offset_to_seconds(query.target.end_offset)

        return Context(
            task_type=task_type,
            entity_table_names=entity_table_names,
            subgraph=subgraph,
            y_train=y_train,
            y_test=y_test,
            top_k=query.top_k,
            step_size=step_size,
        )

    @staticmethod
    def _validate_metrics(
        metrics: List[str],
        task_type: TaskType,
    ) -> None:

        if task_type == TaskType.BINARY_CLASSIFICATION:
            supported_metrics = [
                'acc', 'precision', 'recall', 'f1', 'auroc', 'auprc', 'ap'
            ]
        elif task_type == TaskType.MULTICLASS_CLASSIFICATION:
            supported_metrics = ['acc', 'precision', 'recall', 'f1', 'mrr']
        elif task_type == TaskType.REGRESSION:
            supported_metrics = ['mae', 'mape', 'mse', 'rmse', 'smape', 'r2']
        elif task_type == TaskType.TEMPORAL_LINK_PREDICTION:
            supported_metrics = [
                'map@', 'ndcg@', 'mrr@', 'precision@', 'recall@', 'f1@',
                'hit_ratio@'
            ]
        else:
            raise NotImplementedError

        for metric in metrics:
            if '@' in metric:
                metric_split = metric.split('@')
                if len(metric_split) != 2:
                    raise ValueError(f"Unsupported metric '{metric}'. "
                                     f"Available metrics "
                                     f"are {supported_metrics}.")

                name, top_k = f'{metric_split[0]}@', metric_split[1]

                if not top_k.isdigit():
                    raise ValueError(f"Metric '{metric}' does not define a "
                                     f"valid 'top_k' value (got '{top_k}').")

                if int(top_k) <= 0:
                    raise ValueError(f"Metric '{metric}' needs to define a "
                                     f"positive 'top_k' value (got '{top_k}')")

                if int(top_k) > 100:
                    raise ValueError(f"Metric '{metric}' defines a 'top_k' "
                                     f"value greater than 100 "
                                     f"(got '{top_k}'). Please create a "
                                     f"feature request at "
                                     f"'https://github.com/kumo-ai/kumo-rfm' "
                                     f"if you must go beyond this for your "
                                     f"use-case.")

                metric = name

            if metric not in supported_metrics:
                raise ValueError(f"Unsupported metric '{metric}'. Available "
                                 f"metrics are {supported_metrics}. If you "
                                 f"feel a metric is missing, please create a "
                                 f"feature request at "
                                 f"'https://github.com/kumo-ai/kumo-rfm'.")


def format_value(value: Union[int, float]) -> str:
    if value == int(value):
        return f'{int(value):,}'
    if abs(value) >= 1000:
        return f'{value:,.0f}'
    if abs(value) >= 10:
        return f'{value:.1f}'
    return f'{value:.2f}'
