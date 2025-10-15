use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use rayon::prelude::*;
use std::collections::HashMap;

/// 优化版订单浸染函数 - 高性能单线程版本
///
/// # 参数
/// - exchtime: 成交时间数组（纳秒）
/// - order: 订单编号数组
/// - volume: 成交量数组  
/// - top_percentile: 大单百分比阈值 (1-100)，表示前x%，默认10表示前10%
/// - time_window_seconds: 时间窗口（秒），默认1秒
///
/// # 返回
/// 浸染后的订单编号数组
#[pyfunction]
#[pyo3(signature = (exchtime, order, volume, top_percentile = 10.0, time_window_seconds = 1.0))]
pub fn order_contamination(
    exchtime: PyReadonlyArray1<i64>,
    order: PyReadonlyArray1<i64>,
    volume: PyReadonlyArray1<i64>,
    top_percentile: f64,
    time_window_seconds: f64,
) -> PyResult<Py<PyArray1<i64>>> {
    let py = unsafe { Python::assume_gil_acquired() };

    let exchtime = exchtime.as_array();
    let order = order.as_array();
    let volume = volume.as_array();

    // 将秒转换为纳秒
    let time_window_ns = (time_window_seconds * 1_000_000_000.0) as i64;

    let n = exchtime.len();
    if n != order.len() || n != volume.len() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "输入数组长度不一致",
        ));
    }

    if n == 0 {
        return Ok(PyArray1::from_vec(py, vec![]).to_owned());
    }

    // 1. 快速聚合订单成交量（使用容量预分配）
    let mut order_volumes: HashMap<i64, i64> = HashMap::with_capacity(n / 4);
    for i in 0..n {
        *order_volumes.entry(order[i]).or_insert(0) += volume[i];
    }

    // 2. 快速找到大单阈值（避免完整排序）
    let mut volumes: Vec<i64> = order_volumes.values().cloned().collect();
    // 修正：top_percentile是1-100的数值，需要转换为0.01-1.0的比例
    let percentile_ratio = (top_percentile / 100.0).min(1.0).max(0.01);
    let top_count = ((volumes.len() as f64 * percentile_ratio).ceil() as usize)
        .max(1)
        .min(volumes.len()); // 确保不超过数组长度

    // 使用nth_element获取阈值，比完整排序快
    let threshold = if top_count > 0 && top_count <= volumes.len() {
        volumes.select_nth_unstable_by(top_count - 1, |a, b| b.cmp(a));
        volumes[top_count - 1]
    } else {
        // 如果计算出错，回退到完整排序
        volumes.sort_unstable_by(|a, b| b.cmp(a));
        volumes
            .get(top_count.saturating_sub(1))
            .cloned()
            .unwrap_or(0)
    };

    // 3. 预标记大单位置（避免重复HashSet查找）
    let mut is_large_order = vec![false; n];
    let mut large_order_positions = Vec::with_capacity(n / 10);

    for i in 0..n {
        if let Some(&total_vol) = order_volumes.get(&order[i]) {
            if total_vol >= threshold {
                is_large_order[i] = true;
                large_order_positions.push(i);
            }
        }
    }

    let mut result = order.to_vec();

    // 4. 超高效的浸染过程：利用时间排序特性和二分查找
    // 预先计算大单的时间，用于二分查找
    let large_times: Vec<i64> = large_order_positions
        .iter()
        .map(|&pos| exchtime[pos])
        .collect();

    for i in 0..n {
        // 跳过大单本身
        if is_large_order[i] {
            continue;
        }

        let current_time = exchtime[i];
        let window_start = current_time - time_window_ns;
        let window_end = current_time + time_window_ns;

        // 使用二分查找找到窗口边界
        let left_idx = large_times
            .binary_search(&window_start)
            .unwrap_or_else(|i| i);
        let right_idx = large_times.binary_search(&window_end).unwrap_or_else(|i| i);

        // 在窗口内找最近的大单
        let mut closest_large_order = None;
        let mut min_distance = i64::MAX;

        // 检查窗口内的大单
        for j in left_idx..=right_idx.min(large_times.len() - 1) {
            if j >= large_times.len() {
                break;
            }

            let large_time = large_times[j];
            if large_time > window_end {
                break;
            }
            if large_time < window_start {
                continue;
            }

            let distance = (current_time - large_time).abs();
            if distance <= time_window_ns && distance < min_distance {
                min_distance = distance;
                let pos = large_order_positions[j];
                closest_large_order = Some(order[pos]);
            }
        }

        // 如果找到了最近的大单，进行浸染
        if let Some(large_order_id) = closest_large_order {
            result[i] = large_order_id;
        }
    }

    Ok(PyArray1::from_vec(py, result).to_owned())
}

