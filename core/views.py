import os
import base64
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
from io import BytesIO
from datetime import datetime

from django.conf import settings
from django.http import FileResponse, JsonResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import FileUploadLog, ColumnMappingLog

# from .utils import process_dataset

# @api_view(["POST"])
# def process_view(request, dataset_id):
#     process_dataset(dataset_id)
#     return Response({"message": "Processing completed"})


UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, "uploads")
OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------- File Upload ----------------
class FileUploadView(APIView):
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = os.path.join(UPLOAD_DIR, file.name)
        with open(file_path, "wb+") as f:
            for chunk in file.chunks():
                f.write(chunk)

        return Response({"file": file.name}, status=status.HTTP_201_CREATED)


class ProcessFileView(APIView):
    def post(self, request):
        upload_file = request.FILES.get("file")
        if not upload_file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        input_path = os.path.join(UPLOAD_DIR, upload_file.name)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        with open(input_path, "wb") as f:
            for chunk in upload_file.chunks():
                f.write(chunk)

        df_raw = pd.read_excel(input_path, header=None)
        df_master_path = os.path.join(settings.BASE_DIR, "master.xlsx")
        df_master = pd.read_excel(df_master_path)

        # Extract Product headers from row 2, columns 2
        products = df_raw.iloc[2, 1:].tolist()
        drop_products = ["Grand Total", "Growth %", "Market %", "Accretion"]
        products = [p for p in products if p not in drop_products]

        # Slice only insurer + product columns, starting from row 4
        df = df_raw.iloc[3:, : len(products) + 1].copy()

        # Drop completely empty rows
        df = df.dropna(how="all")

        # Remove unwanted rows (totals, headings)
        drop_keywords = ["Total", "Growth", "Market", "Accretion", "General Insurers", "Previous Year"]
        df = df[~df.iloc[:, 0].astype(str).str.contains("|".join(drop_keywords), case=False, na=False)]

        upload_log = FileUploadLog.objects.create(file_name=upload_file.name)
        # Map insurer names
        # mapping = dict(zip(df_master["insurer"], df_master["clubbed_name"])) df.iloc[:, 0] = df.iloc[:, 0].replace(mapping)
        mapping = dict(zip(df_master["insurer"], df_master["clubbed_name"]))
        df.iloc[:, 0] = df.iloc[:, 0].replace(mapping)

        # valid_insurers = set(mapping.values()) df = df[df.iloc[:, 0].isin(valid_insurers)]

        # --- Pair Current vs Previous Year ---
        # rows = [] 
        # for i in range(0, len(df), 2): 
        #     try: 
        #         curr = df.iloc[i] 
        #         prev = df.iloc[i + 1] 
        #         insurer = curr.iloc[0] 
        #         values_curr = curr.iloc[1:len(products)+1] 
        #         values_prev = prev.iloc[1:len(products)+1]
        #save log
        for orig, mapped in mapping.items():
            ColumnMappingLog.objects.create(
                upload=upload_log,
                original_column=orig,
                mapped_column=mapped
            )


        # Keep only mapped insurers
        valid_insurers = set(mapping.values())
        df = df[df.iloc[:, 0].isin(valid_insurers)]

        # --- Pair Current vs Previous Year ---
        rows = []
        today = datetime.today()
        year, month = today.year, today.strftime("%b")
        category = "PVT"

        for i in range(0, len(df), 2):
            try:
                curr = df.iloc[i]
                prev = df.iloc[i + 1]

                insurer = curr.iloc[0]
                values_curr = curr.iloc[1:len(products)+1]
                values_prev = prev.iloc[1:len(products)+1]

                for prod, val in zip(products, values_curr):
                    rows.append([year, month, category, insurer, prod, val, "Current"])
                for prod, val in zip(products, values_prev):
                    rows.append([year-1, month, category, insurer, prod, val, "Previous"])
            except IndexError:
                continue

        tidy_df = pd.DataFrame(
            rows,
            columns=["Year", "Month", "category", "clubbed_name", "Product", "Value", "Period"]
        )

        # Save output
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        name, ext = os.path.splitext(upload_file.name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{name}_{timestamp}{ext}"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        tidy_df.to_excel(output_path, index=False)

        #Save Log
        upload_log.processed = True
        upload_log.processed_at = datetime.now()
        upload_log.processed_file_name = output_filename
        upload_log.num_rows = len(tidy_df)
        upload_log.save()

        return Response({
            "message": "File processed successfully",
            "output_file": output_filename,
            "columns": tidy_df.columns.tolist(),
            "num_rows": len(tidy_df)
        })



class DownloadFileView(APIView):
    def get(self, request):
        filename = request.GET.get("file")
        if not filename:
            return Response({"error": "File parameter missing"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            raise Http404("File not found")

        return FileResponse(open(file_path, "rb"), as_attachment=True, filename=filename)



class GeneratePlotView(APIView):
    def get(self, request):
        filename = request.GET.get("file")
        column = request.GET.get("column")  # column to plot

        if not filename or not column:
            return Response({"error": "file or column parameter missing"}, status=status.HTTP_400_BAD_REQUEST)

        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            raise Http404("Processed file not found")

        df = pd.read_excel(file_path)

        if column not in df.columns:
            return Response({"error": "Invalid column"}, status=status.HTTP_400_BAD_REQUEST)

        # Aggregate by selected column
        if column in ["clubbed_name","Product"]:
            df_plot = df.groupby(column)["Value"].sum().reset_index()
            x = df_plot[column]
            y = df_plot["Value"]
        else:
            # numeric column
            x = df.index
            y = df[column]

        plt.figure(figsize=(8,5))
        plt.bar(x, y, color="skyblue")
        plt.xlabel(column)
        plt.ylabel("Value")
        plt.title(f"Plot of {column}")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close()

        return JsonResponse({"plot": image_base64})
