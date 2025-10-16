import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from tqdm import tqdm
import traceback

def multi_process_tasks(
    data_list,
    func,
    map_func=None,
    batch_size=10000,
    max_workers=os.cpu_count(),
    desc="Processing Data",
    verbose=False,
    **kwargs
):
    results = {}
    failed = {}

    if map_func is None:
        map_func = lambda x: x  # identity function

    assert batch_size > 0, "batch_size must be greater than 0"
    assert max_workers > 0, "max_workers must be greater than 0"
    assert len(data_list) > 0, "data_list must be non-empty"

    batch_size = min(batch_size, len(data_list))

    success_count, fail_count = 0, 0
    with tqdm(total=len(data_list), desc=desc) as pbar:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for i in range(0, len(data_list), batch_size):
                batch_data = data_list[i : i + batch_size]
                future_to_task = {
                    executor.submit(func, data, **kwargs): map_func(data)
                    for data in batch_data
                }
                
                for future in as_completed(future_to_task):
                    taskID = future_to_task[future]
                    try:
                        results[taskID] = future.result()
                        success_count += 1
                    except Exception as exc:
                        fail_count += 1
                        failed[taskID] = str(exc)
                        print(f"{taskID} generated an exception: {exc}")
                        if verbose:
                            traceback.print_exc()
                    finally:
                        pbar.update(1)
                        pbar.set_postfix(
                            {"✅ Success": success_count, "❌ Fail": fail_count}
                        )

    print(f"\nAll Done! ✅ Success: {success_count} | ❌ Fail: {fail_count}")
    return results, failed


def multi_thread_tasks(
    data_list,
    func,
    map_func=None,
    batch_size=10000,
    max_workers=os.cpu_count(),
    desc="Processing Data",
    verbose=False,
    **kwargs
):
    results = {}
    failed = {}

    if map_func is None:
        map_func = lambda x: x  # identity function

    assert batch_size > 0, "batch_size must be greater than 0"
    assert max_workers > 0, "max_workers must be greater than 0"
    assert len(data_list) > 0, "data_list must be non-empty"

    batch_size = min(batch_size, len(data_list))

    success_count, fail_count = 0, 0
    with tqdm(total=len(data_list), desc=desc) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(0, len(data_list), batch_size):
                batch_data = data_list[i : i + batch_size]
                future_to_task = {
                    executor.submit(func, data, **kwargs): map_func(data)
                    for data in batch_data
                }
                
                for future in as_completed(future_to_task):
                    taskID = future_to_task[future]
                    try:
                        results[taskID] = future.result()
                        success_count += 1
                    except Exception as exc:
                        fail_count += 1
                        failed[taskID] = str(exc)
                        print(f"{taskID} generated an exception: {exc}")
                        if verbose:
                            traceback.print_exc()
                    finally:
                        pbar.update(1)
                        pbar.set_postfix(
                            {"✅ Success": success_count, "❌ Fail": fail_count}
                        )

    print(f"\nAll Done! ✅ Success: {success_count} | ❌ Fail: {fail_count}")
    return results, failed


def split_task_to_nodes(all_uids, total_nodes, GPUs_per_node, verbose=False):
    # Split UIDs among nodes
    node_uid_list = []
    chunk_size = len(all_uids) // total_nodes
    remainder = len(all_uids) % total_nodes

    start = 0
    for i in range(total_nodes):
        extra = 1 if i < remainder else 0  # Distribute remainder across first few nodes
        end = start + chunk_size + extra
        node_uid_list.append(all_uids[start:end])
        if verbose:
            print(f"Node {i}: {start} - {end-1} UIDs assigned.")
        start = end

    # Split UIDs among GPUs within each node
    gpu_uid_list_per_node = []
    for i, node_uids in enumerate(node_uid_list):
        gpu_uid_list = []
        chunk_size_gpu = len(node_uids) // GPUs_per_node
        remainder_gpu = len(node_uids) % GPUs_per_node

        start = 0
        for j in range(GPUs_per_node):
            extra_gpu = 1 if j < remainder_gpu else 0  # Distribute remainder across GPUs
            end = start + chunk_size_gpu + extra_gpu
            gpu_uid_list.append(node_uids[start:end])
            if verbose:
                print(f"Node {i} GPU {j}: {start} - {end-1} UIDs assigned.")
            start = end
        gpu_uid_list_per_node.append(gpu_uid_list)

    # Return the list for the specified node and GPU
    return gpu_uid_list_per_node