import os
import re
import logging
from ciocore import data as coredata
from ciohoudini import (
    controller,
    rops,
)

logger = logging.getLogger(__name__)


def get_hfs_from_environment_or_detect():
    """Get HFS from environment or try to detect it (Linux only)"""
    # First try environment variable
    hfs = os.environ.get('HFS')
    if hfs and os.path.exists(hfs):
        return hfs

    # Try to get from HB if available
    hb = os.environ.get('HB')
    if hb and os.path.exists(hb):
        # HB is typically HFS/bin
        hfs = os.path.dirname(hb)
        if os.path.exists(os.path.join(hfs, 'houdini')):
            return hfs

    # Try to get from Houdini module if available
    try:
        import hou
        # Get from current Houdini session
        hfs = hou.expandString("$HFS")
        if hfs and os.path.exists(hfs):
            return hfs
    except:
        pass

    # Try common Linux installation paths
    common_paths = [
        '/opt/sidefx/houdini/21',
        '/opt/sidefx/houdini/20',
        '/opt/sidefx/houdini/19',
    ]

    for base_path in common_paths:
        if os.path.exists(base_path):
            # Look for actual version directories
            for item in sorted(os.listdir(base_path), reverse=True):  # Sort to get latest version first
                full_path = os.path.join(base_path, item)
                # Check if it's a valid Houdini installation
                if os.path.isdir(full_path) and os.path.exists(os.path.join(full_path, 'houdini')):
                    logger.debug(f"Found Houdini installation at: {full_path}")
                    return full_path

    # Last resort - raise error instead of using hardcoded path
    raise RuntimeError("Could not determine HFS (Houdini installation directory). Please set HFS environment variable.")


def get_hh_from_hfs(hfs):
    """Get HH (Houdini Home) from HFS

    Args:
        hfs: Houdini File System root path

    Returns:
        str: HH path (HFS/houdini)
    """
    if not hfs:
        raise ValueError("HFS path is required to determine HH")

    hh = os.path.join(hfs, 'houdini').replace("\\", "/")

    # Don't check existence - this is a render farm path
    logger.debug(f"HH path for render farm: {hh}")

    return hh


def get_hb_from_hfs(hfs):
    """Get HB (Houdini Bin) from HFS

    Args:
        hfs: Houdini File System root path

    Returns:
        str: HB path (HFS/bin)
    """
    if not hfs:
        raise ValueError("HFS path is required to determine HB")

    hb = os.path.join(hfs, 'bin').replace("\\", "/")

    # Don't check existence - this is a render farm path
    logger.debug(f"HB path for render farm: {hb}")

    return hb


def get_hhp_dir(hfs):
    """Determine the HHP (Houdini Python Path) directory based on HFS and Houdini version"""
    if not hfs:
        hfs = get_hfs_from_environment_or_detect()

    hhp_dir = None

    # Try to extract version number from path
    version_match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', hfs)

    if version_match:
        major = int(version_match.group(1))
        minor = int(version_match.group(2))

        # Map Houdini version to Python version
        if major >= 21:
            hhp_dir = os.path.join(hfs, 'houdini', 'python3.11libs')
        elif major >= 20 and minor >= 5:
            hhp_dir = os.path.join(hfs, 'houdini', 'python3.11libs')
        elif major >= 20:
            hhp_dir = os.path.join(hfs, 'houdini', 'python3.10libs')
        elif major >= 19 and minor >= 5:
            hhp_dir = os.path.join(hfs, 'houdini', 'python3.9libs')
        elif major >= 19:
            hhp_dir = os.path.join(hfs, 'houdini', 'python3.7libs')
        elif major >= 18 and minor >= 5:
            hhp_dir = os.path.join(hfs, 'houdini', 'python3.7libs')
        elif major >= 18:
            hhp_dir = os.path.join(hfs, 'houdini', 'python2.7libs')
        else:
            hhp_dir = os.path.join(hfs, 'houdini', 'python2.7libs')

    # Don't check local existence - these are render farm paths
    # Just use the version-based determination
    if not hhp_dir:
        # Default fallback based on version or use python3.11libs as default
        hhp_dir = os.path.join(hfs, 'houdini', 'python3.11libs')
        logger.debug(f"Using default Python version: python3.11libs")

    hhp_dir = hhp_dir.replace("\\", "/")
    logger.debug(f"HHP path for render farm: {hhp_dir}")
    return hhp_dir

def get_all_houdini_paths(hfs=None, hb=None):
    """Get all standard Houdini environment paths for Linux render farm

    Args:
        hfs: Houdini File System root path (optional)
        hb: Houdini Bin path (optional)

    Returns:
        dict: Dictionary with HFS, HH, HB, HHP paths
    """
    # If we have HB but not HFS, derive HFS from HB
    if not hfs and hb and os.path.exists(hb):
        # HB is typically HFS/bin
        potential_hfs = os.path.dirname(hb)
        if os.path.exists(os.path.join(potential_hfs, 'houdini')):
            hfs = potential_hfs
            logger.debug(f"Derived HFS from HB: {hfs}")

    # If we still don't have HFS, try to detect it
    if not hfs:
        hfs = get_hfs_from_environment_or_detect()

    # Normalize path
    hfs = os.path.normpath(hfs).replace("\\", "/")

    # Calculate HH (Houdini Home)
    hh = get_hh_from_hfs(hfs)

    # Calculate HB if not provided
    if not hb:
        hb = get_hb_from_hfs(hfs)
    else:
        hb = os.path.normpath(hb).replace("\\", "/")

    # Get HHP using existing function
    hhp = get_hhp_dir(hfs).replace("\\", "/")

    return {
        'HFS': hfs,
        'HH': hh,
        'HB': hb,
        'HHP': hhp
    }


def get_houdini_path_additions(hh):
    """Get directories that should be added to PATH and HOUDINI_PATH for Linux

    Args:
        hh: Houdini Home directory

    Returns:
        dict: Dictionary with path_additions and houdini_path_additions
    """
    path_additions = []
    houdini_path_additions = []

    # Add scripts directory to PATH for executable scripts
    scripts_dir = os.path.join(hh, 'scripts').replace("\\", "/")
    # Don't check existence - these are render farm paths
    path_additions.append(scripts_dir)
    houdini_path_additions.append(scripts_dir)

    # Add to HOUDINI_PATH for resource discovery
    # These are data directories, not executable directories
    for subdir in ['geo', 'pic', 'glsl', 'vex', 'ocl', 'config']:
        dir_path = os.path.join(hh, subdir).replace("\\", "/")
        # Don't check existence - these are render farm paths
        houdini_path_additions.append(dir_path)

    logger.debug(f"Path additions for render farm: {path_additions}")
    logger.debug(f"HOUDINI_PATH additions for render farm: {houdini_path_additions}")

    return {
        'path_additions': path_additions,
        'houdini_path_additions': houdini_path_additions
    }


