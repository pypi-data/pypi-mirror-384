import warnings
from typing import Dict, List, Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd
from kumoapi.pquery import QueryType
from kumoapi.rfm import PQueryDefinition

import kumoai.kumolib as kumolib
from kumoai.experimental.rfm.local_graph_store import LocalGraphStore
from kumoai.experimental.rfm.pquery import PQueryPandasBackend

_coverage_warned = False


class LocalPQueryDriver:
    def __init__(
        self,
        graph_store: LocalGraphStore,
        query: PQueryDefinition,
        random_seed: Optional[int] = None,
    ) -> None:
        self._graph_store = graph_store
        self._query = query
        self._random_seed = random_seed
        self._rng = np.random.default_rng(random_seed)

    def _get_candidates(
        self,
        exclude_node: Optional[np.ndarray] = None,
    ) -> np.ndarray:

        if self._query.query_type == QueryType.TEMPORAL:
            assert exclude_node is None

        table_name = self._query.entity.pkey.table_name
        num_nodes = len(self._graph_store.df_dict[table_name])
        mask_dict = self._graph_store.mask_dict

        candidate: np.ndarray

        # Case 1: All nodes are valid and nothing to exclude:
        if exclude_node is None and table_name not in mask_dict:
            candidate = np.arange(num_nodes)

        # Case 2: Not all nodes are valid - lookup valid nodes:
        if exclude_node is None:
            pkey_map = self._graph_store.pkey_map_dict[table_name]
            candidate = pkey_map['arange'].to_numpy().copy()

        # Case 3: Exclude nodes - use a mask to exclude them:
        else:
            mask = np.full((num_nodes, ), fill_value=True, dtype=bool)
            mask[exclude_node] = False
            if table_name in mask_dict:
                mask &= mask_dict[table_name]
            candidate = mask.nonzero()[0]

        self._rng.shuffle(candidate)

        return candidate

    def _filter_candidates_by_time(
        self,
        candidate: np.ndarray,
        anchor_time: pd.Timestamp,
    ) -> np.ndarray:

        entity = self._query.entity.pkey.table_name

        # Filter out entities that do not exist yet in time:
        time_sec = self._graph_store.time_dict.get(entity)
        if time_sec is not None:
            mask = time_sec[candidate] <= (anchor_time.value // (1000**3))
            candidate = candidate[mask]

        # Filter out entities that no longer exist in time:
        end_time_col = self._graph_store.end_time_column_dict.get(entity)
        if end_time_col is not None:
            ser = self._graph_store.df_dict[entity][end_time_col]
            ser = ser.iloc[candidate]
            mask = (anchor_time < ser) | ser.isna().to_numpy()
            candidate = candidate[mask]

        return candidate

    def collect_test(
        self,
        size: int,
        anchor_time: Union[pd.Timestamp, Literal['entity']],
        batch_size: Optional[int] = None,
        max_iterations: int = 20,
        guarantee_train_examples: bool = True,
    ) -> Tuple[np.ndarray, pd.Series, pd.Series]:
        r"""Collects test nodes and their labels used for evaluation.

        Args:
            size: The number of test nodes to collect.
            anchor_time: The anchor time.
            batch_size: How many nodes to process in a single batch.
            max_iterations: The number of steps to run before aborting.
            guarantee_train_examples: Ensures that test examples do not occupy
                the entire set of entity candidates.

        Returns:
            A triplet holding the nodes, timestamps and labels.
        """
        batch_size = size if batch_size is None else batch_size

        candidate = self._get_candidates()

        nodes: List[np.ndarray] = []
        times: List[pd.Series] = []
        ys: List[pd.Series] = []

        reached_end = False
        num_labels = candidate_offset = 0
        for _ in range(max_iterations):
            node = candidate[candidate_offset:candidate_offset + batch_size]

            if isinstance(anchor_time, pd.Timestamp):
                node = self._filter_candidates_by_time(node, anchor_time)
                time = pd.Series(anchor_time).repeat(len(node))
                time = time.astype('datetime64[ns]').reset_index(drop=True)
            else:
                assert anchor_time == 'entity'
                time = self._graph_store.time_dict[
                    self._query.entity.pkey.table_name]
                time = pd.Series(time[node] * 1000**3, dtype='datetime64[ns]')

            y, mask = self(node, time)

            nodes.append(node[mask])
            times.append(time[mask].reset_index(drop=True))
            ys.append(y)

            num_labels += len(y)

            if num_labels > size:
                reached_end = True
                break  # Sufficient number of labels collected. Abort.

            candidate_offset += batch_size
            if candidate_offset >= len(candidate):
                reached_end = True
                break

        if len(nodes) > 1:
            node = np.concatenate(nodes, axis=0)[:size]
            time = pd.concat(times, axis=0).reset_index(drop=True).iloc[:size]
            y = pd.concat(ys, axis=0).reset_index(drop=True).iloc[:size]
        else:
            node = nodes[0][:size]
            time = times[0].iloc[:size]
            y = ys[0].iloc[:size]

        if len(node) == 0:
            raise RuntimeError("Failed to collect any test examples for "
                               "evaluation. Is your predictive query too "
                               "restrictive?")

        global _coverage_warned
        if not _coverage_warned and not reached_end and len(node) < size // 2:
            _coverage_warned = True
            warnings.warn(f"Failed to collect {size:,} test examples within "
                          f"{max_iterations} iterations. To improve coverage, "
                          f"consider increasing the number of PQ iterations "
                          f"using the 'max_pq_iterations' option. This "
                          f"warning will not be shown again in this run.")

        if (guarantee_train_examples
                and self._query.query_type == QueryType.STATIC
                and candidate_offset >= len(candidate)):
            # In case all valid entities are used as test examples, we can no
            # longer find any training example. Fallback to a 50/50 split:
            size = len(node) // 2
            node = node[:size]
            time = time.iloc[:size]
            y = y.iloc[:size]

        return node, time, y

    def collect_train(
        self,
        size: int,
        anchor_time: Union[pd.Timestamp, Literal['entity']],
        exclude_node: Optional[np.ndarray] = None,
        batch_size: Optional[int] = None,
        max_iterations: int = 20,
    ) -> Tuple[np.ndarray, pd.Series, pd.Series]:
        r"""Collects training nodes and their labels.

        Args:
            size: The number of test nodes to collect.
            anchor_time: The anchor time.
            exclude_node: The nodes to exclude for use as in-context examples.
            batch_size: How many nodes to process in a single batch.
            max_iterations: The number of steps to run before aborting.

        Returns:
            A triplet holding the nodes, timestamps and labels.
        """
        batch_size = size if batch_size is None else batch_size

        candidate = self._get_candidates(exclude_node)

        if len(candidate) == 0:
            raise RuntimeError("Failed to generate any context examples "
                               "since not enough entities exist")

        nodes: List[np.ndarray] = []
        times: List[pd.Series] = []
        ys: List[pd.Series] = []

        reached_end = False
        num_labels = candidate_offset = 0
        for _ in range(max_iterations):
            node = candidate[candidate_offset:candidate_offset + batch_size]

            if isinstance(anchor_time, pd.Timestamp):
                node = self._filter_candidates_by_time(node, anchor_time)
                time = pd.Series(anchor_time).repeat(len(node))
                time = time.astype('datetime64[ns]').reset_index(drop=True)
            else:
                assert anchor_time == 'entity'
                time = self._graph_store.time_dict[
                    self._query.entity.pkey.table_name]
                time = pd.Series(time[node] * 1000**3, dtype='datetime64[ns]')

            y, mask = self(node, time)

            nodes.append(node[mask])
            times.append(time[mask].reset_index(drop=True))
            ys.append(y)

            num_labels += len(y)

            if num_labels > size:
                reached_end = True
                break  # Sufficient number of labels collected. Abort.

            candidate_offset += batch_size
            if candidate_offset >= len(candidate):
                # Restart with an earlier anchor time (if applicable).
                if self._query.query_type == QueryType.STATIC:
                    reached_end = True
                    break  # Cannot jump back in time for static PQs. Abort.
                if anchor_time == 'entity':
                    reached_end = True
                    break
                candidate_offset = 0
                anchor_time = anchor_time - (self._query.target.end_offset *
                                             self._query.num_forecasts)
                if anchor_time < self._graph_store.min_time:
                    reached_end = True
                    break  # No earlier anchor time left. Abort.

        if len(nodes) > 1:
            node = np.concatenate(nodes, axis=0)[:size]
            time = pd.concat(times, axis=0).reset_index(drop=True).iloc[:size]
            y = pd.concat(ys, axis=0).reset_index(drop=True).iloc[:size]
        else:
            node = nodes[0][:size]
            time = times[0].iloc[:size]
            y = ys[0].iloc[:size]

        if len(node) == 0:
            raise ValueError("Failed to collect any context examples. Is your "
                             "predictive query too restrictive?")

        global _coverage_warned
        if not _coverage_warned and not reached_end and len(node) < size // 2:
            _coverage_warned = True
            warnings.warn(f"Failed to collect {size:,} context examples "
                          f"within {max_iterations} iterations. To improve "
                          f"coverage, consider increasing the number of PQ "
                          f"iterations using the 'max_pq_iterations' option. "
                          f"This warning will not be shown again in this run.")

        return node, time, y

    def is_valid(
        self,
        node: np.ndarray,
        anchor_time: Union[pd.Timestamp, Literal['entity']],
        batch_size: int = 10_000,
    ) -> np.ndarray:
        r"""Denotes which nodes are valid for a given anchor time, *e.g.*,
        which nodes fulfill entity filter constraints.

        Args:
            node: The nodes to check for.
            anchor_time: The anchor time.
            batch_size: How many nodes to process in a single batch.

        Returns:
            The mask.
        """
        mask: Optional[np.ndarray] = None

        if isinstance(anchor_time, pd.Timestamp):
            node = self._filter_candidates_by_time(node, anchor_time)
            time = pd.Series(anchor_time).repeat(len(node))
            time = time.astype('datetime64[ns]').reset_index(drop=True)
        else:
            assert anchor_time == 'entity'
            time = self._graph_store.time_dict[
                self._query.entity.pkey.table_name]
            time = pd.Series(time[node] * 1000**3, dtype='datetime64[ns]')

        if self._query.entity.filter is not None:
            # Mask out via (temporal) entity filter:
            backend = PQueryPandasBackend()
            masks: List[np.ndarray] = []
            for start in range(0, len(node), batch_size):
                feat_dict, time_dict, batch_dict = self._sample(
                    node[start:start + batch_size],
                    time.iloc[start:start + batch_size],
                )
                _mask = backend.eval_filter(
                    filter=self._query.entity.filter,
                    feat_dict=feat_dict,
                    time_dict=time_dict,
                    batch_dict=batch_dict,
                    anchor_time=time.iloc[start:start + batch_size],
                )
                masks.append(_mask)

            _mask = np.concatenate(masks)
            mask = (mask & _mask) if mask is not None else _mask

        if mask is None:
            mask = np.ones(len(node), dtype=bool)

        return mask

    def _sample(
        self,
        node: np.ndarray,
        anchor_time: pd.Series,
    ) -> Tuple[
            Dict[str, pd.DataFrame],
            Dict[str, pd.Series],
            Dict[str, np.ndarray],
    ]:
        r"""Samples a subgraph that contains all relevant information to
        evaluate the predictive query.

        Args:
            node: The nodes to check for.
            anchor_time: The anchor time.

        Returns:
            The feature dictionary, the time column dictionary and the batch
            dictionary.
        """
        specs = self._query.get_sampling_specs(self._graph_store.edge_types)
        num_hops = max([spec.hop for spec in specs] + [0])
        num_neighbors: Dict[Tuple[str, str, str], list[int]] = {}
        time_offsets: Dict[
            Tuple[str, str, str],
            List[List[Optional[int]]],
        ] = {}
        for spec in specs:
            if spec.end_offset is not None:
                if spec.edge_type not in time_offsets:
                    time_offsets[spec.edge_type] = [[0, 0]
                                                    for _ in range(num_hops)]
                offset: Optional[int] = date_offset_to_seconds(spec.end_offset)
                time_offsets[spec.edge_type][spec.hop - 1][1] = offset
                if spec.start_offset is not None:
                    offset = date_offset_to_seconds(spec.start_offset)
                else:
                    offset = None
                time_offsets[spec.edge_type][spec.hop - 1][0] = offset
            else:
                if spec.edge_type not in num_neighbors:
                    num_neighbors[spec.edge_type] = [0] * num_hops
                num_neighbors[spec.edge_type][spec.hop - 1] = -1

        edge_types = list(num_neighbors.keys()) + list(time_offsets.keys())
        node_types = list(
            set([self._query.entity.pkey.table_name])
            | set(src for src, _, _ in edge_types)
            | set(dst for _, _, dst in edge_types))

        sampler = kumolib.NeighborSampler(
            node_types,
            edge_types,
            {
                '__'.join(edge_type): self._graph_store.colptr_dict[edge_type]
                for edge_type in edge_types
            },
            {
                '__'.join(edge_type): self._graph_store.row_dict[edge_type]
                for edge_type in edge_types
            },
            {
                node_type: time
                for node_type, time in self._graph_store.time_dict.items()
                if node_type in node_types
            },
        )

        anchor_time = anchor_time.astype('datetime64[ns]')
        _, _, node_dict, batch_dict, _, _ = sampler.sample(
            {
                '__'.join(edge_type): np.array(values)
                for edge_type, values in num_neighbors.items()
            },
            {
                '__'.join(edge_type): np.array(values)
                for edge_type, values in time_offsets.items()
            },
            self._query.entity.pkey.table_name,
            node,
            anchor_time.astype(int).to_numpy() // 1000**3,
        )

        feat_dict: Dict[str, pd.DataFrame] = {}
        time_dict: Dict[str, pd.Series] = {}
        column_dict = self._query.column_dict
        time_tables = self._query.time_tables
        for table_name in set(list(column_dict.keys()) + time_tables):
            df = self._graph_store.df_dict[table_name]
            row_id = node_dict[table_name]
            df = df.iloc[row_id].reset_index(drop=True)
            if table_name in column_dict:
                feat_dict[table_name] = df[list(column_dict[table_name])]
            if table_name in time_tables:
                time_col = self._graph_store.time_column_dict[table_name]
                time_dict[table_name] = df[time_col]

        return feat_dict, time_dict, batch_dict

    def __call__(
        self,
        node: np.ndarray,
        anchor_time: pd.Series,
    ) -> Tuple[pd.Series, np.ndarray]:

        feat_dict, time_dict, batch_dict = self._sample(node, anchor_time)

        y, mask = PQueryPandasBackend().eval_pquery(
            query=self._query,
            feat_dict=feat_dict,
            time_dict=time_dict,
            batch_dict=batch_dict,
            anchor_time=anchor_time,
            num_forecasts=self._query.num_forecasts,
        )

        return y, mask


def date_offset_to_seconds(offset: pd.DateOffset) -> int:
    r"""Convert a :class:`pandas.DateOffset` into a maximum number of
    nanoseconds.

    .. note::
        We are conservative and take months and years as their maximum value.
        Additional values are then dropped in label computation where we know
        the actual dates.
    """
    # Max durations for months and years in nanoseconds:
    MAX_DAYS_IN_MONTH = 31
    MAX_DAYS_IN_YEAR = 366

    # Conversion factors:
    SECONDS_IN_MINUTE = 60
    SECONDS_IN_HOUR = 60 * SECONDS_IN_MINUTE
    SECONDS_IN_DAY = 24 * SECONDS_IN_HOUR

    total_ns = 0
    multiplier = getattr(offset, 'n', 1)  # The multiplier (if present).

    for attr, value in offset.__dict__.items():
        if value is None or value == 0:
            continue
        scaled_value = value * multiplier
        if attr == 'years':
            total_ns += scaled_value * MAX_DAYS_IN_YEAR * SECONDS_IN_DAY
        elif attr == 'months':
            total_ns += scaled_value * MAX_DAYS_IN_MONTH * SECONDS_IN_DAY
        elif attr == 'days':
            total_ns += scaled_value * SECONDS_IN_DAY
        elif attr == 'hours':
            total_ns += scaled_value * SECONDS_IN_HOUR
        elif attr == 'minutes':
            total_ns += scaled_value * SECONDS_IN_MINUTE
        elif attr == 'seconds':
            total_ns += scaled_value

    return total_ns
