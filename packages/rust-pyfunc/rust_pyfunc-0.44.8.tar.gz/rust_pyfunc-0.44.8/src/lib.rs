#[allow(unused_imports)]
use pyo3::prelude::*;

pub mod backup_reader;
pub mod column_correlation;
pub mod difference_matrix;
pub mod entropy_analysis;
pub mod error;
pub mod grouping;
pub mod market_correlation;
pub mod order_contamination;
pub mod order_neighborhood;
pub mod order_records_ultra_sorted;
pub mod pandas_ext;
pub mod parallel_computing;
pub mod price_cycle_b_segments_enhanced;
pub mod sequence;
pub mod simple_parallel;
pub mod statistics;
pub mod text;
pub mod time_series;
pub mod trade_peak_analysis;
pub mod trade_records_ultra_sorted;
pub mod tree;
pub mod vector_similarity;
pub mod vector_similarity_optimized;

pub mod factor_neutralization_io_optimized;

pub mod abnormal_asks_analyzer;
pub mod frontier_dist;
pub mod gp_correlation_dimension;
pub mod lagged_regression;
pub mod lagged_regression_incremental;
pub mod lagged_regression_optimized;
pub mod lagged_regression_simd;
pub mod lz_complexity;
pub mod lz_complexity_detailed;
pub mod permutation_analysis_v0816_fixed;
pub mod price_breakthrough_stats;
pub mod series_rank;