def connect_to_conductor(node):
    """Connect to Conductor and ensure valid connection before proceeding"""
    if not node:
        logger.debug(f"ERROR: Node is unavailable: {node}")
        raise RuntimeError("Cannot connect to Conductor without a valid node")

    # Check if already connected
    if coredata.valid():
        logger.debug(f"  Already connected to Conductor")
        return True

    logger.debug(f"  Connecting to Conductor...")
    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        logger.debug(f"  Connection attempt {attempt}/{max_attempts}")

        try:
            kwargs = {
                "force": True
            }
            controller.connect(node, **kwargs)

            # Verify the connection was successful
            if coredata.valid():
                logger.debug(f"  ✓ Successfully connected to Conductor")
                return True
            else:
                logger.debug(f"  ✗ Connection attempt {attempt} failed - data not valid")
                if attempt < max_attempts:
                    import time
                    wait_time = attempt * 2  # Exponential backoff
                    logger.debug(f"  Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)

        except Exception as e:
            logger.debug(f"  ✗ Connection attempt {attempt} failed with error: {e}")
            if attempt < max_attempts:
                import time
                wait_time = attempt * 2
                logger.debug(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

    # All attempts failed
    error_msg = "Failed to connect to Conductor after {} attempts. Please check your network connection and credentials.".format(
        max_attempts)
    logger.debug(f"  ERROR: {error_msg}")

    # Check if we should show UI message
    try:
        import hou
        if hou.isUIAvailable():
            hou.ui.displayMessage(
                error_msg,
                severity=hou.severityType.Error
            )
    except:
        pass  # If hou not available or UI not available, just continue

    raise RuntimeError(error_msg)


def get_parameter_value(node, param_name, default_value=None):
    """Get parameter value from node with fallback to default"""
    try:
        value = rops.get_parameter_value(node, param_name)
        if value is None and default_value is not None:
            return default_value
        return value
    except:
        if default_value is not None:
            return default_value
        return None


def set_parameter_value(node, param_name, value):
    """Set parameter value on node"""
    try:
        rops.set_parameter_value(node, param_name, value)
        return True
    except Exception as e:
        logger.warning(f"Could not set parameter {param_name}: {e}")
        return False


def get_core_count_from_instance_type(instance_type):
    """Extract hardware specifications from a Conductor instance type string.

    Parses Conductor cloud render farm instance type identifiers to determine
    the number of CPU cores, GPU count, and GPU type. This information is
    critical for the PDG scheduler's automatic optimization system, which
    configures performance settings based on available hardware resources.

    The function handles multiple instance naming patterns:
    - CPU-only instances: 'cw-xeonv3-{cores}'
    - GPU instances: 'cw-epycmilan-{cores}-{gpu_type}-{gpu_count}'
    - Legacy GPU instances: 'cw-epycmilan-{cores}-{gpu_type}{gpu_count}'

    Parameters
    ----------
    instance_type : str or None
        The Conductor instance type identifier string. Common formats include:
        - 'cw-xeonv3-16' (16-core CPU instance)
        - 'cw-xeonv3-64' (64-core CPU instance)
        - 'cw-epycmilan-32-rtx4000-1' (32 cores with 1 RTX 4000 GPU)
        - 'cw-epycmilan-64-rtxa6000-2' (64 cores with 2 RTX A6000 GPUs)
        - 'cw-epycmilan-16-rtx4000' (legacy format, assumes 1 GPU)

    Returns
    -------
    tuple[int, int, str or None]
        A 3-tuple containing:
        - core_count (int): Number of CPU cores/threads available on the instance.
          Defaults to 16 if parsing fails or instance_type is None/empty.
        - gpu_count (int): Number of GPUs available. 0 for CPU-only instances.
        - gpu_type (str or None): GPU model identifier (e.g., 'rtx4000', 'rtxa6000').
          None for CPU-only instances or if GPU type cannot be determined.

    Examples
    --------
    >>> # CPU-only instance with 32 cores
    >>> get_core_count_from_instance_type('cw-xeonv3-32')
    (32, 0, None)

    >>> # GPU instance with 64 cores and 2 RTX A6000 GPUs
    >>> get_core_count_from_instance_type('cw-epycmilan-64-rtxa6000-2')
    (64, 2, 'rtxa6000')

    >>> # Legacy GPU format (assumes single GPU)
    >>> get_core_count_from_instance_type('cw-epycmilan-16-rtx4000')
    (16, 1, 'rtx4000')

    >>> # Invalid or unrecognized format returns defaults
    >>> get_core_count_from_instance_type('unknown-instance-type')
    (16, 0, None)

    >>> # None or empty string returns defaults
    >>> get_core_count_from_instance_type(None)
    (16, 0, None)

    Notes
    -----
    - The extracted core count is used to AUTO-CALCULATE numerous performance
      settings including thread counts, memory limits, cache sizes, and batch
      sizes throughout the PDG scheduler optimization system.
    - GPU information determines GPU-specific optimizations like CUDA cache
      sizes, OptiX settings, and renderer-specific GPU memory limits.
    - The function defaults to 16 cores when parsing fails to ensure the
      scheduler can still operate with reasonable performance settings.
    - All pattern matching is case-sensitive as Conductor instance types
      follow a consistent lowercase naming convention.
    - The function logs debug information about successful parsing and
      warnings about failures to aid in troubleshooting.

    See Also
    --------
    update_thread_dependent_parameters : Updates parameters based on core count
    configure_instance_and_threads : Main configuration function using this parser
    """
    if not instance_type:
        logger.warning("    No instance type provided, defaulting to 16 cores")
        return 16, 0, None

    core_count = None
    gpu_count = 0
    gpu_type = None

    # Pattern for CPU instances: cw-xeonv3-{cores}
    cpu_match = re.match(r'cw-xeonv3-(\d+)', instance_type)
    if cpu_match:
        core_count = int(cpu_match.group(1))
        logger.debug(f"    Detected CPU instance with {core_count} cores")
        return core_count, 0, None

    # Pattern for GPU instances: cw-epycmilan-{cores}-{gpu_type}-{gpu_count}
    gpu_match = re.match(r'cw-epycmilan-(\d+)-(rtx[a-z0-9]+)-(\d+)', instance_type)
    if gpu_match:
        core_count = int(gpu_match.group(1))
        gpu_type = gpu_match.group(2)
        gpu_count = int(gpu_match.group(3))
        logger.debug(f"    Detected GPU instance with {core_count} cores and {gpu_count} {gpu_type.upper()} GPU(s)")
        return core_count, gpu_count, gpu_type

    # Fallback pattern for GPU instances
    gpu_fallback_match = re.match(r'cw-epycmilan-(\d+)-', instance_type)
    if gpu_fallback_match:
        core_count = int(gpu_fallback_match.group(1))

        # Try to extract GPU info
        if 'rtx4000' in instance_type:
            gpu_type = 'rtx4000'
            gpu_count_match = re.search(r'-(\d+)$', instance_type)
            if gpu_count_match:
                gpu_count = int(gpu_count_match.group(1))
        elif 'rtxa6000' in instance_type:
            gpu_type = 'rtxa6000'
            gpu_count_match = re.search(r'-(\d+)$', instance_type)
            if gpu_count_match:
                gpu_count = int(gpu_count_match.group(1))

        logger.debug(f"    Detected GPU instance with {core_count} cores")
        if gpu_count > 0:
            logger.debug(f"    Detected {gpu_count} {gpu_type.upper() if gpu_type else 'GPU'}(s)")

        return core_count, gpu_count, gpu_type

    # Default to 16 cores if parsing fails
    logger.warning(f"    Could not parse instance type: {instance_type}, defaulting to 16 cores")
    return 16, 0, None


def update_thread_dependent_parameters(node, thread_count, gpu_count=0, gpu_type=None,
                                       original_thread_count=None, use_max_processors=1):
    """Update all parameters that depend on thread_count when instance_type changes

    This function updates all AUTO-CALCULATED parameters based on the new thread count

    Parameters:
    -----------
    node : HDA node
    thread_count : int - The actual thread count to use
    gpu_count : int - Number of GPUs
    gpu_type : str - GPU type identifier
    original_thread_count : int - The original detected/manual thread count
    use_max_processors : int - The use_max_processors parameter value (0, 1, or 2)
    """
    logger.debug(f"Updating thread-dependent parameters for {thread_count} cores")

    # If no original thread count provided, use thread_count
    if original_thread_count is None:
        original_thread_count = thread_count

    # Update core thread count based on mode
    # Mode 0: Keep user value (don't update)
    # Mode 1 & 2: Update with calculated value
    if use_max_processors != 0:
        # Only update the displayed value in auto modes
        set_parameter_value(node, "houdini_max_threads", thread_count)
    # In mode 0, the user controls the value directly

    # Only update auto-calculated values if their respective auto modes are enabled

    # PDG Performance parameters
    if get_parameter_value(node, "conductor_batch_size_mode", 0) == 0:  # Auto mode
        # Batch size is calculated as slots * 2, but we don't override the multiplier
        pass  # Multiplier is user-controlled

    # Memory settings (only if auto mode is on)
    if get_parameter_value(node, "auto_memory_settings", 1):
        # These will be calculated in get_memory_settings_for_core_count
        # We don't set them here as they're calculated dynamically
        pass

    # Cache sizes that scale with threads
    if get_parameter_value(node, "enable_cache_optimization", 1):
        # These are calculated dynamically in get_cache_optimization_settings
        pass

    # File I/O thread counts
    if get_parameter_value(node, "enable_io_optimization", 1):
        # BGEO compression threads
        bgeo_threads = min(thread_count, 8)
        if get_parameter_value(node, "bgeo_compress_threads", 8) == 8:  # If at default
            set_parameter_value(node, "bgeo_compress_threads", bgeo_threads)

    # Single machine optimizations
    if not get_parameter_value(node, "multiple_machines", 1):
        if get_parameter_value(node, "enable_single_machine_opt", 1):
            # Shared memory size
            shared_mem_size = min(32, thread_count // 2)
            if get_parameter_value(node, "shared_memory_size", 32) == 32:  # If at default
                set_parameter_value(node, "shared_memory_size", shared_mem_size)

            # Local cache size
            local_cache_size = min(100, thread_count)
            if get_parameter_value(node, "local_cache_size", 100) == 100:  # If at default
                set_parameter_value(node, "local_cache_size", local_cache_size)

    # GPU settings update
    if gpu_count > 0 and gpu_type:
        if get_parameter_value(node, "enable_gpu_optimization", 1):
            # Update GPU memory limits based on type
            if get_parameter_value(node, "gpu_memory_limit_override", 0) == 0:  # Auto mode
                # Will be calculated in get_gpu_optimization_settings
                pass

    logger.debug(f"Thread-dependent parameters updated for {thread_count} cores")


def on_use_max_processors_changed(node, **kwargs):
    """Callback function when use_max_processors parameter changes

    This function should be called when the use_max_processors parameter changes
    to recalculate and update the houdini_max_threads value
    """
    try:
        use_max_processors = get_parameter_value(node, "use_max_processors", 1)

        # Get the actual hardware thread count (not the user-specified value)
        hardware_thread_count = get_hardware_thread_count(node)

        # Calculate and set the new thread count based on the mode
        if use_max_processors == 0:
            # User Specified - don't change the value, just enable the parameter
            pass  # User will enter their own value
        elif use_max_processors == 1:
            # Use All Processors - set to hardware thread count
            set_parameter_value(node, "houdini_max_threads", hardware_thread_count)
        elif use_max_processors == 2:
            # Use All Processors Except One
            set_parameter_value(node, "houdini_max_threads", max(1, hardware_thread_count - 1))

        # Re-run the full configuration to update all dependent parameters
        configure_instance_and_threads(node, **kwargs)

    except Exception as e:
        logger.error(f"Error in on_use_max_processors_changed: {e}")

def on_instance_type_changed(node, **kwargs):
    """Callback function when instance_type parameter changes

    This ensures the hardware thread count is updated when instance type changes
    """
    try:
        # Re-run the configuration which will update the hardware thread count
        configure_instance_and_threads(node, **kwargs)
    except Exception as e:
        logger.error(f"Error in on_instance_type_changed: {e}")

# Additional helper function to check if houdini_max_threads should be editable
def is_houdini_max_threads_editable(node):
    """Check if houdini_max_threads parameter should be editable

    Returns True only when use_max_processors is set to 0 (User Specified)
    """
    use_max_processors = get_parameter_value(node, "use_max_processors", 1)
    return use_max_processors == 0


def configure_instance_and_threads(node, **kwargs):
    """Configure instance type parsing and thread settings for a node

    This is the main function triggered when instance_type changes
    """
    try:
        # Check for the new use_max_processors parameter
        use_max_processors = get_parameter_value(node, "use_max_processors", 1)  # Default to "Use All Processors"

        # ALWAYS get the base hardware thread count first, regardless of mode
        # This ensures we have the actual hardware count for calculations

        # Check for manual override first (legacy parameter)
        if get_parameter_value(node, "override_instance_detection", 0):
            # Manual override mode - get base thread count
            hardware_thread_count = get_parameter_value(node, "manual_core_count", 16)
            gpu_count = get_parameter_value(node, "manual_gpu_count", 0)
            gpu_type_idx = get_parameter_value(node, "manual_gpu_type", 0)
            gpu_types = ["none", "rtx4000", "rtxa6000", "rtx3090", "rtx4090", "a100", "h100"]
            gpu_type = gpu_types[gpu_type_idx] if gpu_type_idx > 0 else None
            instance_type = "manual"

            logger.debug(f"    Using manual override: {hardware_thread_count} cores, {gpu_count} GPUs")
        else:
            # Auto detection from instance_type
            instance_type = get_parameter_value(node, "instance_type", "")
            logger.debug(f"    Instance type: {instance_type}")

            # Parse instance type to get core and GPU count
            hardware_thread_count, gpu_count, gpu_type = get_core_count_from_instance_type(instance_type)

        # Store the hardware thread count for reference
        # This is important for switching between modes
        store_hardware_thread_count(node, hardware_thread_count)

        # Apply use_max_processors logic to determine final thread count
        final_thread_count = hardware_thread_count

        if use_max_processors == 0:
            # User Specified Thread Count - get value from houdini_max_threads
            # But only if it's a valid user-entered value
            user_threads = get_parameter_value(node, "houdini_max_threads", hardware_thread_count)
            final_thread_count = user_threads
            logger.debug(f"    Using user-specified thread count: {final_thread_count}")
        elif use_max_processors == 1:
            # Use All Processors - use detected/manual thread count as-is
            final_thread_count = hardware_thread_count
            # Update the displayed value in houdini_max_threads
            set_parameter_value(node, "houdini_max_threads", final_thread_count)
            logger.debug(f"    Using all processors: {final_thread_count}")
        elif use_max_processors == 2:
            # Use All Processors Except One
            final_thread_count = max(1, hardware_thread_count - 1)
            # Update the displayed value in houdini_max_threads
            set_parameter_value(node, "houdini_max_threads", final_thread_count)
            logger.debug(f"    Using all processors except one: {final_thread_count}")

        # Check if single machine mode
        use_single_machine = not get_parameter_value(node, "multiple_machines", 1)

        # Update all thread-dependent parameters with the final thread count
        update_thread_dependent_parameters(node, final_thread_count, gpu_count, gpu_type,
                                           original_thread_count=hardware_thread_count,
                                           use_max_processors=use_max_processors)

        # Log configuration summary
        logger.debug(f"    Instance configuration:")
        logger.debug(f"      Type: {instance_type}")
        logger.debug(f"      CPU cores detected: {hardware_thread_count}")
        logger.debug(f"      CPU threads to use: {final_thread_count}")
        logger.debug(f"      GPU count: {gpu_count}")
        logger.debug(f"      GPU type: {gpu_type if gpu_type else 'None'}")
        logger.debug(f"      Single machine mode: {use_single_machine}")

        # Return configuration dictionary
        return {
            "instance_type": instance_type,
            "thread_count": final_thread_count,
            "gpu_count": gpu_count,
            "gpu_type": gpu_type,
            "use_single_machine": use_single_machine,
            "hardware_thread_count": hardware_thread_count  # Keep track of actual hardware
        }
    except Exception as e:
        print(f"Error in configure_instance_and_threads: {e}")

def store_hardware_thread_count(node, thread_count):
    """Store the actual hardware thread count for mode switching

    This stores the real hardware thread count in a hidden parameter or user data
    so we can retrieve it when switching between modes
    """
    try:
        # Store as user data on the node
        node.setUserData("hardware_thread_count", str(thread_count))
    except:
        # Fallback: try to store in a hidden parameter if available
        pass

def get_hardware_thread_count(node):
    """Get the stored hardware thread count

    Returns the actual hardware thread count, not the user-specified value
    """
    try:
        # Try to get from user data first
        stored_count = node.userData("hardware_thread_count")
        if stored_count:
            return int(stored_count)
    except:
        pass

    # Fallback: re-detect from instance type or manual settings
    if get_parameter_value(node, "override_instance_detection", 0):
        return get_parameter_value(node, "manual_core_count", 16)
    else:
        instance_type = get_parameter_value(node, "instance_type", "")
        thread_count, _, _ = get_core_count_from_instance_type(instance_type)
        return thread_count

def configure_cook_mode_advanced(node, thread_count, use_single_machine, network_complexity=None):
    """Configure advanced cooking mode based on parameters"""
    cook_env = {}

    # Get network complexity from parameter if not provided
    if network_complexity is None:
        complexity_idx = get_parameter_value(node, "network_complexity", 1)
        network_complexity = ["simple", "medium", "complex"][complexity_idx]

    # Check for cook mode override
    cook_mode_override = get_parameter_value(node, "cook_mode_override", 0)

    if cook_mode_override == 0:  # Auto mode
        # Determine optimal cook mode based on configuration
        if use_single_machine and thread_count >= 64:
            cook_env["HOUDINI_COOK_MODE"] = "aggressive"
            cook_env["HOUDINI_COOK_PARALLEL_THRESHOLD"] = "1"
            cook_env["HOUDINI_COOK_BATCH_SIZE"] = str(min(200, thread_count * 3))
            logger.debug(f"    Cook mode: aggressive (64+ cores single machine)")
        elif use_single_machine and thread_count >= 32:
            cook_env["HOUDINI_COOK_MODE"] = "aggressive"
            cook_env["HOUDINI_COOK_PARALLEL_THRESHOLD"] = "2"
            cook_env["HOUDINI_COOK_BATCH_SIZE"] = str(min(100, thread_count * 2))
            logger.debug(f"    Cook mode: aggressive (32+ cores single machine)")
        elif use_single_machine and thread_count >= 16:
            cook_env["HOUDINI_COOK_MODE"] = "parallel"
            cook_env["HOUDINI_COOK_PARALLEL_THRESHOLD"] = "5"
            cook_env["HOUDINI_COOK_BATCH_SIZE"] = str(thread_count)
            logger.debug(f"    Cook mode: parallel (16+ cores single machine)")
        elif thread_count >= 8:
            cook_env["HOUDINI_COOK_MODE"] = "hybrid"
            cook_env["HOUDINI_COOK_PARALLEL_THRESHOLD"] = "10"
            cook_env["HOUDINI_COOK_BATCH_SIZE"] = str(max(10, thread_count // 2))
            logger.debug(f"    Cook mode: hybrid (8+ cores)")
        else:
            cook_env["HOUDINI_COOK_MODE"] = "automatic"
            cook_env["HOUDINI_COOK_PARALLEL_THRESHOLD"] = "20"
            cook_env["HOUDINI_COOK_BATCH_SIZE"] = "5"
            logger.debug(f"    Cook mode: automatic (<8 cores)")
    else:
        # Manual override
        cook_modes = ["", "serial", "parallel", "hybrid", "aggressive"]
        cook_env["HOUDINI_COOK_MODE"] = cook_modes[cook_mode_override]

        # Get threshold from parameter
        threshold = get_parameter_value(node, "cook_parallel_threshold", 10)
        cook_env["HOUDINI_COOK_PARALLEL_THRESHOLD"] = str(threshold)

        # Get batch size override
        batch_size_override = get_parameter_value(node, "cook_batch_size_override", 0)
        if batch_size_override > 0:
            cook_env["HOUDINI_COOK_BATCH_SIZE"] = str(batch_size_override)
        else:
            cook_env["HOUDINI_COOK_BATCH_SIZE"] = str(thread_count)

    # Adjust for network complexity
    if network_complexity == "complex":
        if cook_env["HOUDINI_COOK_MODE"] == "aggressive":
            cook_env["HOUDINI_COOK_MODE"] = "parallel"
        cook_env["HOUDINI_COOK_PARALLEL_THRESHOLD"] = str(
            min(20, int(cook_env.get("HOUDINI_COOK_PARALLEL_THRESHOLD", "10")) * 2)
        )
        logger.debug(f"    Adjusted for complex network")
    elif network_complexity == "simple":
        if cook_env["HOUDINI_COOK_MODE"] == "automatic":
            cook_env["HOUDINI_COOK_MODE"] = "parallel"
        cook_env["HOUDINI_COOK_PARALLEL_THRESHOLD"] = str(
            max(1, int(cook_env.get("HOUDINI_COOK_PARALLEL_THRESHOLD", "10")) // 2)
        )
        logger.debug(f"    Adjusted for simple network")

    # Additional cooking optimization from parameters
    if get_parameter_value(node, "cook_prefer_parallel", 1):
        cook_env["HOUDINI_COOK_PREFER_PARALLEL"] = "1"

    cook_env["HOUDINI_COOK_MAX_PARALLEL_CHAINS"] = str(thread_count)
    cook_env["HOUDINI_COOK_QUEUE_SIZE"] = str(thread_count * 4)
    cook_env["HOUDINI_COOK_THREAD_POOL_SIZE"] = str(thread_count)

    # Memory management for cooking
    if thread_count >= 32:
        cook_env["HOUDINI_COOK_MEMORY_LIMIT"] = "65536"
    elif thread_count >= 16:
        cook_env["HOUDINI_COOK_MEMORY_LIMIT"] = "32768"
    else:
        cook_env["HOUDINI_COOK_MEMORY_LIMIT"] = "16384"

    # Profiling from parameters
    if get_parameter_value(node, "enable_cook_profiling", 1):
        cook_env["HOUDINI_COOK_PROFILE"] = "1"
        threshold_ms = get_parameter_value(node, "cook_profile_threshold", 100)
        cook_env["HOUDINI_COOK_PROFILE_THRESHOLD"] = str(threshold_ms / 1000.0)  # Convert to seconds

    return cook_env


def get_memory_settings_for_core_count(node, core_count):
    """Determine memory settings based on core count and parameters"""
    memory_settings = {}

    # Check if auto memory is enabled
    if get_parameter_value(node, "auto_memory_settings", 1):
        # Auto-calculate based on core count
        if core_count <= 4:
            memory_settings["texture_cache"] = "1024"
            memory_settings["geometry_cache"] = "512"
            memory_settings["vop_cache"] = "256"
            memory_settings["font_cache"] = "64"
            memory_settings["ldpath_cache"] = "128"
            memory_settings["audio_cache"] = "64"
            memory_settings["max_memory_usage"] = "12288"
            memory_settings["opencl_memory"] = "2048"
        elif core_count <= 16:
            memory_settings["texture_cache"] = "4096"
            memory_settings["geometry_cache"] = "2048"
            memory_settings["vop_cache"] = "512"
            memory_settings["font_cache"] = "128"
            memory_settings["ldpath_cache"] = "256"
            memory_settings["audio_cache"] = "128"
            memory_settings["max_memory_usage"] = "51200"
            memory_settings["opencl_memory"] = "8192"
        elif core_count <= 32:
            memory_settings["texture_cache"] = "8192"
            memory_settings["geometry_cache"] = "4096"
            memory_settings["vop_cache"] = "1024"
            memory_settings["font_cache"] = "256"
            memory_settings["ldpath_cache"] = "512"
            memory_settings["audio_cache"] = "256"
            memory_settings["max_memory_usage"] = "102400"
            memory_settings["opencl_memory"] = "16384"
        else:
            memory_settings["texture_cache"] = "16384"
            memory_settings["geometry_cache"] = "8192"
            memory_settings["vop_cache"] = "2048"
            memory_settings["font_cache"] = "512"
            memory_settings["ldpath_cache"] = "1024"
            memory_settings["audio_cache"] = "512"
            memory_settings["max_memory_usage"] = "153600"
            memory_settings["opencl_memory"] = "32768"
    else:
        # Use manual overrides from parameters
        memory_settings["texture_cache"] = str(get_parameter_value(node, "texture_cache_override", 4096))
        memory_settings["geometry_cache"] = str(get_parameter_value(node, "geometry_cache_override", 2048))
        memory_settings["vop_cache"] = str(get_parameter_value(node, "vop_cache_override", 512))
        memory_settings["font_cache"] = "128"  # No UI parameter for this
        memory_settings["ldpath_cache"] = "256"  # No UI parameter for this
        memory_settings["audio_cache"] = "128"  # No UI parameter for this
        memory_settings["max_memory_usage"] = str(get_parameter_value(node, "max_memory_usage", 51200))
        memory_settings["opencl_memory"] = "8192"  # No UI parameter for this

    logger.debug(f"    Memory settings for {core_count} cores configured")
    return memory_settings


def get_pdg_performance_settings(node, core_count):
    """Get PDG-specific performance settings from parameters"""
    pdg_settings = {}

    # PDG slot configuration from multiplier
    multiplier = get_parameter_value(node, "conductor_slots_multiplier", 0.75)
    pdg_slots = max(1, int(core_count * multiplier))

    pdg_settings["PDG_SLOTS"] = str(pdg_slots)
    pdg_settings["PDG_MAXPROCS"] = str(core_count)
    pdg_settings["PDG_MAXTHREADS"] = str(core_count)

    # Batch size based on mode
    batch_mode = get_parameter_value(node, "conductor_batch_size_mode", 0)
    if batch_mode == 0:  # Auto
        pdg_settings["PDG_BATCH_SIZE"] = str(min(100, pdg_slots * 2))
    elif batch_mode == 1:  # Conservative
        pdg_settings["PDG_BATCH_SIZE"] = str(pdg_slots)
    else:  # Aggressive
        pdg_settings["PDG_BATCH_SIZE"] = str(min(200, pdg_slots * 3))

    pdg_settings["PDG_DIRTY_WHEN"] = "oncook"
    pdg_settings["PDG_SCHEDULETHRESHOLD"] = str(pdg_slots * 2)

    # Cache mode from parameter
    cache_mode = get_parameter_value(node, "conductor_cache_mode", 2)
    pdg_settings["conductor_cache_mode"] = str(cache_mode)
    pdg_settings["PDG_CACHE_SIZE"] = str(min(1000000, core_count * 10000))
    pdg_settings["PDG_WORK_ITEM_DATA_CACHE"] = "1"

    # PDG networking from parameters
    pdg_settings["PDG_RPC_TIMEOUT"] = str(get_parameter_value(node, "conductor_rpc_timeout", 120))
    pdg_settings["PDG_RPC_MAX_ERRORS"] = str(get_parameter_value(node, "conductor_rpc_max_errors", 50))
    pdg_settings["PDG_RPC_BATCH"] = "1"
    pdg_settings["PDG_RPC_RETRY_DELAY"] = "2"
    pdg_settings["PDG_RPC_BACKOFF"] = "1.5"
    pdg_settings["PDG_RPC_CONNECT_TIMEOUT"] = "30"

    # File handling from parameters
    if get_parameter_value(node, "conductor_compress_work_item_data", 1):
        pdg_settings["PDG_COMPRESS_WORK_ITEM_DATA"] = "1"
    if get_parameter_value(node, "conductor_use_pdgnet", 1):
        pdg_settings["PDG_USE_PDGNET"] = "1"

    pdg_settings["PDG_TASK_CALLBACK_THROTTLE"] = "0.1"

    logger.debug(f"    PDG settings configured for {pdg_slots} slots")
    return pdg_settings


def get_single_machine_optimization_settings(node, core_count):
    """Get single machine optimizations from parameters"""
    single_machine_settings = {}

    if not get_parameter_value(node, "enable_single_machine_opt", 1):
        return single_machine_settings

    # NUMA optimization
    if get_parameter_value(node, "enable_numa_aware", 1):
        single_machine_settings["HOUDINI_NUMA_AWARE"] = "1"
        single_machine_settings["HOUDINI_NUMA_NODES"] = "all"

    # CPU affinity
    cpu_affinity = get_parameter_value(node, "cpu_affinity", 0)
    if cpu_affinity == 0:
        single_machine_settings["HOUDINI_CPU_AFFINITY"] = "auto"
    elif cpu_affinity == 1:
        single_machine_settings["HOUDINI_CPU_AFFINITY"] = "manual"
    else:
        single_machine_settings["HOUDINI_CPU_AFFINITY"] = "disabled"

    if get_parameter_value(node, "thread_affinity", 1):
        single_machine_settings["HOUDINI_THREAD_AFFINITY"] = "1"

    # Scheduler mode
    scheduler_modes = ["performance", "balanced", "powersave"]
    scheduler_mode = get_parameter_value(node, "scheduler_mode", 0)
    single_machine_settings["HOUDINI_SCHEDULER_MODE"] = scheduler_modes[scheduler_mode]

    # Batching
    if get_parameter_value(node, "batch_mode_aggressive", 1):
        batch_size = min(500, core_count * 10)
        single_machine_settings["PDG_BATCH_MODE"] = "aggressive"
        single_machine_settings["PDG_BATCH_SIZE"] = str(batch_size)
        poll_rate = get_parameter_value(node, "batch_poll_rate", 50)
        single_machine_settings["PDG_BATCH_POLL_RATE"] = str(poll_rate / 1000.0)  # Convert to seconds
        single_machine_settings["PDG_BATCH_TIMEOUT"] = "30"

    # Shared memory
    if get_parameter_value(node, "use_shared_memory", 1):
        single_machine_settings["PDG_USE_SHARED_MEMORY"] = "1"
        shared_mem_size = get_parameter_value(node, "shared_memory_size", 32)
        single_machine_settings["PDG_SHARED_MEMORY_SIZE"] = str(shared_mem_size * 1024)  # Convert to MB
        single_machine_settings["PDG_SHARED_MEMORY_TIMEOUT"] = "5"

    # Local cache
    if get_parameter_value(node, "use_local_cache", 1):
        single_machine_settings["PDG_USE_LOCAL_CACHE"] = "1"
        single_machine_settings["PDG_LOCAL_CACHE_PATH"] = "/tmp/pdg_cache"
        local_cache_size = get_parameter_value(node, "local_cache_size", 100)
        single_machine_settings["PDG_LOCAL_CACHE_SIZE"] = str(local_cache_size * 1024)  # Convert to MB

    # Process pool
    pool_size_override = get_parameter_value(node, "process_pool_size_override", 0)
    if pool_size_override > 0:
        single_machine_settings["PDG_PROCESS_POOL_SIZE"] = str(pool_size_override)
    else:
        single_machine_settings["PDG_PROCESS_POOL_SIZE"] = str(core_count)

    single_machine_settings["PDG_PROCESS_POOL_TIMEOUT"] = "300"

    if get_parameter_value(node, "reuse_processes", 1):
        single_machine_settings["PDG_REUSE_PROCESSES"] = "1"

    # Zero-copy
    if get_parameter_value(node, "enable_zero_copy", 1):
        single_machine_settings["PDG_ZERO_COPY"] = "1"
        mmap_threshold = get_parameter_value(node, "mmap_threshold", 64)
        single_machine_settings["PDG_MMAP_THRESHOLD"] = str(mmap_threshold * 1024)  # Convert to bytes

    logger.debug(f"    Single machine optimizations configured")
    return single_machine_settings


def get_parallel_cooking_settings(node, core_count):
    """Get parallel cooking settings from parameters"""
    parallel_settings = {}

    parallel_settings["HOUDINI_COOK_RECURSION_LIMIT"] = "1000"
    parallel_settings["HOUDINI_PARALLEL_COOK_THRESHOLD"] = str(
        get_parameter_value(node, "cook_parallel_threshold", 10)
    )
    parallel_settings["HOUDINI_PARALLEL_COOK_MODE"] = "aggressive"

    # Task stealing
    if get_parameter_value(node, "enable_task_stealing", 1):
        parallel_settings["HOUDINI_TASK_STEALING"] = "1"
        queue_multiplier = get_parameter_value(node, "task_queue_multiplier", 4)
        parallel_settings["HOUDINI_TASK_QUEUE_SIZE"] = str(core_count * queue_multiplier)
        parallel_settings["HOUDINI_TASK_STEAL_ATTEMPTS"] = "3"

    # Lock-free
    if get_parameter_value(node, "use_lockfree", 1):
        parallel_settings["HOUDINI_USE_LOCKFREE"] = "1"
        parallel_settings["HOUDINI_LOCKFREE_QUEUE_SIZE"] = str(core_count * 100)

    # Graph partitioning
    partition_mode = get_parameter_value(node, "graph_partition_mode", 0)
    if partition_mode == 0:
        parallel_settings["PDG_GRAPH_PARTITION_MODE"] = "auto"
        parallel_settings["PDG_GRAPH_PARTITION_SIZE"] = str(max(4, core_count // 8))
    elif partition_mode == 1:
        parallel_settings["PDG_GRAPH_PARTITION_MODE"] = "manual"
    else:
        parallel_settings["PDG_GRAPH_PARTITION_MODE"] = "disabled"

    parallel_settings["PDG_GRAPH_PARTITION_BALANCE"] = "1"

    # Speculative execution
    if get_parameter_value(node, "enable_speculative_execution", 1):
        parallel_settings["PDG_SPECULATIVE_EXECUTION"] = "1"
        parallel_settings["PDG_SPECULATIVE_THRESHOLD"] = "0.8"

    logger.debug(f"    Parallel cooking settings configured")
    return parallel_settings


def get_cache_optimization_settings(node, core_count):
    """Get cache optimization settings from parameters"""
    cache_settings = {}

    if not get_parameter_value(node, "enable_cache_optimization", 1):
        return cache_settings

    # L1/L2/L3 cache optimization
    cache_settings["HOUDINI_CACHE_LINE_SIZE"] = "64"
    cache_settings["HOUDINI_CACHE_ALIGN_DATA"] = "1"
    cache_settings["HOUDINI_PREFETCH_DISTANCE"] = "4"

    # Attribute cache
    attrib_cache = get_parameter_value(node, "attrib_cache_size", 8192)
    cache_settings["HOUDINI_ATTRIB_CACHE_SIZE"] = str(attrib_cache)
    cache_settings["HOUDINI_ATTRIB_CACHE_MODE"] = "lru"

    # Expression cache
    expr_cache = get_parameter_value(node, "expr_cache_size", 4096)
    cache_settings["HOUDINI_EXPR_CACHE_SIZE"] = str(expr_cache)
    cache_settings["HOUDINI_EXPR_CACHE_TIMEOUT"] = "3600"

    # Compilation cache
    if get_parameter_value(node, "compile_cache", 1):
        cache_settings["HOUDINI_COMPILE_CACHE"] = "1"
        cache_settings["HOUDINI_COMPILE_CACHE_SIZE"] = str(min(2048, core_count * 32))
        cache_settings["HOUDINI_COMPILE_CACHE_PATH"] = "/tmp/houdini_compile_cache"

    # Dependency cache
    if get_parameter_value(node, "dependency_cache", 1):
        cache_settings["PDG_DEPENDENCY_CACHE"] = "1"
        cache_settings["PDG_DEPENDENCY_CACHE_SIZE"] = str(min(1024, core_count * 16))

    # Result cache
    cache_settings["PDG_RESULT_CACHE"] = "1"
    cache_settings["PDG_RESULT_CACHE_SIZE"] = str(min(4096, core_count * 64))

    # Compression
    compression_modes = ["none", "lz4", "zstd", "gzip"]
    compression = get_parameter_value(node, "result_cache_compression", 1)
    cache_settings["PDG_RESULT_CACHE_COMPRESSION"] = compression_modes[compression]

    logger.debug(f"    Cache optimization settings configured")
    return cache_settings


def get_scheduler_optimization_settings(node, core_count):
    """Get scheduler optimization settings from parameters"""
    scheduler_settings = {}

    # Scheduler algorithm
    algorithms = ["work_stealing", "round_robin", "priority", "load_balanced"]
    algorithm = get_parameter_value(node, "scheduler_algorithm", 0)
    scheduler_settings["PDG_SCHEDULER_ALGORITHM"] = algorithms[algorithm]
    scheduler_settings["PDG_SCHEDULER_GRANULARITY"] = "fine"

    # Priority scheduling
    if get_parameter_value(node, "enable_priority_scheduling", 1):
        scheduler_settings["PDG_PRIORITY_SCHEDULING"] = "1"
        levels = get_parameter_value(node, "priority_levels", 10)
        scheduler_settings["PDG_PRIORITY_LEVELS"] = str(levels)
        scheduler_settings["PDG_PRIORITY_BOOST_INTERVAL"] = "5"

    # Load balancing
    load_modes = ["static", "dynamic", "adaptive"]
    load_mode = get_parameter_value(node, "load_balance_mode", 1)
    scheduler_settings["PDG_LOAD_BALANCE_MODE"] = load_modes[load_mode]
    scheduler_settings["PDG_LOAD_BALANCE_INTERVAL"] = "1"
    scheduler_settings["PDG_LOAD_BALANCE_THRESHOLD"] = "0.2"

    # Predictive scheduling
    if get_parameter_value(node, "enable_predictive_scheduling", 1):
        scheduler_settings["PDG_PREDICTIVE_SCHEDULING"] = "1"
        scheduler_settings["PDG_PREDICTION_WINDOW"] = "100"
        scheduler_settings["PDG_PREDICTION_ACCURACY_THRESHOLD"] = "0.7"

    # Batch scheduling
    if get_parameter_value(node, "batch_scheduler", 1):
        scheduler_settings["PDG_BATCH_SCHEDULER"] = "1"
        scheduler_settings["PDG_BATCH_MIN_SIZE"] = "10"
        scheduler_settings["PDG_BATCH_MAX_SIZE"] = str(min(1000, core_count * 20))
        scheduler_settings["PDG_BATCH_TIMEOUT"] = "0.1"

    logger.debug(f"    Scheduler optimization settings configured")
    return scheduler_settings


def get_memory_pool_settings(node, core_count):
    """Get memory pool settings from parameters"""
    memory_pool_settings = {}

    if not get_parameter_value(node, "use_memory_pools", 1):
        return memory_pool_settings

    memory_pool_settings["HOUDINI_USE_MEMORY_POOLS"] = "1"
    memory_pool_settings["HOUDINI_MEMORY_POOL_SIZE"] = str(min(65536, core_count * 1024))

    chunk_size = get_parameter_value(node, "memory_pool_chunk_size", 4096)
    memory_pool_settings["HOUDINI_MEMORY_POOL_CHUNK_SIZE"] = str(chunk_size)

    # Arena allocator
    if get_parameter_value(node, "use_arena_allocator", 1):
        memory_pool_settings["HOUDINI_USE_ARENA_ALLOCATOR"] = "1"
        memory_pool_settings["HOUDINI_ARENA_SIZE"] = str(min(16384, core_count * 256))
        memory_pool_settings["HOUDINI_ARENA_THREAD_CACHE"] = "1"

    # Slab allocator
    if get_parameter_value(node, "slab_allocator", 1):
        memory_pool_settings["HOUDINI_SLAB_ALLOCATOR"] = "1"
        memory_pool_settings["HOUDINI_SLAB_SIZE"] = "256"
        memory_pool_settings["HOUDINI_SLAB_CACHE_SIZE"] = str(core_count * 10)

    # Jemalloc tuning
    memory_pool_settings["MALLOC_CONF"] = f"narenas:{core_count},lg_dirty_mult:8,lg_chunk:22"
    memory_pool_settings["MALLOC_ARENA_MAX"] = str(core_count)

    logger.debug(f"    Memory pool settings configured")
    return memory_pool_settings


def get_file_io_performance_settings(node, core_count):
    """Get file I/O settings from parameters"""
    io_settings = {}

    if not get_parameter_value(node, "enable_io_optimization", 1):
        return io_settings

    # File system caching
    if get_parameter_value(node, "buffered_io", 1):
        io_settings["HOUDINI_BUFFERED_IO"] = "1"

    io_settings["HOUDINI_FILE_CACHE_SIZE"] = str(min(4096, core_count * 64))
    io_settings["HOUDINI_SOPNODE_CACHE_SIZE"] = str(min(1000, core_count * 10))

    # Parallel I/O
    if get_parameter_value(node, "parallel_io", 1):
        bgeo_level = get_parameter_value(node, "bgeo_compress_level", 9)
        bgeo_threads = get_parameter_value(node, "bgeo_compress_threads", 8)

        io_settings["HOUDINI_BGEO_COMPRESS_LEVEL"] = str(bgeo_level)
        io_settings["HOUDINI_BGEO_COMPRESS_THREADS"] = str(bgeo_threads)

        if get_parameter_value(node, "geo_parallel_load", 1):
            io_settings["HOUDINI_GEO_PARALLEL_LOAD"] = "1"

    # USD I/O optimization
    io_settings["USD_ENABLE_PARALLEL_WRITE"] = "1"
    io_settings["USD_NUM_THREADS"] = str(core_count)
    io_settings["USDC_USE_PREAD"] = "1"
    io_settings["USDC_ENABLE_MMAP"] = "1"

    # Alembic I/O
    io_settings["ALEMBIC_NUM_THREADS"] = str(core_count)
    io_settings["ALEMBIC_CACHE_SIZE"] = str(min(2048, core_count * 32))

    logger.debug(f"    File I/O settings configured")
    return io_settings


def get_filesystem_optimization_settings(node):
    """Get filesystem optimization settings from parameters"""
    fs_settings = {}

    # Direct I/O
    if get_parameter_value(node, "use_direct_io", 1):
        fs_settings["HOUDINI_USE_DIRECT_IO"] = "1"
        threshold_mb = get_parameter_value(node, "direct_io_threshold", 10)
        fs_settings["HOUDINI_DIRECT_IO_THRESHOLD"] = str(threshold_mb * 1048576)  # Convert to bytes

    # Async I/O
    if get_parameter_value(node, "async_io", 1):
        fs_settings["HOUDINI_ASYNC_IO"] = "1"
        async_threads = get_parameter_value(node, "async_io_threads", 8)
        fs_settings["HOUDINI_ASYNC_IO_THREADS"] = str(async_threads)
        fs_settings["HOUDINI_ASYNC_IO_QUEUE_SIZE"] = "1024"

    # Readahead
    readahead_mb = get_parameter_value(node, "readahead_size", 4)
    fs_settings["HOUDINI_READAHEAD_SIZE"] = str(readahead_mb * 1048576)  # Convert to bytes
    fs_settings["HOUDINI_READAHEAD_WINDOW"] = "16"

    # Write combining
    fs_settings["HOUDINI_WRITE_COMBINE"] = "1"
    fs_settings["HOUDINI_WRITE_COMBINE_SIZE"] = "1048576"

    # tmpfs
    if get_parameter_value(node, "use_tmpfs", 1):
        fs_settings["PDG_USE_TMPFS"] = "1"
        fs_settings["PDG_TMPFS_PATH"] = "/dev/shm/pdg"

    logger.debug(f"    Filesystem optimization settings configured")
    return fs_settings


def get_network_performance_settings(node):
    """Get network settings from parameters"""
    network_settings = {}

    # Network buffer sizes
    socket_buffer_mb = get_parameter_value(node, "socket_buffer_size", 4)
    network_settings["HOUDINI_SOCKET_BUFFER_SIZE"] = str(socket_buffer_mb * 1048576)  # Convert to bytes
    network_settings["HOUDINI_MAX_FILE_HANDLES"] = "4096"

    # Connection pooling
    pool_size = get_parameter_value(node, "connection_pool_size", 32)
    network_settings["HOUDINI_CONNECTION_POOL_SIZE"] = str(pool_size)

    timeout = get_parameter_value(node, "connection_timeout", 120)
    network_settings["HOUDINI_CONNECTION_TIMEOUT"] = str(timeout)

    # HTTP settings
    retries = get_parameter_value(node, "http_retries", 5)
    network_settings["HOUDINI_HTTP_RETRIES"] = str(retries)
    network_settings["HOUDINI_HTTP_TIMEOUT"] = "60"

    logger.debug(f"    Network settings configured")
    return network_settings


def get_gpu_optimization_settings(node, gpu_count, gpu_type):
    """Get GPU settings from parameters"""
    gpu_settings = {}

    if gpu_count == 0 or not get_parameter_value(node, "enable_gpu_optimization", 1):
        return gpu_settings

    # Device selection
    device_selection = get_parameter_value(node, "gpu_device_selection", 0)
    if device_selection == 0:  # Auto
        gpu_devices = ','.join(str(i) for i in range(gpu_count))
    elif device_selection == 1:  # Primary only
        gpu_devices = "0"
    elif device_selection == 2:  # All available
        gpu_devices = ','.join(str(i) for i in range(gpu_count))
    else:  # Manual
        gpu_devices = "0"  # Default to first GPU

    gpu_settings["HOUDINI_OCL_DEVICENUMBER"] = "0"
    gpu_settings["HOUDINI_OCL_VENDOR"] = "NVIDIA Corporation"
    gpu_settings["HOUDINI_USE_GPU_FOR_OPENCL"] = "1"

    # CUDA settings
    gpu_settings["CUDA_VISIBLE_DEVICES"] = gpu_devices
    gpu_settings["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    gpu_settings["CUDA_CACHE_DISABLE"] = "0"

    cuda_cache_gb = get_parameter_value(node, "cuda_cache_size", 2)
    gpu_settings["CUDA_CACHE_MAXSIZE"] = str(cuda_cache_gb * 1073741824)  # Convert to bytes
    gpu_settings["CUDA_LAUNCH_BLOCKING"] = "0"

    # OptiX settings
    gpu_settings["OPTIX_CACHE_PATH"] = "/tmp/optix_cache"
    optix_cache_gb = get_parameter_value(node, "optix_cache_size", 4)
    gpu_settings["OPTIX_CACHE_MAXSIZE"] = str(optix_cache_gb * 1073741824)  # Convert to bytes
    gpu_settings["OPTIX_FORCE_DEPRECATED_LAUNCHER"] = "0"

    # Renderer-specific GPU settings
    gpu_settings["REDSHIFT_GPUDEVICES"] = gpu_devices
    gpu_settings["REDSHIFT_CUDADEVICES"] = gpu_devices
    gpu_settings["OCTANE_GPUDEVICES"] = gpu_devices
    gpu_settings["VRAY_OPENCL_PLATFORMS_x64"] = gpu_devices
    gpu_settings["VRAY_GPU_DEVICE_SELECT"] = gpu_devices

    # GPU memory settings
    memory_limit_override = get_parameter_value(node, "gpu_memory_limit_override", 0)
    if memory_limit_override > 0:
        gpu_settings["REDSHIFT_GPUMAXMEM"] = str(memory_limit_override)
        gpu_settings["ARNOLD_GPU_MAX_MEMORY"] = str(memory_limit_override)
    elif gpu_type:
        if gpu_type == "rtxa6000":
            gpu_settings["REDSHIFT_GPUMAXMEM"] = "45000"
            gpu_settings["ARNOLD_GPU_MAX_MEMORY"] = "45000"
        elif gpu_type == "rtx4000":
            gpu_settings["REDSHIFT_GPUMAXMEM"] = "7500"
            gpu_settings["ARNOLD_GPU_MAX_MEMORY"] = "7500"

    logger.debug(f"    GPU settings configured for {gpu_count} {gpu_type} GPU(s)")
    return gpu_settings


def get_renderer_optimization_settings(node, core_count):
    """Get renderer settings from parameters"""
    renderer_settings = {}

    if not get_parameter_value(node, "enable_renderer_optimization", 1):
        return renderer_settings

    # Thread count override
    thread_override = get_parameter_value(node, "renderer_thread_override", 0)
    if thread_override > 0:
        thread_count_str = str(thread_override)
    else:
        thread_count_str = str(core_count)

    # VEX optimization
    if get_parameter_value(node, "vex_threaded", 1):
        renderer_settings["HOUDINI_VEX_THREADED"] = "1"
        renderer_settings["HOUDINI_VEX_MAXTHREADS"] = thread_count_str

    if get_parameter_value(node, "vex_simd", 1):
        renderer_settings["HOUDINI_VEX_SIMD"] = "1"

    jit_level = get_parameter_value(node, "vex_jit_optimize", 3)
    renderer_settings["HOUDINI_VEX_JIT_OPTIMIZE"] = str(jit_level)

    # Karma settings
    karma_devices = ["CPU GPU", "CPU", "GPU"]
    karma_device = get_parameter_value(node, "karma_xpu_devices", 0)
    renderer_settings["KARMA_XPU_OPTIX_DENOISER"] = "1"
    renderer_settings["KARMA_XPU_DEVICES"] = karma_devices[karma_device]

    bucket_size = get_parameter_value(node, "renderer_bucket_size", 64)
    renderer_settings["KARMA_BUCKET_SIZE"] = str(bucket_size)
    renderer_settings["KARMA_RENDER_THREADS"] = thread_count_str

    # Mantra settings
    mantra_tiles = get_parameter_value(node, "mantra_tiles", 0)
    if mantra_tiles > 0:
        renderer_settings["MANTRA_TILES"] = str(mantra_tiles)
    else:
        renderer_settings["MANTRA_TILES"] = str(max(4, core_count // 4))

    renderer_settings["MANTRA_BUCKET_SIZE"] = str(bucket_size)
    renderer_settings["MANTRA_CACHE_RATIO"] = "0.25"
    renderer_settings["MANTRA_PLANE_CACHE"] = "1"
    renderer_settings["MANTRA_GEOCACHE_SIZE"] = "4096"
    renderer_settings["MANTRA_THREADS"] = thread_count_str
    renderer_settings["MANTRA_NONRAT_THREADS"] = thread_count_str

    # Arnold settings
    renderer_settings["ARNOLD_BUCKET_SIZE"] = str(bucket_size)
    renderer_settings["ARNOLD_BUCKET_SCANNING"] = "spiral"
    arnold_cache = get_parameter_value(node, "arnold_texture_cache", 4096)
    renderer_settings["ARNOLD_TEXTURE_CACHE_SIZE"] = str(arnold_cache)
    renderer_settings["ARNOLD_TEXTURE_MAX_OPEN_FILES"] = "512"
    renderer_settings["ARNOLD_THREADS"] = thread_count_str
    renderer_settings["ARNOLD_THREAD_PRIORITY"] = "normal"
    renderer_settings["ARNOLD_AUTO_THREADS"] = "0"

    # Redshift settings
    renderer_settings["REDSHIFT_LOGCONSOLE"] = "0"
    renderer_settings["REDSHIFT_SKIPLOADINGPLUGINS"] = "0"
    renderer_settings["REDSHIFT_CACHEDIRECTORY"] = "/tmp/redshift_cache"
    renderer_settings["REDSHIFT_LOCALDATACACHEPATH"] = "/tmp/redshift_data"
    renderer_settings["REDSHIFT_TEXTURECACHEDIRECTORY"] = "/tmp/redshift_textures"

    redshift_cache = get_parameter_value(node, "redshift_texture_cache", 8)
    renderer_settings["REDSHIFT_TEXTURECACHEBUDGET"] = str(redshift_cache * 1024)  # Convert to MB
    renderer_settings["REDSHIFT_COREMAXTHREADS"] = thread_count_str

    if get_parameter_value(node, "redshift_prefer_gpus", 1):
        renderer_settings["REDSHIFT_PREFERGPUS"] = "1"

    # V-Ray settings
    vray_cache = get_parameter_value(node, "vray_texture_cache", 4096)
    renderer_settings["VRAY_TEXTURE_CACHE"] = str(vray_cache)
    renderer_settings["VRAY_OPENCL_TEXSIZE"] = "2048"
    renderer_settings["VRAY_DISPLIMIT"] = "2048"
    renderer_settings["VRAY_NUM_THREADS"] = thread_count_str
    renderer_settings["VRAY_USE_THREAD_AFFINITY"] = "1"
    renderer_settings["VRAY_LOW_THREAD_PRIORITY"] = "0"

    # RenderMan settings
    renderer_settings["RMAN_BUCKETORDER"] = "spiral"
    renderer_settings["RMAN_BUCKETSIZE"] = "16"
    renderer_settings["RMAN_CHECKPOINT_INTERVAL"] = "300"
    renderer_settings["PRMAN_NTHREADS"] = thread_count_str
    renderer_settings["RMAN_NTHREADS"] = thread_count_str
    renderer_settings["RMAN_TRACE_MEMORY"] = "0"

    # USD/Hydra threading
    renderer_settings["PXR_WORK_THREAD_LIMIT"] = thread_count_str
    renderer_settings["USD_SCHEDULER_THREADS"] = thread_count_str

    logger.debug(f"    Renderer optimization settings configured")
    return renderer_settings


def get_profiling_and_monitoring_settings(node):
    """Get profiling settings from parameters"""
    profiling_settings = {}

    # Performance monitoring
    if get_parameter_value(node, "enable_conductor_stats", 1):
        profiling_settings["PDG_ENABLE_STATS"] = "1"
        interval = get_parameter_value(node, "stats_interval", 10)
        profiling_settings["PDG_STATS_INTERVAL"] = str(interval)

        if get_parameter_value(node, "stats_verbose", 0):
            profiling_settings["PDG_STATS_VERBOSE"] = "1"
        else:
            profiling_settings["PDG_STATS_VERBOSE"] = "0"

    # Adaptive optimization
    if get_parameter_value(node, "enable_adaptive_optimization", 1):
        profiling_settings["PDG_ADAPTIVE_OPTIMIZATION"] = "1"
        window = get_parameter_value(node, "adaptive_window", 100)
        profiling_settings["PDG_ADAPTIVE_WINDOW"] = str(window)
        threshold = get_parameter_value(node, "adaptive_threshold", 0.1)
        profiling_settings["PDG_ADAPTIVE_THRESHOLD"] = str(threshold)

    # Bottleneck detection
    if get_parameter_value(node, "enable_bottleneck_detection", 1):
        profiling_settings["PDG_DETECT_BOTTLENECKS"] = "1"
        bottleneck_threshold = get_parameter_value(node, "bottleneck_threshold", 0.8)
        profiling_settings["PDG_BOTTLENECK_THRESHOLD"] = str(bottleneck_threshold)

    logger.debug(f"    Profiling and monitoring settings configured")
    return profiling_settings


def configure_threading_environment(node):
    """Main function to configure all environment variables from HDA parameters"""

    job_env = {}
    try:

        # Check if all optimizations are disabled
        if get_parameter_value(node, "disable_all_optimizations", 0):
            logger.debug("All optimizations disabled")
            return {}

        # Check main threading switch
        use_threading = get_parameter_value(node, "use_threading", 1)


        if not use_threading:
            logger.debug("Threading optimizations disabled")
            return job_env

        logger.debug(f"  Enabling maximum performance configuration for render farm")

        # Configure instance and threads (this also updates parameters)
        kwargs = {}
        instance_config = configure_instance_and_threads(node, **kwargs)

        # Extract configuration values
        thread_count = instance_config["thread_count"]
        gpu_count = instance_config["gpu_count"]
        gpu_type = instance_config["gpu_type"]
        use_single_machine = instance_config["use_single_machine"]

        thread_count_str = str(thread_count)

        # Core threading settings
        job_env["HOUDINI_MAXTHREADS"] = thread_count_str
        job_env["HOUDINI_THREADED_COOK"] = "1"

        # Cook mode configuration
        cook_mode_settings = configure_cook_mode_advanced(node, thread_count, use_single_machine)
        job_env.update(cook_mode_settings)

        # PDG performance settings
        pdg_settings = get_pdg_performance_settings(node, thread_count)
        job_env.update(pdg_settings)

        # Single machine optimizations
        if use_single_machine:
            single_machine_settings = get_single_machine_optimization_settings(node, thread_count)
            job_env.update(single_machine_settings)

            # Override PDG settings for single machine
            job_env["PDG_SLOTS"] = str(thread_count)
            job_env["PDG_COOK_MODE"] = "in_process"
            job_env["PDG_SERVICE_MODE"] = "standard"

            logger.debug(f"    Applied single machine optimizations")

        # Parallel cooking settings
        parallel_settings = get_parallel_cooking_settings(node, thread_count)
        job_env.update(parallel_settings)

        # Cache optimization
        cache_settings = get_cache_optimization_settings(node, thread_count)
        job_env.update(cache_settings)

        # Scheduler optimization
        scheduler_settings = get_scheduler_optimization_settings(node, thread_count)
        job_env.update(scheduler_settings)

        # Memory pool optimization
        memory_pool_settings = get_memory_pool_settings(node, thread_count)
        job_env.update(memory_pool_settings)

        # Filesystem optimization
        fs_settings = get_filesystem_optimization_settings(node)
        job_env.update(fs_settings)

        # Profiling and monitoring
        profiling_settings = get_profiling_and_monitoring_settings(node)
        job_env.update(profiling_settings)

        # Memory settings
        memory_settings = get_memory_settings_for_core_count(node, thread_count)
        job_env["HOUDINI_TEXTURE_CACHE_SIZE"] = memory_settings["texture_cache"]
        job_env["HOUDINI_GEOMETRY_CACHE_SIZE"] = memory_settings["geometry_cache"]
        job_env["HOUDINI_VOP_CACHE_SIZE"] = memory_settings["vop_cache"]
        job_env["HOUDINI_FONT_CACHE_SIZE"] = memory_settings["font_cache"]
        job_env["HOUDINI_LDPATH_CACHE_SIZE"] = memory_settings["ldpath_cache"]
        job_env["HOUDINI_AUDIO_CACHE_SIZE"] = memory_settings["audio_cache"]
        job_env["HOUDINI_MAX_MEMORY_USAGE"] = memory_settings["max_memory_usage"]
        job_env["HOUDINI_OCL_MEMORY"] = memory_settings["opencl_memory"]

        # File I/O optimization
        io_settings = get_file_io_performance_settings(node, thread_count)
        job_env.update(io_settings)

        # Network optimization
        network_settings = get_network_performance_settings(node)
        job_env.update(network_settings)

        # GPU optimization
        if gpu_count > 0:
            gpu_settings = get_gpu_optimization_settings(node, gpu_count, gpu_type)
            job_env.update(gpu_settings)

        # Renderer optimization
        renderer_settings = get_renderer_optimization_settings(node, thread_count)
        job_env.update(renderer_settings)

        # OS-level optimizations
        job_env["OMP_NUM_THREADS"] = thread_count_str
        job_env["MKL_NUM_THREADS"] = thread_count_str
        job_env["NUMEXPR_NUM_THREADS"] = thread_count_str
        job_env["TBB_NUM_THREADS"] = thread_count_str
        job_env["OPENBLAS_NUM_THREADS"] = thread_count_str
        job_env["VECLIB_MAXIMUM_THREADS"] = thread_count_str

        # Additional performance flags
        if get_parameter_value(node, "disable_console_output", 1):
            job_env["HOUDINI_DISABLE_CONSOLE"] = "1"

        if get_parameter_value(node, "verbose_errors", 0):
            job_env["HOUDINI_VERBOSE_ERROR"] = "1"
        else:
            job_env["HOUDINI_VERBOSE_ERROR"] = "0"

        job_env["HOUDINI_DISABLE_BACKGROUND_HELP_INDEXING"] = "1"
        job_env["HOUDINI_SPLASH_SCREEN"] = "0"
        job_env["HOUDINI_NO_START_PAGE_SPLASH"] = "1"
        job_env["HOUDINI_ANONYMOUS_STATISTICS"] = "0"
        job_env["HOUDINI_DISABLE_DUPLICATE_POINT_WARNING"] = "1"
        job_env["HOUDINI_DISABLE_SHADER_MENU_REFRESH"] = "1"

        # Python optimization
        python_opt = get_parameter_value(node, "python_optimization", 2)
        job_env["PYTHONDONTWRITEBYTECODE"] = "1"
        job_env["PYTHONUNBUFFERED"] = "1"
        job_env["PYTHONOPTIMIZE"] = str(python_opt)

        # Compiler optimization flags
        compiler_flags = get_parameter_value(node, "compiler_optimization", "-O3 -march=native -mtune=native")
        job_env["HOUDINI_VEX_COMPILER_FLAGS"] = compiler_flags
        job_env["HOUDINI_DSO_COMPILER_FLAGS"] = compiler_flags

        # Custom environment variables
        custom_vars = get_parameter_value(node, "custom_env_vars", "")
        if custom_vars:
            for pair in custom_vars.split(';'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    job_env[key.strip()] = value.strip()

        logger.debug(f"  Complete performance configuration:")
        logger.debug(f"    Instance type: {instance_config['instance_type']}")
        logger.debug(f"    CPU cores/threads: {thread_count}")
        logger.debug(f"    Single machine mode: {use_single_machine}")
        logger.debug(f"    Cook mode: {job_env.get('HOUDINI_COOK_MODE', 'N/A')}")
        logger.debug(f"    PDG slots: {job_env.get('PDG_SLOTS', 'N/A')}")
        logger.debug(f"    GPU count: {gpu_count}")
        logger.debug(f"    GPU type: {gpu_type if gpu_type else 'None'}")
        logger.debug(f"    Total environment variables set: {len(job_env)}")

    except Exception as e:
        logger.warning(f"Error configuring threading environment")

    return job_env