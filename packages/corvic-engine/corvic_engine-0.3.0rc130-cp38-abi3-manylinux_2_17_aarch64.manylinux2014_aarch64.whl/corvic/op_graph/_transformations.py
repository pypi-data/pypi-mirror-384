import copy
from collections.abc import Sequence
from typing import Literal, cast

import corvic.op_graph.ops as op
from corvic import result


def _replace_join_op_source(
    join_op: op.Join, source_indexes: Sequence[int], new_sources: Sequence[op.Op]
):
    for i, source in zip(source_indexes, new_sources, strict=True):
        if i == 0:
            return source.join(
                join_op.right_source,
                join_op.left_join_columns,
                join_op.right_join_columns,
                how=join_op.how,
            )

        if i == 1:
            return join_op.left_source.join(
                source,
                join_op.left_join_columns,
                join_op.right_join_columns,
                how=join_op.how,
            )

    return result.InvalidArgumentError("source_idx is out of bounds")


def _replace_rollup_by_aggregation_op_source(
    rollup_op: op.RollupByAggregation,
    source_indexes: Sequence[int],
    new_sources: Sequence[op.Op],
):
    return new_sources[0].rollup_by_aggregation(
        group_by=rollup_op.group_by_column_names,
        target=rollup_op.target_column_name,
        aggregation=rollup_op.aggregation_type,
    )


def _replace_embed_node2vec_from_edge_lists_op(
    node2vec_op: op.EmbedNode2vecFromEdgeLists,
    source_indexes: Sequence[int],
    new_sources: Sequence[op.Op],
):
    new_edge_list_tables = copy.copy(node2vec_op.edge_list_tables)
    for i, new_source in zip(source_indexes, new_sources, strict=True):
        elt = new_edge_list_tables[i]
        new_edge_list_tables[i] = op.EdgeListTable(
            new_source,
            start_column_name=elt.start_column_name,
            end_column_name=elt.end_column_name,
            start_entity_name=elt.start_entity_name,
            end_entity_name=elt.end_entity_name,
        )
    return op.embed_node2vec_from_edge_lists(
        new_edge_list_tables,
        node2vec_op.to_proto().embed_node2vec_from_edge_lists.node2vec_parameters,
    )


def _replace_concat_op_source(
    concat_op: op.Concat, source_indexes: Sequence[int], new_source: Sequence[op.Op]
):
    new_tables = copy.copy(concat_op.tables)
    for i, table in zip(source_indexes, new_source, strict=True):
        new_tables[i] = table
    return op.concat(new_tables, concat_op.how)


