//! Create pipeline graph for a ScopeView

use std::collections::HashMap;

use ligo_hires_gps_time::PipDuration;
use petgraph::graph::NodeIndex;

use crate::analysis::graph::analysis::{AnalysisEdge, AnalysisGraph, AnalysisNode};
use crate::analysis::graph::scheme::{SchemeEdge, SchemeGraph, SchemeNode, SchemePipelineType};
use crate::analysis::result::EdgeResultsWrapper;
use crate::errors::DTTError;
use crate::params::channel_params::{Channel, ChannelSettings, TrendStat};
use crate::run_context::RunContext;
use crate::scope_view::ScopeView;
use crate::{AnalysisId, AnalysisSettingsId};

pub fn create_pipeline_graph<'b>(
    _rc: Box<RunContext>,
    view: &ScopeView,
) -> Result<AnalysisGraph<'b>, DTTError> {
    let mut nodes = HashMap::new();
    let mut graph = AnalysisGraph::new();

    let data_source = AnalysisNode {
        pipeline_type: SchemePipelineType::DataSource,
        name: "data_source".to_string(),
        id: None,
    };

    let ds_id = graph.add_node(data_source);

    let results = AnalysisNode {
        pipeline_type: SchemePipelineType::Results,
        name: "results".to_string(),
        id: None,
    };

    let result_id = graph.add_node(results);

    let results_store = AnalysisNode {
        pipeline_type: SchemePipelineType::StoreResultsToView,
        name: "results_store".to_string(),
        id: None,
    };

    let result_store_id = graph.add_node(results_store);

    for id in &view.set.members {
        add_id_to_graph(
            &mut graph,
            &mut nodes,
            id,
            ds_id,
            result_id,
            result_store_id,
        )?;
    }

    graph.set_result_types()?;

    Ok(graph)
}

fn add_id_to_graph<'a>(
    graph: &'_ mut AnalysisGraph,
    nodes: &'_ mut HashMap<&'a AnalysisId, NodeIndex>,
    id: &'a AnalysisId,
    ds_id: NodeIndex,
    result_id: NodeIndex,
    result_store_id: NodeIndex,
) -> Result<NodeIndex, DTTError> {
    if nodes.contains_key(id) {
        return Ok(nodes.get(id).expect("checked for membership").clone());
    }

    let first_chan = id
        .first_channel()
        .expect("should always be at least one channel");

    let (connect_result, out_node) = match id {
        AnalysisId::Simple { channel } => {
            let (in_node, out_node) = add_simple_to_graph(graph, channel);

            let in_scheme_edge = SchemeEdge::new(1);
            let in_edge = AnalysisEdge::new(in_scheme_edge, channel.data_type.clone().into());
            graph.add_edge(ds_id, in_node, in_edge);
            let do_decim = !channel.data_type.is_complex();
            (do_decim, out_node)
        }
        AnalysisId::Compound { name, args } => {
            log::debug!("got compound analysis '{}'", name);

            let (connect_result, node_id) = if name == "complex" {
                let complex_id = graph.add_node(AnalysisNode {
                    pipeline_type: SchemePipelineType::Complex,
                    name: format!("{}.complex", id),
                    id: Some(id.clone().into()),
                });

                (false, complex_id)
            } else if name == "phase" {
                let phase_id = graph.add_node(AnalysisNode {
                    pipeline_type: SchemePipelineType::Phase,
                    name: format!("{}.phase", id),
                    id: Some(id.clone().into()),
                });

                (true, phase_id)
            } else {
                panic!("unrecognized analysis '{}'", name);
            };

            // connect up all the arguments, but first make
            // sure they are already graphed
            let mut arg_nodes = Vec::with_capacity(args.len());

            for arg in args {
                let arg_id = add_id_to_graph(graph, nodes, arg, ds_id, result_id, result_store_id)?;
                arg_nodes.push(arg_id);
            }

            for (i, arg_node) in arg_nodes.into_iter().enumerate() {
                graph.add_edge(
                    arg_node,
                    node_id,
                    AnalysisEdge::new(
                        SchemeEdge::new(i + 1),
                        args.get(i)
                            .expect("enumerated, so i must exist")
                            .try_into()?,
                    ),
                );
            }

            // only connect to result if output is real
            // complex outputs not yet handled.
            (connect_result, node_id)
        }
    };

    // attach decimator
    if connect_result {
        let decim = AnalysisNode {
            pipeline_type: SchemePipelineType::Downsample,
            name: format!("{}_downsample", id),
            id: Some(id.clone().into()),
        };

        let decim_id = graph.add_node(decim);

        let decim_edge = AnalysisEdge::new(SchemeEdge::new(1), first_chan.data_type.clone().into());
        graph.add_edge(out_node, decim_id, decim_edge);

        // attach to results
        let results_scheme_edge =
            SchemeEdge::new(1).set_result_wrapper(EdgeResultsWrapper::TimeDomainReal);
        let results_edge =
            AnalysisEdge::new(results_scheme_edge, first_chan.data_type.clone().into());
        graph.add_edge(decim_id, result_id, results_edge);

        // attach to results store
        let results_store_scheme_edge =
            SchemeEdge::new(1).set_result_wrapper(EdgeResultsWrapper::TimeDomainReal);
        let results_store_edge = AnalysisEdge::new(
            results_store_scheme_edge,
            first_chan.data_type.clone().into(),
        );
        graph.add_edge(out_node, result_store_id, results_store_edge);
    };

    nodes.insert(id, out_node);

    Ok(out_node)
}

