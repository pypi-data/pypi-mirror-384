import argparse
import json
import logging
import multiprocessing.dummy as mt
import time
from typing import Any, Dict, List


def get_parquet_datasets_info_from_txt(
    dataset_txt_file: str,
    output_file_path: str,
    file_system_config: Dict[str, Any] | None = None,
    workers: int = 100,
    existing_json_paths: List[str] | None = None,
):
    """
    Read a single flat text file containing parquet file paths (one per line).
    Compute parquet sub_ds_info and write a list of objects to output JSON.
    The JSON structure is a flat list of {"filepath", "sub_ds_info"}.

    Any exception during processing will cause the function to fail and no output file
    will be written.

    Args:
        dataset_txt_file: a text file containing parquet paths (one per line)
        output_file_path: path where to save the result as JSON (list-of-lists of objects)
        file_system_config: file system configuration dict (for S3 support)
        workers: number of parallel workers (default: 180)
        existing_json_paths: optional list of JSON file paths, each being a nested list
            [dataset][{"filepath", "sub_ds_info"}] to reuse already-computed info.
            If multiple files contain the same filepath, later files in the list
            overwrite earlier ones.

    """
    try:
        from tqdm import tqdm  # type: ignore
    except Exception:
        tqdm = None

    print(dataset_txt_file)
    from .parquet_dataset import ParquetConcateDataset, create_pyarrow_s3fs

    # Read the single dataset file to get all file paths
    with open(dataset_txt_file, "r") as f:
        all_filepaths: List[str] = [line.strip() for line in f if line.strip()]

    if not all_filepaths:
        raise ValueError("No valid file paths found in dataset text file")

    if not all_filepaths:
        raise ValueError("No valid file paths found in datasets")

    # Setup file system
    file_system = None
    if file_system_config and file_system_config.get("type") == "pyarrow_s3":
        file_system = create_pyarrow_s3fs(file_system_config)

    total = len(all_filepaths)
    print(f"Starting processing with {workers} workers (total files: {total:,})...")
    start_time = time.time()

    def _get_sub_ds_length(args: tuple[str, int]):
        path, file_idx = args
        row, row_groups = ParquetConcateDataset._get_sub_ds_length(
            path, file_system=file_system
        )
        return file_idx, row, row_groups

    # Prepare result container
    all_files_sub_ds_info: List[list[int | list[int]] | None] = [None] * total

    # Load existing JSONs (if provided) and prefill known entries. Later files overwrite earlier ones.
    existing_map: Dict[str, list[int | list[int]]] = {}
    if existing_json_paths:
        for json_path in existing_json_paths:
            try:
                with open(json_path, "r") as f:
                    existing_records = json.load(f)
                if isinstance(existing_records, list) and all(
                    isinstance(ds, list) for ds in existing_records
                ):
                    # Nested list [dataset][{filepath, sub_ds_info}]
                    for ds in existing_records:
                        for rec in ds:
                            if (
                                isinstance(rec, dict)
                                and "filepath" in rec
                                and "sub_ds_info" in rec
                            ):
                                existing_map[str(rec["filepath"])] = rec["sub_ds_info"]
            except FileNotFoundError:
                pass

    # Prefill from existing map and collect missing args
    missing_args: List[tuple[str, int]] = []
    for i, filepath in enumerate(all_filepaths):
        if filepath in existing_map:
            all_files_sub_ds_info[i] = existing_map[filepath]
            print(f"Reusing existing sub_ds_info for: {filepath}")
        else:
            missing_args.append((filepath, i))

    # Run with imap_unordered for fast completion updates on missing files only
    if missing_args:
        with mt.Pool(workers) as p:
            iterator = p.imap_unordered(_get_sub_ds_length, missing_args)
            progress = (
                tqdm(total=len(missing_args), mininterval=1.0, smoothing=0)
                if tqdm is not None
                else None
            )
            try:
                for file_idx, row, row_groups in iterator:
                    all_files_sub_ds_info[file_idx] = [row, row_groups]
                    if progress is not None:
                        progress.update(1)
            except Exception:
                if progress is not None:
                    progress.close()
                raise
            finally:
                if progress is not None and progress.n < progress.total:
                    progress.close()

    # Verify there were no failures
    if any(info is None for info in all_files_sub_ds_info):
        failed = sum(1 for info in all_files_sub_ds_info if info is None)
        raise RuntimeError(
            f"Failed to process {failed} files out of {total}. Aborting without writing output."
        )

    # Build flat output: list of {filepath, sub_ds_info}
    output_list: List[Dict[str, Any]] = []
    for i, path in enumerate(all_filepaths):
        info = all_files_sub_ds_info[i]
        output_list.append({"filepath": path, "sub_ds_info": info})

    # Write result to output file as JSON (flat list of objects)
    with open(output_file_path, "w") as f:
        json.dump(output_list, f, indent=2)

    # Summary
    total_files_done = len(output_list)
    total_rows = sum(rec["sub_ds_info"][0] for rec in output_list)  # type: ignore[index]
    elapsed = time.time() - start_time
    rate = total_files_done / elapsed if elapsed > 0 else 0.0

    logging.info(
        f"Processed {total_files_done}/{total} files in {elapsed:.1f}s (~{rate:.1f} files/s)"
    )
    logging.info(f"Total rows: {total_rows:,}")
    logging.info(f"Result saved to {output_file_path}")

    return output_list


