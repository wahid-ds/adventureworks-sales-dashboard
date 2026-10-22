# Data source and reproduction

Source: [Microsoft Learn — AdventureWorks Sales sample](https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-dimensional-model-report).

The processed `processed/sales_dashboard.csv` is included for running the dashboard. It contains 121,253 sales lines and 16 columns, derived from Microsoft's sample workbook.

To reproduce the analysis, follow the source page's **AdventureWorks Sales sample Excel workbook** download link. Save the workbook here as `AdventureWorks Sales.xlsx`, then run `notebooks/sales_analysis.ipynb` from beginning to end. The original workbook is downloaded separately; Microsoft's source terms apply to its sample data.

The notebook joins sales, product, sales territory and sales order tables with many-to-one checks, derives gross profit and exports the dashboard CSV. Amounts retain source-data units; currency has not been independently verified.