/// 并行版本的订单浸染函数（使用5核心，适用于大数据量）
#[pyfunction]
#[pyo3(signature = (exchtime, order, volume, top_percentile = 10.0, time_window_seconds = 1.0))]
pub fn order_contamination_parallel(
    exchtime: PyReadonlyArray1<i64>,
    order: PyReadonlyArray1<i64>,
    volume: PyReadonlyArray1<i64>,
    top_percentile: f64,
    time_window_seconds: f64,
) -> PyResult<Py<PyArray1<i64>>> {
    let py = unsafe { Python::assume_gil_acquired() };

    let exchtime = exchtime.as_array();
    let order = order.as_array();
    let volume = volume.as_array();

    // 将秒转换为纳秒
    let time_window_ns = (time_window_seconds * 1_000_000_000.0) as i64;

    let n = exchtime.len();
    if n != order.len() || n != volume.len() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "输入数组长度不一致",
        ));
    }

    // 创建5核心的线程池
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(5)
        .build()
        .map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("创建线程池失败: {}", e))
        })?;

    // 1. 并行聚合订单成交量（使用5核心）
    let order_volumes: HashMap<i64, i64> = pool.install(|| {
        (0..n)
            .into_par_iter()
            .map(|i| (order[i], volume[i]))
            .fold(HashMap::new, |mut acc, (ord, vol)| {
                *acc.entry(ord).or_insert(0) += vol;
                acc
            })
            .reduce(HashMap::new, |mut acc1, acc2| {
                for (ord, vol) in acc2 {
                    *acc1.entry(ord).or_insert(0) += vol;
                }
                acc1
            })
    });

    // 2. 找到前top_percentile%的大单（使用5核心）
    let mut volumes: Vec<i64> = order_volumes.values().cloned().collect();
    pool.install(|| {
        volumes.par_sort_unstable_by(|a, b| b.cmp(a));
    });

    // 修正：top_percentile是1-100的数值，需要转换为0.01-1.0的比例
    let percentile_ratio = (top_percentile / 100.0).min(1.0).max(0.01);
    let top_count = ((volumes.len() as f64 * percentile_ratio).ceil() as usize).max(1);
    let threshold = volumes.get(top_count - 1).cloned().unwrap_or(0);

    let large_orders: std::collections::HashSet<i64> = pool.install(|| {
        order_volumes
            .par_iter()
            .filter(|(_, &vol)| vol >= threshold)
            .map(|(&ord, _)| ord)
            .collect()
    });

    // 3. 创建结果数组并进行浸染
    let mut result = order.to_vec();

    // 找到所有大单的位置
    let large_order_positions: Vec<usize> = (0..n)
        .filter(|&i| large_orders.contains(&order[i]))
        .collect();

    // 标记大单位置
    let mut is_large_order = vec![false; n];
    for &pos in &large_order_positions {
        is_large_order[pos] = true;
    }

    // 4. 高效的并行浸染过程：利用时间排序特性（使用5核心）
    // 预先计算大单的时间和位置，用于快速查找
    let large_data: Vec<(i64, usize)> = large_order_positions
        .iter()
        .map(|&pos| (exchtime[pos], pos))
        .collect();

    let updates: Vec<(usize, i64)> = pool.install(|| {
        (0..n)
            .into_par_iter()
            .filter(|&i| !is_large_order[i]) // 只处理非大单
            .filter_map(|i| {
                let current_time = exchtime[i];
                let window_start = current_time - time_window_ns;
                let window_end = current_time + time_window_ns;

                // 找到时间窗口内最近的大单
                let mut closest_large_order = None;
                let mut min_distance = i64::MAX;

                // 由于数据按时间排序，我们可以更高效地搜索
                for &(large_time, pos) in &large_data {
                    // 如果大单时间超出窗口右边界，由于排序特性，后面的都会超出
                    if large_time > window_end {
                        break;
                    }

                    // 如果大单时间在窗口左边界之前，跳过
                    if large_time < window_start {
                        continue;
                    }

                    let distance = (current_time - large_time).abs();
                    if distance < min_distance {
                        min_distance = distance;
                        closest_large_order = Some(order[pos]);
                    }
                }

                // 如果找到了最近的大单，返回更新信息
                closest_large_order.map(|large_order_id| (i, large_order_id))
            })
            .collect()
    });

    // 应用更新
    for (i, new_order) in updates {
        result[i] = new_order;
    }

    Ok(PyArray1::from_vec(py, result).to_owned())
}