def replace_op_sources(  # noqa: C901
    root_op: op.Op, source_indexes: Sequence[int], new_sources: Sequence[op.Op]
) -> result.Ok[op.Op] | result.InvalidArgumentError:
    if any(source_index >= len(root_op.sources()) for source_index in source_indexes):
        return result.InvalidArgumentError("source_index is out of bounds")

    match root_op:
        case (
            op.SelectFromStaging()
            | op.Empty()
            | op.SelectFromVectorStaging()
            | op.ReadFromParquet()
            | op.InMemoryInput()
        ):
            return result.InvalidArgumentError(
                "root_op does not have a source to replace"
            )
        case op.RenameColumns():
            return new_sources[0].rename_columns(root_op.old_name_to_new)
        case op.Join():
            return _replace_join_op_source(root_op, source_indexes, new_sources)
        case op.SelectColumns():
            return new_sources[0].select_columns(root_op.columns)
        case op.LimitRows():
            return new_sources[0].limit_rows(root_op.num_rows)
        case op.OffsetRows():
            return new_sources[0].offset_rows(root_op.num_rows)
        case op.OrderBy():
            return new_sources[0].order_by(root_op.columns, desc=root_op.desc)
        case op.FilterRows():
            return new_sources[0].filter_rows(row_filter=root_op.row_filter)
        case op.DistinctRows():
            return new_sources[0].distinct_rows()
        case op.UpdateMetadata():
            return new_sources[0].update_metadata(root_op.metadata_updates)
        case op.SetMetadata():
            return new_sources[0].set_metadata(root_op.new_metadata)
        case op.RemoveFromMetadata():
            return new_sources[0].remove_from_metadata(root_op.keys_to_remove)
        case op.UpdateFeatureTypes():
            return new_sources[0].update_feature_types(root_op.new_feature_types)
        case op.RollupByAggregation():
            return _replace_rollup_by_aggregation_op_source(
                root_op, source_indexes, new_sources
            )
        case op.EmbedNode2vecFromEdgeLists():
            return _replace_embed_node2vec_from_edge_lists_op(
                root_op, source_indexes, new_sources
            )
        case op.EmbeddingMetrics():
            return op.quality_metrics_from_embedding(
                new_sources[0], root_op.embedding_column_name
            )
        case op.EmbeddingCoordinates():
            return op.coordinates_from_embedding(
                new_sources[0],
                root_op.embedding_column_name,
                root_op.n_components,
                cast(Literal["cosine", "euclidean"], root_op.metric),
            )
        case op.Concat():
            return _replace_concat_op_source(root_op, source_indexes, new_sources)
        case op.UnnestStruct():
            return new_sources[0].unnest_struct(root_op.struct_column_name)
        case op.NestIntoStruct():
            return new_sources[0].nest_into_struct(
                root_op.struct_column_name, root_op.column_names_to_nest
            )
        case op.AddLiteralColumn():
            new_proto = root_op.to_proto()
            new_proto.add_literal_column.source.CopyFrom(new_sources[0].to_proto())
            return result.Ok(op.from_proto(new_proto, skip_validate=True))
        case op.CombineColumns():
            new_proto = root_op.to_proto()
            new_proto.combine_columns.source.CopyFrom(new_sources[0].to_proto())
            return result.Ok(op.from_proto(new_proto, skip_validate=True))
        case op.EmbedColumn():
            return new_sources[0].embed_column(
                column_name=root_op.column_name,
                embedding_column_name=root_op.embedding_column_name,
                model_name=root_op.model_name,
                tokenizer_name=root_op.tokenizer_name,
                expected_vector_length=root_op.expected_vector_length,
                expected_coordinate_bitwidth=root_op.expected_coordinate_bitwidth,
            )
        case op.EncodeColumns():
            return new_sources[0].encode_columns(root_op.encoded_columns)
        case op.AggregateColumns():
            return new_sources[0].aggregate_columns(
                root_op.column_names, root_op.aggregation
            )
        case op.CorrelateColumns():
            return new_sources[0].correlate_columns(root_op.column_names)
        case op.HistogramColumn():
            return new_sources[0].histogram(
                root_op.column_name,
                breakpoint_column_name=root_op.breakpoint_column_name,
                count_column_name=root_op.count_column_name,
            )
        case op.ConvertColumnToString():
            return new_sources[0].convert_column_to_string(root_op.column_name)
        case op.AddRowIndex():
            return new_sources[0].add_row_index(
                root_op.row_index_column_name, offset=root_op.offset
            )
        case op.OutputCsv():
            return new_sources[0].output_csv(
                url=root_op.csv_url, include_header=root_op.include_header
            )
        case op.TruncateList():
            new_proto = root_op.to_proto()
            new_proto.truncate_list.source.CopyFrom(new_sources[0].to_proto())
            return result.Ok(op.from_proto(new_proto, skip_validate=True))
        case op.Union():
            new_tables = root_op.sources()
            for i, new_source in zip(source_indexes, new_sources, strict=True):
                new_tables[i] = new_source
            return op.union(new_tables, distinct=root_op.distinct)
        case op.EmbedImageColumn():
            return new_sources[0].embed_image_column(
                column_name=root_op.column_name,
                embedding_column_name=root_op.embedding_column_name,
                model_name=root_op.model_name,
                expected_vector_length=root_op.expected_vector_length,
                expected_coordinate_bitwidth=root_op.expected_coordinate_bitwidth,
            )
        case op.AddDecisionTreeSummary():
            return new_sources[0].add_decision_tree_summary(
                feature_column_names=root_op.feature_column_names,
                label_column_name=root_op.label_column_name,
                max_depth=root_op.max_depth,
                output_metric_key=root_op.output_metric_key,
                classes_names=root_op.classes_names,
            )
        case op.UnnestList():
            return new_sources[0].unnest_list(
                list_column_name=root_op.list_column_name,
                new_column_names=root_op.column_names,
            )
        case op.SampleRows():
            return new_sources[0].sample_rows(
                sample_strategy=root_op.sample_strategy, num_rows=root_op.num_rows
            )
        case op.DescribeColumns():
            return new_sources[0].describe(
                column_names=root_op.column_names,
                interpolation=root_op.interpolation,
                statistic_column_name=root_op.statistic_column_name,
            )
    return result.InvalidArgumentError("could not identify root_op")
