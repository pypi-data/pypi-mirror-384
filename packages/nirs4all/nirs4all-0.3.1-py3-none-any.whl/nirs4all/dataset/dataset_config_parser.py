from pathlib import Path
from typing import Dict, Any
import numpy as np

def normalize_config_keys(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize dataset configuration keys to standard format.
    Maps variations like 'x_train', 'X_train', 'Xtrain' to 'train_x'
    Maps metadata variations like 'metadata_train', 'train_metadata', 'm_train' to 'train_group'

    Args:
        config: Original configuration dictionary

    Returns:
        Normalized configuration with standardized keys
    """
    # Base patterns for each standard key
    base_patterns = {
        'train_x': ['train_x', 'x_train', 'xtrain', 'trainx'],
        'train_y': ['train_y', 'y_train', 'ytrain', 'trainy'],
        'test_x': ['test_x', 'x_test', 'xtest', 'testx', 'val_x', 'x_val', 'xval', 'valx'],
        'test_y': ['test_y', 'y_test', 'ytest', 'testy', 'val_y', 'y_val', 'yval', 'valy'],
        'train_group': ['train_group', 'group_train', 'grouptrain', 'traingroup',
                        'train_metadata', 'metadata_train', 'metadatatrain', 'trainmetadata',
                        'train_meta', 'meta_train', 'metatrain', 'trainmeta',
                        'train_m', 'm_train', 'mtrain', 'trainm'],
        'test_group': ['test_group', 'group_test', 'grouptest', 'testgroup',
                       'test_metadata', 'metadata_test', 'metadatatest', 'testmetadata',
                       'test_meta', 'meta_test', 'metatest', 'testmeta',
                       'test_m', 'm_test', 'mtest', 'testm',
                       'val_group', 'group_val', 'groupval', 'valgroup',
                       'val_metadata', 'metadata_val', 'metadataval', 'valmetadata',
                       'val_meta', 'meta_val', 'metaval', 'valmeta',
                       'val_m', 'm_val', 'mval', 'valm'],
    }

    # Build case-insensitive mapping
    key_mappings = {}
    for standard_key, variations in base_patterns.items():
        for variation in variations:
            # Add all case combinations
            key_mappings[variation.lower()] = standard_key
            key_mappings[variation.upper()] = standard_key
            key_mappings[variation.capitalize()] = standard_key
            key_mappings[variation.title()] = standard_key

    normalized_config = {}
    for key, value in config.items():
        normalized_key = key_mappings.get(key.lower(), key)
        normalized_config[normalized_key] = value

    return normalized_config

def _s_(path):
    """Convert path(s) to POSIX format. Handles both single paths and lists of paths."""
    if path is None:
        return None
    if isinstance(path, list):
        return [Path(p).as_posix() for p in path]
    return Path(path).as_posix()

def browse_folder(folder_path, global_params=None):
    config = {
        "train_x": None, "train_x_filter": None, "train_x_params": None,
        "train_y": None, "train_y_filter": None, "train_y_params": None,
        "train_group": None, "train_group_filter": None, "train_group_params": None,
        "train_params": None,
        "test_x": None, "test_x_filter": None, "test_x_params": None,
        "test_y": None, "test_y_filter": None, "test_y_params": None,
        "test_group": None, "test_group_filter": None, "test_group_params": None,
        "test_params": None,
        "global_params": global_params
    }

    files_re = {
        "train_x": ["Xcal", "X_cal", "Cal_X", "calX", "train_X", "trainX", "X_train", "Xtrain"],
        "test_x": ["Xval", "X_val", "val_X", "valX", "Xtest", "X_test", "test_X", "testX"],
        "train_y": ["Ycal", "Y_cal", "Cal_Y", "calY", "train_Y", "trainY", "Y_train", "Ytrain"],
        "test_y": ["Ytest", "Y_test", "test_Y", "testY", "Yval", "Y_val", "val_Y", "valY"],
        "train_group": ["Mcal", "M_cal", "Cal_M", "calM", "train_M", "trainM", "M_train", "Mtrain",
                        "Metacal", "Meta_cal", "Cal_Meta", "calMeta", "train_Meta", "trainMeta", "Meta_train", "Metatrain",
                        "metadatacal", "metadata_cal", "Cal_metadata", "calMetadata", "train_metadata", "trainMetadata", "metadata_train", "metadatatrain"],
        "test_group": ["Mtest", "M_test", "test_M", "testM", "Mval", "M_val", "val_M", "valM",
                       "Metatest", "Meta_test", "test_Meta", "testMeta", "Metaval", "Meta_val", "val_Meta", "valMeta",
                       "metadatatest", "metadata_test", "test_metadata", "testMetadata", "metadataval", "metadata_val", "val_metadata", "valMetadata"],
    }

    dataset_dir = Path(folder_path)
    if not dataset_dir.exists():
        print(f"\033[91m❌ Folder does not exist: {folder_path}\033[0m")
        return config

    for key, patterns in files_re.items():
        matched_files = []
        for pattern in patterns:
            pattern_lower = pattern.lower()
            for file in dataset_dir.glob("*"):
                if pattern_lower in file.name.lower():
                    matched_files.append(str(file))

        if len(matched_files) == 0:
            # print(f"⚠️ Dataset does not have data for {key}.")
            # logging.warning("No %s file found for %s.", key, dataset_name)
            continue
        elif len(matched_files) == 1:
            # Single source - store as single path for backward compatibility
            config[key] = _s_(matched_files[0])
        else:
            # Multi-source - store as array of paths
            print(f"📊 Multiple {key} files found for {folder_path}: {len(matched_files)} sources detected.")
            config[key] = _s_(matched_files)

    return config


def folder_to_name(folder_path):
    path = Path(folder_path)
    for part in reversed(path.parts):
        clean_part = ''.join(c if c.isalnum() else '_' for c in part)
        if clean_part:
            return clean_part.lower()
    return "Unknown_dataset"


def parse_config(data_config):
    # a single folder path
    if isinstance(data_config, str):
        return browse_folder(data_config), folder_to_name(data_config)

    elif isinstance(data_config, dict):
        # a folder tag, idem as single path but with params
        if "folder" in data_config:
            return browse_folder(data_config["folder"], data_config.get("params")), folder_to_name(data_config["folder"])
        else:
            # Normalize keys before processing
            normalized_config = normalize_config_keys(data_config)

            # a full config dict
            # print(f"🔍 Parsing dataset config dict: {normalized_config.keys()}")
            # Accept configs with either train_x or test_x (for prediction scenarios)
            required_keys_pattern = ['train_x']
            alternative_keys_pattern = ['test_x']

            if all(key in normalized_config for key in required_keys_pattern):
                # Standard case: has train_x
                train_file = normalized_config.get("train_x")

                # Check if data is already a numpy array (not a file path)
                if isinstance(train_file, np.ndarray):
                    dataset_name = normalized_config.get("name", "array_dataset")
                    return normalized_config, dataset_name

                if isinstance(train_file, list):
                    train_file = train_file[0]
                train_file = Path(str(train_file))
                dataset_name = f"{train_file.parent.name}_{train_file.stem}"
                return normalized_config, dataset_name
            elif all(key in normalized_config for key in alternative_keys_pattern):
                # Prediction case: has test_x but no train_x
                test_file = normalized_config.get("test_x")

                # Check if data is already a numpy array (not a file path)
                if isinstance(test_file, np.ndarray):
                    dataset_name = normalized_config.get("name", "array_dataset")
                    return normalized_config, dataset_name

                if isinstance(test_file, list):
                    test_file = test_file[0]
                test_file = Path(str(test_file))
                dataset_name = f"{test_file.parent.name}_{test_file.stem}"
                return normalized_config, dataset_name

    print(f"❌ Error in config: unsupported dataset config >> {type(data_config)}: {data_config}")
    return None, 'Unknown_dataset'


