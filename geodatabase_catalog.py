# ---------------------------------------------------------------------------
# GEODATABASE INVENTORY SCRIPT (FINAL CLEAN)
#
# Scans all file geodatabases under a root directory and writes an inventory
# of their contents to an Excel file.
#
# Intended to be run from an ArcGIS Pro Python environment.
#
#
# NOTE ON FILE GEODATABASE DETECTION
#
# Environments where regular files are mistakenly named with a .gdb extension
# can cause ArcGIS Pro and ArcPy to behave unpredictably (e.g., false positives
# during directory walks, workspace errors, or silent failures). As a result,
# this script is sensitive to that distinction and should only process true
# file geodatabases.
#
# If unexpected behavior occurs, verify that all *.gdb items encountered are
# actual file geodatabase directories and not standalone files or improperly
# structured folders.
#
# ---------------------------------------------------------------------------

import os
import arcpy
import datetime
import pandas as pd

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Root folder containing file geodatabases ***UPDATE ME FIRST***
ROOT_DIR = r""

# Output Excel file ***UPDATE ME SECOND***
OUTPUT_EXCEL = r"xxx.xlsx"

# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

# Convert a filesystem timestamp to a formatted datetime string
def format_timestamp(timestamp):
    try:
        return datetime.datetime.fromtimestamp(timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except Exception:
        return None

# Build a dictionary describing a single dataset
def describe_dataset(
    gdb_name,
    gdb_path,
    gdb_last_modified,
    dataset_path,
    feature_dataset=None
):
    desc = arcpy.Describe(dataset_path)

    dataset_type = getattr(desc, "datasetType", "Unknown")

    geometry_type = (
        getattr(desc, "shapeType", None)
        if dataset_type == "FeatureClass"
        else None
    )

    # Get feature count for feature classes and tables
    feature_count = None
    try:
        if dataset_type in ("FeatureClass", "Table"):
            feature_count = int(
                arcpy.management.GetCount(dataset_path)[0]
            )
    except Exception:
        feature_count = None

    # Get spatial reference name
    spatial_reference = None
    try:
        if hasattr(desc, "spatialReference") and desc.spatialReference:
            spatial_reference = desc.spatialReference.name
    except Exception:
        spatial_reference = None

    return {
        "GDB_Name": gdb_name,
        "GDB_Path": gdb_path,
        "GDB_Last_Modified": gdb_last_modified,
        "Feature_Dataset": feature_dataset,
        "Dataset_Name": desc.name,
        "Dataset_Path": dataset_path,
        "Dataset_Type": dataset_type,
        "Geometry_Type": geometry_type,
        "Feature_Count": feature_count,
        "Spatial_Reference": spatial_reference,
    }

# ---------------------------------------------------------------------------
# GEODATABASE INVENTORY LOGIC
# ---------------------------------------------------------------------------

# Walk the root directory and inventory all file geodatabases
def inventory_geodatabases(root_dir):
    records = []

    for dirpath, dirnames, _ in os.walk(root_dir):
        for dirname in dirnames:
            if not dirname.lower().endswith(".gdb"):
                continue

            gdb_path = os.path.join(dirpath, dirname)
            print(f"Scanning geodatabase: {gdb_path}")

            # Get geodatabase last modified date
            try:
                gdb_last_modified = format_timestamp(
                    os.path.getmtime(gdb_path)
                )
            except Exception:
                gdb_last_modified = None

            # Set workspace to the geodatabase
            arcpy.env.workspace = gdb_path

            # Inventory top-level feature classes
            for fc in arcpy.ListFeatureClasses() or []:
                records.append(
                    describe_dataset(
                        dirname,
                        gdb_path,
                        gdb_last_modified,
                        os.path.join(gdb_path, fc)
                    )
                )

            # Inventory feature datasets and their feature classes
            for fds in arcpy.ListDatasets("", "Feature") or []:
                fds_path = os.path.join(gdb_path, fds)
                arcpy.env.workspace = fds_path

                for fc in arcpy.ListFeatureClasses() or []:
                    records.append(
                        describe_dataset(
                            dirname,
                            gdb_path,
                            gdb_last_modified,
                            os.path.join(fds_path, fc),
                            feature_dataset=fds
                        )
                    )

                # Reset workspace to geodatabase
                arcpy.env.workspace = gdb_path

            # Inventory standalone tables
            for table in arcpy.ListTables() or []:
                records.append(
                    describe_dataset(
                        dirname,
                        gdb_path,
                        gdb_last_modified,
                        os.path.join(gdb_path, table)
                    )
                )

            # Inventory rasters
            for raster in arcpy.ListRasters() or []:
                records.append(
                    describe_dataset(
                        dirname,
                        gdb_path,
                        gdb_last_modified,
                        os.path.join(gdb_path, raster)
                    )
                )

            # Clear workspace
            arcpy.env.workspace = None

    return records

# ---------------------------------------------------------------------------
# SCRIPT ENTRY POINT
# ---------------------------------------------------------------------------

# Run the inventory and write results to Excel
def main():
    print(f"Starting geodatabase inventory for: {ROOT_DIR}")

    records = inventory_geodatabases(ROOT_DIR)

    if not records:
        print("No datasets found.")
        return

    # Create DataFrame and sort for readability
    df = pd.DataFrame(records)
    df.sort_values(
        by=["GDB_Name", "Feature_Dataset", "Dataset_Name"],
        inplace=True
    )

    # Write output to Excel
    print(f"Writing inventory to Excel: {OUTPUT_EXCEL}")
    df.to_excel(OUTPUT_EXCEL, index=False)

    print("Inventory complete.")


if __name__ == "__main__":
    main()