/// returns node to attach data source, node to get undecimated result
fn add_simple_to_graph<'a>(
    graph: &'a mut AnalysisGraph,
    channel: &'_ Channel,
) -> (NodeIndex, NodeIndex) {
    // Because we aren't handling functions yet, we can just hook data source to results
    // and pass it as a per-channel graph
    // When arbitrary functions are allowed on individual channels, then
    // Some more involved method will be needed.

    // for this early code we'll just assume if one channel is a trend then they are all trends of the same size.
    //
    // shift trends later in time by 1/2 step to make their time stamps centered in the time
    // region they summarize
    //
    // this is just period/2, but a more correct formula would be period *  (n-1)/2*n)
    // where n is the number of points per region.
    let trend_shift = if channel.trend_stat != TrendStat::Raw {
        Some(-(channel.period / 2usize))
    } else {
        None
    };

    let id = Some(AnalysisSettingsId::from_channel(channel.clone().into()));

    let condition = AnalysisNode {
        pipeline_type: SchemePipelineType::Conditioning,
        name: format!("{}_condition", channel),
        id: id.clone(),
    };
    let condition_index = graph.add_node(condition);

    // only shift if trend
    let shift_index = if let Some(shift) = trend_shift {
        let idx = graph.add_node(AnalysisNode {
            name: format!("{}_center_trend", channel),
            pipeline_type: SchemePipelineType::TimeShift { shift },
            id,
        });
        graph.add_edge(
            condition_index,
            idx,
            AnalysisEdge::new(SchemeEdge::new(1), channel.data_type.clone().into()),
        );
        idx
        //condition_index
    } else {
        condition_index
    };

    (condition_index, shift_index)
}