/// 双边订单浸染函数 - 分别处理买单和卖单的浸染
///
/// # 参数
/// - exchtime: 成交时间数组（纳秒）
/// - bid_order: 买单编号数组
/// - ask_order: 卖单编号数组  
/// - volume: 成交量数组
/// - top_percentile: 大单百分比阈值 (1-100)，表示前x%，默认10表示前10%
/// - time_window_seconds: 时间窗口（秒），默认1秒
///
/// # 返回
/// (浸染后的买单编号数组, 浸染后的卖单编号数组)
#[pyfunction]
#[pyo3(signature = (exchtime, bid_order, ask_order, volume, top_percentile = 10.0, time_window_seconds = 1.0))]
pub fn order_contamination_bilateral(
    exchtime: PyReadonlyArray1<i64>,
    bid_order: PyReadonlyArray1<i64>,
    ask_order: PyReadonlyArray1<i64>,
    volume: PyReadonlyArray1<i64>,
    top_percentile: f64,
    time_window_seconds: f64,
) -> PyResult<(Py<PyArray1<i64>>, Py<PyArray1<i64>>)> {
    let py = unsafe { Python::assume_gil_acquired() };

    let exchtime = exchtime.as_array();
    let bid_order = bid_order.as_array();
    let ask_order = ask_order.as_array();
    let volume = volume.as_array();

    // 将秒转换为纳秒
    let time_window_ns = (time_window_seconds * 1_000_000_000.0) as i64;

    let n = exchtime.len();
    if n != bid_order.len() || n != ask_order.len() || n != volume.len() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "输入数组长度不一致",
        ));
    }

    if n == 0 {
        return Ok((
            PyArray1::from_vec(py, vec![]).to_owned(),
            PyArray1::from_vec(py, vec![]).to_owned(),
        ));
    }

    // 1. 分别聚合买单和卖单的成交量
    let mut bid_order_volumes: HashMap<i64, i64> = HashMap::with_capacity(n / 4);
    let mut ask_order_volumes: HashMap<i64, i64> = HashMap::with_capacity(n / 4);

    for i in 0..n {
        *bid_order_volumes.entry(bid_order[i]).or_insert(0) += volume[i];
        *ask_order_volumes.entry(ask_order[i]).or_insert(0) += volume[i];
    }

    // 2. 分别计算买单和卖单的大单阈值
    let mut bid_volumes: Vec<i64> = bid_order_volumes.values().cloned().collect();
    let mut ask_volumes: Vec<i64> = ask_order_volumes.values().cloned().collect();

    let percentile_ratio = (top_percentile / 100.0).min(1.0).max(0.01);

    // 计算买单大单阈值
    let bid_top_count = ((bid_volumes.len() as f64 * percentile_ratio).ceil() as usize)
        .max(1)
        .min(bid_volumes.len());

    let bid_threshold = if bid_top_count > 0 && bid_top_count <= bid_volumes.len() {
        bid_volumes.select_nth_unstable_by(bid_top_count - 1, |a, b| b.cmp(a));
        bid_volumes[bid_top_count - 1]
    } else {
        bid_volumes.sort_unstable_by(|a, b| b.cmp(a));
        bid_volumes
            .get(bid_top_count.saturating_sub(1))
            .cloned()
            .unwrap_or(0)
    };

    // 计算卖单大单阈值
    let ask_top_count = ((ask_volumes.len() as f64 * percentile_ratio).ceil() as usize)
        .max(1)
        .min(ask_volumes.len());

    let ask_threshold = if ask_top_count > 0 && ask_top_count <= ask_volumes.len() {
        ask_volumes.select_nth_unstable_by(ask_top_count - 1, |a, b| b.cmp(a));
        ask_volumes[ask_top_count - 1]
    } else {
        ask_volumes.sort_unstable_by(|a, b| b.cmp(a));
        ask_volumes
            .get(ask_top_count.saturating_sub(1))
            .cloned()
            .unwrap_or(0)
    };

    // 3. 标记买单和卖单的大单位置
    let mut is_large_bid = vec![false; n];
    let mut is_large_ask = vec![false; n];
    let mut large_bid_positions = Vec::with_capacity(n / 10);
    let mut large_ask_positions = Vec::with_capacity(n / 10);

    for i in 0..n {
        // 检查是否为大买单
        if let Some(&total_vol) = bid_order_volumes.get(&bid_order[i]) {
            if total_vol >= bid_threshold {
                is_large_bid[i] = true;
                large_bid_positions.push(i);
            }
        }

        // 检查是否为大卖单
        if let Some(&total_vol) = ask_order_volumes.get(&ask_order[i]) {
            if total_vol >= ask_threshold {
                is_large_ask[i] = true;
                large_ask_positions.push(i);
            }
        }
    }

    // 初始化结果数组
    let mut result_bid = bid_order.to_vec();
    let mut result_ask = ask_order.to_vec();

    // 4. 大买单浸染卖单非大单的过程
    let large_bid_times: Vec<i64> = large_bid_positions
        .iter()
        .map(|&pos| exchtime[pos])
        .collect();

    for i in 0..n {
        // 跳过卖单大单本身，只对卖单非大单进行浸染
        if is_large_ask[i] {
            continue;
        }

        let current_time = exchtime[i];
        let window_start = current_time - time_window_ns;
        let window_end = current_time + time_window_ns;

        // 使用二分查找找到窗口边界
        let left_idx = large_bid_times
            .binary_search(&window_start)
            .unwrap_or_else(|i| i);
        let right_idx = large_bid_times
            .binary_search(&window_end)
            .unwrap_or_else(|i| i);

        // 在窗口内找最近的大买单
        let mut closest_large_bid = None;
        let mut min_distance = i64::MAX;

        for j in left_idx..=right_idx.min(large_bid_times.len() - 1) {
            if j >= large_bid_times.len() {
                break;
            }

            let large_time = large_bid_times[j];
            if large_time > window_end {
                break;
            }
            if large_time < window_start {
                continue;
            }

            let distance = (current_time - large_time).abs();
            if distance <= time_window_ns && distance < min_distance {
                min_distance = distance;
                let pos = large_bid_positions[j];
                closest_large_bid = Some(bid_order[pos]);
            }
        }

        // 如果找到了最近的大买单，将卖单浸染为该大买单编号
        if let Some(large_bid_id) = closest_large_bid {
            result_ask[i] = large_bid_id;
        }
    }

    // 5. 大卖单浸染买单非大单的过程
    let large_ask_times: Vec<i64> = large_ask_positions
        .iter()
        .map(|&pos| exchtime[pos])
        .collect();

    for i in 0..n {
        // 跳过买单大单本身，只对买单非大单进行浸染
        if is_large_bid[i] {
            continue;
        }

        let current_time = exchtime[i];
        let window_start = current_time - time_window_ns;
        let window_end = current_time + time_window_ns;

        // 使用二分查找找到窗口边界
        let left_idx = large_ask_times
            .binary_search(&window_start)
            .unwrap_or_else(|i| i);
        let right_idx = large_ask_times
            .binary_search(&window_end)
            .unwrap_or_else(|i| i);

        // 在窗口内找最近的大卖单
        let mut closest_large_ask = None;
        let mut min_distance = i64::MAX;

        for j in left_idx..=right_idx.min(large_ask_times.len() - 1) {
            if j >= large_ask_times.len() {
                break;
            }

            let large_time = large_ask_times[j];
            if large_time > window_end {
                break;
            }
            if large_time < window_start {
                continue;
            }

            let distance = (current_time - large_time).abs();
            if distance <= time_window_ns && distance < min_distance {
                min_distance = distance;
                let pos = large_ask_positions[j];
                closest_large_ask = Some(ask_order[pos]);
            }
        }

        // 如果找到了最近的大卖单，将买单浸染为该大卖单编号
        if let Some(large_ask_id) = closest_large_ask {
            result_bid[i] = large_ask_id;
        }
    }

    Ok((
        PyArray1::from_vec(py, result_bid).to_owned(),
        PyArray1::from_vec(py, result_ask).to_owned(),
    ))
}