/// Formats the sum of two numbers as string.
#[pyfunction]
#[pyo3(signature = (a, b))]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn rust_pyfunc(_py: Python, m: &PyModule) -> PyResult<()> {
    let _ = m.add_function(wrap_pyfunction!(sum_as_string, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::dtw_distance, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::fast_dtw_distance, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::super_dtw_distance, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::transfer_entropy, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::transfer_entropy_safe, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::ols, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::ols_predict, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::ols_residuals, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::min_range_loop, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::max_range_loop, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::rolling_volatility, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::rolling_cv, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::rolling_qcv, m)?);
    let _ = m.add_function(wrap_pyfunction!(text::vectorize_sentences, m)?);
    let _ = m.add_function(wrap_pyfunction!(text::vectorize_sentences_list, m)?);
    let _ = m.add_function(wrap_pyfunction!(text::jaccard_similarity, m)?);
    let _ = m.add_function(wrap_pyfunction!(sequence::identify_segments, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::trend, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::trend_fast, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::trend_2d, m)?);
    let _ = m.add_function(wrap_pyfunction!(sequence::find_max_range_product, m)?);
    let _ = m.add_function(wrap_pyfunction!(text::min_word_edit_distance, m)?);
    let _ = m.add_function(wrap_pyfunction!(text::check_string_proximity, m)?);
    let _ = m.add_function(wrap_pyfunction!(text::check_string_proximity_matrix, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        text::check_string_proximity_with_tolerance,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        text::check_string_proximity_matrix_with_tolerance,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::find_local_peaks_within_window,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(pandas_ext::rolling_window_stat, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        pandas_ext::rolling_window_stat_backward,
        m
    )?);
    let _ = m.add_class::<tree::PriceTree>()?;
    // m.add_function(wrap_pyfunction!(sequence::compute_top_eigenvalues, m)?)?;
    let _ = m.add_function(wrap_pyfunction!(sequence::compute_max_eigenvalue, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::find_follow_volume_sum_same_price,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::find_follow_volume_sum_same_price_and_flag,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(time_series::mark_follow_groups, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::mark_follow_groups_with_flag,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(time_series::find_half_energy_time, m)?);
    let _ = m.add_function(wrap_pyfunction!(time_series::find_half_extreme_time, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::fast_extreme::fast_find_half_extreme_time,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::super_extreme::super_find_half_extreme_time,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::calculate_large_order_nearby_small_order_time_gap,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        sequence::calculate_shannon_entropy_change,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        sequence::calculate_shannon_entropy_change_at_low,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(sequence::calculate_base_entropy, m)?);
    let _ = m.add_function(wrap_pyfunction!(sequence::calculate_window_entropy, m)?);
    let _ = m.add_function(wrap_pyfunction!(sequence::brachistochrone_curve, m)?);
    let _ = m.add_function(wrap_pyfunction!(sequence::brachistochrone_curve_v2, m)?);
    let _ = m.add_function(wrap_pyfunction!(statistics::dataframe_corrwith, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::dataframe_corrwith_single_thread,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(time_series::rolling_dtw_distance, m)?);
    let _ = m.add_function(wrap_pyfunction!(sequence::segment_and_correlate, m)?);
    let _ = m.add_function(wrap_pyfunction!(sequence::test_function, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::retreat_advance::analyze_retreat_advance,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::retreat_advance_v2::analyze_retreat_advance_v2,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(pandas_ext::rank_axis1, m)?);
    let _ = m.add_function(wrap_pyfunction!(pandas_ext::fast_merge, m)?);
    let _ = m.add_function(wrap_pyfunction!(pandas_ext::fast_merge_mixed, m)?);
    let _ = m.add_function(wrap_pyfunction!(pandas_ext::fast_inner_join_dataframes, m)?);
    let _ = m.add_function(wrap_pyfunction!(grouping::factor_grouping, m)?);
    let _ = m.add_function(wrap_pyfunction!(grouping::factor_correlation_by_date, m)?);
    let _ = m.add_function(wrap_pyfunction!(parallel_computing::run_pools_queue, m)?);
    let _ = m.add_function(wrap_pyfunction!(simple_parallel::run_pools_simple, m)?);
    let _ = m.add_function(wrap_pyfunction!(backup_reader::query_backup, m)?);
    let _ = m.add_function(wrap_pyfunction!(backup_reader::query_backup_fast, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        backup_reader::query_backup_single_column,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        backup_reader::query_backup_single_column_with_filter,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        backup_reader::query_backup_columns_range_with_filter,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        backup_reader::query_backup_factor_only,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        backup_reader::query_backup_factor_only_with_filter,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        backup_reader::query_backup_factor_only_ultra_fast,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        order_contamination::order_contamination,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        order_contamination::order_contamination_parallel,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        order_contamination::order_contamination_bilateral,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        trade_peak_analysis::trade_peak_analysis,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        order_neighborhood::order_neighborhood_analysis,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        trade_records_ultra_sorted::calculate_trade_time_gap_and_price_percentile_ultra_sorted,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        order_records_ultra_sorted::calculate_order_time_gap_and_price_percentile_ultra_sorted,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        order_records_ultra_sorted::calculate_order_time_gap_and_price_percentile_ultra_sorted_v2,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        time_series::lyapunov::calculate_lyapunov_exponent,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::local_correlation::local_correlation,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::eigenvalue_analysis::matrix_eigenvalue_analysis,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::eigenvalue_analysis::matrix_eigenvalue_analysis_optimized,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::eigenvalue_analysis_modified::matrix_eigenvalue_analysis_modified,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::eigenvalue_analysis_modified::matrix_eigenvalue_analysis_modified_ultra,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::fast_correlation::fast_correlation_matrix,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::fast_correlation_v2::fast_correlation_matrix_v2,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::rolling_correlation_mean::rolling_correlation_mean,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::rolling_correlation_mean::rolling_correlation_skew,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::rolling_window_core_feature::rolling_window_core_feature,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::rolling_window_core_feature_optimized::rolling_window_core_feature_optimized,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::rolling_window_core_feature_simd::rolling_window_core_feature_simd,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::rolling_window_core_feature_ultra::rolling_window_core_feature_ultra,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        market_correlation::price_volume_orderbook_correlation,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(entropy_analysis::calculate_entropy_1d, m)?);
    let _ = m.add_function(wrap_pyfunction!(entropy_analysis::calculate_entropy_2d, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        entropy_analysis::calculate_entropy_discrete_1d,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        entropy_analysis::calculate_entropy_discrete_2d,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        entropy_analysis::calculate_binned_entropy_1d,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        entropy_analysis::calculate_binned_entropy_2d,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        factor_neutralization_io_optimized::batch_factor_neutralization_io_optimized,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        permutation_analysis_v0816_fixed::analyze_sequence_permutations_v0816_fixed,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        statistics::hmm_trend_prediction::hmm_trend_prediction,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(abnormal_asks_analyzer::analyze_asks, m)?);
    let _ = m.add_function(wrap_pyfunction!(series_rank::pandas_series_rank, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        price_breakthrough_stats::compute_non_breakthrough_stats,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        lagged_regression::rolling_lagged_regression,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        lagged_regression::rolling_lagged_regression_ridge,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        lagged_regression_optimized::rolling_lagged_regression_ridge_fast,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        lagged_regression_simd::rolling_lagged_regression_ridge_simd,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        lagged_regression_incremental::rolling_lagged_regression_ridge_incremental,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        price_cycle_b_segments_enhanced::compute_price_cycle_features_b_segments_enhanced,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        vector_similarity_optimized::vector_similarity_matrices,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        vector_similarity_optimized::cosine_similarity_matrix,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        column_correlation::column_correlation_fast,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        column_correlation::column_correlation_batch,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(difference_matrix::difference_matrix, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        difference_matrix::difference_matrix_memory_efficient,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(lz_complexity::lz_complexity, m)?);
    let _ = m.add_function(wrap_pyfunction!(lz_complexity_detailed::lz_complexity_detailed, m)?);
    let _ = m.add_function(wrap_pyfunction!(
        gp_correlation_dimension::gp_correlation_dimension_auto,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        gp_correlation_dimension::gp_correlation_dimension,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        gp_correlation_dimension::gp_create_default_options,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(
        gp_correlation_dimension::gp_create_options,
        m
    )?);
    let _ = m.add_function(wrap_pyfunction!(frontier_dist::distances_to_frontier, m)?);
    // m.add_function(wrap_pyfunction!(text::normalized_diff, m)?)?;
    Ok(())
}
