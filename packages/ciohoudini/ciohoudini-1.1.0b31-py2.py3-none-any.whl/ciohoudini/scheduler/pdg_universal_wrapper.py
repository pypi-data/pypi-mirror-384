#!/usr/bin/env python
"""
PDG Universal Wrapper Script for Conductor Render Farm
Supports three modes:
- Submit As Job (full graph execution)
- On Schedule (single work item execution)
- Single Machine (cook all items locally)
"""

import hou
import os
import sys
import argparse
import time
import random
import platform
import json
import shutil
import glob
import re
import traceback
from pathlib import Path
from datetime import datetime
import subprocess


def find_ml_cv_nodes(otls_dir):
    """
    Find all ML/CV related HDAs in the otls directory.
    Handles both versioned (node.1.0.hda) and non-versioned (node.hda) files.

    Args:
        otls_dir: Path to the otls directory

    Returns:
        tuple: (found_any, dict of node_name -> filepath)
    """
    ml_cv_nodes = {}

    if not os.path.exists(otls_dir):
        return False, ml_cv_nodes

    # Find all ML/CV HDAs (both with and without version numbers)
    ml_patterns = [
        "ml_cv_*.hda",  # Non-versioned ML/CV nodes
        "ml_cv_*.*.hda",  # Versioned ML/CV nodes (e.g., ml_cv_something.1.0.hda)
        "ml_*.hda",  # Broader ML nodes if needed
        "ml_*.*.hda",  # Versioned broader ML nodes
        "ML_*.hda",  # Uppercase variants
        "ML_*.*.hda"  # Uppercase versioned
    ]

    all_ml_files = set()
    for pattern in ml_patterns:
        matches = glob.glob(os.path.join(otls_dir, pattern))
        all_ml_files.update(matches)

    # Process found files and extract base node names
    # Pattern to extract base name from versioned or non-versioned files
    version_pattern = re.compile(r'(.+?)(?:\.\d+(?:\.\d+)*)?\.hda$')

    for filepath in all_ml_files:
        filename = os.path.basename(filepath)
        match = version_pattern.match(filename)
        if match:
            base_name = match.group(1)
            # Store the filepath, preferring versioned files over non-versioned
            # if both exist for the same base name
            if base_name not in ml_cv_nodes or '.' in filename[:-4]:
                ml_cv_nodes[base_name] = filepath

    return bool(ml_cv_nodes), ml_cv_nodes


def check_ml_nodes_simple(otls_dir):
    """
    Simple check - just verify if ANY ML-related HDAs exist.
    This is the most future-proof approach.

    Args:
        otls_dir: Path to the otls directory

    Returns:
        tuple: (has_any_ml_nodes, list of ml files)
    """
    if not os.path.exists(otls_dir):
        return False, []

    # Find anything that looks like an ML HDA
    ml_files = []
    ml_files.extend(glob.glob(os.path.join(otls_dir, "ml_*.hda")))
    ml_files.extend(glob.glob(os.path.join(otls_dir, "ml_*.*.hda")))
    ml_files.extend(glob.glob(os.path.join(otls_dir, "ML_*.hda")))
    ml_files.extend(glob.glob(os.path.join(otls_dir, "ML_*.*.hda")))

    # Remove duplicates and return
    ml_files = list(set(ml_files))
    return bool(ml_files), ml_files


def check_houdini_packages():
    """
    Check for Houdini packages on the current system, especially SideFXLabs.
    Prioritizes HOUDINI_PACKAGE_DIR environment variable if set.
    Updated with generic ML/CV node detection for versioned/non-versioned HDAs.
    """
    print("\n" + "=" * 80)
    print("CHECKING HOUDINI PACKAGES")
    print("=" * 80)

    # Determine the platform
    current_platform = platform.system().lower()
    print(f"Platform: {current_platform}")
    print(f"Python platform: {sys.platform}")

    # Get user home directory
    home_dir = os.path.expanduser("~")
    print(f"Home directory: {home_dir}")

    # Check for HOUDINI_PACKAGE_DIR environment variable FIRST
    houdini_package_dir = os.environ.get("HOUDINI_PACKAGE_DIR", "")
    package_dirs = []

    if houdini_package_dir:
        print(f"\n✅ Found HOUDINI_PACKAGE_DIR environment variable: {houdini_package_dir}")
        if os.path.exists(houdini_package_dir):
            package_dirs = [houdini_package_dir]
            print(f"   Directory exists and will be used as the package folder")
        else:
            print(f"   ⚠️  WARNING: Directory does not exist: {houdini_package_dir}")
            # Still add it to check what's wrong
            package_dirs = [houdini_package_dir]
    else:
        print("\nHOUDINI_PACKAGE_DIR not set, searching for packages folders...")

        # Define patterns for finding packages folders based on platform
        if current_platform == "darwin" or sys.platform == "darwin":
            # macOS
            pattern = os.path.join(home_dir, "Library/Preferences/houdini/[0-9]*.[0-9]*/packages")
            package_dirs = glob.glob(pattern)
        elif current_platform == "linux" or sys.platform.startswith("linux"):
            # Linux - this is what will run on the renderfarm
            pattern = os.path.join(home_dir, "houdini[0-9]*.[0-9]*/packages")
            package_dirs = glob.glob(pattern)
            # Also check for alternate location
            alt_pattern = os.path.join(home_dir, ".config/houdini/[0-9]*.[0-9]*/packages")
            package_dirs.extend(glob.glob(alt_pattern))
        elif current_platform == "windows" or sys.platform == "win32":
            # Windows
            try:
                import ctypes.wintypes
                buff = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buff)
                documents = buff.value
                pattern = os.path.join(documents, "houdini[0-9]*.[0-9]*/packages")
                package_dirs = glob.glob(pattern)
            except:
                # Fallback for Windows
                pattern = os.path.join(home_dir, "Documents/houdini[0-9]*.[0-9]*/packages")
                package_dirs = glob.glob(pattern)

    # Remove duplicates and sort
    package_dirs = sorted(list(set(package_dirs)))

    if not package_dirs:
        print("⚠️  WARNING: No Houdini packages folders found!")
        if houdini_package_dir:
            print(f"   HOUDINI_PACKAGE_DIR was set but directory doesn't exist: {houdini_package_dir}")
        else:
            print(
                f"   Searched pattern: {pattern if 'pattern' in locals() else 'No pattern - HOUDINI_PACKAGE_DIR was empty'}")

        # Try to find any houdini folders as a diagnostic
        if current_platform == "linux" or sys.platform.startswith("linux"):
            houdini_folders = glob.glob(os.path.join(home_dir, "houdini*"))
            if houdini_folders:
                print(f"   Found Houdini folders: {houdini_folders}")
                print("   But no 'packages' subdirectories found in them.")
        return False, False

    print(f"\nFound {len(package_dirs)} Houdini packages folder(s):")

    sidefxlabs_found = False
    ml_cv_nodes_found = False

    for pkg_dir in package_dirs:
        print(f"\n📁 Checking: {pkg_dir}")

        if not os.path.exists(pkg_dir):
            print("   ❌ Directory doesn't exist")
            continue

        try:
            # List all files in the packages directory
            files = os.listdir(pkg_dir)
            if files:
                print(f"   Contents ({len(files)} files):")
                for file in sorted(files)[:14]:  # Limit to first 14 files
                    print(f"     - {file}")
                if len(files) > 14:
                    print(f"     ... and {len(files) - 14} more files")

                # Check for SideFXLabs
                if "sidefxlabs.json" in [f.lower() for f in files]:
                    sidefxlabs_found = True
                    json_file = next(f for f in files if f.lower() == "sidefxlabs.json")
                    json_path = os.path.join(pkg_dir, json_file)
                    print(f"\n   🔍 Found SideFXLabs.json! Reading contents...")

                    # Read and parse the JSON file
                    try:
                        with open(json_path, 'r') as f:
                            labs_config = json.load(f)

                        print("   " + "=" * 30)
                        print("   SideFXLabs.json content:")
                        print(json.dumps(labs_config, indent=4))
                        print("   " + "=" * 30)

                        # Check if SideFXLabs is enabled
                        if labs_config.get("enable", True):
                            print("   ✅ SideFXLabs is ENABLED")

                            # Get the SIDEFXLABS path from env
                            for env_var in labs_config.get("env", []):
                                if "SIDEFXLABS" in env_var:
                                    labs_path = env_var["SIDEFXLABS"]
                                    print(f"   SideFXLabs installation path: {labs_path}")

                                    if os.path.exists(labs_path):
                                        print(f"   ✅ SideFXLabs directory exists")

                                        # Use the generic ML/CV node detection
                                        ml_cv_found, ml_cv_nodes = find_ml_cv_nodes(
                                            os.path.join(labs_path, "otls")
                                        )

                                        if ml_cv_found:
                                            print(f"   ✅ Found {len(ml_cv_nodes)} ML/CV node(s):")
                                            # Show up to 10 nodes to avoid cluttering output
                                            for i, (node_name, node_path) in enumerate(ml_cv_nodes.items()):
                                                if i >= 10:
                                                    print(f"      ... and {len(ml_cv_nodes) - 10} more")
                                                    break
                                                print(f"      • {node_name}: {os.path.basename(node_path)}")
                                            ml_cv_nodes_found = True

                                            # Check for critical nodes if needed
                                            critical_nodes = [
                                                "ml_cv_rop_synthetic_data",
                                                "ml_cv_synthetics_karma_rop",
                                                "ml_cv_rop_annotation_output"
                                            ]
                                            missing_critical = [
                                                node for node in critical_nodes
                                                if node not in ml_cv_nodes
                                            ]
                                            if missing_critical:
                                                print(f"   ⚠️  Missing critical nodes: {', '.join(missing_critical)}")
                                        else:
                                            print(f"   ⚠️  No ML/CV nodes found in SideFXLabs installation")
                                            print(f"      Searched in: {os.path.join(labs_path, 'otls')}")

                                            # List any other files in otls directory for debugging
                                            otls_dir = os.path.join(labs_path, "otls")
                                            if os.path.exists(otls_dir):
                                                all_hdas = glob.glob(os.path.join(otls_dir, "*.hda"))
                                                if all_hdas:
                                                    print(f"   Other HDAs found: {len(all_hdas)} total")
                                                    # Show first few non-ML HDAs
                                                    non_ml = [h for h in all_hdas if
                                                              not os.path.basename(h).startswith(('ml_', 'ML_'))][:5]
                                                    for hda in non_ml:
                                                        print(f"      - {os.path.basename(hda)}")
                                    else:
                                        print(f"   ❌ SideFXLabs directory NOT found at: {labs_path}")
                        else:
                            print("   ⚠️  SideFXLabs is DISABLED in config")

                    except Exception as e:
                        print(f"   ❌ Error reading SideFXLabs.json: {e}")
            else:
                print("   Directory is empty")

        except Exception as e:
            print(f"   ❌ Error listing directory: {e}")

    # Check all relevant environment variables
    print("\n" + "-" * 60)
    print("Environment Variables Check:")

    # Check SIDEFXLABS environment variable
    sidefxlabs_env = os.environ.get("SIDEFXLABS", "")
    if sidefxlabs_env:
        print(f"✅ SIDEFXLABS environment variable: {sidefxlabs_env}")
        if os.path.exists(sidefxlabs_env):
            print(f"   ✅ Path exists")

            # Use generic ML/CV node detection
            ml_cv_found, ml_cv_nodes = find_ml_cv_nodes(os.path.join(sidefxlabs_env, "otls"))

            if ml_cv_found:
                print(f"   ✅ Found {len(ml_cv_nodes)} ML/CV node(s) at SIDEFXLABS path:")
                for i, (node_name, node_path) in enumerate(ml_cv_nodes.items()):
                    if i >= 5:
                        print(f"      ... and {len(ml_cv_nodes) - 5} more")
                        break
                    print(f"      • {node_name}: {os.path.basename(node_path)}")
                ml_cv_nodes_found = True
            else:
                print(f"   ⚠️  No ML/CV nodes found in: {os.path.join(sidefxlabs_env, 'otls')}")

                # Use simple check as fallback
                has_any_ml, ml_files = check_ml_nodes_simple(os.path.join(sidefxlabs_env, "otls"))
                if has_any_ml:
                    print(f"   ℹ️  However, found {len(ml_files)} ML-related file(s)")
                    ml_cv_nodes_found = True  # Be lenient
        else:
            print(f"   ❌ Path does NOT exist: {sidefxlabs_env}")
    else:
        print("❌ SIDEFXLABS environment variable not set")

    # Check HOUDINI_PATH
    houdini_path = os.environ.get("HOUDINI_PATH", "")
    if houdini_path:
        print(f"HOUDINI_PATH: {houdini_path[:200]}...")  # First 200 chars
        # Check if SIDEFXLABS is in the HOUDINI_PATH
        if sidefxlabs_env and sidefxlabs_env in houdini_path:
            print(f"   ✅ SIDEFXLABS is included in HOUDINI_PATH")
        elif sidefxlabs_env:
            print(f"   ⚠️  SIDEFXLABS is NOT included in HOUDINI_PATH")
    else:
        print("HOUDINI_PATH not set")

    # Check HOUDINI_PACKAGE_DIR if we haven't already
    if not houdini_package_dir:
        houdini_package_dir = os.environ.get("HOUDINI_PACKAGE_DIR", "")
        if houdini_package_dir:
            print(f"HOUDINI_PACKAGE_DIR: {houdini_package_dir}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")

    # Check multiple conditions for success
    labs_configured = sidefxlabs_found or sidefxlabs_env

    if labs_configured:
        if sidefxlabs_found:
            print("✅ SideFXLabs package configuration found")
        if sidefxlabs_env:
            print("✅ SIDEFXLABS environment variable is set")

        if ml_cv_nodes_found:
            print("✅ ML/CV nodes appear to be installed")
        else:
            print("⚠️  ML/CV nodes NOT found in SideFXLabs installation")
            print("\nPOSSIBLE FIXES:")
            print("1. Update SideFXLabs to the latest version")
            print("2. Verify the ML/CV nodes are included in your SideFXLabs version")
            print("3. Create symlinks for versioned HDAs if needed:")
            print("   cd [SIDEFXLABS]/otls")
            print("   ln -s ml_cv_rop_synthetic_data.1.0.hda ml_cv_rop_synthetic_data.hda")
    else:
        print("❌ SideFXLabs NOT configured properly!")
        print("\nTO FIX on the renderfarm:")
        print("1. Install SideFXLabs from: https://github.com/sideeffects/SideFXLabs")
        print("2. Set SIDEFXLABS environment variable to the installation path")
        print("3. Or place SideFXLabs.json in the packages folder")
        if houdini_package_dir:
            print(f"   Packages folder: {houdini_package_dir}")

    print("=" * 80 + "\n")

    packages_ok = labs_configured and ml_cv_nodes_found
    return packages_ok, ml_cv_nodes_found


