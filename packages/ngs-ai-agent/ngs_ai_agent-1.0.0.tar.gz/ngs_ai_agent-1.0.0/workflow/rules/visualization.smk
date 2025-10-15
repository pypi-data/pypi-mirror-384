"""
Visualization Rules - Dynamic based on pipeline type
"""

def get_fitness_input_file():
    """Get the appropriate fitness file based on pipeline type"""
    if DMS_PIPELINE_TYPE == "barcode_coupled":
        return f"{RESULTS_DIR}/dms/fitness_scores.csv"
    else:
        return f"{RESULTS_DIR}/dms/annotated_variants.csv"

rule create_heatmap:
    input:
        fitness=get_fitness_input_file()
    output:
        heatmap=f"{RESULTS_DIR}/visualization/dms_heatmap.png",
        interactive=f"{RESULTS_DIR}/visualization/dms_heatmap.html"
    params:
        colormap=config["visualization"]["heatmap"]["colormap"],
        figsize=config["visualization"]["heatmap"]["figsize"],
        dpi=config["visualization"]["heatmap"]["dpi"],
        exclude_multi_mutations=config["visualization"]["heatmap"]["exclude_multi_mutations"]
    script:
        "../scripts/create_heatmap.py"

rule fitness_distribution:
    input:
        fitness=get_fitness_input_file()
    output:
        histogram=f"{RESULTS_DIR}/visualization/fitness_distribution.png"
    script:
        "../scripts/fitness_plots.py"