def _build_s3_config_from_args(args: Any) -> Dict[str, Any] | None:
    """
    Build an s3_config dict from CLI args if any S3-related fields are provided.
    Returns None if no S3-related args are given.
    """
    has_any = any(
        [
            getattr(args, "s3_type", None),
            getattr(args, "s3_access_key", None),
            getattr(args, "s3_secret_key", None),
            getattr(args, "s3_endpoint_override", None),
        ]
    )
    if not has_any:
        return None

    cfg: Dict[str, Any] = {}
    if args.s3_type:
        cfg["type"] = args.s3_type
    if args.s3_access_key:
        cfg["access_key"] = args.s3_access_key
    if args.s3_secret_key:
        cfg["secret_key"] = args.s3_secret_key
    if args.s3_endpoint_override:
        cfg["endpoint_override"] = args.s3_endpoint_override
    return cfg


def _parse_args() -> Any:
    parser = argparse.ArgumentParser(
        description=(
            "Compute parquet file info from a single text file list and save as JSON."
        )
    )

    parser.add_argument(
        "--dataset-txt-file",
        dest="dataset_txt_file",
        required=True,
        help="A text file containing parquet paths (one per line).",
    )

    parser.add_argument(
        "--output-file-path",
        dest="output_file_path",
        required=True,
        help="Path to save the resulting JSON list (flat list of {filepath, sub_ds_info}).",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=180,
        help="Number of parallel workers (default: 180).",
    )

    parser.add_argument(
        "--existing-json-paths",
        dest="existing_json_paths",
        nargs="+",
        default=None,
        help=(
            "Optional JSON file paths to reuse entries. Later paths take precedence."
            "Each file must be a nested list [dataset][{filepath, sub_ds_info}]."
        ),
    )

    # Optional S3 configuration
    parser.add_argument(
        "--s3-type",
        dest="s3_type",
        default=None,
        help='S3 filesystem type (e.g., "pyarrow_s3"). If provided, enables S3 access.',
    )
    parser.add_argument(
        "--s3-access-key",
        dest="s3_access_key",
        default=None,
        help="S3 access key.",
    )
    parser.add_argument(
        "--s3-secret-key",
        dest="s3_secret_key",
        default=None,
        help="S3 secret key.",
    )
    parser.add_argument(
        "--s3-endpoint-override",
        dest="s3_endpoint_override",
        default=None,
        help="S3 endpoint override URL, e.g. https://s3.example.com.",
    )

    return parser.parse_args()


"""
python -m anc_data.parquet_tools \
  --dataset-txt-file /path/ds_a.txt \
  --output-file-path /tmp/datasets_sub_ds_info.json \
  --existing-json-paths /tmp/prev_datasets_sub_ds_info.json /tmp/another_datasets_sub_ds_info.json \
  --workers 100 \
  --s3-type pyarrow_s3 \
  --s3-access-key "$AWS_ACCESS_KEY_ID" \
  --s3-secret-key "$AWS_SECRET_ACCESS_KEY" \
  --s3-endpoint-override https://s3.example.com

for --existing-json-paths: if the same parquet file exists in multiple jsons, the last one wins
"""
if __name__ == "__main__":
    args = _parse_args()
    get_parquet_datasets_info_from_txt(
        dataset_txt_file=args.dataset_txt_file,
        output_file_path=args.output_file_path,
        file_system_config=_build_s3_config_from_args(args),
        workers=args.workers,
        existing_json_paths=args.existing_json_paths,
    )
