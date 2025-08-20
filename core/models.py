from django.db import models

class FileUploadLog(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_file_name = models.CharField(max_length=255, null=True, blank=True)
    num_rows = models.IntegerField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.file_name

class ColumnMappingLog(models.Model):
    upload = models.ForeignKey(FileUploadLog, on_delete=models.CASCADE, related_name='mappings')
    original_column = models.CharField(max_length=255)
    mapped_column = models.CharField(max_length=255)
    mapped_at = models.DateTimeField(auto_now_add=True)

# class TransformationStepLog(models.Model):
#     upload = models.ForeignKey(FileUploadLog, on_delete=models.CASCADE, related_name='steps')
#     step_name = models.CharField(max_length=255)
#     status = models.CharField(max_length=50, choices=[('Started','Started'), ('Completed','Completed')])
#     timestamp = models.DateTimeField(auto_now_add=True)
#     details = models.TextField(null=True, blank=True)
    
# class Dataset(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     month = models.CharField(max_length=20, null=True, blank=True)
#     year = models.IntegerField(null=True, blank=True)
#     file = models.FileField(upload_to="uploads/")
#     output_file = models.FileField(upload_to="outputs/", null=True, blank=True)
#     plot_image = models.ImageField(upload_to="plots/", null=True, blank=True)

#     def __str__(self):
#         return f"Dataset {self.id} - {self.month} {self.year}"

# class DataRow(models.Model):
#     dataset = models.ForeignKey(Dataset, related_name="rows", on_delete=models.CASCADE)
#     year = models.IntegerField()
#     month = models.CharField(max_length=20)
#     category = models.CharField(max_length=255)
#     clubbed_name = models.CharField(max_length=255)
#     product = models.CharField(max_length=255)
#     value = models.FloatField()

#     def __str__(self):
#         return f"{self.clubbed_name} - {self.product} - {self.value}"