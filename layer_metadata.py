import os 
import glob
import arcpy
from datetime import datetime
import datetime as dt

def extract_layer_metadata(lyrx_files):
    """Extract metadata from layer files."""
    data_list = []
    contents = []

    contents_header = (
        f"### Table of Contents \n\n"
    )
    contents.append(contents_header)

    for file_path in lyrx_files:
        try:
            layer_file = arcpy.mp.LayerFile(file_path)

            # Get file metadata
            file_stats = os.stat(file_path)
            file_created = datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            file_modified = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            file_size = file_stats.st_size / 1024  # Convert to KB

            file_info = (
                f"### File Information:\n\n"
                f"- File Path: {file_path}\n"
                f"- File Name: {os.path.basename(file_path)}\n"
                f"- Created: {file_created}\n"
                f"- Last Modified: {file_modified}\n"
                f"- File Size: {file_size:.2f} KB\n\n"
            )
            data_list.append(file_info)

            toc_entry = (
                f"- {file_path}\n"
            )
            contents.append(toc_entry)

            for layer in layer_file.listLayers():
                # Add layer name and data source
                if layer.supports("DATASOURCE"):
                    layer_info = (
                        f"## Layer: {layer.name}\n\n"
                        f"Source: {layer.dataSource}\n\n"
                    )
                    data_list.append(layer_info)

                    # Add data source metadata
                    try:
                        if os.path.exists(layer.dataSource):
                            source_stats = os.stat(layer.dataSource)
                            source_created = datetime.fromtimestamp(source_stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                            source_modified = datetime.fromtimestamp(source_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                            source_info = (
                                f"Data Source Metadata:\n\n"
                                f"- Created: {source_created}\n"
                                f"- Last Modified: {source_modified}\n\n"
                            )
                            data_list.append(source_info)
                    except:
                        pass

                    # Add detailed field information
                    try:
                        desc = arcpy.da.Describe(layer.dataSource)

                        # Field details
                        field_info = "### Fields:\n\n"
                        for field in desc["fields"]:
                            field_info += (
                                f"- {field.name}\n"
                                f"  - Type: {field.type}\n"
                                f"  - Length: {field.length}\n"
                                f"  - Alias: {field.aliasName}\n"
                                f"  - Nullable: {field.isNullable}\n\n"
                            )
                        data_list.append(field_info)

                    except Exception as e:
                        data_list.append(f"Error reading fields: {str(e)}\n\n")

                    # Add layer properties
                    try:
                        layer_props = "### Layer Properties:\n\n"
                        layer_props += f"- Description: {layer.metadata.description}\n"
                        layer_props += f"- Visible: {layer.visible}\n"
                        layer_props += f"- Min Scale: {layer.metadata.minScale}\n"
                        layer_props += f"- Max Scale: {layer.metadata.maxScale}\n"
                        layer_props += f"- Transparency: {layer.transparency}%\n"

                        if layer.supports("DEFINITIONQUERY"):
                            layer_props += f"- Definition Query: {layer.definitionQuery}\n"

                        data_list.append(layer_props + "\n")
                    except Exception as e:
                        data_list.append(f"Error reading layer properties: {str(e)}\n\n")

                    # Add symbology information
                    try:
                        symbology_info = "### Symbology:\n\n"

                        if layer.supports("SYMBOLOGY"):
                            sym = layer.symbology
                            symbology_info += f"- Renderer Type: {sym.renderer.type}\n"

                            # For simple renderer
                            if hasattr(sym.renderer, 'symbol'):
                                symbol = sym.renderer.symbol
                                symbology_info += f"- Symbol Type: {symbol.type}\n"
                                if hasattr(symbol, 'color'):
                                    symbology_info += f"- Color: RGB{symbol.color}\n"
                                if hasattr(symbol, 'size'):
                                    symbology_info += f"- Size: {symbol.size}\n"

                            # For unique value or graduated renderers
                            if hasattr(sym.renderer, 'fields'):
                                symbology_info += f"- Classification Field(s): {sym.renderer.fields}\n"

                            if hasattr(sym.renderer, 'classBreakCount'):
                                symbology_info += f"- Class Breaks: {sym.renderer.classBreakCount}\n"

                            if hasattr(sym.renderer, 'groups'):
                                symbology_info += f"- Number of Groups: {len(sym.renderer.groups)}\n"

                        data_list.append(symbology_info + "\n")
                    except Exception as e:
                        data_list.append(f"Error reading symbology: {str(e)}\n\n")

        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue
        
    data_list.insert(0,contents)
    return data_list

def write_metadata_to_file(data_list, output_file):
    """Write collected metadata to a markdown file."""
    current_time = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(output_file, 'w') as md_file:
        md_file.write("# Layer Metadata Report\n\n")
        md_file.write(f"**Generated:** {current_time}\n\n")
        md_file.write(f"**Script Version:** 1.0\n\n")
        md_file.write(f"**Author:** {os.getenv('USERNAME', 'Unknown')}\n\n")
        md_file.write(f"**Source Directory:** {DIRECTORY_PATH}\n\n")
        md_file.write("---\n\n")

        for data in data_list[0]:
            md_file.write(data)
            
        md_file.write("---\n\n")
        
        for data in data_list[1]:
            md_file.write(data)
        
        md_file.write("\n---\n\n")
        md_file.write(f"**End of Report**\n\n")
        md_file.write(f"Report completed at: {current_time}\n")

def main():
    # Find all .lyrx files in the directory
    lyrx_files = glob.glob(os.path.join(DIRECTORY_PATH, '*.lyrx'))
    
    if not lyrx_files:
        print(f"No .lyrx files found in {DIRECTORY_PATH}")
        return
    
    print(f"Found {len(lyrx_files)} layer files to process")
    
    # Extract metadata
    data_list = extract_layer_metadata(lyrx_files)
    
    # Define output file path
    output_file = os.path.join(os.path.dirname(DIRECTORY_PATH), OUTPUT_FILENAME)
    admin_output_file = os.path.join(ADMIN_DIRECTORY_PATH, OUTPUT_FILENAME)
    
    # Write to file
    write_metadata_to_file(data_list, output_file)
    write_metadata_to_file(data_list, admin_output_file)
    
    print(f"Metadata written to: {output_file}")


# Configuration
DIRECTORY_PATH = r""
ADMIN_DIRECTORY_PATH = r""
OUTPUT_FILENAME = "transportation_layer_metadata.txt"

if __name__ == "__main__":
    main()
