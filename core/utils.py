# from .models import TransformationStepLog, Dataset

# def log_step(dataset, step_name, status, details=""):
#     TransformationStepLog.objects.create(
#         dataset=dataset,
#         step_name=step_name,
#         status=status,
#         details=details
#     )

# def process_dataset(dataset_id):
#     dataset = Dataset.objects.get(id=dataset_id)

#     # Step 1: Load Excel
#     log_step(dataset, "Load Excel", "Started")
#     try:
#         df = pd.read_excel(dataset.file.path)
#         log_step(dataset, "Load Excel", "Completed", f"Rows loaded: {len(df)}")
#     except Exception as e:
#         log_step(dataset, "Load Excel", "Failed", str(e))
#         raise

#     # Step 2: Apply mappings
#     log_step(dataset, "Apply Column Mappings", "Started")
#     try:
#         # (example mapping logic)
#         df.rename(columns={"OldName": "NewName"}, inplace=True)
#         log_step(dataset, "Apply Column Mappings", "Completed", f"Columns mapped: {len(df.columns)}")
#     except Exception as e:
#         log_step(dataset, "Apply Column Mappings", "Failed", str(e))
#         raise

#     # Step 3: Transform Data
#     log_step(dataset, "Normalize Data", "Started")
#     try:
#         # (example transformation logic)
#         df = df.dropna()
#         log_step(dataset, "Normalize Data", "Completed", f"Remaining rows: {len(df)}")
#     except Exception as e:
#         log_step(dataset, "Normalize Data", "Failed", str(e))
#         raise

#     # Step 4: Save Output
#     log_step(dataset, "Save Output", "Started")
#     try:
#         output_path = f"media/outputs/output_{dataset.id}.xlsx"
#         df.to_excel(output_path, index=False)
#         dataset.output_file.name = output_path.replace("media/", "")
#         dataset.processed = True
#         dataset.save()
#         log_step(dataset, "Save Output", "Completed", f"File saved at {output_path}")
#     except Exception as e:
#         log_step(dataset, "Save Output", "Failed", str(e))
#         raise
