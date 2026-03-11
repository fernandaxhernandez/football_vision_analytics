from match_analysis.pipeline import run_pipeline

if __name__ == "__main__":
    input_path = "outputs/records_paula.json"
    output_path = "outputs/tracks_annotated_paula.json"

    run_pipeline(input_path, output_path)