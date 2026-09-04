from app.config import settings
from app.services.excel.base import ExcelServiceInterface
from app.services.excel.local_excel_service import LocalExcelService
from app.services.excel.graph_excel_service import GraphExcelService

_excel_service_instance = None


def get_excel_service() -> ExcelServiceInterface:
    """
    Factory to resolve Excel storage service singleton.
    Returns GraphExcelService when configured for cloud Microsoft Graph Excel Online,
    or LocalExcelService for offline / development .xlsx file management.
    """
    global _excel_service_instance
    if _excel_service_instance is None:
        if settings.EXCEL_STORAGE_TYPE == "graph" and settings.AZURE_CLIENT_ID and settings.EXCEL_DRIVE_ID:
            _excel_service_instance = GraphExcelService()
        else:
            _excel_service_instance = LocalExcelService()
    return _excel_service_instance


__all__ = [
    "ExcelServiceInterface",
    "LocalExcelService",
    "GraphExcelService",
    "get_excel_service",
]