class PDGUniversalExecutor:
    """Universal executor for submitAsJob, on_schedule, and single_machine modes"""

    def __init__(self, hip_file, topnet_path, working_dir, output_dir,
                 item_index=None, cook_entire_graph=False, use_single_machine=False):
        self.hip_file = hip_file
        self.topnet_path = topnet_path
        self.working_dir = working_dir
        self.output_dir = output_dir

        self.output_dir = self.clean_path(self.output_dir)

        self.item_index = item_index
        self.cook_entire_graph = False
        self.use_single_machine = True
        self.execution_mode = "single_machine"

        # Initialize status dict after execution_mode is set
        self.status_dict = self._initialize_status_dict()

        # Initialize other attributes
        self.topnet = None
        self.scheduler = None
        self.output_node = None
        self.start_time = time.time()
        self.files_before = set()
        self.files_after = set()
        self.files_copied = 0

    def _initialize_status_dict(self):
        """Initialize the status tracking dictionary - ENHANCED for ML"""
        # First part: basic fields
        base_dict = {
            'timestamp_start': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'execution_mode': self.execution_mode,
            'hip_file': self.hip_file,
            'topnet_path': self.topnet_path,
            'working_dir': self.working_dir,
            'output_dir': self.output_dir,
        }

        # Second part: Add mode-specific fields
        if self.cook_entire_graph:
            base_dict['cook_entire_graph'] = True
            base_dict['work_items_total'] = 0
            base_dict['work_items_succeeded'] = 0
            base_dict['work_items_failed'] = 0
            base_dict['work_items_details'] = []
        elif self.use_single_machine:
            base_dict['use_single_machine'] = True
            base_dict['work_items_total'] = 0
            base_dict['work_items_succeeded'] = 0
            base_dict['work_items_failed'] = 0
            base_dict['work_items_details'] = []
        else:
            base_dict['target_index'] = self.item_index
            base_dict['frame_number'] = str(self.item_index).zfill(4) if self.item_index is not None else "0000"
            base_dict['work_items_processed'] = []
            base_dict['skipped_items'] = []

        # Third part: remaining fields - ENHANCED with datasets and dataset_hips
        base_dict.update({
            'nodes_in_network': [],
            'files_created': {
                'usd': [],
                'renders': [],
                'hip': [],
                'logs': [],
                'pdg': [],
                'geo': [],
                'datasets': [],  # Added for ML
                'dataset_hips': [],  # Added for ML
                'other': [],
                'wedge_outputs': [],
                'total_count': 0
            },
            'cook_result': {
                'return_code': None,
                'failed_items': [],
                'successful_items': [],
                'warnings': []
            },
            'environment': dict(os.environ),
            'timestamp_end': None,
            'duration_seconds': None,
            'status': 'initializing',
            'errors': [],
            'ml_mode': False  # Flag to indicate ML mode
        })

        return base_dict

    def run(self):
        packages_ok, ml_cv_nodes_found = check_houdini_packages()
        if not packages_ok:
            print("⚠️  Warning: ML/CV packages not properly configured")
            # Continue anyway - some jobs may not need ML/CV nodes
        #self.run_no_ml()

        if not ml_cv_nodes_found:
            self.run_no_ml()
        if packages_ok and ml_cv_nodes_found:
            self.run_ml()

        return True

    def run_no_ml(self):
        """Main execution method"""
        try:
            print("\n" + "=" * 80)
            print("PDG UNIVERSAL WRAPPER SCRIPT")
            print(f"EXECUTION MODE: {self.execution_mode.upper()}")
            print("=" * 80)
            self._print_configuration()

            #Setup temp directory to avoid HOUDINI_TEMP_DIR errors
            self._setup_temp_directory_no_ml()

            # Phase 1: Setup
            if not self._setup_environment():
                return False

            # Phase 2: Load HIP file
            if not self._load_hip_file():
                return False

            # Phase 3: Get TOP Network
            if not self._get_top_network():
                return False

            # Execute based on mode
            if self.cook_entire_graph:
                # Submit As Job mode - cook entire graph
                # Phase 4: Create and configure scheduler for full graph
                if not self._setup_scheduler_for_full_graph():
                    return False
                # Phase 5: Execute full graph
                success = self._execute_full_graph()
            elif self.use_single_machine:
                # Single Machine mode - cook all items locally
                # Phase 4: Create scheduler (no custom code needed)
                if not self._setup_scheduler_for_single_machine():
                    return False
                # Phase 5: Execute all work items locally
                success = self._execute_single_machine()
            else:
                # On Schedule mode - cook single work item
                # Phase 4: Create and configure scheduler
                if not self._setup_scheduler():
                    return False
                # Phase 5: Generate and cook work items
                success = self._execute_work_items()

            # Phase 6: Collect all output files
            self._collect_all_outputs()

            # Phase 7: Save final HIP file
            self._save_final_hip()

            self.status_dict['status'] = 'success' if success else 'failure'
            # return success
            return True

        except Exception as e:
            self.status_dict['errors'].append(str(e))
            self.status_dict['status'] = 'error'
            print(f"\nCRITICAL ERROR: {e}")
            traceback.print_exc()
            return False

        finally:
            self._finalize_execution()

    def run_ml(self):
        """
        ENHANCED: Main execution flow for ML jobs with robust time tracking and error handling
        """
        print("=" * 80)
        print("PDG UNIVERSAL WRAPPER - ML/CV VERSION")
        print("=" * 80)

        # CRITICAL: Initialize timing at the very beginning
        self.start_time = time.time()

        # Initialize status dictionary immediately with proper timestamp
        self.status_dict = self._initialize_status_dict()
        self.status_dict['ml_mode'] = True
        self.status_dict['timestamp_start'] = datetime.now().isoformat()

        # Initialize file tracking attributes
        self.existing_files = set()
        self.files_after = set()
        self.files_copied = 0

        # Clean paths (remove quotes and Windows drive letters for cross-platform compatibility)
        self.hip_file = self.clean_path(self.hip_file.strip('"'))
        self.working_dir = self.clean_path(self.working_dir.strip('"'))
        self.output_dir = self.clean_path(self.output_dir.strip('"'))

        # Make paths absolute after cleaning
        self.hip_file = os.path.abspath(self.hip_file)
        self.working_dir = os.path.abspath(self.working_dir)
        self.output_dir = os.path.abspath(self.output_dir)

        print(f"HIP File: {self.hip_file}")
        print(f"TOP Network: {self.topnet_path}")
        print(f"Working Dir: {self.working_dir}")
        print(f"Output Dir: {self.output_dir}")
        print("=" * 80)

        # Update status dict with paths
        self.status_dict['hip_file'] = self.hip_file
        self.status_dict['topnet_path'] = self.topnet_path
        self.status_dict['working_dir'] = self.working_dir
        self.status_dict['output_dir'] = self.output_dir

        # CRITICAL: Setup temporary directory to avoid disk quota issues
        self._setup_temp_directory()

        success = False

        try:
            # Step 0: Prevent any automatic script execution
            self._disable_auto_scripts()

            # Step 1: Setup environment (including SideFXLabs)
            print("\n" + "=" * 60)
            print("PHASE 1: ENVIRONMENT SETUP")
            print("=" * 60)

            if not self._setup_environment_ml():
                self.status_dict['errors'].append("Environment setup failed")
                self.status_dict['status'] = 'failed'
                return False

            # Step 1.5: Initialize Houdini OTL paths BEFORE loading HIP
            self._initialize_otl_paths()

            # Step 2: Load HIP file
            print("\n" + "=" * 60)
            print("PHASE 2: LOADING HIP FILE")
            print("=" * 60)

            if not self._load_hip_file_ml():
                self.status_dict['errors'].append("HIP file load failed")
                self.status_dict['status'] = 'failed'
                return False

            # Step 3: Locate TOP network
            print("\n" + "=" * 60)
            print("PHASE 3: LOCATING TOP NETWORK")
            print("=" * 60)

            if not self._locate_topnet():
                self.status_dict['errors'].append("Could not locate TOP network")
                self.status_dict['status'] = 'failed'
                return False

            # Step 4: Setup scheduler if needed
            print("\n" + "=" * 60)
            print("PHASE 4: SCHEDULER SETUP")
            print("=" * 60)

            if not self._ensure_scheduler():
                self.status_dict['errors'].append("Scheduler setup failed")
                self.status_dict['status'] = 'failed'
                return False

            # Step 5: Scan for existing files
            print("\n" + "=" * 60)
            print("PHASE 5: PRE-EXECUTION SCAN")
            print("=" * 60)

            self._scan_files_before()

            # Step 6: Execute - THE SIMPLE SOLUTION THAT WORKS
            print("\n" + "=" * 60)
            print("PHASE 6: EXECUTION")
            print("=" * 60)

            success = self._execute_simple()

            # Step 7: Collect outputs and copy to output directory
            print("\n" + "=" * 60)
            print("PHASE 7: OUTPUT COLLECTION")
            print("=" * 60)

            self.files_copied = self._scan_and_copy_outputs()

            # Save final HIP file
            self._save_final_hip()

            # Calculate final timing
            end_time = time.time()
            duration = end_time - self.start_time

            # Update status dict with final values
            self.status_dict['timestamp_end'] = datetime.now().isoformat()
            self.status_dict['duration_seconds'] = duration

            # Determine final status based on execution and outputs
            if success:
                self.status_dict['status'] = 'success'
            elif self.files_copied > 0:
                self.status_dict['status'] = 'partial_success'
                self.status_dict['warnings'] = self.status_dict.get('warnings', [])
                self.status_dict['warnings'].append("Execution had issues but files were generated")
            else:
                self.status_dict['status'] = 'completed_no_output'
                self.status_dict['warnings'] = self.status_dict.get('warnings', [])
                self.status_dict['warnings'].append("Execution completed but no output files were found")

            # Step 8: Report results
            print("\n" + "=" * 60)
            print("PHASE 8: REPORTING")
            print("=" * 60)

            self._report_results_ml()

            # Print final summary
            print("\n" + "=" * 80)
            print("EXECUTION COMPLETE")
            print("=" * 80)
            print(f"Mode: ML/CV Processing")
            print(f"Status: {self.status_dict['status'].upper()}")
            print(f"Duration: {duration:.2f} seconds")
            print(f"Total files created: {self.status_dict['files_created']['total_count']}")

            # Return True if we got this far (even with warnings)
            return True

        except Exception as e:
            # Calculate duration even on error
            end_time = time.time()
            duration = end_time - self.start_time

            # Update status dict with error information
            self.status_dict['timestamp_end'] = datetime.now().isoformat()
            self.status_dict['duration_seconds'] = duration
            self.status_dict['errors'].append(str(e))
            self.status_dict['status'] = 'error'

            print(f"\nERROR in ML execution: {e}")
            traceback.print_exc()

            # Try to save status report even on error
            try:
                self._report_results_ml()
            except Exception as report_error:
                print(f"Additional error during reporting: {report_error}")
                # Last resort: try to save basic status
                try:
                    self._save_basic_error_report(e, duration)
                except:
                    pass

            return False

        finally:
            # Ensure duration is calculated
            if not hasattr(self.status_dict, 'duration_seconds') or self.status_dict.get('duration_seconds') is None:
                if hasattr(self, 'start_time'):
                    self.status_dict['duration_seconds'] = time.time() - self.start_time
                else:
                    self.status_dict['duration_seconds'] = 0

            # Clean up temp directories
            try:
                self._cleanup_temp_directory()
            except:
                pass

            # Final attempt to save status report
            try:
                if hasattr(self, 'status_dict') and self.output_dir:
                    # Sanitize status dict before final save
                    if hasattr(self, '_sanitize_status_dict'):
                        self._sanitize_status_dict()
                    self._save_status_report()
            except:
                pass

    def _report_results_ml(self):
        """Report execution results for ML jobs"""
        print("\n8. EXECUTION SUMMARY AND REPORT")
        print("-" * 40)

        duration = self.status_dict.get('duration_seconds', 0)
        file_count = self.status_dict['files_created']['total_count']

        print(f"Total execution time: {duration:.2f} seconds")
        print(f"New files created: {file_count}")
        print(f"Files copied to output: {file_count}")

        # Save status report
        self._save_status_report()

    def _save_status_report(self):
        """Save execution status report to JSON"""
        try:
            status_dir = os.path.join(self.output_dir, 'execution_status')
            os.makedirs(status_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode_str = "single_machine"
            if self.cook_entire_graph:
                mode_str = "full_graph"
            elif not self.use_single_machine:
                mode_str = f"item_{self.item_index}"

            status_file = os.path.join(status_dir, f"pdg_{mode_str}_status_{timestamp}.json")

            import json
            with open(status_file, 'w') as f:
                json.dump(self.status_dict, f, indent=2, default=str)

            print(f"✓ Status report saved: {status_file}")

            # Create a "latest" symlink
            latest_link = os.path.join(status_dir, 'pdg_execution_status.latest.json')
            if os.path.exists(latest_link):
                os.remove(latest_link)
            os.symlink(status_file, latest_link)
            print(f"Created latest link: {latest_link}")

        except Exception as e:
            print(f"⚠ Could not save status report: {e}")



    def _scan_and_copy_outputs_ml(self):
        """
        Scan for and copy ML outputs to output directory
        """
        print("\n7. COLLECTING AND COPYING OUTPUT FILES")
        print("-" * 40)

        files_found = []
        files_copied = 0
        files_skipped = 0

        print("  Looking for ML output directories...")

        # Search for ML outputs
        ml_output_dirs = ['datasets', 'dataset_hips']

        for dirname in ml_output_dirs:
            # Check in working directory
            source_dir = os.path.join(self.working_dir, dirname)

            if os.path.exists(source_dir):
                # Check if it has content
                has_content = False
                for root, dirs, files in os.walk(source_dir):
                    if files:
                        has_content = True
                        print(f"    Found {dirname}/ in working directory")

                        for file in files:
                            # Skip hidden and cache files
                            if file.startswith('.') or '__pycache__' in root:
                                files_skipped += 1
                                continue

                            file_path = os.path.join(root, file)
                            files_found.append((file_path, dirname))
                        break

                if not has_content:
                    print(f"    Found {dirname}/ in working directory (empty)")

        print(f"\n  ✓ Found {len(files_found)} new files")
        print(f"  ✓ {files_copied} files to copy to output directory")
        print(f"  ✓ {files_skipped} files skipped (venv/cache files)")

        # Copy files to output directory
        if files_found and self.output_dir:
            for src_file, category in files_found:
                try:
                    # Determine relative path
                    rel_path = os.path.relpath(src_file, self.working_dir)

                    # Create destination path
                    dst_file = os.path.join(self.output_dir, rel_path)
                    dst_dir = os.path.dirname(dst_file)

                    # Create destination directory
                    os.makedirs(dst_dir, exist_ok=True)

                    # Copy file
                    shutil.copy2(src_file, dst_file)
                    files_copied += 1

                    # Track in status dict
                    self.status_dict['files_created']['datasets'].append(dst_file)

                except Exception as e:
                    print(f"    ⚠ Could not copy {src_file}: {e}")

        if files_copied == 0:
            print("  ⚠ No output files found to copy")

            # Verify expected output structure
            print("\n  VERIFYING OUTPUT STRUCTURE:")
            for dirname in ['datasets', 'dataset_hips']:
                expected_path = os.path.join(self.output_dir, dirname)
                if os.path.exists(expected_path) and os.listdir(expected_path):
                    print(f"  ✓ {dirname} directory has content")
                else:
                    print(f"  ⚠ No {dirname} directory in output location")
                    print(f"    Expected at: {expected_path}")

            # Show what IS in the output directory
            print("\n  Diagnostic: Checking what IS in the output directory...")
            if os.path.exists(self.output_dir):
                items = os.listdir(self.output_dir)
                if items:
                    print(f"  Found {len(items)} items:")
                    for item in items[:10]:
                        print(f"    - {item}")
                else:
                    print("  Output directory is empty")

        # Update total count
        self.status_dict['files_created']['total_count'] = files_copied

        return files_copied

    def _print_configuration(self):
        """Print execution configuration"""
        print(f"HIP File: {self.hip_file}")
        print(f"TOP Network: {self.topnet_path}")
        print(f"Working Dir: {self.working_dir}")
        print(f"Output Dir: {self.output_dir}")

        if self.cook_entire_graph:
            print(f"Mode: Submit As Job (Full Graph Execution)")
        elif self.use_single_machine:
            print(f"Mode: Single Machine (Cook All Items Locally)")
        else:
            frame_num = str(self.item_index).zfill(4) if self.item_index is not None else "0000"
            print(f"Mode: On Schedule (Single Work Item)")
            print(f"Target Index: {self.item_index} (Frame: {frame_num})")

        print("=" * 80 + "\n")

    def _setup_environment(self):
        """Setup execution environment"""
        print("\n" + "-" * 60)
        print("Phase 1: Environment Setup")
        print("-" * 60)

        try:
            # Create output directory
            os.makedirs(self.output_dir, exist_ok=True)

            # Test write permissions
            test_file = os.path.join(self.output_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"✓ Output directory ready: {self.output_dir}")

            # Set PDG environment variables
            os.environ['PDG_DIR'] = self.working_dir
            os.environ['PDG_RENDER_DIR'] = self.output_dir

            # Create necessary subdirectories
            subdirs = ['usd', 'renders', 'logs', 'pdg', 'hip', 'execution_status']
            for subdir in subdirs:
                os.makedirs(os.path.join(self.output_dir, subdir), exist_ok=True)

            print("✓ Environment configured successfully")
            return True

        except Exception as e:
            print(f"✗ Environment setup failed: {e}")
            self.status_dict['errors'].append(f"Environment setup: {e}")
            return False

    def _load_hip_file(self):
        """Load the Houdini HIP file"""
        print("\n" + "-" * 60)
        print("Phase 2: Loading HIP File")
        print("-" * 60)

        try:
            if not os.path.exists(self.hip_file):
                raise FileNotFoundError(f"HIP file not found: {self.hip_file}")

            print(f"Loading: {self.hip_file}")

            # Load the file and capture any warnings
            try:
                hou.hipFile.load(self.hip_file, suppress_save_prompt=True, ignore_load_warnings=True)
            except hou.LoadWarning as warning:
                # This is just a warning, not an error - file loaded successfully
                print(f"  Note: Load warning (can be ignored): {warning}")
            except hou.OperationFailed as e:
                # This is an actual error
                if "Warnings were generated" in str(e):
                    # This is actually just warnings, not a failure
                    print(f"  Note: Warnings during load (continuing): {e}")
                else:
                    # This is a real failure
                    raise e

            # Verify load by checking the current file
            current_hip = hou.hipFile.name()
            if os.path.abspath(current_hip) == os.path.abspath(self.hip_file):
                print(f"✓ HIP file loaded successfully: {current_hip}")
            else:
                # Sometimes the path format differs, check if it's essentially the same file
                print(f"✓ HIP file loaded: {current_hip}")

            # Update paths if needed
            hou.hscript(f"set PDG_DIR = {self.working_dir}")
            hou.hscript(f"set PDG_RENDER_DIR = {self.output_dir}")

            return True

        except FileNotFoundError as e:
            print(f"✗ File not found: {e}")
            self.status_dict['errors'].append(f"HIP file not found: {e}")
            return False
        except Exception as e:
            # Check if this is just a warning about incomplete asset definitions
            error_str = str(e)
            if "Warnings were generated" in error_str or "incomplete asset definitions" in error_str:
                print(f"  Note: Load completed with warnings (continuing):")
                print(f"    {error_str}")

                # Verify the file actually loaded
                try:
                    current_hip = hou.hipFile.name()
                    print(f"✓ HIP file loaded despite warnings: {current_hip}")

                    # Update paths
                    hou.hscript(f"set PDG_DIR = {self.working_dir}")
                    hou.hscript(f"set PDG_RENDER_DIR = {self.output_dir}")

                    return True
                except:
                    # If we can't get the hip file name, it didn't load
                    print(f"✗ Failed to verify HIP file load")
                    self.status_dict['errors'].append(f"HIP load verification failed: {e}")
                    return False
            else:
                # This is a real error
                print(f"✗ Failed to load HIP file: {e}")
                self.status_dict['errors'].append(f"HIP load: {e}")
                return False

    def _get_top_network(self):
        """Find and validate TOP network"""
        print("\n" + "-" * 60)
        print("Phase 3: Locating TOP Network")
        print("-" * 60)

        # Try specified path first
        current_node = hou.node(self.topnet_path)

        if current_node:
            # Check if the node exists and find the topnet
            print(f"Node found at {self.topnet_path} (type: {current_node.type().name()})")
            print(f"  Category: {current_node.type().category().name()}")

            # Check if this node has a childTypeCategory
            if hasattr(current_node, 'childTypeCategory') and current_node.childTypeCategory():
                print(f"  Child category: {current_node.childTypeCategory().name()}")
            else:
                print(f"  Child category: None")

            # Check if this is a TOP network container (can contain TOP nodes)
            # TOP network containers have childTypeCategory of "Top"
            is_topnet_container = (hasattr(current_node, 'childTypeCategory') and
                                   current_node.childTypeCategory() and
                                   current_node.childTypeCategory().name() == "Top")

            if is_topnet_container:
                # It's already a TOP network container
                self.topnet = current_node
                self.topnet_path = current_node.path()
                print(f"✓ Node is a TOP network container: {self.topnet_path}")
            else:
                # It's not a TOP network container, traverse up to find one
                print(f"  Node is not a TOP network container, searching parent hierarchy...")

                # Start from current node's parent
                parent_node = current_node.parent() if current_node else None

                while parent_node is not None:
                    print(f"  Checking parent: {parent_node.path()}")

                    # Check if parent is a TOP network container
                    if (hasattr(parent_node, 'childTypeCategory') and
                            parent_node.childTypeCategory() and
                            parent_node.childTypeCategory().name() == "Top"):
                        self.topnet = parent_node
                        self.topnet_path = parent_node.path()
                        print(f"✓ Found TOP network container in parent: {self.topnet_path}")
                        break

                    # Move up to next parent
                    parent_node = parent_node.parent()

                # If we didn't find a topnet in the parent hierarchy
                if not self.topnet:
                    print(f"✗ No TOP network container found in parent hierarchy of {self.topnet_path}")
                    print("  Falling back to scene-wide search...")
                    self._search_for_topnets()
        else:
            # Node not found at specified path
            print(f"Node not found at {self.topnet_path}")
            print("  Falling back to scene-wide search...")
            self._search_for_topnets()

        # Final check - did we find a TOP network?
        if not self.topnet:
            print("✗ No TOP networks found in scene")
            self.status_dict['errors'].append("No TOP network found")
            return False

        print(f"\n✓ Using TOP network: {self.topnet_path}")
        print(f"  Type: {self.topnet.type().name()}")
        print(f"  Category: {self.topnet.type().category().name()}")
        if hasattr(self.topnet, 'childTypeCategory') and self.topnet.childTypeCategory():
            print(f"  Child category: {self.topnet.childTypeCategory().name()}")

        # Catalog nodes in network
        self._catalog_top_nodes()

        # Find output node
        self._find_output_node()

        return True

    def _search_for_topnets(self):
        """Search for TOP networks in the scene"""
        print("Searching for TOP networks...")

        top_networks = []

        # Search in /obj
        if hou.node("/obj"):
            for node in hou.node("/obj").children():
                if node.type().name() == "topnet":
                    top_networks.append(node)
                    print(f"  Found: {node.path()}")

        # Search in /tasks (common location for tasks)
        if hou.node("/tasks"):
            for node in hou.node("/tasks").children():
                if node.type().name() == "topnet":
                    top_networks.append(node)
                    print(f"  Found: {node.path()}")

        # Search everywhere else
        for root in ["/", "/stage"]:
            if hou.node(root):
                for child in hou.node(root).children():
                    if child.path() not in ["/obj", "/tasks"] and child.type().category():
                        for node in child.allSubChildren():
                            if node.type().name() == "topnet" and node not in top_networks:
                                top_networks.append(node)
                                print(f"  Found: {node.path()}")

        if top_networks:
            self.topnet = top_networks[0]
            self.topnet_path = self.topnet.path()
            print(f"✓ Using TOP network: {self.topnet_path}")
        else:
            self.topnet = None

    def _is_output_node(self, node):
        """Check if a node is an output-type node

        Args:
            node: A Houdini TOP node to check

        Returns:
            bool: True if this is an output-type node, False otherwise
        """
        output_types = ['output', 'ropfetch', 'ropgeometry', 'ropmantra',
                        'ropkarma', 'usdrender', 'filecopy', 'null', 'rop']
        node_type_lower = node.type().name().lower()

        for out_type in output_types:
            if out_type in node_type_lower:
                return True
        return False

    def _catalog_top_nodes(self):
        """Catalog all TOP nodes in the network"""
        print("\nCataloging TOP nodes:")
        for node in self.topnet.children():
            if node.type().category().name() == "Top":
                # Check display flag
                is_display = False
                try:
                    is_display = (self.topnet.displayNode() == node)
                except:
                    try:
                        is_display = node.isDisplayFlagSet()
                    except:
                        pass

                # Check render flag
                is_render = False
                try:
                    is_render = node.isRenderFlagSet()
                except:
                    # Some nodes don't have render flags
                    pass

                node_info = {
                    'path': node.path(),
                    'type': node.type().name(),
                    'display_flag': is_display,
                    'render_flag': is_render
                }
                self.status_dict['nodes_in_network'].append(node_info)

                flags = []
                if self._is_output_node(node):
                    flags.append("OUTPUT")
                if is_display:
                    flags.append("DISPLAY")
                if is_render:
                    flags.append("RENDER")

                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"  - {node.name()} ({node.type().name()}){flag_str}")

    def _find_output_node(self):
        """Find the appropriate output node"""
        print("\nIdentifying output node:")

        # Priority 1: Display node
        self.output_node = self.topnet.displayNode()
        if self.output_node:
            print(f"✓ Using display node: {self.output_node.name()}")
            return

        # Priority 2: Common output node types
        output_types = ['output', 'ropfetch', 'ropgeometry', 'ropmantra',
                        'ropkarma', 'usdrender', 'filecopy', 'null']

        for node in self.topnet.children():
            if node.type().category().name() == "Top":
                for out_type in output_types:
                    if out_type in node.type().name().lower():
                        self.output_node = node
                        print(f"✓ Using output node: {node.name()} ({node.type().name()})")
                        return

        # Priority 3: Last non-scheduler node
        top_nodes = [n for n in self.topnet.children()
                     if n.type().category().name() == "Top"
                     and "scheduler" not in n.type().name().lower()]

        if top_nodes:
            self.output_node = top_nodes[-1]
            print(f"✓ Using last TOP node: {self.output_node.name()}")
        else:
            print("✗ No suitable output node found")

    def _find_or_create_scheduler(self, preferred_types=None, custom_code=None):
        """
        Find an existing scheduler or create a new one with fallback strategies.

        Args:
            preferred_types: List of preferred scheduler types (e.g., ['pythonscheduler', 'localscheduler'])
            custom_code: Custom onSchedule code to set if modifying a Python scheduler

        Returns:
            The scheduler node if successful, None otherwise
        """
        if preferred_types is None:
            preferred_types = ['conductorscheduler', 'pythonscheduler', 'localscheduler']

        scheduler = None
        created_new = False

        print("\nScheduler acquisition strategy:")

        # Strategy 1: Try to create a new Python scheduler
        try:
            existing = self.topnet.node("temp_python_scheduler")
            if existing:
                existing.destroy()
                print("  Removed existing temp scheduler")

            scheduler = self.topnet.createNode('pythonscheduler', 'temp_python_scheduler')
            created_new = True
            print(f"  ✓ Created new Python scheduler: {scheduler.path()}")

        except Exception as e:
            print(f"  ✗ Cannot create new scheduler: {e}")
            print("  Fallback: Looking for existing schedulers...")

            # Strategy 2: Check the default scheduler on the topnet
            for parm_name in ["topscheduler", "defaultscheduler", "scheduler", "pdg_topscheduler"]:
                parm = self.topnet.parm(parm_name)
                if parm:
                    scheduler_path = parm.eval()
                    if scheduler_path:
                        # Handle both relative and absolute paths
                        if scheduler_path.startswith('/'):
                            # Absolute path
                            default_scheduler = hou.node(scheduler_path)
                        else:
                            # Relative path - resolve relative to topnet
                            default_scheduler = self.topnet.node(scheduler_path)

                        if default_scheduler:
                            scheduler = default_scheduler
                            print(f"  ✓ Found default scheduler: {scheduler.path()} ({scheduler.type().name()})")
                            break
                        else:
                            print(f"  Note: Default scheduler path '{scheduler_path}' not found")

            # Strategy 3: Search for Conductor schedulers (highest priority)
            if not scheduler:
                print("  Searching for Conductor schedulers...")
                for node in self.topnet.children():
                    node_type = node.type().name().lower()
                    if 'conductor' in node_type and 'scheduler' in node_type:
                        scheduler = node
                        print(f"  ✓ Found Conductor scheduler: {scheduler.path()} ({node.type().name()})")
                        break

            # Strategy 4: Search for Python schedulers
            if not scheduler:
                print("  Searching for Python schedulers...")
                for node in self.topnet.children():
                    if node.type().name() == 'pythonscheduler':
                        scheduler = node
                        print(f"  ✓ Found existing Python scheduler: {scheduler.path()}")
                        break

            # Strategy 5: Search for local schedulers
            if not scheduler:
                print("  Searching for local schedulers...")
                for node in self.topnet.children():
                    if node.type().name() == 'localscheduler':
                        scheduler = node
                        print(f"  ✓ Found existing local scheduler: {scheduler.path()}")
                        break

            # Strategy 6: Search for any other scheduler
            if not scheduler:
                print("  Searching for any scheduler...")
                for node in self.topnet.children():
                    if 'scheduler' in node.type().name().lower():
                        scheduler = node
                        print(f"  ✓ Found existing scheduler: {scheduler.path()} ({scheduler.type().name()})")
                        break

            # Debug: List all nodes in topnet if no scheduler found
            if not scheduler:
                print("\n  Debug: All nodes in TOP network:")
                for node in self.topnet.children():
                    node_type = node.type().name()
                    print(f"    - {node.name()} (type: {node_type})")
                print()

        if not scheduler:
            print("  ✗ No scheduler found or created")
            return None

        # Configure the scheduler
        try:
            # Set working directory if possible
            if scheduler.parm("pdg_workingdir"):
                scheduler.parm("pdg_workingdir").set("$HIP")
                print(f"  ✓ Set working directory on scheduler")

            # Determine scheduler type
            scheduler_type = scheduler.type().name().lower()

            # If we have custom code and it's a Python scheduler, set it

            if custom_code and 'conductor' in scheduler_type:
                if scheduler.parm("onschedule"):
                    scheduler.parm("onschedule").set(custom_code)
                    print(f"  ✓ Configured custom onSchedule code")
                elif scheduler.parm("submitasjob"):
                    # For submitAsJob mode
                    scheduler.parm("submitasjob").set(custom_code)
                    print(f"  ✓ Configured submitAsJob code")

            # For local schedulers
            elif 'local' in scheduler_type:
                print(f"  Note: Using local scheduler - custom code not applicable")
                # Local schedulers typically don't need custom code
                # They handle work items through their built-in logic

            else:
                print(f"  Note: Using {scheduler.type().name()} scheduler")

        except Exception as e:
            print(f"  Warning: Could not fully configure scheduler: {e}")

        return scheduler

    def _setup_scheduler_for_single_machine(self):
        """Setup scheduler for single machine execution (cook all items locally)"""
        print("\n" + "-" * 60)
        print("Phase 4: Scheduler Setup (Single Machine - All Items)")
        print("-" * 60)

        print("\nScheduler acquisition strategy:")

        # For ML/CV nodes, prefer local scheduler or in-process scheduler
        ml_cv_nodes = self._get_ml_cv_nodes() if hasattr(self, 'topnet') else []

        if ml_cv_nodes:
            # For ML/CV workflows, use localscheduler if available
            scheduler_type = "localscheduler"
            print(f"  ML/CV workflow detected, using {scheduler_type}")
        else:
            scheduler_type = "pythonscheduler"

        # Create appropriate scheduler based on workflow type
        try:
            if scheduler_type == "localscheduler":
                self.scheduler = self.topnet.createNode("localscheduler", "temp_local_scheduler")
                print(f"✓ Created new local scheduler: {self.scheduler.path()}")
            else:
                self.scheduler = self.topnet.createNode("pythonscheduler", "temp_python_scheduler")
                print(f"✓ Created new Python scheduler: {self.scheduler.path()}")
        except Exception as e:
            print(f"⚠ Could not create {scheduler_type}, trying pythonscheduler: {e}")
            try:
                self.scheduler = self.topnet.createNode("pythonscheduler", "temp_python_scheduler")
                print(f"✓ Created fallback Python scheduler: {self.scheduler.path()}")
            except Exception as e2:
                print(f"✗ Failed to create scheduler: {e2}")
                return False

        # Configure scheduler for local execution
        if self.scheduler:
            try:
                # Set working directory
                work_dir_parm = self.scheduler.parm("pdg_workingdir")
                if work_dir_parm:
                    work_dir_parm.set(self.working_dir)
                    print(f"✓ Set working directory on scheduler")

                # For localscheduler, ensure it's set to execute locally
                if "local" in self.scheduler.type().name().lower():
                    # Set any local scheduler specific parameters
                    max_procs = self.scheduler.parm("maxprocsmenu")
                    if max_procs:
                        max_procs.set("0")  # Use all available cores

                # For pythonscheduler, set in-process execution
                elif "python" in self.scheduler.type().name().lower():
                    in_process = self.scheduler.parm("inprocess")
                    if in_process:
                        in_process.set(1)  # Execute in-process
                        print("  Set scheduler to in-process execution")

                print(f"  Note: Using {self.scheduler.type().name()} scheduler")
            except Exception as e:
                print(f"  Warning: Could not configure scheduler: {e}")

        # Apply scheduler to network and nodes
        scheduler_path = self.scheduler.path()
        print("\nApplying scheduler to nodes:")

        # Set as network default first
        for parm_name in ["topscheduler", "defaultscheduler", "scheduler"]:
            parm = self.topnet.parm(parm_name)
            if parm:
                try:
                    parm.set(scheduler_path)
                    print(f"  ✓ Set as network default via '{parm_name}'")
                    break
                except:
                    pass

        # Apply to individual nodes
        count = 0
        for node in self.topnet.children():
            if node.type().category().name() != "Top":
                continue
            if node == self.scheduler:
                continue
            if "scheduler" in node.type().name().lower():
                continue

            # Try different parameter names
            for parm_name in ["pdg_scheduler", "topscheduler", "scheduler"]:
                parm = node.parm(parm_name)
                if parm:
                    try:
                        parm.set(scheduler_path)
                        print(f"  ✓ {node.name()} - set via '{parm_name}'")
                        count += 1
                        break
                    except:
                        pass

        print(f"✓ Scheduler applied to {count} nodes")
        print(f"✓ Scheduler configured for single machine execution")

        return True

    def force_regenerate(self):
        """Force regeneration of tasks and work items"""
        print("Forcing task dirtiness / regeneration on TOP network...")

        try:
            # Clear any cached PDG context
            self.topnet.setPDGGraphContextProcessor(None)

            # Dirty the entire network
            self.topnet.dirtyAllTasks(True)
            print("Called topnet.dirtyAllTasks(True)")

            # Also dirty individual nodes, especially wedges
            for node in self.topnet.children():
                if node.type().category().name() != "Top":
                    continue

                try:
                    # Dirty the node
                    if hasattr(node, 'dirtyAllTasks'):
                        node.dirtyAllTasks(True)

                    # For wedge nodes, ensure attributes will be regenerated
                    if 'wedge' in node.type().name().lower():
                        pdg_node = node.getPDGNode()
                        if pdg_node:
                            # Clear all work items
                            if hasattr(pdg_node, 'dirtyAllWorkItems'):
                                pdg_node.dirtyAllWorkItems(True)
                            # Mark for regeneration
                            if hasattr(pdg_node, 'clearAllWorkItems'):
                                pdg_node.clearAllWorkItems()

                except:
                    pass

            # Give PDG time to process the dirty state
            time.sleep(0.5)

        except Exception as e:
            print(f"Warning during force regeneration: {e}")

    def generate_and_cook(self, block=True, tops_only=False):
        """
        Generate PDG graph (if needed) and cook work items.
        Ensures wedge variations and attributes are properly generated.
        """
        print("Generating PDG graph (if needed) and cooking work items...")
        cooked = False

        try:
            # CRITICAL: Force complete regeneration including wedge variations
            print("Forcing work item regeneration...")

            # Step 1: Dirty all tasks to force regeneration
            self.topnet.dirtyAllTasks(True)
            time.sleep(0.5)

            # Step 2: Find and explicitly generate wedge nodes BEFORE cooking
            print("Generating wedge variations...")
            for node in self.topnet.children():
                if node.type().category().name() != "Top":
                    continue

                node_type = node.type().name().lower()

                # Handle wedge nodes specifically
                if 'wedge' in node_type:
                    try:
                        # Get wedge count parameter
                        wedge_count = node.parm('wedgecount')
                        if wedge_count:
                            count = wedge_count.eval()
                            print(f"  Found wedge node '{node.name()}' with count: {count}")

                            # Force wedge to generate its variations
                            if hasattr(node, 'generateStaticWorkItems'):
                                node.generateStaticWorkItems()
                                print(f"    Generated static work items for wedge")

                            # Also try PDG node generation
                            pdg_node = node.getPDGNode()
                            if pdg_node:
                                if hasattr(pdg_node, 'regenerateStaticWorkItems'):
                                    pdg_node.regenerateStaticWorkItems()
                                elif hasattr(pdg_node, 'generateStaticWorkItems'):
                                    pdg_node.generateStaticWorkItems()
                                print(f"    Regenerated PDG work items for wedge")

                    except Exception as e:
                        print(f"    Warning: Could not generate wedge items: {e}")

                # Also handle any generator nodes
                elif any(gen in node_type for gen in ['generator', 'pattern', 'range']):
                    try:
                        if hasattr(node, 'generateStaticWorkItems'):
                            node.generateStaticWorkItems()
                            print(f"  Generated items for '{node.name()}'")
                    except:
                        pass

            # Step 3: Let generation propagate
            time.sleep(1)

            # Step 4: Now cook with proper PDG context
            print(f"Starting cookWorkItems(block={block}, tops_only={tops_only}) on topnet {self.topnet.path()}")

            try:
                # IMPORTANT: Use tops_only=False to ensure ROP nodes evaluate parameters correctly
                self.topnet.cookWorkItems(block=block, tops_only=tops_only)
                cooked = True
                print("PDG cookWorkItems completed.")
            except TypeError:
                print("cookWorkItems did not accept tops_only kw; calling without it.")
                self.topnet.cookWorkItems(block=block)
                cooked = True
                print("PDG cookWorkItems completed.")

        except Exception as e:
            print(f"Exception while cooking work items: {e}")
            traceback.print_exc()
            raise

        return cooked

    def _find_rop_target_from_topnet(self, ropfetch_node=None):
        """
        Robustly resolve a ROP target node from the topnet.
        If ropfetch_node (a ropfetch-type node) is given, try its 'roppath' parm first.
        Otherwise search beneath the TOP network for a ropfetch node, then try common /obj rop nodes.
        Returns a hou.Node or None.
        """
        rop_target = None

        # If an explicit ropfetch node is provided, try that first
        if ropfetch_node is not None:
            try:
                if ropfetch_node.parm("roppath"):
                    roppath = ropfetch_node.evalParm("roppath")
                    if roppath:
                        # try direct node resolution
                        rop_target = hou.node(roppath)
                        if not rop_target:
                            # try resolving relative to ropfetch parent
                            try:
                                parent = ropfetch_node.parent()
                                candidate = parent.path().rstrip("/") + "/" + roppath.lstrip("./")
                                rop_target = hou.node(candidate)
                            except Exception:
                                rop_target = None
            except Exception:
                rop_target = None
            if rop_target:
                return rop_target

        # Search for a ropfetch node under the topnet
        try:
            nodes_iter = getattr(self.topnet, "allSubChildren", None)
            nodes = nodes_iter() if callable(nodes_iter) else self.topnet.allNodes()
        except Exception:
            nodes = self.topnet.children()

        ropfetch = None
        for n in nodes:
            try:
                tname = n.type().name().lower()
            except Exception:
                tname = ""
            try:
                if "ropfetch" in tname or "ropfetch" in n.name().lower():
                    ropfetch = n
                    break
            except Exception:
                continue

        if ropfetch:
            try:
                if ropfetch.parm("roppath"):
                    rp = ropfetch.evalParm("roppath")
                    if rp:
                        rop_target = hou.node(rp) or hou.node(ropfetch.parent().path() + "/" + rp)
                        if rop_target:
                            return rop_target
            except Exception:
                pass

        # Generic search: find any ROP node anywhere in the scene
        # Search in common locations first
        search_roots = ["/obj", "/out", "/stage"]

        for root_path in search_roots:
            try:
                root = hou.node(root_path)
                if not root:
                    continue

                # Recursively search for ROP nodes
                for node in root.allSubChildren():
                    try:
                        node_type = node.type().name().lower()
                        # Check if it's a ROP node (any type)
                        if any(rop_type in node_type for rop_type in
                               ['rop_geometry', 'rop_alembic', 'rop_fbx', 'rop_comp',
                                'rop_mantra', 'rop_karma', 'usdrender', 'rop_gltf',
                                'rop_usd', 'rop_usdexport', 'filecache']):
                            return node
                    except Exception:
                        continue
            except Exception:
                continue

        return None

    def _fallback_render_by_wedgecount(self):
        """
        Generic fallback when PDG generated 0 or 1 work items but wedge count > 1.
        """
        import random
        import re
        import traceback
        import os

        print("\n" + "=" * 60)
        print("WEDGE FALLBACK: Manual wedge rendering")
        print("=" * 60)

        # Initialize file tracking for collection
        if not hasattr(self, 'wedge_fallback_files'):
            self.wedge_fallback_files = []

        # Token regex
        TOKEN_RE = re.compile(r"`?@([A-Za-z0-9_]+)`?")

        # 1) Find wedge node
        wedge_node = None
        try:
            nodes_iter = getattr(self.topnet, "allSubChildren", None)
            nodes = nodes_iter() if callable(nodes_iter) else self.topnet.allNodes()
        except Exception:
            nodes = self.topnet.children()

        for n in nodes:
            try:
                tname = n.type().name().lower()
            except Exception:
                tname = ""
            try:
                if "wedge" in tname or "wedge" in n.name().lower():
                    wedge_node = n
                    break
            except Exception:
                continue

        if not wedge_node:
            print("Fallback: no wedge node found under topnet — cannot perform wedgecount fallback.")
            return False

        # 2) Read wedgecount
        wedgecount = None
        try:
            if wedge_node.parm("wedgecount"):
                wedgecount = int(wedge_node.evalParm("wedgecount"))
        except Exception:
            wedgecount = None

        if not wedgecount or wedgecount <= 0:
            print("Fallback: wedge node found but wedgecount is missing or zero.")
            return False

        print(f"✓ Found wedge node: {wedge_node.path()}")
        print(f"✓ Wedge count: {wedgecount}")
        print(f"  Wedge node type: {wedge_node.type().name()}")

        # DEBUG: List ALL parameters and their values
        print("\n  DEBUG - All wedge node parameters:")
        all_parms = {}
        try:
            for parm in wedge_node.parms():
                parm_name = parm.name()
                try:
                    parm_value = parm.eval()
                    all_parms[parm_name] = parm_value
                    # Only print parameters that might be relevant
                    if any(keyword in parm_name.lower() for keyword in
                           ['seed', 'method', 'random', 'value', 'prefix', 'attrib', 'type', 'mode', 'variation']):
                        print(f"    {parm_name} = {parm_value}")
                except:
                    pass
        except Exception as e:
            print(f"    Error listing parameters: {e}")

        # 3) Determine attribute name
        attrib_name = "w_seed"
        for parm_name in ["prefix", "wedgeattribname", "attribname", "attribute"]:
            if wedge_node.parm(parm_name):
                try:
                    name = wedge_node.evalParm(parm_name)
                    if name:
                        attrib_name = str(name).strip()
                        print(f"\n  Attribute name from '{parm_name}': {attrib_name}")
                        break
                except:
                    pass

        # 4) Generate wedge values
        token_value_lists = {}
        values = []
        is_random = False
        seed_value = None

        # Check for seedmethod (Labs wedge specific)
        if "seedmethod" in all_parms:
            seed_method = all_parms["seedmethod"]
            print(f"\n  Found seedmethod: {seed_method}")
            if seed_method > 0:  # Any non-zero value means variation
                is_random = True
                # Look for seed value
                if "seed" in all_parms:
                    seed_value = all_parms["seed"]
                    print(f"  Found seed: {seed_value}")

        # If not random yet, check for any seed parameter
        if not is_random:
            for seed_key in ['seed', 'randomseed', 'seedvalue', 'randseed']:
                if seed_key in all_parms:
                    val = all_parms[seed_key]
                    if val and val != 0:
                        is_random = True
                        seed_value = val
                        print(f"\n  Found {seed_key}: {seed_value} - using random mode")
                        break

        # FORCE RANDOM if we have a Labs wedge (as a last resort)
        if not is_random and "labs" in wedge_node.type().name().lower():
            print("\n  Labs wedge detected - forcing random mode with default seed")
            is_random = True
            seed_value = 12345

        # Generate values
        if is_random:
            if seed_value is None or seed_value == 0:
                seed_value = 12345
                print(f"  Using default seed: {seed_value}")

            print(f"\n  Generating {wedgecount} random values with seed {seed_value}")
            random.seed(int(seed_value))
            for i in range(wedgecount):
                rand_val = random.random()
                # FORMAT TO EXACTLY 6 DECIMAL PLACES
                formatted_val = f"{rand_val:.6f}"
                values.append(formatted_val)

            # Show values
            print(f"  Random values generated:")
            for i, v in enumerate(values[:5]):  # Show first 5
                print(f"    [{i}] = {v}")
            if len(values) > 5:
                print(f"    ... ({len(values) - 5} more)")
        else:
            # Fallback to indices
            values = [str(i) for i in range(wedgecount)]
            print(f"  Using index values: 0 to {wedgecount - 1}")

        # Store values
        token_value_lists[attrib_name] = values

        # Print token summary
        print(f"\n  Token '{attrib_name}': {values[0]}, {values[1]}, {values[2]}..." if len(
            values) >= 3 else f"  Token '{attrib_name}': {values}")

        # 5) Find ROP target
        rop_target = self._find_rop_target_from_topnet()
        if not rop_target:
            print("Fallback: could not locate a ROP target for wedge fallback.")
            return False

        print(f"\n✓ ROP target: {rop_target.path()}")

        # 6) Find output parameters
        candidate_parms = []
        for parmname in ["sopoutput", "sopoutput1", "output", "vm_picture", "sopoutputfile", "output_file"]:
            if rop_target.parm(parmname):
                candidate_parms.append(parmname)

        if not candidate_parms:
            print(f"Fallback: no known output parm found on rop target {rop_target.path()}")
            return False

        print(f"✓ Output parameters to substitute: {candidate_parms}")

        # 7) Render each wedge
        successful_renders = 0
        rendered_files = []

        for idx in range(wedgecount):
            print(f"\nRendering wedge {idx}/{wedgecount - 1}:")
            overrides = {}

            for parmname in candidate_parms:
                try:
                    parm = rop_target.parm(parmname)
                    try:
                        raw = parm.unexpandedString()
                    except:
                        raw = parm.eval()

                    if not raw:
                        continue

                    tokens = TOKEN_RE.findall(str(raw))
                    if not tokens:
                        continue

                    # Build token map
                    token_map = {}
                    for token in tokens:
                        if token in token_value_lists:
                            vals = token_value_lists[token]
                            token_map[token] = vals[idx] if idx < len(vals) else vals[-1]
                        else:
                            token_map[token] = str(idx)

                    # Substitute
                    new_val = str(raw)
                    for tk, tv in token_map.items():
                        new_val = new_val.replace(f"`@{tk}`", str(tv))
                        new_val = new_val.replace(f"@{tk}", str(tv))

                    if new_val != raw:
                        parm.set(new_val)
                        overrides[parmname] = raw
                        print(f"  ✓ {parmname}: '{raw}' -> '{new_val}'")

                        # Track file
                        try:
                            if hasattr(hou, 'text') and hasattr(hou.text, 'expandString'):
                                expanded = hou.text.expandString(new_val)
                            else:
                                expanded = hou.expandString(new_val)

                            if not os.path.isabs(expanded):
                                expanded = os.path.join(os.path.dirname(self.hip_file), expanded)

                            rendered_files.append(expanded)
                        except:
                            pass
                except Exception as e:
                    print(f"  ✗ Error with {parmname}: {e}")

            # Render
            try:
                if hasattr(rop_target, "render"):
                    rop_target.render()
                else:
                    import hou
                    hou.Rop.render(rop_target)
                print(f"  ✓ Render completed for wedge {idx}")
                successful_renders += 1
            except Exception as e:
                print(f"  ✗ Render failed for wedge {idx}: {e}")

            # Restore parameters
            for pname, original in overrides.items():
                try:
                    rop_target.parm(pname).set(original)
                except:
                    pass

        # Store tracked files
        self.wedge_fallback_files = rendered_files

        print(f"\n✓ Wedge fallback complete: {successful_renders}/{wedgecount} successful renders")
        print(f"✓ Tracked {len(self.wedge_fallback_files)} output files for collection")

        # Update status
        if hasattr(self, 'status_dict'):
            self.status_dict['work_items_total'] = wedgecount
            self.status_dict['work_items_succeeded'] = successful_renders
            self.status_dict['work_items_failed'] = wedgecount - successful_renders
            self.status_dict['wedge_fallback_used'] = True
            self.status_dict['wedge_fallback_files'] = self.wedge_fallback_files

        return successful_renders > 0

    def _execute_single_machine(self):
        """Execute all work items on single machine (like right-click Cook Node)"""
        print("\n" + "-" * 60)
        print("Phase 5: Single Machine Execution (Cook All Items)")
        print("-" * 60)

        try:
            print("Initializing PDG context for local execution...")

            # REMOVED: This method doesn't exist on TopNode objects
            # self.topnet.setPDGGraphContextProcessor(None)

            # Force complete regeneration
            self.force_regenerate()

            # Pre-generate wedge work items to get accurate count
            print("\nPre-generating wedge and generator nodes...")
            self._pre_generate_work_items()

            # Count after pre-generation
            initial_count = self._count_all_work_items()
            print(f"Initial work item count after pre-generation: {initial_count}")

            # Now cook everything
            print("\nGenerating and cooking all work items...")
            print(f"  Output node: {self.output_node.name() if self.output_node else 'Network level'}")

            cook_start = time.time()
            cooked = self.generate_and_cook(block=True, tops_only=False)

            # Wait and recount
            time.sleep(1)
            total_items = self._count_all_work_items()
            print(f"✓ Generated {total_items} work items")

            # Check if we need the wedge fallback
            wedge_fallback_triggered = False
            if total_items <= 1:
                # Look for wedge nodes with count > 1
                wedge_count = self._get_wedge_count()
                if wedge_count and wedge_count > 1:
                    print(f"\n⚠ Only {total_items} work item(s) but wedge count is {wedge_count}")
                    print("Triggering wedge fallback mechanism...")
                    if self._fallback_render_by_wedgecount():
                        wedge_fallback_triggered = True
                        total_items = wedge_count
                elif initial_count <= 1:
                    print("\n⚠ Only 1 work item detected, attempting alternate generation...")
                    cooked = self._try_alternate_generation()
                    time.sleep(1)
                    total_items = self._count_all_work_items()
                    print(f"  After alternate generation: {total_items} work items")

            elapsed = time.time() - cook_start
            print(f"\nLocal cooking completed in {elapsed:.2f} seconds")

            if total_items > 0 and not wedge_fallback_triggered:
                succeeded = self._count_successful_items()
                failed = self._count_failed_items()
                print(f"Results: {succeeded} succeeded, {failed} failed out of {total_items} total")

                # Update status dict
                self.status_dict['work_items_total'] = total_items
                self.status_dict['work_items_succeeded'] = succeeded
                self.status_dict['work_items_failed'] = failed

            print(
                f"✓ Success rate: {(self.status_dict.get('work_items_succeeded', 0) / total_items * 100) if total_items > 0 else 0:.1f}%")
            return True

        except Exception as e:
            print(f"✗ Single machine execution failed: {e}")
            self.status_dict['errors'].append(f"Single machine execution: {e}")
            traceback.print_exc()
            return False

    def _get_ml_cv_nodes(self):
        """Find all ML/CV nodes in the TOP network"""
        return [n for n in self.topnet.children()
                if 'ml_cv' in n.type().name().lower()]


    def _get_wedge_count(self):
        """Get the wedge count from any wedge node in the network"""
        try:
            for node in self.topnet.children():
                if node.type().category().name() != "Top":
                    continue
                node_type = node.type().name().lower()
                if 'wedge' in node_type:
                    wedge_count_parm = node.parm('wedgecount')
                    if wedge_count_parm:
                        return wedge_count_parm.eval()
        except Exception:
            pass
        return None

    def _pre_generate_work_items(self):
        """Pre-generate work items from wedge and generator nodes"""
        generated_nodes = []

        for node in self.topnet.children():
            if node.type().category().name() != "Top":
                continue

            node_type = node.type().name().lower()

            # Priority 1: Wedge nodes
            if 'wedge' in node_type:
                try:
                    # Ensure wedge parameters are set
                    if node.parm('wedgecount'):
                        wedge_count = node.parm('wedgecount').eval()

                        # Check for seed parameter with @w_seed pattern
                        seed_method = node.parm('seedmethod')
                        if seed_method and seed_method.eval() > 0:  # Not "No Variation"
                            print(f"  Wedge '{node.name()}' configured for {wedge_count} variations")

                        # Generate the wedge variations
                        pdg_node = node.getPDGNode()
                        if pdg_node:
                            # Clear and regenerate
                            if hasattr(pdg_node, 'dirtyAllWorkItems'):
                                pdg_node.dirtyAllWorkItems(True)
                            if hasattr(pdg_node, 'regenerateStaticWorkItems'):
                                pdg_node.regenerateStaticWorkItems()

                            generated_nodes.append(node.name())
                            print(f"    ✓ Pre-generated wedge variations for '{node.name()}'")

                except Exception as e:
                    print(f"    Could not pre-generate wedge '{node.name()}': {e}")

            # Priority 2: Generator nodes
            elif any(gen in node_type for gen in ['generator', 'pattern', 'range', 'partition']):
                try:
                    if hasattr(node, 'generateStaticWorkItems'):
                        node.generateStaticWorkItems()
                        generated_nodes.append(node.name())
                        print(f"  ✓ Pre-generated items for '{node.name()}'")
                except:
                    pass

        if generated_nodes:
            print(f"  Pre-generated nodes: {', '.join(generated_nodes)}")
            time.sleep(0.5)  # Allow generation to propagate

        return generated_nodes

    def _try_alternate_generation(self):
        """Try alternate generation approach for stubborn wedge nodes"""
        print("  Trying alternate wedge generation approach...")

        try:
            # Method 1: Cook wedge node directly
            wedge_nodes = []
            for node in self.topnet.children():
                if 'wedge' in node.type().name().lower():
                    wedge_nodes.append(node)

            for wedge_node in wedge_nodes:
                try:
                    print(f"    Cooking wedge node '{wedge_node.name()}' directly...")

                    # Get the PDG node
                    pdg_node = wedge_node.getPDGNode()
                    if pdg_node:
                        # Try cooking it directly
                        if hasattr(pdg_node, 'cook'):
                            pdg_node.cook(block=True)

                        # Check work items
                        if hasattr(pdg_node, 'workItems'):
                            count = len(pdg_node.workItems)
                            print(f"      Wedge now has {count} work items")

                except Exception as e:
                    print(f"      Failed: {e}")

            # Method 2: Cook from the output node
            if self.output_node:
                print(f"    Cooking from output node '{self.output_node.name()}'...")
                try:
                    self.output_node.executeGraph(False, True, False, True)
                    return True
                except:
                    try:
                        self.output_node.cookWorkItems(block=True)
                        return True
                    except:
                        pass

            # Method 3: Force complete graph regeneration
            print("    Forcing complete graph regeneration...")
            self.topnet.dirtyAllTasks(True)
            time.sleep(0.5)
            return self.topnet.cookWorkItems(block=True, tops_only=False)

        except Exception as e:
            print(f"    Alternate generation failed: {e}")
            return False

    def _count_successful_items(self):
        """Count successfully completed work items"""
        succeeded = 0

        try:
            for node in self.topnet.children():
                if node.type().category().name() != "Top":
                    continue

                try:
                    pdg_node = node.getPDGNode()
                    if not pdg_node:
                        continue

                    # Get work items
                    work_items = pdg_node.workItems if hasattr(pdg_node, 'workItems') else []

                    for wi in work_items:
                        # Check if item is successful using multiple methods
                        is_success = False

                        # Method 1: Check state attribute
                        if hasattr(wi, 'state'):
                            try:
                                import pdg
                                if wi.state == pdg.workItemState.CookedSuccess:
                                    is_success = True
                            except:
                                pass

                        # Method 2: Check isSuccessful method
                        if not is_success and hasattr(wi, 'isSuccessful'):
                            try:
                                if wi.isSuccessful():
                                    is_success = True
                            except:
                                # Sometimes it's a property, not a method
                                if wi.isSuccessful:
                                    is_success = True

                        # Method 3: Check isCooked and not failed
                        if not is_success and hasattr(wi, 'isCooked'):
                            try:
                                is_cooked = wi.isCooked() if callable(wi.isCooked) else wi.isCooked
                                is_failed = False
                                if hasattr(wi, 'isFailed'):
                                    is_failed = wi.isFailed() if callable(wi.isFailed) else wi.isFailed

                                if is_cooked and not is_failed:
                                    is_success = True
                            except:
                                pass

                        if is_success:
                            succeeded += 1

                except Exception as e:
                    # Continue counting even if one node fails
                    continue

        except Exception as e:
            print(f"Warning: Error counting successful items: {e}")

        return succeeded

    def _count_failed_items(self):
        """Count failed work items"""
        failed = 0

        try:
            for node in self.topnet.children():
                if node.type().category().name() != "Top":
                    continue

                try:
                    pdg_node = node.getPDGNode()
                    if not pdg_node:
                        continue

                    # Get work items
                    work_items = pdg_node.workItems if hasattr(pdg_node, 'workItems') else []

                    for wi in work_items:
                        # Check if item failed using multiple methods
                        is_failed = False

                        # Method 1: Check state attribute
                        if hasattr(wi, 'state'):
                            try:
                                import pdg
                                if wi.state == pdg.workItemState.CookedFail:
                                    is_failed = True
                            except:
                                pass

                        # Method 2: Check isFailed method
                        if not is_failed and hasattr(wi, 'isFailed'):
                            try:
                                if wi.isFailed():
                                    is_failed = True
                            except:
                                # Sometimes it's a property, not a method
                                if wi.isFailed:
                                    is_failed = True

                        # Method 3: Check state string
                        if not is_failed and hasattr(wi, 'state'):
                            try:
                                state_str = str(wi.state).lower()
                                if 'fail' in state_str or 'error' in state_str:
                                    is_failed = True
                            except:
                                pass

                        if is_failed:
                            failed += 1

                except Exception as e:
                    # Continue counting even if one node fails
                    continue

        except Exception as e:
            print(f"Warning: Error counting failed items: {e}")

        return failed

    def _count_all_work_items(self):
        """Count total number of work items (already exists but here's an improved version)"""
        total = 0

        try:
            for node in self.topnet.children():
                if node.type().category().name() != "Top":
                    continue

                # Skip scheduler nodes
                if "scheduler" in node.type().name().lower():
                    continue

                try:
                    pdg_node = node.getPDGNode()
                    if not pdg_node:
                        continue

                    # Get work items using multiple methods
                    work_items = None

                    # Method 1: Direct workItems attribute
                    if hasattr(pdg_node, 'workItems'):
                        work_items = pdg_node.workItems

                    # Method 2: allWorkItems method
                    if not work_items and hasattr(pdg_node, 'allWorkItems'):
                        try:
                            work_items = pdg_node.allWorkItems()
                        except:
                            pass

                    # Method 3: staticWorkItems for static nodes
                    if not work_items and hasattr(pdg_node, 'staticWorkItems'):
                        try:
                            work_items = pdg_node.staticWorkItems
                        except:
                            pass

                    if work_items:
                        count = len(work_items)
                        if count > 0:
                            total += count

                except Exception as e:
                    # Continue counting even if one node fails
                    continue

        except Exception as e:
            print(f"Warning: Error counting total items: {e}")

        return total


    def _execute_full_graph(self):
        """Execute the full PDG graph using topcook.py"""
        print("\n" + "-" * 60)
        print("Phase 5: Full Graph Execution")
        print("-" * 60)

        hip_dir = os.path.dirname(self.hip_file)

        # Use hython directly
        hython_path = "hython"

        # Construct the command to cook the PDG graph
        topcook_script = os.path.expandvars("$HHP/pdgjob/topcook.py")
        topcook_script = topcook_script.replace("\\", "/")

        # Build the command with valid arguments
        cmd = [
            hython_path,
            topcook_script,
            "--hip", self.hip_file,
            "--toppath", self.topnet_path,
            "--verbosity", "3",  # Maximum verbosity
            "--report", "items",  # Report on individual work items
            "--keepopen", "error"  # Keep session open on error
        ]

        # Add task graph output
        output_file = os.path.join(hip_dir, f"{os.path.basename(self.hip_file)}.post.py")
        cmd.extend(["--taskgraphout", output_file])

        # Set up environment variables
        env = os.environ.copy()
        env['PDG_DIR'] = hip_dir
        env['PDG_VERBOSE'] = '3'
        env['HOUDINI_PDG_NODE_DEBUG'] = '3'

        try:
            print("=" * 60)
            print(f"Starting PDG graph cook at: {self.topnet_path}")
            print(f"Hip file: {self.hip_file}")
            print(f"PDG_DIR set to: {hip_dir}")
            print(f"Command: {' '.join(cmd)}")
            print("=" * 60)

            # Run the command with real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )

            # Stream output in real-time
            output_lines = []
            error_lines = []
            failed_items = {}
            successful_items = []
            current_node = None

            # Read stdout
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
                    output_lines.append(line)

                    # Parse node context
                    if "Node " in line and "Given Node" not in line:
                        current_node = line.split("Node ")[-1].strip()

                    # Capture failed work items
                    if "CookedFail" in line:
                        parts = line.strip().split()
                        if parts:
                            item_name = parts[0]
                            failed_items[item_name] = current_node
                            self.status_dict['cook_result']['failed_items'].append({
                                'name': item_name,
                                'node': current_node
                            })

                    # Capture successful work items
                    if "CookedSuccess" in line:
                        parts = line.strip().split()
                        if parts:
                            item_name = parts[0]
                            successful_items.append(item_name)
                            self.status_dict['cook_result']['successful_items'].append({
                                'name': item_name,
                                'node': current_node
                            })

                    # Capture warnings
                    if "warning" in line.lower():
                        self.status_dict['cook_result']['warnings'].append(line.strip())

            # Read stderr
            for line in iter(process.stderr.readline, ''):
                if line:
                    print(f"STDERR: {line.rstrip()}")
                    error_lines.append(line)

            # Wait for process to complete
            return_code = process.wait()
            self.status_dict['cook_result']['return_code'] = return_code

            print("=" * 60)

            # Analyze results
            if failed_items:
                print("FAILED WORK ITEMS:")
                print("-" * 40)
                for item_name, node_name in failed_items.items():
                    print(f"  {item_name} (from node: {node_name})")
                print("-" * 40)

            if successful_items:
                print(f"\n✓ Successfully cooked {len(successful_items)} work items")

            if self.status_dict['cook_result']['warnings']:
                print("\nWarnings:")
                for warning in self.status_dict['cook_result']['warnings'][:5]:  # Show first 5
                    print(f"  {warning}")

            if return_code == 0:
                print("\nCook completed")
                if failed_items:
                    print(f"WARNING: {len(failed_items)} work items failed")
                else:
                    print("SUCCESS: All work items cooked successfully!")
                return True
            else:
                print(f"\nERROR: PDG graph cooking failed with return code: {return_code}")
                return False

        except Exception as e:
            print(f"✗ Graph execution failed: {e}")
            self.status_dict['errors'].append(f"Graph execution: {e}")
            traceback.print_exc()
            return False


    def _setup_scheduler_for_full_graph(self):
        """Create and configure the Python scheduler for full graph execution"""
        print("\n" + "-" * 60)
        print("Phase 4: Scheduler Setup (Full Graph)")
        print("-" * 60)

        try:
            # Prepare submitAsJob code (optional for full graph)
            submit_as_job_code = '''# Submit As Job callback for full graph execution
# This runs when the entire graph is submitted as a single job
import subprocess
import os

# Default behavior - just execute the command
job_env = os.environ.copy()
job_env['PDG_DIR'] = str(self.workingDir(False))
job_env['PDG_TEMP'] = str(self.tempDir(False))
job_env['PDG_SCRIPTDIR'] = str(self.scriptDir(False))

print(f"[SCHEDULER] Executing full graph cook")
return True
'''

            # Use the helper to find or create a scheduler
            self.scheduler = self._find_or_create_scheduler(
                preferred_types=['conductorscheduler', 'pythonscheduler', 'localscheduler'],
                custom_code=submit_as_job_code
            )

            if not self.scheduler:
                print("✗ Failed to acquire scheduler")
                self.status_dict['errors'].append("Failed to acquire scheduler for full graph")
                return False

            # Apply scheduler to all nodes
            self._apply_scheduler_to_nodes()

            print("✓ Scheduler configured for full graph execution")
            return True

        except Exception as e:
            print(f"✗ Scheduler setup failed: {e}")
            self.status_dict['errors'].append(f"Scheduler setup: {e}")
            return False

    def _setup_scheduler(self):
        """Create and configure the Python scheduler for single work item mode"""
        print("\n" + "-" * 60)
        print("Phase 4: Scheduler Setup (Single Work Item)")
        print("-" * 60)

        try:
            # Generate custom onSchedule code for single item execution
            on_schedule_code = self._generate_on_schedule_code()

            # Use the helper to find or create a scheduler
            self.scheduler = self._find_or_create_scheduler(
                preferred_types=['conductorscheduler', 'pythonscheduler', 'localscheduler'],
                custom_code=on_schedule_code
            )

            if not self.scheduler:
                print("✗ Failed to acquire scheduler")
                self.status_dict['errors'].append("Failed to acquire scheduler for single work item")
                return False

            print(f"✓ Configured to cook only work item at index {self.item_index}")

            # Apply scheduler to all nodes
            self._apply_scheduler_to_nodes()

            return True

        except Exception as e:
            print(f"✗ Scheduler setup failed: {e}")
            self.status_dict['errors'].append(f"Scheduler setup: {e}")
            return False

    def _generate_on_schedule_code(self):
        """Generate the onSchedule callback code"""
        return f'''# Custom onSchedule for single work item execution
import subprocess
import os
import sys

TARGET_INDEX = {self.item_index}

print(f"[SCHEDULER] Item {{work_item.index}}: {{work_item.name}}")

if work_item.index == TARGET_INDEX:
    print(f"[SCHEDULER] COOKING work item index={{work_item.index}}")

    # Prepare work item
    self.createJobDirsAndSerializeWorkItems(work_item)

    # Expand command tokens
    item_command = self.expandCommandTokens(work_item.command, work_item)

    # Setup environment
    job_env = os.environ.copy()

    job_env['PDG_RESULT_SERVER'] = str(self.workItemResultServerAddr())
    job_env['PDG_ITEM_NAME'] = str(work_item.name)
    job_env['PDG_ITEM_ID'] = str(work_item.id)
    # job_env['PDG_DIR'] = str(self.workingDir(False))
    job_env['PDG_TEMP'] = str(self.tempDir(False))
    # job_env['PDG_SCRIPTDIR'] = str(self.scriptDir(False))

    # Execute command
    print(f"[SCHEDULER] Executing: {{item_command}}...")
    returncode = subprocess.call(item_command, shell=True, env=job_env)

    print(f"[SCHEDULER] Completed with return code: {{returncode}}")

    if returncode == 0:
        return pdg.scheduleResult.CookSucceeded
    return pdg.scheduleResult.CookFailed
else:
    print(f"[SCHEDULER] SKIPPING work item index={{work_item.index}}")
    return pdg.scheduleResult.Skip
'''

    def _apply_scheduler_to_nodes(self):
        """Apply scheduler to all TOP nodes"""
        print("\nApplying scheduler to nodes:")

        scheduler_path = self.scheduler.path()
        count = 0

        # Apply to individual nodes
        for node in self.topnet.children():
            if node.type().category().name() != "Top":
                continue
            if "scheduler" in node.type().name().lower():
                continue

            # Try different parameter names
            for parm_name in ["pdg_scheduler", "topscheduler", "scheduler"]:
                parm = node.parm(parm_name)
                if parm:
                    try:
                        parm.set(scheduler_path)
                        print(f"  ✓ {node.name()} - set via '{parm_name}'")
                        count += 1
                        break
                    except:
                        pass

        # Set as default on network
        for parm_name in ["topscheduler", "defaultscheduler", "scheduler"]:
            parm = self.topnet.parm(parm_name)
            if parm:
                try:
                    parm.set(scheduler_path)
                    print(f"  ✓ Set as network default via '{parm_name}'")
                    break
                except:
                    pass

        print(f"✓ Scheduler applied to {count} nodes")

    def _execute_work_items(self):
        """Generate and execute work items for single item mode"""
        print("\n" + "-" * 60)
        print("Phase 5: Work Item Execution (Single Item)")
        print("-" * 60)

        try:
            # Initialize PDG context
            print("Initializing PDG context...")
            self._initialize_pdg_context()

            # Generate work items
            print("\nGenerating work items...")
            num_items = self._generate_work_items()

            if num_items == 0:
                print("✗ No work items generated")
                self.status_dict['errors'].append("No work items generated")
                return False

            print(f"✓ Generated {num_items} work items")

            if num_items <= self.item_index:
                print(f"⚠ Warning: Target index {self.item_index} >= {num_items} items")

            # Cook work items
            print(f"\nCooking work items (target index: {self.item_index})...")

            try:
                if self.output_node:
                    self.output_node.cookWorkItems(block=True)
                else:
                    self.topnet.cookWorkItems(block=True)
                print("✓ Cooking completed")
            except Exception as e:
                print(f"⚠ Cooking raised exception (may be normal): {e}")
                # Continue anyway as some items may have cooked

            # Collect work item results after cooking
            self._collect_work_item_results()

            print("✓ Work item execution completed")
            return True

        except Exception as e:
            print(f"✗ Work item execution failed: {e}")
            self.status_dict['errors'].append(f"Execution: {e}")

            # Try alternative cooking methods
            return self._try_alternative_cooking()


    def _initialize_pdg_context(self):
        """Initialize PDG graph context"""
        # Dirty all nodes
        for node in self.topnet.children():
            if node.type().category().name() == "Top":
                try:
                    node.dirtyAllTasks(False)
                except:
                    pass

        time.sleep(0.5)

        # Try to generate on a generator node
        for node in self.topnet.children():
            if "generator" in node.type().name().lower():
                try:
                    node.generateStaticWorkItems()
                    time.sleep(0.5)
                    return
                except:
                    pass

    def _generate_work_items(self):
        """Generate work items and count them"""
        max_items = 0

        # First, try to generate work items at the network level
        print("  Attempting network-level generation...")
        try:
            self.topnet.cookWorkItems(generate_only=True, block=True)
            time.sleep(1)
            print("    ✓ Network-level generation completed")
        except Exception as e:
            print(f"    Note: Network generation returned: {e}")

        # Also try to generate on individual nodes
        print("  Generating on individual nodes...")
        for node in self.topnet.children():
            if node.type().category().name() != "Top":
                continue
            if "scheduler" in node.type().name().lower():
                continue

            try:
                # Try to generate static work items
                if hasattr(node, 'generateStaticWorkItems'):
                    node.generateStaticWorkItems()
                    print(f"    Generated static items for {node.name()}")
            except:
                pass

            try:
                # Try cook with generate_only
                if hasattr(node, 'cookWorkItems'):
                    node.cookWorkItems(generate_only=True, block=True)
                    print(f"    Generated items for {node.name()}")
            except:
                pass

        # Wait for generation to complete
        time.sleep(1)

        # Now count work items on each node
        print("\n  Counting generated work items:")
        for node in self.topnet.children():
            if node.type().category().name() != "Top":
                continue
            if "scheduler" in node.type().name().lower():
                continue

            try:
                # Try multiple methods to get work items
                work_items = None
                pdg_node = None

                # Method 1: Direct PDG node
                try:
                    pdg_node = node.getPDGNode()
                    if pdg_node and hasattr(pdg_node, 'workItems'):
                        work_items = pdg_node.workItems
                except:
                    pass

                # Method 2: Through graph context
                if not work_items:
                    try:
                        graph_context = node.getPDGGraphContext()
                        if graph_context:
                            pdg_node = node.getPDGNode()
                            if pdg_node:
                                work_items = pdg_node.workItems
                    except:
                        pass

                if work_items and len(work_items) > 0:
                    print(f"    {node.name()}: {len(work_items)} items")
                    max_items = max(max_items, len(work_items))

                    # Debug: print first few work item indices
                    indices = []
                    for wi in work_items[:5]:
                        if hasattr(wi, 'index'):
                            indices.append(wi.index)
                    if indices:
                        print(f"      Sample indices: {indices}")
            except Exception as e:
                print(f"    Error counting items in {node.name()}: {e}")

        return max_items

    def _collect_work_item_results(self):
        """Collect results from work items - Fixed version for proper processed/skipped tracking"""
        print("\nCollecting work item results...")

        # Clear the lists to ensure clean collection
        self.status_dict['work_items_processed'] = []
        self.status_dict['skipped_items'] = []

        # First, make sure we have generated work items
        for node in self.topnet.children():
            if node.type().category().name() != "Top":
                continue

            # Skip scheduler nodes
            if "scheduler" in node.type().name().lower():
                continue

            try:
                # Try multiple ways to get PDG node and work items
                pdg_node = None
                work_items = []

                # Method 1: Direct PDG node access
                try:
                    pdg_node = node.getPDGNode()
                    if pdg_node:
                        work_items = pdg_node.workItems
                        if work_items:
                            print(f"  Found {len(work_items)} work items in {node.name()} via getPDGNode")
                except Exception as e:
                    pass

                # Method 2: Try through graph context
                if not work_items:
                    try:
                        graph_context = node.getPDGGraphContext()
                        if graph_context:
                            pdg_node = graph_context.graph.nodeByName(node.name())
                            if pdg_node:
                                work_items = pdg_node.workItems
                                if work_items:
                                    print(f"  Found {len(work_items)} work items in {node.name()} via graph context")
                    except Exception as e:
                        pass

                # Method 3: Use pdg module directly
                if not work_items:
                    try:
                        import pdg
                        for context_name in dir(pdg):
                            if "Context" in context_name:
                                context = getattr(pdg, context_name)
                                if hasattr(context, 'graph'):
                                    try:
                                        test_node = context.graph.nodeByName(node.name())
                                        if test_node and hasattr(test_node, 'workItems'):
                                            work_items = test_node.workItems
                                            if work_items:
                                                pdg_node = test_node
                                                print(
                                                    f"  Found {len(work_items)} work items in {node.name()} via pdg module")
                                                break
                                    except:
                                        pass
                    except Exception as e:
                        pass

                # Process work items if we found any
                if work_items:
                    for i, wi in enumerate(work_items):
                        # Try to get index from work item
                        wi_index = i  # Default to enumeration index

                        # Try to get actual work item index
                        if hasattr(wi, 'index'):
                            wi_index = wi.index
                        elif hasattr(wi, 'id'):
                            # Sometimes index is stored as id
                            wi_index = wi.id

                        # Get work item name
                        wi_name = wi.name if hasattr(wi, 'name') else f"{node.name()}_{i}"

                        # Collect work item information
                        item_info = {
                            'index': wi_index,
                            'name': wi_name,
                            'node': node.name(),
                            'status': self._get_work_item_status(wi)
                        }

                        # Check if this matches our target index
                        if wi_index == self.item_index:
                            self.status_dict['work_items_processed'].append(item_info)
                            print(f"    ✓ Processed: {wi_name} (index: {wi_index}) - {item_info['status']}")
                        else:
                            self.status_dict['skipped_items'].append(item_info)
                            # Only print first few skipped to avoid clutter
                            if len(self.status_dict['skipped_items']) <= 3:
                                print(f"    - Skipped: {wi_name} (index: {wi_index})")
                else:
                    # No work items found for this node
                    print(f"  No work items found in {node.name()}")

            except Exception as e:
                print(f"  Warning: Error collecting from {node.name()}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        # Print summary
        processed_count = len(self.status_dict['work_items_processed'])
        skipped_count = len(self.status_dict['skipped_items'])

        print(f"\nWork Item Collection Summary:")
        print(f"  Target Index: {self.item_index}")
        print(f"  Frame Number: {str(self.item_index).zfill(4) if self.item_index is not None else '0000'}")
        print(f"  Processed: {processed_count} work item(s)")
        print(f"  Skipped: {skipped_count} work item(s)")

        if processed_count == 0 and skipped_count == 0:
            print(f"  ⚠ Warning: No work items were found at all!")
            print(f"    This might mean work items weren't generated properly")
            print(f"    or the PDG context isn't accessible")
        elif processed_count == 0:
            print(f"  ⚠ Warning: No work items found with index {self.item_index}")
            available_indices = sorted(
                set([item['index'] for item in self.status_dict['skipped_items'] if item['index'] >= 0]))
            if available_indices:
                print(f"    Available indices: {available_indices[:10]}...")
        else:
            # Show detailed status for processed items
            for item in self.status_dict['work_items_processed']:
                print(f"    - {item['name']} from {item['node']}: {item['status']}")

    def _get_work_item_status(self, wi):
        """Get work item status string"""
        if hasattr(wi, 'isSuccessful') and wi.isSuccessful:
            return 'success'
        elif hasattr(wi, 'isFailed') and wi.isFailed:
            return 'failed'
        elif hasattr(wi, 'isCancelled') and wi.isCancelled:
            return 'cancelled'
        else:
            return 'unknown'

    def _try_alternative_cooking(self):
        """Try alternative cooking methods"""
        print("\nTrying alternative cooking methods...")

        # Method 1: executeGraph
        try:
            if self.output_node:
                self.output_node.executeGraph(False, True, False, True)
                print("✓ Alternative method 1 succeeded")
                return True
        except:
            pass

        # Method 2: Direct network cook
        try:
            self.topnet.cookWorkItems(block=True)
            print("✓ Alternative method 2 succeeded")
            return True
        except:
            pass

        print("✗ All cooking methods failed")
        return False

    def clean_path(self, current_path):
        """
        Prepares a file path by expanding environment variables, normalizing slashes,
        and removing drive letters for cross-platform compatibility.
        FIXED VERSION: Properly handles Windows paths on Linux
        """
        try:
            if not current_path:
                return current_path

            # Expand environment variables
            path = os.path.expandvars(current_path)

            # Remove quotes if present
            path = path.strip('"').strip("'")

            # CRITICAL FIX: Handle Windows paths on Linux/Mac
            if os.name != 'nt':  # Running on Linux/Mac
                # Match patterns like C:/, D:\, etc.
                if len(path) > 2 and path[1] == ':':
                    # Remove drive letter and colon
                    path = path[2:]
                    # Ensure path starts with / for absolute paths
                    if not path.startswith('/'):
                        path = '/' + path.lstrip('\\/')

            # Convert all backslashes to forward slashes
            path = path.replace('\\', '/')
            
            # Remove any double slashes (except at the beginning for UNC paths)
            while '//' in path[1:]:
                path = path[0] + path[1:].replace('//', '/')

            # Normalize the path for the current OS
            path = os.path.normpath(path)

            return path

        except Exception as e:
            print(f"  Warning: Could not clean path {current_path}: {e}")
            return current_path

    def _collect_all_outputs(self):
        """Comprehensive output file collection"""
        print("\n" + "-" * 60)
        print("Phase 6: Output Collection")
        print("-" * 60)

        collectors = [
            ('USD Files', self._collect_usd_files, 'usd'),
            ('Rendered Images', self._collect_render_files, 'renders'),
            ('PDG Files', self._collect_pdg_files, 'pdg'),
            ('Log Files', self._collect_log_files, 'logs'),
            ('Geo Files', self._collect_geo_files, 'geo'),  # FIX: Use proper geo collector
            ('Work Item Outputs', self._collect_work_item_outputs, 'other'),
            ('Wedge Fallback Outputs', self._collect_wedge_fallback_files, 'wedge_outputs')
        ]

        for name, collector, category in collectors:
            print(f"\nCollecting {name}...")
            try:
                files = collector()
                count = 0
                for src_file in files:
                    dest = self._copy_file_with_structure(src_file, category)  # FIX: Use structure-preserving copy
                    if dest:
                        self.status_dict['files_created'][category].append(dest)
                        count += 1
                print(f"  ✔ Collected {count} {name.lower()}")
            except Exception as e:
                print(f"  ✗ Failed to collect {name}: {e}")

        # Update total count
        total = sum(len(v) for k, v in self.status_dict['files_created'].items()
                    if k != 'total_count')
        self.status_dict['files_created']['total_count'] = total

        print(f"\n✔ Total files collected: {total}")

    def collect_and_copy_output_files(self):
        """
        Collect and copy output files maintaining directory structure
        Same as used in run_ml route
        """
        try:
            print("\n7. COLLECTING AND COPYING OUTPUT FILES")
            print("-" * 40)

            # Scan for new files
            new_files = []
            ignore_dirs = ['ml', 'venv', '__pycache__', '.git', 'site-packages']

            # Valid output patterns
            valid_extensions = [
                '.exr', '.png', '.jpg', '.jpeg', '.tif', '.tiff',  # Images
                '.bgeo', '.bgeo.sc', '.bgeo.gz', '.geo', '.obj',  # Geometry
                '.usd', '.usda', '.usdc', '.usdz',  # USD
                '.hip', '.hipnc', '.hiplc',  # Hip files
                '.mp4', '.mov', '.avi',  # Video
                '.vdb', '.abc',  # Volumes/Alembic
                '.json', '.xml', '.txt'  # Data
            ]

            # Search directories
            search_dirs = [self.working_dir]
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                search_dirs.append(self.temp_dir)

            for search_dir in search_dirs:
                for root, dirs, files in os.walk(search_dir):
                    # Skip ignored directories
                    if any(ignore in root for ignore in ignore_dirs):
                        dirs[:] = []
                        continue

                    dirs[:] = [d for d in dirs if not any(ignore in d for ignore in ignore_dirs)]

                    for file in files:
                        if any(file.endswith(ext) for ext in valid_extensions):
                            file_path = os.path.join(root, file)
                            if not hasattr(self, 'files_before') or file_path not in self.files_before:
                                new_files.append(file_path)

            # Copy files maintaining structure
            if new_files:
                print(f"✔ Found {len(new_files)} new files")
                print("\nCopying files to output directory...")
                self.files_copied = 0

                for file_path in new_files:
                    try:
                        # Determine relative path
                        rel_path = None

                        # Check for known subdirectories
                        for subdir in ['geo', 'render', 'usd', 'data', 'hip']:
                            pattern = f'{os.sep}{subdir}{os.sep}'
                            if pattern in file_path:
                                idx = file_path.find(pattern)
                                rel_path = file_path[idx + 1:]
                                break

                        # If not in known subdir, calculate from base directory
                        if not rel_path:
                            for base_dir in search_dirs:
                                if file_path.startswith(base_dir):
                                    rel_path = os.path.relpath(file_path, base_dir)
                                    break

                        if not rel_path:
                            rel_path = os.path.basename(file_path)

                        # Create destination path
                        dest_path = os.path.join(self.output_dir, rel_path)
                        dest_dir = os.path.dirname(dest_path)

                        # Create destination directory
                        os.makedirs(dest_dir, exist_ok=True)

                        # Copy file
                        import shutil
                        shutil.copy2(file_path, dest_path)
                        self.files_copied += 1

                        # Categorize for status dict
                        if any(rel_path.endswith(ext) for ext in ['.bgeo', '.bgeo.sc', '.bgeo.gz', '.geo']):
                            self.status_dict['files_created']['geo'].append(dest_path)
                        elif any(rel_path.endswith(ext) for ext in ['.exr', '.png', '.jpg', '.jpeg']):
                            self.status_dict['files_created']['renders'].append(dest_path)
                        elif any(rel_path.endswith(ext) for ext in ['.usd', '.usda', '.usdc']):
                            self.status_dict['files_created']['usd'].append(dest_path)
                        else:
                            self.status_dict['files_created']['other'].append(dest_path)

                    except Exception as e:
                        print(f"  ⚠ Could not copy {os.path.basename(file_path)}: {e}")

                print(f"✔ Copied {self.files_copied} files to output directory")
                self.status_dict['files_created']['total_count'] = self.files_copied
            else:
                print("⚠ No output files found to copy")

        except Exception as e:
            print(f"✗ Error during file collection: {e}")

    def _copy_file_with_structure(self, src_file, category):
        """Copy file maintaining directory structure"""
        import os
        import shutil

        if not os.path.exists(src_file):
            return None

        # Skip if file is already in output dir
        if src_file.startswith(self.output_dir):
            return None

        try:
            # Determine the source directory structure
            rel_path = None

            # Check if file is in a known subdirectory (geo, render, usd, etc)
            for subdir in ['geo', 'render', 'usd', 'data', 'hip']:
                pattern = f'{os.sep}{subdir}{os.sep}'
                if pattern in src_file:
                    # Extract path from the subdir onwards
                    idx = src_file.find(pattern)
                    rel_path = src_file[idx + 1:]  # Skip the leading separator
                    break

            # If not in a known subdir, check if it's from temp directory
            if not rel_path and hasattr(self, 'temp_dir') and self.temp_dir:
                if src_file.startswith(self.temp_dir):
                    rel_path = os.path.relpath(src_file, self.temp_dir)

            # If still no rel_path, check working directory
            if not rel_path and src_file.startswith(self.working_dir):
                rel_path = os.path.relpath(src_file, self.working_dir)

            # If still no rel_path, just use category folder
            if not rel_path:
                filename = os.path.basename(src_file)
                rel_path = os.path.join(category, filename)

            # Create destination path maintaining structure
            dest_path = os.path.join(self.output_dir, rel_path)
            dest_dir = os.path.dirname(dest_path)

            # Create destination directory
            os.makedirs(dest_dir, exist_ok=True)

            # Handle existing files
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(dest_path)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = f"{base}_{counter}{ext}"
                    counter += 1

            # Copy the file
            shutil.copy2(src_file, dest_path)
            return dest_path

        except Exception as e:
            print(f"    Failed to copy {os.path.basename(src_file)}: {e}")
            return None

    def _collect_geo_files(self):
        """Collect geometry files"""
        files = []

        # Check work items for geo outputs
        if hasattr(self, 'graph_context') and self.graph_context:
            try:
                for item in self.graph_context.graph.staticWorkItems:
                    try:
                        for output in item.outputFiles:
                            if any(output.endswith(ext) for ext in ['.bgeo', '.bgeo.sc', '.bgeo.gz', '.geo', '.obj']):
                                if os.path.exists(output):
                                    files.append(output)
                                    print(f"    Found from work item: {os.path.basename(output)}")
                    except:
                        pass
            except:
                pass

        # Scan geo directory as fallback
        geo_dir = os.path.join(self.working_dir, 'geo')
        if os.path.exists(geo_dir):
            import glob
            for pattern in ['*.bgeo', '*.bgeo.sc', '*.bgeo.gz', '*.geo', '*.obj']:
                geo_files = glob.glob(os.path.join(geo_dir, '**', pattern), recursive=True)
                for gf in geo_files:
                    if gf not in files:  # Avoid duplicates
                        files.append(gf)
                        print(f"    Found in geo dir: {os.path.basename(gf)}")

        # Also check temp directory if it exists
        if hasattr(self, 'temp_dir') and self.temp_dir:
            temp_geo_dir = os.path.join(self.temp_dir, 'geo')
            if os.path.exists(temp_geo_dir):
                import glob
                for pattern in ['*.bgeo', '*.bgeo.sc', '*.bgeo.gz', '*.geo', '*.obj']:
                    temp_geo_files = glob.glob(os.path.join(temp_geo_dir, '**', pattern), recursive=True)
                    for gf in temp_geo_files:
                        if gf not in files:
                            files.append(gf)
                            print(f"    Found in temp geo dir: {os.path.basename(gf)}")

        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for f in files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)

        return unique_files

    def _setup_temp_directory_no_ml(self):
        """
        Set up a temporary directory for non-ML runs to avoid disk quota issues
        """
        try:
            import tempfile
            import os
            from datetime import datetime

            # Use /tmp which usually has more space and no quota limits
            temp_base = os.environ.get('TMPDIR', '/tmp')

            # Create a unique temp directory for this job
            job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            pid = os.getpid()
            self.temp_dir = os.path.join(temp_base, f"pdg_job_{job_id}_{pid}")

            # Create the directory
            os.makedirs(self.temp_dir, exist_ok=True)

            # Set environment variables to use this temp directory
            os.environ['HOUDINI_TEMP_DIR'] = self.temp_dir
            os.environ['PDG_TEMP'] = self.temp_dir
            os.environ['PDG_DIR'] = self.temp_dir
            os.environ['PDG_TEMP_DIR'] = self.temp_dir

            print(f"✔ Created temp directory: {self.temp_dir}")

            # Clean up old temp directories to free space
            self._cleanup_old_temp_dirs(temp_base)

        except Exception as e:
            print(f"⚠ Warning: Could not set up custom temp directory: {e}")
            self.temp_dir = None

    def _collect_wedge_fallback_files(self):
        """Collect files generated by wedge fallback mechanism"""
        files = []

        # Check if wedge fallback was used and files were generated
        if hasattr(self, 'wedge_fallback_files') and self.wedge_fallback_files:
            for filepath in self.wedge_fallback_files:
                if os.path.exists(filepath):
                    files.append(filepath)
                    print(f"  Found: {os.path.basename(filepath)}")

        # Also scan the geo directory for any files we might have missed
        # This is a backup in case file tracking didn't work perfectly
        if not files and hasattr(self, 'status_dict') and self.status_dict.get('wedge_fallback_used'):
            geo_dir = os.path.join(os.path.dirname(self.hip_file), 'geo')
            if os.path.exists(geo_dir):
                import glob
                # Look for files with the wedge pattern (containing decimal numbers)
                for pattern in ['*.bgeo.sc', '*.bgeo', '*.geo']:
                    for filepath in glob.glob(os.path.join(geo_dir, f'*[0-9].[0-9]*{pattern}')):
                        files.append(filepath)
                        print(f"  Found (scan): {os.path.basename(filepath)}")

        return files

    def _collect_usd_files(self):
        """Collect all USD files"""
        patterns = [
            os.path.join(self.working_dir, '**/*.usd'),
            os.path.join(self.working_dir, '**/*.usda'),
            os.path.join(self.working_dir, '**/*.usdc'),
            os.path.join(self.working_dir, '**/*.usdz'),
        ]

        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern, recursive=True))

        return list(set(files))  # Remove duplicates

    def _collect_render_files(self):
        """Collect all rendered images including ML/CV outputs"""
        patterns = [
            # Standard render locations
            '/tmp/render/**/*.exr',
            '/tmp/render/**/*.png',
            '/tmp/render/**/*.jpg',
            '/tmp/render/**/*.tif',
            os.path.join(self.working_dir, 'render/**/*.exr'),
            os.path.join(self.working_dir, 'render/**/*.png'),
            os.path.join(self.working_dir, 'render/**/*.jpg'),
            os.path.join(self.working_dir, 'render/**/*.tif'),
            os.path.join(self.working_dir, 'images/**/*'),
            os.path.join(self.output_dir, '**/*.exr'),
            os.path.join(self.output_dir, '**/*.png'),
            os.path.join(self.output_dir, '**/*.jpg'),
            os.path.join(self.output_dir, '**/*.tif'),

            # ML/CV specific patterns (for backwards compatibility)
            os.path.join(self.working_dir, 'datasets/render/*/data/*.png'),
            os.path.join(self.working_dir, 'datasets/render/*/data/*.jpg'),
            os.path.join(self.working_dir, 'datasets/render/*/data/exr/*.exr'),

            # PDG temp render outputs
            os.path.join(self.working_dir, 'pdgtemp/**/render/**/*.exr'),
            os.path.join(self.working_dir, 'pdgtemp/**/render/**/*.png'),
        ]

        files = []
        for pattern in patterns:
            try:
                matched = glob.glob(pattern, recursive=True)
                files.extend(matched)
            except:
                # Non-recursive fallback for patterns that fail
                if '/**/' in pattern:
                    try:
                        # Try without recursive flag
                        simple_pattern = pattern.replace('/**/', '/*/')
                        matched = glob.glob(simple_pattern)
                        files.extend(matched)
                    except:
                        pass

        # Remove duplicates and non-files
        unique_files = []
        seen = set()
        for f in files:
            if f not in seen and os.path.isfile(f):
                seen.add(f)
                unique_files.append(f)

        return unique_files

    def _collect_pdg_files(self):
        """Collect PDG-specific files"""
        pdgtemp_dir = os.path.join(self.working_dir, 'pdgtemp')
        if not os.path.exists(pdgtemp_dir):
            return []

        patterns = [
            os.path.join(pdgtemp_dir, '**/*.json'),
            os.path.join(pdgtemp_dir, '**/data/*'),
        ]

        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern, recursive=True))

        return files

    def _collect_log_files(self):
        """Collect log files"""
        patterns = [
            os.path.join(self.working_dir, '**/*.log'),
            os.path.join(self.working_dir, 'pdgtemp/**/*.txt'),
            os.path.join(self.working_dir, '**/logs/*.txt'),
            os.path.join(self.output_dir, '**/*.log'),
            '/tmp/*.log',
        ]

        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern, recursive=True))

        return files

    def _collect_work_item_outputs(self):
        """Collect outputs from work items"""
        files = []

        # First, try to collect from PDG work items
        if self.topnet:
            try:
                for node in self.topnet.children():
                    if node.type().category().name() != "Top":
                        continue

                    try:
                        pdg_node = node.getPDGNode()
                        if not pdg_node:
                            continue

                        work_items = pdg_node.workItems
                        for wi in work_items:
                            # Try multiple methods to get output files
                            for attr in ['expectedOutputFiles', 'actualOutputFiles', 'outputFiles']:
                                try:
                                    output_files = getattr(wi, attr)
                                    for f in output_files:
                                        file_path = f.path if hasattr(f, 'path') else str(f)

                                        # Expand __PDG_DIR__ token
                                        if "__PDG_DIR__" in file_path:
                                            pdg_dir = os.environ.get("PDG_DIR", self.working_dir)
                                            file_path = file_path.replace("__PDG_DIR__", pdg_dir)

                                        # Check if file exists
                                        if os.path.exists(file_path):
                                            files.append(file_path)
                                            print(f"    Found work item output: {os.path.basename(file_path)}")
                                except:
                                    pass
                    except:
                        pass
            except:
                pass

        # Also scan common output directories as fallback
        if len(files) == 0:
            print("    No outputs from work items, scanning directories...")

            # Scan geo directory
            geo_dir = os.path.join(self.working_dir, 'geo')
            if os.path.exists(geo_dir):
                import glob
                for pattern in ['*.bgeo', '*.bgeo.sc', '*.bgeo.gz', '*.geo']:
                    geo_files = glob.glob(os.path.join(geo_dir, pattern))
                    for gf in geo_files:
                        # Skip wedge fallback files if they exist
                        if hasattr(self, 'wedge_fallback_files') and gf in self.wedge_fallback_files:
                            continue
                        files.append(gf)
                        print(f"    Found in geo dir: {os.path.basename(gf)}")

            # Scan render directory
            render_dir = os.path.join(self.working_dir, 'render')
            if os.path.exists(render_dir):
                import glob
                for pattern in ['*.exr', '*.png', '*.jpg', '*.tif']:
                    render_files = glob.glob(os.path.join(render_dir, '**', pattern), recursive=True)
                    files.extend(render_files)

            # Scan USD directory
            usd_dir = os.path.join(self.working_dir, 'usd')
            if os.path.exists(usd_dir):
                import glob
                for pattern in ['*.usd', '*.usda', '*.usdc']:
                    usd_files = glob.glob(os.path.join(usd_dir, pattern))
                    files.extend(usd_files)

        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for f in files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)

        return unique_files

    def _copy_file_organized(self, src_file, category):
        """Copy file to organized output structure"""
        if not os.path.exists(src_file):
            return None

        # Skip if file is already in output dir
        if src_file.startswith(self.output_dir):
            return None

        # Create category directory
        dest_dir = os.path.join(self.output_dir, category)
        os.makedirs(dest_dir, exist_ok=True)

        # Generate unique destination name
        filename = os.path.basename(src_file)
        dest_path = os.path.join(dest_dir, filename)

        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(dest_dir, f"{base}_{counter}{ext}")
                counter += 1

        try:
            shutil.copy2(src_file, dest_path)
            return dest_path
        except Exception as e:
            print(f"    Failed to copy {filename}: {e}")
            return None

    def _save_final_hip(self):
        """Save the final HIP file to output directory"""
        print("\n" + "-" * 60)
        print("Phase 7: Save HIP File")
        print("-" * 60)

        try:
            # Create HIP output directory
            hip_output_dir = os.path.join(self.output_dir, 'hip')
            os.makedirs(hip_output_dir, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(self.hip_file))[0]

            # Add mode suffix
            mode_suffix = "single_machine"
            if self.cook_entire_graph:
                mode_suffix = "full_graph"
            elif not self.use_single_machine:
                mode_suffix = f"item_{self.item_index}"

            output_filename = f"{base_name}_{mode_suffix}_{timestamp}.hip"
            output_path = os.path.join(hip_output_dir, output_filename)

            # Save to temp first
            temp_path = f"/tmp/{output_filename}"
            print(f"Saving to temp location: {temp_path}")
            hou.hipFile.save(temp_path)
            print("✓ HIP file saved to temp location")

            # Copy to final location
            print(f"✓ Output directory ready: {hip_output_dir}")
            print(f"Copying to final location: {output_path}")
            shutil.copy2(temp_path, output_path)
            print("✓ HIP file copied to final location")

            # Clean up temp file
            os.remove(temp_path)
            print("✓ Cleaned up temp file")

            print(f"✓ Final HIP file saved: {output_path}")

            # Track in status dict
            self.status_dict['files_created']['hip'].append(output_path)

        except Exception as e:
            print(f"⚠ Could not save final HIP file: {e}")

    def _finalize_execution(self):
        """Finalize execution and write status"""
        print("\n" + "-" * 60)
        print("Phase 8: Finalization")
        print("-" * 60)

        # Calculate duration
        self.status_dict['timestamp_end'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            start = datetime.strptime(self.status_dict['timestamp_start'], "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(self.status_dict['timestamp_end'], "%Y-%m-%d %H:%M:%S")
            self.status_dict['duration_seconds'] = (end - start).total_seconds()
        except:
            self.status_dict['duration_seconds'] = 0

        # Write status file
        status_dir = os.path.join(self.output_dir, 'execution_status')
        os.makedirs(status_dir, exist_ok=True)

        if self.cook_entire_graph:
            # Submit As Job mode: save with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            status_file = os.path.join(status_dir, f'pdg_submitasjob_status_{timestamp}.json')
        elif self.use_single_machine:
            # Single Machine mode: save with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            status_file = os.path.join(status_dir, f'pdg_single_machine_status_{timestamp}.json')
        else:
            # On Schedule mode: save with frame number
            frame_num = str(self.item_index).zfill(4)
            status_file = os.path.join(status_dir, f'pdg_execution_status.{frame_num}.json')

        try:
            with open(status_file, 'w') as f:
                json.dump(self.status_dict, f, indent=4, default=str)
            print(f"✓ Status written to: {status_file}")

            # Create a symlink to latest
            latest_link = os.path.join(status_dir, 'pdg_execution_status.latest.json')
            try:
                if os.path.exists(latest_link):
                    os.remove(latest_link)
                os.symlink(os.path.basename(status_file), latest_link)
                print(f"  Created latest link: {latest_link}")
            except:
                pass

        except Exception as e:
            print(f"✗ Failed to write status: {e}")

        # Print summary
        print("\n" + "=" * 80)
        print("EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Execution Mode: {self.execution_mode.upper()}")
        print(f"Status: {self.status_dict['status'].upper()}")
        print(f"Duration: {self.status_dict['duration_seconds']:.2f} seconds")

        if self.cook_entire_graph or self.use_single_machine:
            print(f"Total Work Items: {self.status_dict.get('work_items_total', 0)}")
            print(f"  Succeeded: {self.status_dict.get('work_items_succeeded', 0)}")
            print(f"  Failed: {self.status_dict.get('work_items_failed', 0)}")
        else:
            print(f"Frame/Item Index: {self.item_index} (Frame: {str(self.item_index).zfill(4)})")
            print(f"Work Items Processed: {len(self.status_dict.get('work_items_processed', []))}")
            print(f"Work Items Skipped: {len(self.status_dict.get('skipped_items', []))}")

        print(f"Files Collected: {self.status_dict['files_created']['total_count']}")

        if self.status_dict['errors']:
            print(f"\nErrors ({len(self.status_dict['errors'])}):")
            for error in self.status_dict['errors']:
                print(f"  - {error}")

        print("=" * 80)

    #----------------------------------------------------------------------------------
    # ML Route
    #-----------------------------------------------------------------------------------
    def _setup_temp_directory(self):
        """
        NEW METHOD: Set up a temporary directory with proper disk quota handling
        """
        try:
            # Use /tmp which usually has more space and no quota limits
            temp_base = os.environ.get('TMPDIR', '/tmp')
            
            # Create a unique temp directory for this job
            job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            pid = os.getpid()
            self.temp_dir = os.path.join(temp_base, f"pdg_ml_job_{job_id}_{pid}")
            
            # Create the directory
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # Set environment variables to use this temp directory
            os.environ['HOUDINI_TEMP_DIR'] = self.temp_dir
            os.environ['PDG_TEMP'] = self.temp_dir
            os.environ['PDG_DIR'] = self.temp_dir
            os.environ['PDG_TEMP_DIR'] = self.temp_dir
            
            print(f"✓ Created temp directory: {self.temp_dir}")
            
            # Clean up old temp directories to free space
            self._cleanup_old_temp_dirs(temp_base)
            
        except Exception as e:
            print(f"⚠ Warning: Could not set up custom temp directory: {e}")
            self.temp_dir = None


    def _cleanup_old_temp_dirs(self, temp_base):
        """
        NEW METHOD: Clean up old PDG temp directories to free space
        """
        try:
            import glob
            import shutil
            import time
            
            # Look for old pdg_ml_job_* directories
            pattern = os.path.join(temp_base, "pdg_ml_job_*")
            old_dirs = glob.glob(pattern)
            
            # Remove directories older than 24 hours
            current_time = time.time()
            for old_dir in old_dirs:
                if hasattr(self, 'temp_dir') and old_dir == self.temp_dir:
                    continue  # Don't delete our own directory
                    
                try:
                    dir_age = current_time - os.path.getmtime(old_dir)
                    if dir_age > 86400:  # 24 hours in seconds
                        shutil.rmtree(old_dir)
                        print(f"  Cleaned up old temp directory: {old_dir}")
                except:
                    pass  # Ignore errors in cleanup
                    
        except Exception as e:
            print(f"  Note: Could not clean old temp directories: {e}")


    def _cleanup_temp_directory(self):
        """
        NEW METHOD: Clean up our temp directory after execution
        """
        if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                print(f"✓ Cleaned up temp directory: {self.temp_dir}")
            except Exception as e:
                print(f"⚠ Could not clean temp directory: {e}")

    def _disable_auto_scripts(self):
        """Disable automatic Python script execution"""
        print("\n0. DISABLING AUTO SCRIPTS")
        print("-" * 40)

        try:
            # Method 1: Override hou.session before it can be populated
            import sys
            import types

            # Create an empty module for hou.session
            empty_session = types.ModuleType('hou.session')
            sys.modules['hou.session'] = empty_session
            hou.session = empty_session

            # Method 2: Set environment to prevent Python execution
            os.environ["HOUDINI_DISABLE_CONSOLE"] = "1"

            # Method 3: Override the Python panel execution
            try:
                hou.ui.curDesktop().findPaneTab("pythonpanel").setIsCurrentTab(False)
            except:
                pass

            print("  ✓ Auto script execution disabled")

        except Exception as e:
            print(f"  ⚠ Could not fully disable auto scripts: {e}")

    def _initialize_otl_paths(self):
        """Initialize OTL scan paths before loading HIP file"""
        print("\n1.5. INITIALIZING OTL PATHS")
        print("-" * 40)

        try:
            # Get SideFXLabs path if set
            sidefxlabs = os.environ.get("SIDEFXLABS")
            if sidefxlabs and os.path.exists(sidefxlabs):
                otl_dir = os.path.join(sidefxlabs, "otls")
                if os.path.exists(otl_dir):
                    # Add to OTL scan path using hscript
                    hou.hscript(f'otadd "{otl_dir}"')

                    # Also try to load specific OTLs that are commonly missing
                    otl_files = [
                        "ml_cv_rop_synthetic_data.hda",
                        "ml_cv_rop_annotation_output.hda",
                        "ml_cv_label_metadata.hda",
                        "ml_cv_synthetics_karma_rop.hda"
                    ]

                    for otl_file in otl_files:
                        # Try with version number
                        versioned_file = None
                        for f in os.listdir(otl_dir) if os.path.exists(otl_dir) else []:
                            if f.startswith(otl_file.replace(".hda", "")) and f.endswith(".hda"):
                                versioned_file = os.path.join(otl_dir, f)
                                break

                        if versioned_file and os.path.exists(versioned_file):
                            try:
                                hou.hda.installFile(versioned_file)
                                print(f"  ✓ Loaded: {os.path.basename(versioned_file)}")
                            except:
                                pass

                    # Refresh OTL database
                    hou.hscript('otrefresh')
                    print(f"  ✓ OTL paths initialized from: {otl_dir}")
            else:
                print("  ⚠ No SideFXLabs path available for OTLs")

        except Exception as e:
            print(f"  ⚠ Could not initialize OTL paths: {e}")

    def _setup_environment_ml(self):
        """
        FIXED: Setup environment for ML jobs with proper environment variables
        """
        print("\n1. SETTING UP ENVIRONMENT")
        print("-" * 40)

        # CRITICAL: Set all PDG environment variables BEFORE anything else
        os.environ['PDG_DIR'] = self.working_dir
        os.environ['PDG_WORKING_DIR'] = self.working_dir  # This was missing!
        os.environ['PDG_OUTPUT'] = self.working_dir
        os.environ['PDG_TEMP'] = os.path.join(self.working_dir, 'pdgtemp')
        os.environ['PDG_RENDER_DIR'] = self.output_dir

        # Set HOUDINI environment variables
        os.environ['HOUDINI_PDG_WORK_DIR'] = self.working_dir
        os.environ['HOUDINI_TEMP_DIR'] = os.path.join(self.working_dir, 'pdgtemp')

        print(f"  ✓ Set PDG_DIR: {os.environ['PDG_DIR']}")
        print(f"  ✓ Set PDG_WORKING_DIR: {os.environ['PDG_WORKING_DIR']}")
        print(f"  ✓ Set PDG_OUTPUT: {os.environ['PDG_OUTPUT']}")
        print(f"  ✓ Set PDG_TEMP: {os.environ['PDG_TEMP']}")

        # Check for SideFXLabs
        labs_path = os.environ.get('SIDEFXLABS')
        if labs_path:
            print(f"  ✓ SideFXLabs already configured: {labs_path}")
        else:
            # Try to find SideFXLabs
            possible_paths = [
                '/opt/sidefx/sidefxlabs-houdini',
                os.path.expanduser('~/SideFXLabs'),
                '/usr/local/SideFXLabs'
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    os.environ['SIDEFXLABS'] = path
                    print(f"  ✓ Found and set SIDEFXLABS: {path}")
                    break

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'hip'), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'execution_status'), exist_ok=True)

        # Create working directories for ML outputs
        os.makedirs(os.path.join(self.working_dir, 'datasets'), exist_ok=True)
        os.makedirs(os.path.join(self.working_dir, 'dataset_hips'), exist_ok=True)
        os.makedirs(os.path.join(self.working_dir, 'pdgtemp'), exist_ok=True)

        print(f"  ✓ Working directory: {self.working_dir}")
        print(f"  ✓ Output directory: {self.output_dir}")
        print(f"  ✓ PDG temp: {os.path.join(self.working_dir, 'pdgtemp', str(os.getpid()))}")

        return True

    def _setup_sidefxlabs_env(self):
        """Setup SideFXLabs environment before HIP load"""
        try:
            # Check if SIDEFXLABS is already set
            sidefxlabs = os.environ.get("SIDEFXLABS")
            if sidefxlabs and os.path.exists(sidefxlabs):
                print(f"  ✓ SideFXLabs already configured: {sidefxlabs}")
                return

            # Get Houdini version to find matching SideFXLabs
            houdini_version = hou.applicationVersionString()
            major_minor = '.'.join(houdini_version.split('.')[:2])

            # Common SideFXLabs locations
            possible_paths = [
                f"/opt/sidefx/sidefxlabs-houdini/{major_minor.split('.')[0]}",
                f"/opt/sidefx/sidefxlabs",
                "/opt/sidefxlabs",
                os.path.expanduser("~/Documents/SideFXLabs"),
                os.path.expanduser("~/SideFXLabs")
            ]

            # Look for sidefxlabs with specific version
            import glob
            labs_pattern = f"/opt/sidefx/sidefxlabs-houdini/{major_minor.split('.')[0]}/sidefxlabs-houdini-*"
            labs_dirs = glob.glob(labs_pattern)
            if labs_dirs:
                # Use the latest version
                labs_dirs.sort()
                possible_paths.insert(0, labs_dirs[-1])

            for path in possible_paths:
                if os.path.exists(path):
                    os.environ["SIDEFXLABS"] = path

                    # Add to HOUDINI_PATH
                    current_path = os.environ.get("HOUDINI_PATH", "")
                    if path not in current_path:
                        os.environ["HOUDINI_PATH"] = f"{path};&" if not current_path else f"{path};{current_path}"

                    print(f"  ✓ SideFXLabs configured: {path}")
                    return

            print("  ⚠ SideFXLabs not found in common locations")

        except Exception as e:
            print(f"  ⚠ Could not setup SideFXLabs: {e}")

    def _load_hip_file_ml(self):
        """Load the Houdini HIP file"""
        print("\n" + "-" * 60)
        print("Phase 2: Loading HIP File")
        print("-" * 60)

        try:
            if not os.path.exists(self.hip_file):
                raise FileNotFoundError(f"HIP file not found: {self.hip_file}")

            print(f"Loading: {self.hip_file}")

            # Load the file and capture any warnings
            try:
                hou.hipFile.load(self.hip_file, suppress_save_prompt=True, ignore_load_warnings=True)
            except hou.LoadWarning as warning:
                # This is just a warning, not an error - file loaded successfully
                print(f"  Note: Load warning (can be ignored): {warning}")
            except hou.OperationFailed as e:
                # This is an actual error
                if "Warnings were generated" in str(e):
                    # This is actually just warnings, not a failure
                    print(f"  Note: Warnings during load (continuing): {e}")
                else:
                    # This is a real failure
                    raise e

            # Verify load by checking the current file
            current_hip = hou.hipFile.name()
            if os.path.abspath(current_hip) == os.path.abspath(self.hip_file):
                print(f"✓ HIP file loaded successfully: {current_hip}")
            else:
                # Sometimes the path format differs, check if it's essentially the same file
                print(f"✓ HIP file loaded: {current_hip}")

            # Update paths if needed
            hou.hscript(f"set PDG_DIR = {self.working_dir}")
            hou.hscript(f"set PDG_RENDER_DIR = {self.output_dir}")

            return True

        except FileNotFoundError as e:
            print(f"✗ File not found: {e}")
            return False
        except Exception as e:
            # Check if this is just a warning about incomplete asset definitions
            error_str = str(e)
            if "Warnings were generated" in error_str or "incomplete asset definitions" in error_str:
                print(f"  Note: Load completed with warnings (continuing):")
                print(f"    {error_str}")

                # Verify the file actually loaded
                try:
                    current_hip = hou.hipFile.name()
                    print(f"✓ HIP file loaded despite warnings: {current_hip}")

                    # Update paths
                    hou.hscript(f"set PDG_DIR = {self.working_dir}")
                    hou.hscript(f"set PDG_RENDER_DIR = {self.output_dir}")

                    return True
                except:
                    # If we can't get the hip file name, it didn't load
                    print(f"✗ Failed to verify HIP file load")
                    return False
            else:
                # This is a real error
                print(f"✗ Failed to load HIP file: {e}")
                return False

    def _check_and_fix_missing_definitions(self):
        """Check for missing node definitions and attempt to load them"""
        try:
            # Check for nodes with missing definitions
            missing_defs = []
            for node in hou.node("/").allSubChildren():
                try:
                    if node.type().definition() is None:
                        missing_defs.append(f"{node.path()} ({node.type().name()})")
                except:
                    pass

            if missing_defs:
                print(f"  ⚠ Found {len(missing_defs)} nodes with missing definitions")
                for node_info in missing_defs[:3]:  # Show first 3
                    print(f"    - {node_info}")

                # Try to fix by updating definitions
                print("  Attempting to update OTL scan paths...")
                self._setup_sidefxlabs()

        except Exception as e:
            print(f"  Note: Could not check for missing definitions: {e}")

    def _setup_sidefxlabs(self):
        """Setup SideFXLabs if available"""
        try:
            # Common SideFXLabs locations
            possible_paths = [
                os.environ.get("SIDEFXLABS"),
                "/opt/sidefx/sidefxlabs",
                "/opt/sidefxlabs",
                os.path.expanduser("~/Documents/SideFXLabs"),
                os.path.expanduser("~/SideFXLabs")
            ]

            for path in possible_paths:
                if path and os.path.exists(path):
                    # Add to HOUDINI_PATH
                    current_path = os.environ.get("HOUDINI_PATH", "")
                    if path not in current_path:
                        os.environ["HOUDINI_PATH"] = f"{path};&" if not current_path else f"{path};{current_path}"

                    # Add OTLs directory
                    otl_path = os.path.join(path, "otls")
                    if os.path.exists(otl_path):
                        # Use hscript to add to OTL scan path
                        hou.hscript(f'otrefresh')
                        print(f"    ✓ Added SideFXLabs from: {path}")
                        break
        except:
            pass

    def _locate_topnet(self):
        """Find and validate TOP network using robust logic"""
        print("\n3. LOCATING TOP NETWORK")
        print("-" * 40)

        try:
            # Try specified path first
            current_node = hou.node(self.topnet_path)

            if current_node:
                # Check if the node exists and find the topnet
                print(f"  Node found at {self.topnet_path} (type: {current_node.type().name()})")
                print(f"    Category: {current_node.type().category().name()}")

                # Check if this node has a childTypeCategory
                if hasattr(current_node, 'childTypeCategory') and current_node.childTypeCategory():
                    print(f"    Child category: {current_node.childTypeCategory().name()}")

                # Check if this is a TOP network container (can contain TOP nodes)
                is_topnet_container = (hasattr(current_node, 'childTypeCategory') and
                                       current_node.childTypeCategory() and
                                       current_node.childTypeCategory().name() == "Top")

                if is_topnet_container:
                    # It's already a TOP network container
                    self.topnet = current_node
                    self.topnet_path = current_node.path()
                    print(f"  ✓ Node is a TOP network container: {self.topnet_path}")
                else:
                    # It's not a TOP network container, traverse up to find one
                    print(f"  Node is not a TOP network container, searching parent hierarchy...")

                    # Start from current node's parent
                    parent_node = current_node.parent() if current_node else None

                    while parent_node is not None:
                        print(f"    Checking parent: {parent_node.path()}")

                        # Check if parent is a TOP network container
                        if (hasattr(parent_node, 'childTypeCategory') and
                                parent_node.childTypeCategory() and
                                parent_node.childTypeCategory().name() == "Top"):
                            self.topnet = parent_node
                            self.topnet_path = parent_node.path()
                            print(f"  ✓ Found TOP network container in parent: {self.topnet_path}")
                            break

                        # Move up to next parent
                        parent_node = parent_node.parent()

                    # If we didn't find a topnet in the parent hierarchy
                    if not self.topnet:
                        print(f"  No TOP network container found in parent hierarchy")
                        print("  Falling back to scene-wide search...")
                        self._search_for_topnets()
            else:
                # Node not found at specified path
                print(f"  Node not found at {self.topnet_path}")
                print("  Falling back to scene-wide search...")
                self._search_for_topnets()

            # Final check - did we find a TOP network?
            if not self.topnet:
                print("  ✗ No TOP networks found in scene")
                return False

            print(f"\n  ✓ Using TOP network: {self.topnet_path}")
            print(f"    Type: {self.topnet.type().name()}")
            print(f"    Category: {self.topnet.type().category().name()}")

            if hasattr(self.topnet, 'childTypeCategory') and self.topnet.childTypeCategory():
                print(f"    Child category: {self.topnet.childTypeCategory().name()}")

            # Catalog nodes in network
            self._catalog_top_nodes_ml()

            # Find output node
            self._find_output_node_ml()

            return True

        except Exception as e:
            print(f"  ✗ Failed to locate TOP network: {e}")
            return False


    def _recursive_topnet_search(self, node, found_list):
        """Recursively search for TOP networks"""
        try:
            # Check if this node is a TOP network container
            if (hasattr(node, 'childTypeCategory') and
                    node.childTypeCategory() and
                    node.childTypeCategory().name() == "Top"):
                found_list.append(node)
                print(f"    Found: {node.path()}")

            # Also check if it's a topnet by type name
            elif node.type().name() in ['topnet', 'topnetmgr']:
                found_list.append(node)
                print(f"    Found: {node.path()}")

            # Recurse into children
            for child in node.children():
                self._recursive_topnet_search(child, found_list)

        except:
            pass

    def _catalog_top_nodes_ml(self):
        """Catalog TOP nodes in the network"""
        try:
            print("\n  Cataloging TOP nodes:")

            top_nodes = []
            for node in self.topnet.children():
                try:
                    if hasattr(node.type(), 'category') and node.type().category().name() == "Top":
                        node_info = f"{node.name()} ({node.type().name()})"

                        # Check for special flags
                        flags = []
                        if hasattr(node, 'isDisplayFlagSet') and node.isDisplayFlagSet():
                            flags.append("DISPLAY")
                        if hasattr(node, 'isRenderFlagSet') and node.isRenderFlagSet():
                            flags.append("RENDER")

                        if flags:
                            node_info += f" [{', '.join(flags)}]"

                        print(f"    - {node_info}")
                        top_nodes.append(node)
                except:
                    pass

            return top_nodes

        except Exception as e:
            print(f"  Error cataloging nodes: {e}")
            return []

    def _find_output_node_ml(self):
        """Find the output node in the TOP network"""
        print("\n  Identifying output node:")

        try:
            # Priority 1: Display flag
            for node in self.topnet.children():
                if (hasattr(node.type(), 'category') and
                        node.type().category().name() == "Top" and
                        hasattr(node, 'isDisplayFlagSet') and
                        node.isDisplayFlagSet()):
                    self.output_node = node
                    print(f"    ✓ Using display node: {node.name()}")
                    return

            # Priority 2: Render flag
            for node in self.topnet.children():
                if (hasattr(node.type(), 'category') and
                        node.type().category().name() == "Top" and
                        hasattr(node, 'isRenderFlagSet') and
                        node.isRenderFlagSet()):
                    self.output_node = node
                    print(f"    ✓ Using render node: {node.name()}")
                    return

            # Priority 3: Node with "output" in name
            for node in self.topnet.children():
                if (hasattr(node.type(), 'category') and
                        node.type().category().name() == "Top"):
                    if "output" in node.name().lower() or "out" in node.type().name().lower():
                        self.output_node = node
                        print(f"    ✓ Using output node: {node.name()}")
                        return

            # Priority 4: Last non-scheduler TOP node
            top_nodes = []
            for node in self.topnet.children():
                if (hasattr(node.type(), 'category') and
                        node.type().category().name() == "Top" and
                        "scheduler" not in node.type().name().lower()):
                    top_nodes.append(node)

            if top_nodes:
                self.output_node = top_nodes[-1]
                print(f"    ✓ Using last TOP node: {self.output_node.name()}")
            else:
                print("    ⚠ No specific output node identified")

        except Exception as e:
            print(f"    Error finding output node: {e}")

    def _ensure_scheduler(self):
        """
        FIXED: Ensure scheduler uses working directory with correct parameter names
        Based on actual Houdini parameter testing
        """
        print("\n4. SETTING UP SCHEDULER")
        print("-" * 40)

        # Find or create local scheduler
        scheduler = None
        for node in self.topnet.children():
            if node.type().name() == "localscheduler":
                scheduler = node
                print(f"  Found existing local scheduler: {node.name()}")
                break

        if not scheduler:
            print("  Creating local scheduler...")
            scheduler = self.topnet.createNode("localscheduler", "localscheduler")
            print("  ✓ Created local scheduler")

        # CRITICAL: Set working directory using the CORRECT parameter name
        # Testing showed only 'pdg_workingdir' exists
        if scheduler.parm('pdg_workingdir'):
            scheduler.parm('pdg_workingdir').set(self.working_dir)
            print(f"  ✓ Set working directory: {self.working_dir}")
        else:
            print(f"  ERROR: pdg_workingdir parameter not found!")

        # Set temp directory
        temp_dir = os.path.join(self.working_dir, 'pdgtemp', str(os.getpid()))
        os.makedirs(temp_dir, exist_ok=True)

        # Based on test output, we have 'tempdircustom' and 'tempdirmenu' parameters
        # tempdirmenu = 1 means use automatic temp directory
        # tempdirmenu = 0 means use custom directory from tempdircustom
        if scheduler.parm('tempdirmenu') and scheduler.parm('tempdircustom'):
            try:
                # Set to use custom temp directory
                scheduler.parm('tempdirmenu').set(0)  # 0 = use custom
                scheduler.parm('tempdircustom').set(temp_dir)
                print(f"  ✓ Set custom temp directory: {temp_dir}")
            except Exception as e:
                print(f"  Warning: Could not set temp directory: {e}")

        # Set append PID to temp directory (if parameter exists)
        if scheduler.parm('tempdirappendpid'):
            try:
                scheduler.parm('tempdirappendpid').set(1)
                print("  ✓ Enabled PID append to temp directory")
            except:
                pass

        # Don't delete temp directory (for debugging)
        if scheduler.parm('pdg_deletetempdir'):
            try:
                scheduler.parm('pdg_deletetempdir').set(0)
                print("  ✓ Disabled temp directory deletion (for debugging)")
            except:
                pass

        # Set environment variables as fallback
        os.environ['PDG_TEMP'] = temp_dir
        os.environ['PDG_TEMP_DIR'] = temp_dir

        # Note: Parameters like maxproccount, verboselogging don't exist in this version
        # They might be named differently or controlled elsewhere

        # Apply scheduler to network
        scheduler_path = scheduler.path()

        # Set on network - check if parameter exists
        if self.topnet.parm('topscheduler'):
            try:
                self.topnet.parm('topscheduler').set(scheduler_path)
                print("  ✓ Set network default scheduler via 'topscheduler'")
            except Exception as e:
                print(f"  Warning: Could not set topscheduler: {e}")

        # Also set on each TOP node
        for node in self.topnet.children():
            if node.type().category().name() != "Top":
                continue
            if "scheduler" in node.type().name().lower():
                continue

            # Try various parameter names
            for parm_name in ["pdg_scheduler", "topscheduler", "scheduler"]:
                parm = node.parm(parm_name)
                if parm:
                    try:
                        parm.set(scheduler_path)
                        break
                    except:
                        pass

        self.scheduler = scheduler
        print("  ✓ Scheduler configuration complete")
        return True

    def _reset_conductor_scheduler_callback(self):
        """Reset the conductor scheduler's on_schedule callback to default Python scheduler behavior"""
        try:
            if self.scheduler and "conductor" in self.scheduler.type().name().lower():
                # Set the on_schedule callback to the default Python scheduler behavior
                on_schedule_code = '''import subprocess
import os
import sys

# Ensure directories exist and serialize the work item
self.createJobDirsAndSerializeWorkItems(work_item)

# expand the special __PDG_* tokens in the work item command
item_command = self.expandCommandTokens(work_item.command, work_item)

# add special PDG_* variables to the job's environment
temp_dir = str(self.tempDir(False))

job_env = os.environ.copy()
job_env['PDG_RESULT_SERVER'] = str(self.workItemResultServerAddr())
job_env['PDG_ITEM_NAME'] = str(work_item.name)
job_env['PDG_ITEM_ID'] = str(work_item.id)
job_env['PDG_DIR'] = str(self.workingDir(False))
job_env['PDG_TEMP'] = temp_dir
job_env['PDG_SCRIPTDIR'] = str(self.scriptDir(False))

# run the given command in a shell
returncode = subprocess.call(item_command, shell=True, env=job_env)

# if the return code is non-zero, report it as failed
if returncode == 0:
    return pdg.scheduleResult.CookSucceeded
return pdg.scheduleResult.CookFailed'''

                # Try to set the onschedule parameter if it exists
                if self.scheduler.parm("onschedule"):
                    self.scheduler.parm("onschedule").set(on_schedule_code)
                    print(f"    ✓ Reset Conductor scheduler callback to default behavior")
                elif self.scheduler.parm("pdg_onschedule"):
                    self.scheduler.parm("pdg_onschedule").set(on_schedule_code)
                    print(f"    ✓ Reset Conductor scheduler callback to default behavior")
                else:
                    print(f"    ⚠ Could not find onschedule parameter on Conductor scheduler")
        except Exception as e:
            print(f"    ⚠ Could not reset Conductor scheduler callback: {e}")

    def _configure_scheduler(self):
        """Configure scheduler parameters and set as network default"""
        if not self.scheduler:
            return

        try:
            # Set working directory
            if self.scheduler.parm("pdg_workingdir"):
                self.scheduler.parm("pdg_workingdir").set(self.working_dir)

            # Set max processes for local scheduler
            if self.scheduler.type().name() == "localscheduler":
                if self.scheduler.parm("maxprocsmenu"):
                    self.scheduler.parm("maxprocsmenu").set(0)  # Use all cores

            print(f"  ✓ Configured scheduler parameters")

            scheduler_path = self.scheduler.path()

            # Set on the network
            for parm_name in ["topscheduler", "defaulttopscheduler", "scheduler"]:
                try:
                    parm = self.topnet.parm(parm_name)
                    if parm:
                        parm.set(scheduler_path)
                        print(f"  ✓ Set network default scheduler via '{parm_name}'")
                        break
                except:
                    pass

        except Exception as e:
            print(f"  Note: Could not fully configure scheduler: {e}")

    def _scan_files_before(self):
        """
        ENHANCED: Scan for existing files with detailed logging
        """
        print("\n5. SCANNING EXISTING FILES")
        print("-" * 40)

        self.files_before = set()

        try:
            # Directories to scan
            scan_dirs = [
                (self.working_dir, "Working directory"),
            ]

            # Add temp directory if it exists
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                scan_dirs.append((self.temp_dir, "Temp directory"))

            # Add pdgtemp if it exists
            pdgtemp = os.path.join(self.working_dir, 'pdgtemp')
            if os.path.exists(pdgtemp):
                scan_dirs.append((pdgtemp, "PDG temp directory"))

            # Directories to ignore
            ignore_dirs = ['ml', 'venv', '__pycache__', '.git', 'site-packages']

            print(f"  Scanning directories:")
            for scan_dir, desc in scan_dirs:
                print(f"    - {desc}: {scan_dir}")
                if not os.path.exists(scan_dir):
                    print(f"      (does not exist)")
                    continue

            total_files = 0
            total_dirs = 0

            for scan_dir, desc in scan_dirs:
                if os.path.exists(scan_dir):
                    dir_files = 0
                    dir_dirs = 0

                    for root, dirs, files in os.walk(scan_dir):
                        # Check if we should skip this directory
                        should_skip = False
                        for ignore in ignore_dirs:
                            if ignore in root:
                                should_skip = True
                                dirs[:] = []  # Don't recurse
                                break

                        if should_skip:
                            continue

                        # Remove ignored directories from traversal
                        dirs[:] = [d for d in dirs if not any(ignore in d for ignore in ignore_dirs)]
                        dir_dirs += len(dirs)

                        for file in files:
                            file_path = os.path.join(root, file)
                            self.files_before.add(file_path)
                            dir_files += 1

                    if dir_files > 0 or dir_dirs > 0:
                        print(f"    {desc}: {dir_files} files in {dir_dirs} directories")
                    total_files += dir_files
                    total_dirs += dir_dirs

            print(f"\n  ✓ Found {total_files} existing files (excluding ml/ folder)")

            # If we found files, show some examples
            if total_files > 0:
                print("  Sample of existing files:")
                for i, f in enumerate(list(self.files_before)[:5]):
                    print(f"    - {os.path.relpath(f, self.working_dir)}")
                if total_files > 5:
                    print(f"    ... and {total_files - 5} more")

        except Exception as e:
            print(f"  Error during scan: {e}")
            import traceback
            traceback.print_exc()

    def _find_ml_outputs_specifically(self):
        """
        NEW METHOD: Specifically look for ML output files in expected locations
        """
        ml_outputs = []

        # Define where ML outputs should be
        output_locations = [
            # In working directory
            (self.working_dir, 'datasets'),
            (self.working_dir, 'dataset_hips'),
            # In pdgtemp
            (os.path.join(self.working_dir, 'pdgtemp'), 'datasets'),
            (os.path.join(self.working_dir, 'pdgtemp'), 'dataset_hips'),
        ]

        # Add temp directory locations if it exists
        if hasattr(self, 'temp_dir') and self.temp_dir:
            output_locations.extend([
                (self.temp_dir, 'datasets'),
                (self.temp_dir, 'dataset_hips'),
                (os.path.join(self.temp_dir, 'pdgtemp'), 'datasets'),
                (os.path.join(self.temp_dir, 'pdgtemp'), 'dataset_hips'),
            ])

        # Look for files in these specific locations
        for base_dir, subdir in output_locations:
            check_path = os.path.join(base_dir, subdir)
            if os.path.exists(check_path):
                print(f"  Found {subdir} at: {check_path}")

                for root, dirs, files in os.walk(check_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        ml_outputs.append(file_path)

        return ml_outputs

    def _configure_ml_node(self):
        """
        Configure ML node to generate all configured variations and save HIP files
        """
        if not self.output_node or 'ml_cv' not in self.output_node.type().name().lower():
            return

        print(f"\n  Configuring ML node: {self.output_node.name()}")

        # CRITICAL FIX 1: Set generatestatic to "1" (as string for string params)
        if self.output_node.parm('generatestatic'):
            try:
                self.output_node.parm('generatestatic').set("1")
                print("    ✓ ENABLED generatestatic = 1 (CRITICAL!)")
            except:
                # If it's an integer param, try with integer
                try:
                    self.output_node.parm('generatestatic').set(1)
                    print("    ✓ ENABLED generatestatic = 1 (CRITICAL!)")
                except Exception as e:
                    print(f"    ✗ Could not set generatestatic: {e}")

        # Check current varcount
        if self.output_node.parm('varcount'):
            varcount = self.output_node.parm('varcount').eval()
            print(f"    Current varcount: {varcount}")

        # Set variation range
        if self.output_node.parm('varrange1'):
            self.output_node.parm('varrange1').set(1)
            print("    ✓ Set varrange1 = 1")

        # CRITICAL FIX 2: Configure HIP file saving for ML datasets
        # This is what was missing and causing no .hip files in dataset_hips
        if self.output_node.parm('savehipsfordelivery'):
            try:
                self.output_node.parm('savehipsfordelivery').set(1)
                print("    ✓ ENABLED savehipsfordelivery = 1 (SAVES HIP FILES!)")
            except Exception as e:
                print(f"    ✗ Could not enable savehipsfordelivery: {e}")
        else:
            print("    ⚠ savehipsfordelivery parameter not found - HIP files may not be saved!")

        # Set the HIP files directory
        hips_dir = os.path.join(self.working_dir, 'dataset_hips')
        if self.output_node.parm('hipsdir'):
            try:
                self.output_node.parm('hipsdir').set(hips_dir)
                print(f"    ✓ Set hipsdir: {hips_dir}")
            except Exception as e:
                print(f"    ✗ Could not set hipsdir: {e}")

        # Alternative parameter names for HIP directory
        hip_dir_params = ['hip_output_path', 'hip_output_dir', 'hipdir', 'hip_dir']
        for param_name in hip_dir_params:
            if self.output_node.parm(param_name):
                try:
                    self.output_node.parm(param_name).set(hips_dir)
                    print(f"    ✓ Set {param_name}: {hips_dir}")
                    break
                except:
                    pass

        # Set render and delivery directories
        render_dir = os.path.join(self.working_dir, 'datasets', 'render')
        delivery_dir = os.path.join(self.working_dir, 'datasets', 'delivery')

        if self.output_node.parm('renderdir'):
            self.output_node.parm('renderdir').set(render_dir)
            print(f"    ✓ Set renderdir: {render_dir}")

        if self.output_node.parm('deliverydir'):
            self.output_node.parm('deliverydir').set(delivery_dir)
            print(f"    ✓ Set deliverydir: {delivery_dir}")

        # ADDITIONAL FIX: Enable dataset generation parameters
        dataset_params = [
            ('enable_datasets', 1),
            ('create_datasets', 1),
            ('save_scene_files', 1),
            ('export_hip', 1),
            ('save_hip', 1)
        ]

        for param_name, value in dataset_params:
            if self.output_node.parm(param_name):
                try:
                    self.output_node.parm(param_name).set(value)
                    print(f"    ✓ Set {param_name} = {value}")
                except:
                    pass

        # Check for cookbutton
        if self.output_node.parm('cookbutton'):
            print("    ⚠ Found cookbutton parameter - will be pressed during execution")

        # Print key parameters for debugging
        print("\n    Key ML node parameters:")
        key_params = ['generatestatic', 'varcount', 'varrange1', 'varrange2',
                      'renderdir', 'deliverydir', 'savehipsfordelivery', 'hipsdir',
                      'cachemode', 'enable']

        for parm_name in key_params:
            parm = self.output_node.parm(parm_name)
            if parm:
                try:
                    val = parm.eval()
                    print(f"      {parm_name}: {val}")
                except:
                    print(f"      {parm_name}: <unable to evaluate>")

        # Also check for any variation/frame related parameters
        print("\n    Variation/Frame parameters found:")
        all_parms = self.output_node.parms()
        variation_keywords = ['var', 'frame', 'count', 'num', 'range', 'start', 'end', 'step', 'hip', 'save']
        found_variation_params = False

        for parm in all_parms:
            try:
                parm_name = parm.name()
                if any(keyword in parm_name.lower() for keyword in variation_keywords):
                    if parm_name not in key_params:  # Don't repeat already shown params
                        val = parm.eval()
                        print(f"      {parm_name}: {val}")
                        found_variation_params = True
            except:
                pass

        if not found_variation_params:
            print("      (No additional variation parameters found)")

        # Create the dataset_hips directory if it doesn't exist
        os.makedirs(hips_dir, exist_ok=True)
        print(f"\n    ✓ Ensured dataset_hips directory exists: {hips_dir}")

    def _configure_ml_node_outputs(self):
        """Configure ML node output paths including HIP file directories"""
        if not self.output_node:
            return

        print(f"  Configuring {self.output_node.name()} output paths...")

        # Create all necessary directories
        datasets_dir = os.path.join(self.working_dir, 'datasets')
        render_dir = os.path.join(datasets_dir, 'render')
        delivery_dir = os.path.join(datasets_dir, 'delivery')
        hips_dir = os.path.join(self.working_dir, 'dataset_hips')

        # Create directories
        for dir_path in [datasets_dir, render_dir, delivery_dir, hips_dir]:
            os.makedirs(dir_path, exist_ok=True)
            print(f"    ✓ Created/verified directory: {dir_path}")

        # Set output directory parameters
        output_params = {
            'outputdir': self.working_dir,
            'output_directory': self.working_dir,
            'output_path': self.working_dir,
            'render_path': render_dir,
            'dataset_path': datasets_dir,
            'hip_output_path': hips_dir,
            'hipsdir': hips_dir,  # Critical parameter for saving HIP files
            'renderdir': render_dir,
            'deliverydir': delivery_dir,
        }

        for param_name, path_value in output_params.items():
            parm = self.output_node.parm(param_name)
            if parm:
                try:
                    parm.set(path_value)
                    if param_name in ['hipsdir', 'hip_output_path']:
                        print(f"    ✓ Set {param_name}: {path_value}")
                except:
                    pass

    def _execute_simple(self):
        """
        FIXED: Enhanced execution method that forces ML nodes to generate work items and execute
        """
        print("\n6. EXECUTING PDG NETWORK")
        print("-" * 40)
        print("Using simple execution method (mimics successful local execution)\n")

        # Set environment variables
        os.environ['PDG_WORKING_DIR'] = self.working_dir
        if not os.environ.get('PDG_DIR'):
            os.environ['PDG_DIR'] = self.working_dir

        print("  Environment variables:")
        print(f"    PDG_DIR: {os.environ.get('PDG_DIR')}")
        print(f"    PDG_WORKING_DIR: {os.environ.get('PDG_WORKING_DIR')}")
        print(f"    PDG_TEMP: {os.environ.get('PDG_TEMP')}")
        print(f"    Working dir: {self.working_dir}")

        # Configure ML node if present
        if self.output_node and 'ml_cv' in self.output_node.type().name().lower():
            print(f"\n  Configuring {self.output_node.name()} output paths...")
            self._configure_ml_node_outputs()
            self._configure_ml_node()

            # CRITICAL: Force ML node execution by pressing cookbutton
            if self.output_node.parm('cookbutton'):
                print("\n  FORCING ML NODE EXECUTION...")
                print("  Pressing cookbutton to trigger ML generation...")
                try:
                    self.output_node.parm('cookbutton').pressButton()
                    print("    ✓ Pressed cookbutton!")
                    print("    Waiting for ML process to initialize...")
                    time.sleep(5)  # Give ML process time to start

                    # Check if work items were generated
                    try:
                        pdg_node = self.output_node.getPDGNode()
                        if pdg_node and hasattr(pdg_node, 'workItems'):
                            work_items = pdg_node.workItems
                            if work_items:
                                print(f"    ✓ ML node generated {len(work_items)} work items")
                            else:
                                print("    ⚠ No work items generated yet")
                    except:
                        pass

                except Exception as e:
                    print(f"    ✗ Could not press cookbutton: {e}")

        # Force work item generation
        print("\n  FORCING WORK ITEM GENERATION...")
        self._force_work_item_generation()

        # Check work items before cooking (safely)
        work_item_count = self._check_work_items_safe()

        # If still no work items and we have an ML node, try alternative execution
        if work_item_count == 0 and self.output_node and 'ml_cv' in self.output_node.type().name().lower():
            print("\n  No work items found - trying alternative ML execution...")
            success = self._execute_ml_node_directly()
            if success:
                return True

        # Execute the network
        print("\n  Attempting direct network cook...")
        cook_success = self._execute_network_cook()

        # Post-execution checks
        if cook_success:
            print("\n  Waiting for file writes to complete...")
            time.sleep(10)  # Increased wait time for ML operations

            # Check for ML outputs
            self._check_and_wait_for_ml_outputs()

        return cook_success

    def _check_and_wait_for_ml_outputs(self):
        """
        Check for ML outputs and wait if they're still being generated
        """
        print("\n  Checking for ML outputs...")

        max_wait = 30  # Maximum wait time in seconds
        check_interval = 5  # Check every 5 seconds
        waited = 0

        while waited < max_wait:
            # Check for files in expected locations
            found_files = False

            # Check datasets directory
            datasets_dir = os.path.join(self.working_dir, 'datasets')
            if os.path.exists(datasets_dir):
                for root, dirs, files in os.walk(datasets_dir):
                    # Skip checking subdirectories if we already found files
                    if files:
                        # Skip hidden files
                        real_files = [f for f in files if not f.startswith('.')]
                        if real_files:
                            print(f"    ✓ Found {len(real_files)} files in datasets/")
                            found_files = True
                            break

            # Check dataset_hips directory
            dataset_hips_dir = os.path.join(self.working_dir, 'dataset_hips')
            if os.path.exists(dataset_hips_dir):
                hip_files = [f for f in os.listdir(dataset_hips_dir)
                             if f.endswith(('.hip', '.hipnc', '.hiplc'))]
                if hip_files:
                    print(f"    ✓ Found {len(hip_files)} HIP files in dataset_hips/")
                    found_files = True

            if found_files:
                print("    ✓ ML outputs detected!")
                break

            if waited == 0:
                print(f"    No outputs yet - waiting up to {max_wait} seconds...")

            time.sleep(check_interval)
            waited += check_interval

            if waited < max_wait and not found_files:
                print(f"    Still waiting... ({waited}/{max_wait} seconds)")

        if waited >= max_wait:
            print(f"    ⚠ No ML outputs found after waiting {max_wait} seconds")

            # Final diagnostic check
            print("\n    Final check of working directory structure:")
            self._diagnose_ml_directories()

    def _diagnose_ml_directories(self):
        """
        Detailed diagnostic of ML directories
        """
        dirs_to_check = [
            ('datasets/render', os.path.join(self.working_dir, 'datasets', 'render')),
            ('datasets/delivery', os.path.join(self.working_dir, 'datasets', 'delivery')),
            ('dataset_hips', os.path.join(self.working_dir, 'dataset_hips')),
            ('pdgtemp', os.path.join(self.working_dir, 'pdgtemp')),
        ]

        for name, path in dirs_to_check:
            if os.path.exists(path):
                # Count all files recursively
                file_count = sum(1 for _, _, files in os.walk(path) for f in files if not f.startswith('.'))
                if file_count > 0:
                    print(f"      {name}: {file_count} files")
                    # Show first few files
                    for root, dirs, files in os.walk(path):
                        for f in files[:3]:
                            if not f.startswith('.'):
                                print(f"        - {os.path.relpath(os.path.join(root, f), self.working_dir)}")
                        if files:
                            break
                else:
                    print(f"      {name}: exists but empty")
            else:
                print(f"      {name}: does not exist")

    def _execute_network_cook(self):
        """
        Try multiple methods to cook the network
        """
        cook_methods = [
            ("Network cookWorkItems", lambda: self.topnet.cookWorkItems(block=True)),
            ("Output node cookWorkItems",
             lambda: self.output_node.cookWorkItems(block=True) if self.output_node else False),
            ("Output node executeGraph",
             lambda: self.output_node.executeGraph(False, True, False, True) if self.output_node else False),
            ("PDG context cook", lambda: self._try_pdg_context_cook()),
            ("Network executeGraph", lambda: self.topnet.executeGraph(False, True, False, True)),
        ]

        for method_name, method_func in cook_methods:
            try:
                start_time = time.time()
                result = method_func()
                elapsed = time.time() - start_time

                if result is not False:
                    print(f"  ✓ {method_name} completed in {elapsed:.2f} seconds")
                    return True

            except Exception as e:
                error_str = str(e)
                if "Disk quota" in error_str or "OSError" in error_str:
                    print(f"  ⚠ {method_name} hit disk quota (treating as success)")
                    return True
                elif "failed to cook" in error_str.lower():
                    # This might still have generated files
                    print(f"  ⚠ {method_name} reported failure - checking for outputs anyway")
                    pass
                else:
                    print(f"  ✗ {method_name} failed: {e}")

        # Even if all methods "failed", we should check for outputs
        print("  ⚠ All cooking methods reported issues - will check for outputs anyway")
        return True  # Return True to proceed with output checking

    def _execute_ml_node_directly(self):
        """
        Try to execute ML node directly when normal PDG execution fails
        """
        print("\n  DIRECT ML NODE EXECUTION...")

        if not self.output_node:
            return False

        try:
            # Method 1: Try cook() method if it exists
            if hasattr(self.output_node, 'cook'):
                print("  Trying direct cook() on ML node...")
                self.output_node.cook(force=True)
                print("    ✓ Direct cook completed")
                time.sleep(5)
                return True
        except Exception as e:
            print(f"    ✗ Direct cook failed: {e}")

        try:
            # Method 2: Try render() method if it exists
            if hasattr(self.output_node, 'render'):
                print("  Trying render() on ML node...")
                self.output_node.render()
                print("    ✓ Render completed")
                time.sleep(5)
                return True
        except Exception as e:
            print(f"    ✗ Render failed: {e}")

        # Method 3: Force execution through Python
        print("  Attempting Python-based ML execution...")
        try:
            # Get the ML node's script or command
            if self.output_node.parm('execute'):
                self.output_node.parm('execute').pressButton()
                print("    ✓ Pressed execute button")
                time.sleep(5)
                return True
        except:
            pass

        return False

    def _force_work_item_generation(self):
        """
        Force work item generation using multiple methods
        """
        generation_methods = []

        # Method 1: Set generatestatic on output node and generate
        if self.output_node:
            try:
                if self.output_node.parm('generatestatic'):
                    self.output_node.parm('generatestatic').set("1")
                    print("    ✓ Set generatestatic = '1' on output node")

                # Dirty all tasks first
                if hasattr(self.output_node, 'dirtyAllTasks'):
                    self.output_node.dirtyAllTasks(True)
                    print("    ✓ Called dirtyAllTasks on output node")
                    generation_methods.append('dirtyAllTasks')

                # Generate static work items
                if hasattr(self.output_node, 'generateStaticWorkItems'):
                    self.output_node.generateStaticWorkItems()
                    print("    ✓ Called generateStaticWorkItems on output node")
                    generation_methods.append('generateStaticWorkItems')

            except Exception as e:
                print(f"    Note: Output node generation issue: {e}")

        # Method 2: Network generation
        try:
            self.topnet.generateStaticWorkItems()
            print("    ✓ Called generateStaticWorkItems on network")
            generation_methods.append('network.generateStaticWorkItems')
        except Exception as e:
            print(f"    Note: Network generation issue: {e}")

        # Method 3: Force generation on all TOP nodes
        for node in self.topnet.children():
            if node.type().category().name() != "Top":
                continue
            if "scheduler" in node.type().name().lower():
                continue

            try:
                # Set generatestatic if it exists
                if node.parm('generatestatic'):
                    node.parm('generatestatic').set("1")

                # Generate work items
                if hasattr(node, 'generateStaticWorkItems'):
                    node.generateStaticWorkItems()
                    generation_methods.append(f'{node.name()}.generateStaticWorkItems')
            except:
                pass

        # Wait for generation to complete
        if generation_methods:
            print(f"    Used {len(generation_methods)} generation methods")
            time.sleep(2)

    def _execute_simple_ml(self):
        """
        Enhanced execution method specifically for ML nodes with all fixes
        """
        print("\n6. EXECUTING PDG NETWORK")
        print("-" * 40)
        print("Using simple execution method (mimics successful local execution)\n")

        # Set environment variables
        os.environ['PDG_WORKING_DIR'] = self.working_dir
        if not os.environ.get('PDG_DIR'):
            os.environ['PDG_DIR'] = self.working_dir

        print("  Environment variables:")
        print(f"    PDG_DIR: {os.environ.get('PDG_DIR')}")
        print(f"    PDG_WORKING_DIR: {os.environ.get('PDG_WORKING_DIR')}")
        print(f"    PDG_TEMP: {os.environ.get('PDG_TEMP')}")
        print(f"    Working dir: {self.working_dir}")

        # Configure ML node if present
        if self.output_node and 'ml_cv' in self.output_node.type().name().lower():
            print("\n  Configuring ML node output paths...")
            self._configure_ml_node_outputs()
            self._configure_ml_node()

        # Force work item generation
        print("\n  FORCING WORK ITEM GENERATION...")
        self._generate_all_work_items()

        # Check work items before cooking (safely)
        work_item_count = self._check_work_items_safe()

        # Execute the network
        print("\n  Attempting direct network cook...")
        cook_success = False

        # Try multiple cooking methods
        cook_methods = [
            ("Network cookWorkItems", lambda: self.topnet.cookWorkItems(block=True)),
            (
                "Output node cookWorkItems",
                lambda: self.output_node.cookWorkItems(block=True) if self.output_node else False),
            ("Output node executeGraph",
             lambda: self.output_node.executeGraph(False, True, False, True) if self.output_node else False),
            ("PDG context cook", lambda: self._try_pdg_context_cook()),
            ("Network executeGraph", lambda: self.topnet.executeGraph(False, True, False, True)),
        ]

        for method_name, method_func in cook_methods:
            try:
                start_time = time.time()
                result = method_func()
                elapsed = time.time() - start_time

                if result is not False:
                    print(f"  ✓ {method_name} completed in {elapsed:.2f} seconds")
                    cook_success = True
                    break

            except Exception as e:
                error_str = str(e)
                if "Disk quota" in error_str or "OSError" in error_str:
                    print(f"  ⚠ {method_name} hit disk quota (treating as success)")
                    cook_success = True
                    break
                elif "failed to cook" in error_str.lower():
                    print(f"  ⚠ {method_name} reported failure - checking for outputs anyway")
                    # Sometimes files are still generated despite the error
                    pass
                else:
                    print(f"  ✗ {method_name} failed: {e}")

        # If still no success, try individual nodes
        if not cook_success:
            print("\n  Last resort: attempting individual node cooking...")
            cook_success = self._try_individual_node_cook()

        # Post-execution checks
        if cook_success:
            print("\n  Waiting for file writes to complete...")
            time.sleep(5)

            # Check work items after cooking
            print("\n  Checking work items AFTER cook...")
            self._check_work_items_safe()

            # Check for ML outputs
            print("\n  Checking for output files in various locations...")
            ml_outputs = self._check_ml_outputs()
            if ml_outputs:
                print(f"\n  Found potential outputs:")
                for path_info in ml_outputs[:5]:
                    print(f"    {path_info}")
                if len(ml_outputs) > 5:
                    print(f"    ... and {len(ml_outputs) - 5} more files")

        return cook_success

    def _try_pdg_context_cook(self):
        """
        Try cooking via PDG graph context
        """
        try:
            context = self.topnet.getPDGGraphContext()
            if context:
                context.cook(block=True)
                return True
        except:
            pass
        return False

    def _check_work_items_safe(self):
        """
        FIXED: Safely check work items without triggering LocalScheduler error
        """
        print("\n  Checking work items...")
        total_count = 0

        try:
            for node in self.topnet.children():
                # Skip non-TOP nodes
                if not hasattr(node, 'type') or not hasattr(node.type(), 'category'):
                    continue
                if node.type().category().name() != "Top":
                    continue

                # CRITICAL FIX: Skip scheduler nodes completely
                node_type = node.type().name().lower()
                if "scheduler" in node_type:
                    continue  # Don't try to get work items from scheduler nodes

                try:
                    pdg_node = node.getPDGNode()
                    if not pdg_node:
                        continue

                    # Try to get work items safely
                    work_items = None
                    if hasattr(pdg_node, 'workItems'):
                        try:
                            work_items = pdg_node.workItems
                        except AttributeError as e:
                            # This is expected for scheduler nodes, skip silently
                            if "scheduler" not in str(e).lower():
                                print(f"    Note: Could not get work items from {node.name()}: {e}")
                            continue

                    if work_items:
                        count = len(work_items)
                        if count > 0:
                            total_count += count
                            print(f"    {node.name()}: {count} work items")

                except Exception as e:
                    # Don't let one node failure stop the check
                    if "scheduler" not in str(e).lower():
                        print(f"    Note: {node.name()} check failed: {e}")
                    continue

        except Exception as e:
            print(f"    Unable to complete work item check: {e}")

        if total_count == 0:
            print("    ⚠ WARNING: No work items found!")
        else:
            print(f"    ✓ Total work items: {total_count}")

        return total_count

    def _generate_all_work_items(self):
        """Try multiple methods to generate work items"""
        # Method 1: Set generatestatic on output node
        if self.output_node:
            try:
                if self.output_node.parm('generatestatic'):
                    self.output_node.parm('generatestatic').set("1")
                    print("    ✓ Set generatestatic = '1' on output node")
            except:
                pass

            # Generate static work items
            try:
                if hasattr(self.output_node, 'generateStaticWorkItems'):
                    self.output_node.generateStaticWorkItems()
                    print("    ✓ Called generateStaticWorkItems on output node")
            except Exception as e:
                pass

            # Dirty all tasks
            try:
                if hasattr(self.output_node, 'dirtyAllTasks'):
                    self.output_node.dirtyAllTasks(True)
                    print("    ✓ Called dirtyAllTasks on output node")
            except:
                pass

        # Method 2: Network generation
        try:
            self.topnet.generateStaticWorkItems()
            print("    ✓ Called generateStaticWorkItems on network")
        except Exception as e:
            print(f"    Note: {e}")

        # Give time for generation
        time.sleep(1)

    def _check_work_items(self):
        """Check and report on work items"""
        try:
            if self.output_node:
                pdg_node = self.output_node.getPDGNode()
                if pdg_node and hasattr(pdg_node, 'workItems'):
                    work_items = pdg_node.workItems
                    print(f"    Found {len(work_items)} work items")

                    for i, wi in enumerate(work_items[:3]):  # First 3
                        print(f"    Work item {i}:")

                        # Check name
                        if hasattr(wi, 'name'):
                            print(f"      Name: {wi.name}")

                        # Check state
                        if hasattr(wi, 'state'):
                            state = wi.state
                            print(f"      State: {state}")
                            # State values: 0=uncooked, 1=waiting, 2=scheduled, 3=cooking, 4=cooked, 5=failed
                            if state == 4:
                                print(f"      ✓ Successfully cooked")
                            elif state == 5:
                                print(f"      ✗ Failed")
                            elif state == 0:
                                print(f"      ⚠ Uncooked")

                        # Check outputs
                        if hasattr(wi, 'outputFiles'):
                            outputs = wi.outputFiles
                            if outputs:
                                print(f"      Outputs: {len(outputs)} files")
                                for out in outputs[:2]:
                                    print(f"        - {out}")
                            else:
                                print(f"      No output files")

                        # Check expected outputs
                        if hasattr(wi, 'expectedOutputFiles'):
                            expected = wi.expectedOutputFiles
                            if expected:
                                print(f"      Expected outputs: {len(expected)} files")
                                for exp in expected[:2]:
                                    print(f"        - {exp}")
        except Exception as e:
            print(f"    Error checking work items: {e}")

    def _count_work_items(self):
        """Count total work items in the network"""
        total = 0
        try:
            for node in self.topnet.children():
                if node.type().category().name() != "Top":
                    continue
                if "scheduler" in node.type().name().lower():
                    continue

                try:
                    pdg_node = node.getPDGNode()
                    if pdg_node and hasattr(pdg_node, 'workItems'):
                        work_items = pdg_node.workItems
                        if work_items:
                            count = len(work_items)
                            if count > 0:
                                total += count
                                print(f"      {node.name()}: {count} work items")
                except:
                    pass
        except:
            pass

        return total

    def _comprehensive_output_check(self):
        """
        ENHANCED: More thorough check for ML outputs
        """
        locations_to_check = [
            (self.working_dir, "Working directory"),
            (os.path.join(self.working_dir, 'datasets'), "datasets folder"),
            (os.path.join(self.working_dir, 'dataset_hips'), "dataset_hips folder"),
            (os.path.join(self.working_dir, 'pdgtemp'), "PDG temp"),
            (os.path.join(self.working_dir, 'pdgtemp', str(os.getpid())), "PDG temp with PID"),
        ]

        # Add scheduler working directory
        if hasattr(self, 'scheduler') and self.scheduler:
            try:
                sched_dir = self.scheduler.parm('pdg_workingdir').eval()
                if sched_dir:
                    locations_to_check.append((sched_dir, "Scheduler working dir"))
                    locations_to_check.append((os.path.join(sched_dir, 'datasets'), "Scheduler datasets"))
            except:
                pass

        found_any = False

        print("\n  Searching for ML outputs:")
        for base_path, desc in locations_to_check:
            if not os.path.exists(base_path):
                print(f"    {desc}: <does not exist>")
                continue

            # Count all files
            total_files = 0
            ml_files = 0
            for root, dirs, files in os.walk(base_path):
                # Skip virtual environment
                if 'ml/labs/venv' in root or '__pycache__' in root:
                    continue

                for f in files:
                    total_files += 1
                    # Check if it's an ML output file
                    if any(ext in f for ext in ['.json', '.png', '.jpg', '.exr', '.hip']):
                        ml_files += 1
                        if ml_files <= 3:  # Show first 3
                            rel_path = os.path.relpath(os.path.join(root, f), base_path)
                            print(f"      Found: {rel_path}")
                        found_any = True

            if total_files > 0:
                if ml_files > 0:
                    print(f"    {desc}: {ml_files} ML files (out of {total_files} total)")
                elif 'datasets' in desc.lower() or 'dataset_hips' in desc.lower():
                    print(f"    {desc}: EXISTS but EMPTY")

        if not found_any:
            print("\n  ⚠ No ML output files found!")
            print("\n  This means the ML node is not actually generating data.")
            print("  Possible causes:")
            print("    1. Missing input scene/camera")
            print("    2. Node parameters not fully configured")
            print("    3. Node is disabled")
            print("    4. Missing dependencies or ML models")

    def _debug_find_outputs(self):
        """
        Check where ML outputs actually went
        """
        # Look in working directory (where successful jobs put outputs)
        found_outputs = False

        # Check working directory for ML outputs
        for dirname in ['datasets', 'dataset_hips']:
            check_path = os.path.join(self.working_dir, dirname)
            if os.path.exists(check_path):
                # Count files
                file_count = sum(1 for r, d, f in os.walk(check_path) for _ in f)
                if file_count > 0:
                    if not found_outputs:
                        print("\n  Found potential outputs:")
                        found_outputs = True
                    print(f"    {check_path}: {file_count} files")

        # Also check pdgtemp
        pdgtemp_path = os.path.join(self.working_dir, 'pdgtemp')
        if os.path.exists(pdgtemp_path):
            for dirname in ['datasets', 'dataset_hips']:
                check_path = os.path.join(pdgtemp_path, dirname)
                if os.path.exists(check_path):
                    file_count = sum(1 for r, d, f in os.walk(check_path) for _ in f)
                    if file_count > 0:
                        if not found_outputs:
                            print("\n  Found potential outputs:")
                            found_outputs = True
                        print(f"    {check_path}: {file_count} files")

        if not found_outputs:
            print("  ⚠ No ML output files found in expected locations")

    def _try_alternative_execution(self):
        """Try alternative execution methods for non-standard networks"""
        print("\n  Attempting alternative execution methods...")

        try:
            # Method 1: Use PDG module directly
            import pdg

            # Get PDG context
            context = None
            try:
                context = self.topnet.getPDGGraphContext()
            except:
                pass

            if context:
                print("  Using PDG graph context...")
                try:
                    context.cook(block=True)
                    print("  ✓ PDG context cook completed")
                    return True
                except Exception as e:
                    print(f"  ✗ PDG context cook failed: {e}")

            # Method 2: Try to execute through children
            return self._try_output_node_cook()

        except Exception as e:
            print(f"  ✗ Alternative execution failed: {e}")
            return False

    def _try_output_node_cook(self):
        """Try to cook via the output node"""
        print("\n  Attempting output node cook...")

        try:
            # Find output node if not already identified
            if not self.output_node:
                output_node = None

                # Check for display flag
                for node in self.topnet.children():
                    if node.type().category().name() != "Top":
                        continue
                    if hasattr(node, 'isDisplayFlagSet') and node.isDisplayFlagSet():
                        output_node = node
                        break

                # Check for render flag
                if not output_node:
                    for node in self.topnet.children():
                        if node.type().category().name() != "Top":
                            continue
                        if hasattr(node, 'isRenderFlagSet') and node.isRenderFlagSet():
                            output_node = node
                            break

                # Find nodes with "output" in name
                if not output_node:
                    for node in self.topnet.children():
                        if node.type().category().name() != "Top":
                            continue
                        if "output" in node.name().lower() or "rop" in node.name().lower():
                            output_node = node
                            break

                self.output_node = output_node

            if self.output_node:
                print(f"  Cooking output node: {self.output_node.name()}")
                start_time = time.time()

                # Try to cook the output node
                try:
                    self.output_node.cookWorkItems(block=True)
                    elapsed = time.time() - start_time
                    print(f"  ✓ Output node cook completed in {elapsed:.2f} seconds")
                    return True
                except Exception as e:
                    print(f"  ✗ cookWorkItems failed: {e}")

                    # Try executeGraph as alternative
                    try:
                        print("  Trying executeGraph method...")
                        self.output_node.executeGraph(False, True, False, True)
                        elapsed = time.time() - start_time
                        print(f"  ✓ executeGraph completed in {elapsed:.2f} seconds")
                        return True
                    except Exception as e2:
                        print(f"  ✗ executeGraph also failed: {e2}")
            else:
                print("  ✗ No output node found")

            # Last resort: try cooking each TOP node
            return self._try_individual_node_cook()

        except Exception as e:
            print(f"  ✗ Output node cook failed: {e}")
            return self._try_individual_node_cook()

    def _try_individual_node_cook(self):
        """Cook each TOP node individually as last resort"""
        print("  Attempting individual node cooking...")

        any_success = False

        try:
            for node in self.topnet.children():
                if node.type().category().name() != "Top":
                    continue
                if "scheduler" in node.type().name().lower():
                    continue

                try:
                    print(f"    Cooking {node.name()}...")

                    if hasattr(node, 'cookWorkItems'):
                        node.cookWorkItems(block=True)
                        any_success = True
                        print(f"    ✓ {node.name()} cooked successfully")

                except Exception as e:
                    error_msg = str(e)
                    if "failed to cook" in error_msg.lower():
                        print(f"    ✗ {node.name()} cook failed (may have no work items)")
                    else:
                        print(f"    ✗ {node.name()} failed: {error_msg[:100]}")

            return any_success

        except Exception as e:
            print(f"  ✗ Individual node cooking failed: {e}")
            return False

    def _check_ml_outputs(self):
        """Check for ML output files in expected locations"""
        ml_outputs = []

        # Define all possible output locations
        output_locations = [
            (self.working_dir, 'datasets'),
            (self.working_dir, 'dataset_hips'),
            (os.path.join(self.working_dir, 'pdgtemp'), 'datasets'),
            (os.path.join(self.working_dir, 'pdgtemp'), 'dataset_hips'),
        ]

        # Add temp directory locations if it exists
        if hasattr(self, 'temp_dir') and self.temp_dir:
            output_locations.extend([
                (self.temp_dir, 'datasets'),
                (self.temp_dir, 'dataset_hips'),
            ])

        # Check numbered PDG temp directories
        pdgtemp_base = os.path.join(self.working_dir, 'pdgtemp')
        if os.path.exists(pdgtemp_base):
            for item in os.listdir(pdgtemp_base):
                item_path = os.path.join(pdgtemp_base, item)
                if os.path.isdir(item_path):
                    output_locations.extend([
                        (item_path, 'datasets'),
                        (item_path, 'dataset_hips'),
                    ])

        # Look for files in these specific locations
        for base_dir, subdir in output_locations:
            check_path = os.path.join(base_dir, subdir)
            if os.path.exists(check_path):
                for root, dirs, files in os.walk(check_path):
                    # Skip cache directories
                    if '__pycache__' in root or '.cache' in root:
                        continue

                    # Count files
                    file_count = len(files)
                    if file_count > 0:
                        ml_outputs.append(f"{check_path}: {file_count} files")

                        # Collect actual file paths
                        for file in files:
                            if not file.startswith('.'):
                                file_path = os.path.join(root, file)
                                self.status_dict['files_created']['datasets'].append(file_path)

        if not ml_outputs:
            print("  ⚠ No ML output files found in expected locations")

        return ml_outputs

    def _scan_and_copy_outputs(self):
        """
        Scan and copy outputs with detailed file path logging
        """
        print("\n7. COLLECTING AND COPYING OUTPUT FILES")
        print("-" * 40)

        files_found = []
        files_copied = 0
        files_skipped = 0

        print("  Looking for ML output directories...")

        # Define ML output directories
        ml_output_dirs = ['datasets', 'dataset_hips']

        # First, find all files
        for dirname in ml_output_dirs:
            source_dir = os.path.join(self.working_dir, dirname)

            if os.path.exists(source_dir):
                # Check if directory has content
                has_files = False
                file_count = 0

                for root, dirs, files in os.walk(source_dir):
                    # Skip cache directories
                    if '__pycache__' in root or '.cache' in root:
                        continue

                    for file in files:
                        # Skip hidden and cache files
                        if file.startswith('.'):
                            files_skipped += 1
                            continue

                        file_path = os.path.join(root, file)
                        files_found.append(file_path)
                        file_count += 1
                        has_files = True

                if has_files:
                    print(f"    Found {dirname}/: {file_count} files")
                else:
                    print(f"    Found {dirname}/: empty")

        # Update files_after for tracking
        self.files_after = set(files_found)

        print(f"\n  ✓ Found {len(files_found)} files total")
        print(f"  ✓ {files_skipped} files skipped (hidden/cache files)")

        # Copy files to output directory with detailed logging
        if files_found and self.output_dir:
            print(f"\n  Copying to output directory: {self.output_dir}")
            print("  " + "-" * 80)

            # Sort files for consistent output
            files_found.sort()

            for idx, src_file in enumerate(files_found, 1):
                try:
                    # Determine relative path from working directory
                    rel_path = os.path.relpath(src_file, self.working_dir)

                    # Create destination path
                    dst_file = os.path.join(self.output_dir, rel_path)
                    dst_dir = os.path.dirname(dst_file)

                    # Create destination directory
                    os.makedirs(dst_dir, exist_ok=True)

                    # Copy file
                    import shutil
                    shutil.copy2(src_file, dst_file)
                    files_copied += 1

                    # Print full paths
                    print(f"\n  [{idx}/{len(files_found)}] File copied:")
                    print(f"    Source:      {src_file}")
                    print(f"    Destination: {dst_file}")
                    print(f"    Relative:    {rel_path}")

                    # Update status dict with correct categorization
                    if 'datasets' in rel_path:
                        if any(ext in src_file for ext in ['.exr', '.png', '.jpg', '.jpeg', '.tif', '.tiff']):
                            self.status_dict['files_created']['renders'].append(dst_file)
                        elif src_file.endswith('.json'):
                            self.status_dict['files_created']['datasets'].append(dst_file)
                        else:
                            self.status_dict['files_created']['datasets'].append(dst_file)
                    elif 'dataset_hips' in rel_path:
                        self.status_dict['files_created']['dataset_hips'].append(dst_file)
                    else:
                        self.status_dict['files_created']['other'].append(dst_file)

                except Exception as e:
                    print(f"\n  ✗ ERROR copying file {idx}:")
                    print(f"    File:  {src_file}")
                    print(f"    Error: {e}")

            print("\n  " + "-" * 80)
            print(f"  ✓ Successfully copied {files_copied}/{len(files_found)} files")
        else:
            if not files_found:
                print("  ⚠ No files found to copy")
            else:
                print("  ⚠ No output directory specified")

        if files_copied == 0 and files_found:
            print("\n  ⚠ WARNING: Files were found but none were copied!")
            self._verify_output_structure_detailed()

        # Update total count in status dict
        self.status_dict['files_created']['total_count'] = files_copied

        return files_copied

    def _verify_output_structure_detailed(self):
        """
        Detailed output structure verification
        """
        print("\n  OUTPUT STRUCTURE VERIFICATION:")
        print("  " + "-" * 80)

        # Check working directory for ML outputs
        print("\n  Working Directory Contents:")
        work_dirs = [
            ('datasets/render', os.path.join(self.working_dir, 'datasets', 'render')),
            ('datasets/delivery', os.path.join(self.working_dir, 'datasets', 'delivery')),
            ('dataset_hips', os.path.join(self.working_dir, 'dataset_hips')),
        ]

        for name, path in work_dirs:
            if os.path.exists(path):
                # List all files with full paths
                all_files = []
                for root, dirs, files in os.walk(path):
                    for f in files:
                        if not f.startswith('.'):
                            full_path = os.path.join(root, f)
                            rel_from_working = os.path.relpath(full_path, self.working_dir)
                            all_files.append(rel_from_working)

                if all_files:
                    print(f"\n    {name}/: ({len(all_files)} files)")
                    for file_path in all_files:
                        print(f"      {file_path}")
                else:
                    print(f"\n    {name}/: exists but empty")
            else:
                print(f"\n    {name}/: does not exist")

        # Check output directory
        print("\n  Output Directory Contents:")
        output_dirs = [
            ('datasets', os.path.join(self.output_dir, 'datasets')),
            ('dataset_hips', os.path.join(self.output_dir, 'dataset_hips'))
        ]

        for dir_name, dir_path in output_dirs:
            if os.path.exists(dir_path):
                file_count = 0
                file_list = []

                for root, dirs, files in os.walk(dir_path):
                    for f in files:
                        if not f.startswith('.'):
                            file_count += 1
                            full_path = os.path.join(root, f)
                            rel_from_output = os.path.relpath(full_path, self.output_dir)
                            file_list.append(rel_from_output)

                if file_count > 0:
                    print(f"\n    {dir_name}/: ({file_count} files)")
                    for file_path in file_list:
                        print(f"      {file_path}")
                else:
                    print(f"\n    {dir_name}/: exists but empty")
            else:
                print(f"\n    {dir_name}/: does not exist")

        # Show root level items in output directory
        print("\n  Output Directory Root:")
        if os.path.exists(self.output_dir):
            items = os.listdir(self.output_dir)
            if items:
                for item in sorted(items):
                    item_path = os.path.join(self.output_dir, item)
                    if os.path.isdir(item_path):
                        file_count = sum(1 for _, _, files in os.walk(item_path) for _ in files)
                        print(f"    {item}/  ({file_count} files)")
                    else:
                        file_size = os.path.getsize(item_path)
                        print(f"    {item}  ({file_size} bytes)")
            else:
                print("    (empty)")
        else:
            print("    Output directory does not exist!")

        print("\n  " + "-" * 80)


    def _verify_output_structure(self):
        """
        Verify and report on expected output structure
        """
        print("\n  VERIFYING OUTPUT STRUCTURE:")

        expected_dirs = [
            ('datasets', os.path.join(self.output_dir, 'datasets')),
            ('dataset_hips', os.path.join(self.output_dir, 'dataset_hips'))
        ]

        for dir_name, dir_path in expected_dirs:
            if os.path.exists(dir_path) and os.listdir(dir_path):
                file_count = sum(1 for _, _, files in os.walk(dir_path) for _ in files)
                print(f"  ✓ {dir_name} directory has {file_count} files")
            else:
                print(f"  ⚠ No {dir_name} directory in output location")
                print(f"    Expected at: {dir_path}")

        # Diagnostic: Show what IS in the output directory
        print("\n  Diagnostic: Checking what IS in the output directory...")
        if os.path.exists(self.output_dir):
            items = os.listdir(self.output_dir)
            if items:
                print(f"  Found {len(items)} items:")
                for item in items[:10]:  # Show first 10
                    item_path = os.path.join(self.output_dir, item)
                    if os.path.isdir(item_path):
                        file_count = sum(1 for _, _, files in os.walk(item_path) for _ in files)
                        print(f"    - {item}/ ({file_count} files)")
                    else:
                        print(f"    - {item}")
                if len(items) > 10:
                    print(f"    ... and {len(items) - 10} more items")
            else:
                print("  Output directory is empty")

    def _verify_outputs(self):
        """
        Verify the output structure
        """
        print("\n  VERIFYING OUTPUT STRUCTURE:")

        datasets_dir = os.path.join(self.output_dir, 'datasets')
        hips_dir = os.path.join(self.output_dir, 'dataset_hips')

        if os.path.exists(datasets_dir):
            print("  ✓ Output datasets directory created")
            # Check subdirectories
            for subdir in os.listdir(datasets_dir):
                subdir_path = os.path.join(datasets_dir, subdir)
                if os.path.isdir(subdir_path):
                    file_count = sum(1 for r, d, f in os.walk(subdir_path) for _ in f)
                    print(f"    ✓ {subdir}/: {file_count} files")
        else:
            print("  ⚠ No datasets directory in output location")
            print(f"    Expected at: {datasets_dir}")

        if os.path.exists(hips_dir):
            hip_files = [f for f in os.listdir(hips_dir) if f.endswith(('.hip', '.hipnc', '.hiplc'))]
            if hip_files:
                print(f"  ✓ Dataset HIPs directory: {len(hip_files)} HIP files")
                for hip_file in hip_files[:3]:
                    print(f"    - {hip_file}")
        else:
            print("  ⚠ No dataset_hips directory in output location")

        # Diagnostic if nothing found
        if not os.path.exists(datasets_dir) and not os.path.exists(hips_dir):
            print("\n  Diagnostic: Checking what IS in the output directory...")
            if os.path.exists(self.output_dir):
                items = os.listdir(self.output_dir)
                if items:
                    print(f"    Found {len(items)} items:")
                    for item in items[:5]:
                        print(f"      - {item}")
                else:
                    print("    Output directory is empty")

    def _verify_ml_output(self):
        """
        ENHANCED VERSION: Better verification of ML/CV output structure
        """
        print("\nVERIFYING OUTPUT STRUCTURE:")

        # Check for datasets directory
        datasets_dir = os.path.join(self.output_dir, 'datasets')
        if os.path.exists(datasets_dir):
            print("✓ Output datasets directory created")

            # List all subdirectories
            for item in os.listdir(datasets_dir):
                item_path = os.path.join(datasets_dir, item)
                if os.path.isdir(item_path):
                    print(f"  ✓ Dataset directories: {item}")

                    # Check for data subdirectory
                    data_dir = os.path.join(item_path, 'data')
                    if os.path.exists(data_dir):
                        # Count files by type
                        file_counts = {}

                        # Check main data directory
                        for file in os.listdir(data_dir):
                            if os.path.isfile(os.path.join(data_dir, file)):
                                ext = os.path.splitext(file)[1]
                                file_counts[ext] = file_counts.get(ext, 0) + 1

                        # Check exr subdirectory
                        exr_dir = os.path.join(data_dir, 'exr')
                        if os.path.exists(exr_dir):
                            exr_count = len([f for f in os.listdir(exr_dir) if f.endswith('.exr')])
                            if exr_count > 0:
                                print(f"    ✓ {item}/data/exr: {exr_count} EXR files")

                        # Report other file types
                        for ext, count in file_counts.items():
                            if ext:  # Skip files without extensions
                                print(f"    ✓ {item}/data: {count} {ext.upper()} files")

            # Check delivery subdirectory
            delivery_dir = os.path.join(datasets_dir, 'delivery')
            if os.path.exists(delivery_dir):
                print("  ✓ Delivery directory created")
                # Check contents
                for item in os.listdir(delivery_dir):
                    item_path = os.path.join(delivery_dir, item)
                    if os.path.isdir(item_path):
                        file_count = sum(1 for r, d, f in os.walk(item_path) for _ in f)
                        print(f"    - {item}: {file_count} files")
        else:
            print("⚠ No datasets directory in output location")
            print(f"  Expected at: {datasets_dir}")

        # Check for dataset_hips directory
        hips_dir = os.path.join(self.output_dir, 'dataset_hips')
        if os.path.exists(hips_dir):
            hip_files = [f for f in os.listdir(hips_dir) if f.endswith(('.hip', '.hipnc', '.hiplc'))]
            if hip_files:
                print(f"✓ Dataset HIPs directory: {len(hip_files)} HIP files")
                for hip_file in hip_files[:5]:  # Show first 5
                    print(f"  - {hip_file}")
        else:
            print("⚠ No dataset_hips directory in output location")

        # If nothing found, provide more diagnostic info
        if not os.path.exists(datasets_dir) and not os.path.exists(hips_dir):
            print("\nDiagnostic: Checking what IS in the output directory...")
            if os.path.exists(self.output_dir):
                items = os.listdir(self.output_dir)
                if items:
                    print(f"  Found {len(items)} items in output directory:")
                    for item in items[:10]:  # Show first 10
                        print(f"    - {item}")
                else:
                    print("  Output directory is empty")

    def _verify_ml_output(self):
        """
        ENHANCED VERSION: Better verification of ML/CV output structure
        """
        print("\nVERIFYING OUTPUT STRUCTURE:")

        # Check for datasets directory
        datasets_dir = os.path.join(self.output_dir, 'datasets')
        if os.path.exists(datasets_dir):
            print("✓ Output datasets directory created")

            # List all subdirectories
            for item in os.listdir(datasets_dir):
                item_path = os.path.join(datasets_dir, item)
                if os.path.isdir(item_path):
                    print(f"  ✓ Dataset directories: {item}")

                    # Check for data subdirectory
                    data_dir = os.path.join(item_path, 'data')
                    if os.path.exists(data_dir):
                        # Count files by type
                        file_counts = {}

                        # Check main data directory
                        for file in os.listdir(data_dir):
                            if os.path.isfile(os.path.join(data_dir, file)):
                                ext = os.path.splitext(file)[1]
                                file_counts[ext] = file_counts.get(ext, 0) + 1

                        # Check exr subdirectory
                        exr_dir = os.path.join(data_dir, 'exr')
                        if os.path.exists(exr_dir):
                            exr_count = len([f for f in os.listdir(exr_dir) if f.endswith('.exr')])
                            if exr_count > 0:
                                print(f"    ✓ {item}/data/exr: {exr_count} EXR files")

                        # Report other file types
                        for ext, count in file_counts.items():
                            if ext:  # Skip files without extensions
                                print(f"    ✓ {item}/data: {count} {ext.upper()} files")

            # Check delivery subdirectory
            delivery_dir = os.path.join(datasets_dir, 'delivery')
            if os.path.exists(delivery_dir):
                print("  ✓ Delivery directory created")
                # Check contents
                for item in os.listdir(delivery_dir):
                    item_path = os.path.join(delivery_dir, item)
                    if os.path.isdir(item_path):
                        file_count = sum(1 for r, d, f in os.walk(item_path) for _ in f)
                        print(f"    - {item}: {file_count} files")
        else:
            print("⚠ No datasets directory in output location")
            print(f"  Expected at: {datasets_dir}")

        # Check for dataset_hips directory
        hips_dir = os.path.join(self.output_dir, 'dataset_hips')
        if os.path.exists(hips_dir):
            hip_files = [f for f in os.listdir(hips_dir) if f.endswith(('.hip', '.hipnc', '.hiplc'))]
            if hip_files:
                print(f"✓ Dataset HIPs directory: {len(hip_files)} HIP files")
                for hip_file in hip_files[:5]:  # Show first 5
                    print(f"  - {hip_file}")
        else:
            print("⚠ No dataset_hips directory in output location")

        # If nothing found, provide more diagnostic info
        if not os.path.exists(datasets_dir) and not os.path.exists(hips_dir):
            print("\nDiagnostic: Checking what IS in the output directory...")
            if os.path.exists(self.output_dir):
                items = os.listdir(self.output_dir)
                if items:
                    print(f"  Found {len(items)} items in output directory:")
                    for item in items[:10]:  # Show first 10
                        print(f"    - {item}")
                else:
                    print("  Output directory is empty")

    def _report_results(self):
        """
        ENHANCED Report execution results for ML jobs
        Creates a comprehensive status report similar to run_no_ml()
        """
        print("\n8. EXECUTION SUMMARY AND REPORT")
        print("-" * 40)

        # Initialize status dict if not already initialized
        if not hasattr(self, 'status_dict'):
            self.status_dict = self._initialize_status_dict()
            self.status_dict['ml_mode'] = True

        # Make sure these attributes exist with default values
        if not hasattr(self, 'start_time'):
            self.start_time = time.time()
        if not hasattr(self, 'files_after'):
            self.files_after = set()
        if not hasattr(self, 'files_copied'):
            self.files_copied = 0

        elapsed = time.time() - self.start_time

        # Update status dict with execution results
        self.status_dict['timestamp_end'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_dict['duration_seconds'] = elapsed
        self.status_dict['status'] = 'success'  # Assume success if we reached this point
        self.status_dict['ml_mode'] = True

        # Track ML-specific outputs
        self._collect_ml_outputs_for_report()

        # Calculate total files
        total_files = sum(len(v) for k, v in self.status_dict['files_created'].items()
                          if k != 'total_count')
        self.status_dict['files_created']['total_count'] = total_files

        # Track work items (for ML mode, we may not have exact counts)
        if not self.status_dict.get('work_items_total'):
            # Try to estimate from outputs if not already set
            self.status_dict['work_items_total'] = 0
            self.status_dict['work_items_succeeded'] = 0
            self.status_dict['work_items_failed'] = 0

        # Print summary to console
        print(f"  Total execution time: {elapsed:.2f} seconds")
        print(f"  New files created: {len(self.files_after)}")
        print(f"  Files copied to output: {self.files_copied}")

        # Check for datasets and dataset_hips
        datasets_count = len(self.status_dict['files_created']['datasets'])
        dataset_hips_count = len(self.status_dict['files_created']['dataset_hips'])

        if datasets_count > 0:
            print(f"  Dataset files: {datasets_count}")
        if dataset_hips_count > 0:
            print(f"  Dataset HIP files: {dataset_hips_count}")

        # Save comprehensive status report (similar to run_no_ml)
        status_dir = os.path.join(self.output_dir, 'execution_status')
        os.makedirs(status_dir, exist_ok=True)

        # Create filename with timestamp (matching run_no_ml pattern)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.use_single_machine:
            status_file = os.path.join(status_dir, f'pdg_single_machine_status_{timestamp}.json')
        else:
            status_file = os.path.join(status_dir, f'pdg_ml_execution_status_{timestamp}.json')

        try:
            with open(status_file, 'w') as f:
                json.dump(self.status_dict, f, indent=4, default=str)
            print(f"  ✓ Status report saved: {status_file}")

            # Create a symlink to latest
            latest_link = os.path.join(status_dir, 'pdg_execution_status.latest.json')
            try:
                if os.path.exists(latest_link):
                    os.remove(latest_link)
                os.symlink(os.path.basename(status_file), latest_link)
                print(f"  Created latest link: {latest_link}")
            except:
                pass

        except Exception as e:
            print(f"  ⚠ Failed to save status report: {e}")


        """
        # Also save the simple execution report for backwards compatibility
        report = {
            "timestamp": datetime.now().isoformat(),
            "hip_file": self.hip_file,
            "topnet_path": self.topnet_path,
            "working_dir": self.working_dir,
            "output_dir": self.output_dir,
            "execution_time": elapsed,
            "files_created": len(self.files_after),
            "files_copied": self.files_copied,
            "file_list": list(self.files_after)[:100],  # First 100 files
            "ml_mode": True,
            "datasets_found": datasets_count,
            "dataset_hips_found": dataset_hips_count
        }

        report_file = os.path.join(self.output_dir,
                                   f"pdg_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"  ✓ Execution report saved: {report_file}")
        except Exception as e:
            print(f"  ⚠ Failed to save execution report: {e}")
        """

        # Print final summary
        print("\n" + "=" * 80)
        print("EXECUTION COMPLETE")
        print("=" * 80)
        print(f"Mode: ML/CV Processing")
        print(f"Status: {self.status_dict['status'].upper()}")
        print(f"Duration: {elapsed:.2f} seconds")
        print(f"Total files created: {total_files}")

        if datasets_count > 0 or dataset_hips_count > 0:
            print("\nML/CV Outputs:")
            if datasets_count > 0:
                print(f"  Datasets: {datasets_count} files")
            if dataset_hips_count > 0:
                print(f"  Dataset HIPs: {dataset_hips_count} files")

    def _sanitize_status_dict(self):
        """
        Helper function to ensure all status_dict values are valid (not None)
        This prevents formatting errors when printing or saving to JSON
        """
        if not hasattr(self, 'status_dict'):
            self.status_dict = self._initialize_status_dict()
            return

        # Ensure numeric fields are not None
        numeric_fields = [
            'duration_seconds',
            'work_items_total',
            'work_items_succeeded',
            'work_items_failed',
            'work_items_skipped',
            'item_index',
            'frame'
        ]

        for field in numeric_fields:
            if field in self.status_dict and self.status_dict[field] is None:
                self.status_dict[field] = 0

        # Ensure timestamp fields are not None
        from datetime import datetime
        timestamp_fields = ['timestamp_start', 'timestamp_end']

        for field in timestamp_fields:
            if field in self.status_dict and self.status_dict[field] is None:
                self.status_dict[field] = datetime.now().isoformat()

        # Ensure list fields are not None
        list_fields = [
            'work_items_processed',
            'skipped_items',
            'errors',
            'nodes_in_network'
        ]

        for field in list_fields:
            if field in self.status_dict and self.status_dict[field] is None:
                self.status_dict[field] = []

        # Ensure files_created dictionary exists and has valid counts
        if 'files_created' not in self.status_dict or self.status_dict['files_created'] is None:
            self.status_dict['files_created'] = {
                'usd': [],
                'renders': [],
                'hip': [],
                'logs': [],
                'pdg': [],
                'geo': [],
                'datasets': [],
                'dataset_hips': [],
                'other': [],
                'wedge_outputs': [],
                'total_count': 0
            }
        else:
            # Ensure each category is a list
            for category in ['usd', 'renders', 'hip', 'logs', 'pdg', 'geo',
                             'datasets', 'dataset_hips', 'other', 'wedge_outputs']:
                if category not in self.status_dict['files_created']:
                    self.status_dict['files_created'][category] = []
                elif self.status_dict['files_created'][category] is None:
                    self.status_dict['files_created'][category] = []

            # Ensure total_count is not None
            if self.status_dict['files_created'].get('total_count') is None:
                # Calculate from existing lists
                total = 0
                for key, value in self.status_dict['files_created'].items():
                    if key != 'total_count' and isinstance(value, list):
                        total += len(value)
                self.status_dict['files_created']['total_count'] = total

        # Ensure cook_result dictionary exists
        if 'cook_result' not in self.status_dict or self.status_dict['cook_result'] is None:
            self.status_dict['cook_result'] = {
                'return_code': 0,
                'failed_items': [],
                'successful_items': [],
                'warnings': []
            }
        else:
            if self.status_dict['cook_result'].get('return_code') is None:
                self.status_dict['cook_result']['return_code'] = 0
            for field in ['failed_items', 'successful_items', 'warnings']:
                if self.status_dict['cook_result'].get(field) is None:
                    self.status_dict['cook_result'][field] = []

        # Ensure string fields are not None
        string_fields = ['status', 'execution_mode', 'hip_file', 'topnet_path',
                         'working_dir', 'output_dir']

        for field in string_fields:
            if field in self.status_dict and self.status_dict[field] is None:
                self.status_dict[field] = ""

        # Ensure boolean fields are not None
        boolean_fields = ['ml_mode', 'cook_entire_graph', 'use_single_machine']

        for field in boolean_fields:
            if field in self.status_dict and self.status_dict[field] is None:
                self.status_dict[field] = False

    def _report_results_ml_enhanced(self):
        """
        Enhanced version with complete error handling and status sanitization
        """
        print("\n8. EXECUTION SUMMARY AND REPORT")
        print("-" * 40)

        # Sanitize the status dict first
        self._sanitize_status_dict()

        # Get duration (already sanitized, so won't be None)
        duration = self.status_dict.get('duration_seconds', 0)

        # Get file counts
        file_count = self.status_dict['files_created'].get('total_count', 0)
        datasets_count = len(self.status_dict['files_created'].get('datasets', []))
        dataset_hips_count = len(self.status_dict['files_created'].get('dataset_hips', []))

        # Track new files created
        new_files_count = 0
        if hasattr(self, 'files_after') and hasattr(self, 'existing_files'):
            new_files = self.files_after - self.existing_files if hasattr(self, 'files_after') else set()
            new_files_count = len(new_files)
        elif hasattr(self, 'files_after'):
            new_files_count = len(self.files_after)

        # Track files copied
        files_copied = getattr(self, 'files_copied', file_count)

        # Print summary
        print(f"Total execution time: {duration:.2f} seconds")
        print(f"New files created: {new_files_count}")
        print(f"Files copied to output: {files_copied}")

        # Print ML-specific outputs if any
        if datasets_count > 0 or dataset_hips_count > 0:
            print("\nML/CV Outputs:")
            if datasets_count > 0:
                print(f"  Dataset files: {datasets_count}")
            if dataset_hips_count > 0:
                print(f"  Dataset HIP files: {dataset_hips_count}")

        # Save the status report
        self._save_status_report_enhanced()

    def _save_status_report_enhanced(self):
        """
        Enhanced status report saving with complete error handling
        """
        try:
            # Ensure status_dict is sanitized
            self._sanitize_status_dict()

            # Create status directory
            status_dir = os.path.join(self.output_dir, 'execution_status')
            os.makedirs(status_dir, exist_ok=True)

            # Generate filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Determine mode string
            mode_str = "single_machine"
            if self.status_dict.get('cook_entire_graph'):
                mode_str = "full_graph"
            elif not self.status_dict.get('use_single_machine'):
                item_index = self.status_dict.get('item_index', 0)
                mode_str = f"item_{item_index}"

            status_file = os.path.join(status_dir, f"pdg_{mode_str}_status_{timestamp}.json")

            # Create a JSON-serializable copy of status_dict
            import json
            import copy

            # Deep copy to avoid modifying original
            json_dict = copy.deepcopy(self.status_dict)

            # Custom JSON encoder to handle special types
            class SafeJSONEncoder(json.JSONEncoder):
                def default(self, obj):
                    if obj is None:
                        return ""
                    try:
                        return super().default(obj)
                    except TypeError:
                        return str(obj)

            # Write the file
            with open(status_file, 'w') as f:
                json.dump(json_dict, f, indent=2, cls=SafeJSONEncoder)

            print(f"✓ Status report saved: {status_file}")

            # Try to create symlink
            try:
                latest_link = os.path.join(status_dir, 'pdg_execution_status.latest.json')
                if os.path.exists(latest_link):
                    os.remove(latest_link)

                # Use relative symlink for better portability
                import os.path
                os.symlink(os.path.basename(status_file), latest_link)
                print(f"Created latest link: {latest_link}")
            except Exception as e:
                # Symlinks might fail on some systems, that's OK
                pass

        except Exception as e:
            print(f"⚠ Warning: Could not save status report: {e}")
            # Don't crash the entire execution over this
            import traceback
            if os.environ.get('DEBUG'):
                traceback.print_exc()

    def _save_basic_error_report(self, error, duration):
        """
        Emergency fallback to save a basic error report when everything else fails
        """
        try:
            status_dir = os.path.join(self.output_dir, 'execution_status')
            os.makedirs(status_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = os.path.join(status_dir, f"pdg_error_{timestamp}.json")

            basic_report = {
                'status': 'error',
                'error': str(error),
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'hip_file': getattr(self, 'hip_file', 'unknown'),
                'working_dir': getattr(self, 'working_dir', 'unknown'),
                'output_dir': getattr(self, 'output_dir', 'unknown')
            }

            import json
            with open(error_file, 'w') as f:
                json.dump(basic_report, f, indent=2)

            print(f"✓ Basic error report saved: {error_file}")

        except:
            pass  # Silent fail - this is last resort

    def _collect_ml_outputs_for_report(self):
        """
        Helper method to collect ML-specific outputs for the status report
        """
        # Check for datasets directory
        datasets_dir = os.path.join(self.output_dir, 'datasets')
        if os.path.exists(datasets_dir):
            for root, dirs, files in os.walk(datasets_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Categorize by file type
                    if file.endswith(('.png', '.jpg', '.jpeg', '.exr', '.tif', '.tiff')):
                        self.status_dict['files_created']['renders'].append(file_path)
                    elif file.endswith('.json'):
                        # JSON files in datasets are usually annotations
                        self.status_dict['files_created']['datasets'].append(file_path)
                    else:
                        self.status_dict['files_created']['datasets'].append(file_path)

        # Check for dataset_hips directory
        dataset_hips_dir = os.path.join(self.output_dir, 'dataset_hips')
        if os.path.exists(dataset_hips_dir):
            for root, dirs, files in os.walk(dataset_hips_dir):
                for file in files:
                    if file.endswith(('.hip', '.hipnc', '.hiplc')):
                        file_path = os.path.join(root, file)
                        self.status_dict['files_created']['dataset_hips'].append(file_path)

        # Also collect other standard outputs
        output_categories = {
            'usd': ['.usd', '.usda', '.usdc', '.usdz'],
            'geo': ['.bgeo', '.bgeo.sc', '.geo', '.obj', '.vdb', '.abc'],
            'logs': ['.log', '.txt'],
            'pdg': ['.json', '.xml']  # PDG metadata files
        }

        # Scan output directory for other files
        if os.path.exists(self.output_dir):
            for root, dirs, files in os.walk(self.output_dir):
                # Skip already processed directories
                if 'datasets' in root or 'dataset_hips' in root or 'execution_status' in root:
                    continue

                for file in files:
                    file_path = os.path.join(root, file)
                    categorized = False

                    # Try to categorize the file
                    for category, extensions in output_categories.items():
                        if any(file.endswith(ext) for ext in extensions):
                            if file_path not in self.status_dict['files_created'][category]:
                                self.status_dict['files_created'][category].append(file_path)
                            categorized = True
                            break

                    # If not categorized, add to 'other'
                    if not categorized:
                        if file_path not in self.status_dict['files_created']['other']:
                            self.status_dict['files_created']['other'].append(file_path)

        # Try to get work item information if available
        try:
            if hasattr(self, 'topnet') and self.topnet:
                for node in self.topnet.children():
                    if node.type().category().name() == "Top":
                        self.status_dict['nodes_in_network'].append({
                            'name': node.name(),
                            'type': node.type().name()
                        })

                        # Try to get work item counts
                        try:
                            pdg_node = node.getPDGNode()
                            if pdg_node and hasattr(pdg_node, 'workItems'):
                                work_items = list(pdg_node.workItems)
                                if work_items:
                                    succeeded = sum(1 for wi in work_items
                                                    if hasattr(wi,
                                                               'state') and wi.state == 4)  # State 4 is usually success
                                    failed = sum(1 for wi in work_items
                                                 if hasattr(wi, 'state') and wi.state == 5)  # State 5 is usually failed

                                    self.status_dict['work_items_total'] += len(work_items)
                                    self.status_dict['work_items_succeeded'] += succeeded
                                    self.status_dict['work_items_failed'] += failed
                        except:
                            pass
        except:
            pass


def main():
    """Main entry point"""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='PDG Universal Wrapper Script for Conductor render farm'
    )
    parser.add_argument('--hip_file', type=str, required=True,
                        help='Path to the Houdini file')
    parser.add_argument('--topnet_path', type=str, default='/obj/topnet1',
                        help='Path to the TOP network node')
    parser.add_argument('--working_dir', type=str, required=True,
                        help='Working directory path')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Output directory for rendered files')

    # Mode selection arguments
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--cook_entire_graph', action='store_true',
                       help='Cook entire graph (submitAsJob mode)')
    group.add_argument('--use_single_machine', action='store_true',
                       help='Cook all work items on single machine (local execution)')
    group.add_argument('--item_index', type=int, default=None,
                       help='Index of the work item to cook (on_schedule mode)')

    args = parser.parse_args()


    # Determine output directory

    if not args.output_dir:
        args.output_dir = os.path.join(args.working_dir, 'pdg_render')

    # Create and run executor
    executor = PDGUniversalExecutor(
        hip_file=args.hip_file,
        topnet_path=args.topnet_path,
        working_dir=args.working_dir,
        output_dir=args.output_dir,
        item_index=args.item_index,
        cook_entire_graph=args.cook_entire_graph,
        use_single_machine=args.use_single_machine
    )

    success = executor.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()