pub fn create_pipeline_graph_old<'b>(
    rc: Box<RunContext>,
    view: &ScopeView,
) -> Result<AnalysisGraph<'b>, DTTError> {
    let channels: Vec<_> = view.set.clone().into();
    let chans: Vec<ChannelSettings> = channels.into_iter().map(|x| x.into()).collect();

    // Because we aren't handling functions yet, we can just hook data source to results
    // and pass it as a per-channel graph
    // When arbitrary functions are allowed on individual channels, then
    // Some more involved method will be needed.

    // for this early code we'll just assume if one channel is a trend then they are all trends of the same size.
    //
    // shift trends later in time by 1/2 step to make their time stamps centered in the time
    // region they summarize
    //
    // this is just period/2, but a more correct formula would be period *  (n-1)/2*n)
    // where n is the number of points per region.
    let trend_shift = if chans.len() > 0 && chans[0].channel.trend_stat != TrendStat::Raw {
        Some(-PipDuration::freq_hz_to_period(chans[0].rate_hz()) / 2)
    } else {
        None
    };

    let mut scheme = SchemeGraph::new();

    let ds_index = scheme.add_node(SchemeNode::new(
        "data_source",
        SchemePipelineType::DataSource,
    ));

    let condition_index = scheme.add_node(SchemeNode::new(
        "condition",
        SchemePipelineType::Conditioning,
    ));

    // only shift if trend
    let shift_index = if let Some(shift) = trend_shift {
        let idx = scheme.add_node(SchemeNode::new(
            "center_trend",
            SchemePipelineType::TimeShift { shift },
        ));
        scheme.add_edge(condition_index, idx, SchemeEdge::new(1));
        idx
        //condition_index
    } else {
        condition_index
    };

    //let splice_index = scheme.add_node(SchemeNode::new("splice", SchemePipelineType::Splice));

    let results_index = scheme.add_node(SchemeNode::new("results", SchemePipelineType::Results));

    let downsample_index = scheme.add_node(SchemeNode::new(
        "downsample",
        SchemePipelineType::Downsample,
    ));

    let store_results_index = scheme.add_node(SchemeNode::new(
        "store_results",
        SchemePipelineType::StoreResultsToView,
    ));
    // let fft_index = scheme.add_node(SchemeNode::new("fft", SchemePipelineType::InlineFFT));
    // let csd_index = scheme.add_node(SchemeNode::new("csd", SchemePipelineType::CSD));
    // let real_index = scheme.add_node(SchemeNode::new("real", SchemePipelineType::Real));
    // let avg_index = scheme.add_node(SchemeNode::new("avg", SchemePipelineType::Average));
    // let sqrt_index = scheme.add_node(SchemeNode::new("sqrt", SchemePipelineType::Sqrt));

    scheme.add_edge(ds_index, condition_index, SchemeEdge::new(1));

    // scheme.add_edge(condition_index, splice_index, SchemeEdge::new(1));
    // scheme.add_edge(splice_index, results_index, SchemeEdge::new(1));

    scheme.add_edge(shift_index, downsample_index, SchemeEdge::new(1));
    scheme.add_edge(
        downsample_index,
        results_index,
        SchemeEdge::new(1).set_result_wrapper(EdgeResultsWrapper::TimeDomainReal),
    );

    scheme.add_edge(
        condition_index,
        store_results_index,
        SchemeEdge::new(1).set_result_wrapper(EdgeResultsWrapper::TimeDomainReal),
    );
    //scheme.add_edge(condition_index, results_index, SchemeEdge::new(1));

    // hook up ASD calc
    // scheme.add_edge(shift_index, fft_index, SchemeEdge::new(1));

    // // send the same fft to the csd node to get PSD output
    // scheme.add_edge(fft_index, csd_index, SchemeEdge::new(1));
    // scheme.add_edge(fft_index, csd_index, SchemeEdge::new(2));

    // scheme.add_edge(csd_index, real_index, SchemeEdge::new(1));
    // scheme.add_edge(real_index, avg_index, SchemeEdge::new(1));
    // scheme.add_edge(avg_index, sqrt_index, SchemeEdge::new(1));
    // scheme.add_edge(sqrt_index, results_index, SchemeEdge::new(1).set_result_wrapper(EdgeResultsWrapper::ASD));

    // test the scheme graphs
    AnalysisGraph::test_schemes(rc, &scheme, &SchemeGraph::new())?;

    // get the list of channels

    // Convert the scheme graph to a real analysis graph

    let graph =
        AnalysisGraph::create_analysis_graph(chans.as_slice(), &scheme, &SchemeGraph::new())?;

    Ok(graph)
}
