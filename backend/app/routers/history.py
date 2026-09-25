from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.history_schema import (
    HistoryDeleteResponse,
    HistoryDetailResponse,
    HistoryListResponse,
    HistorySaveRequest,
    HistorySaveResponse,
)
from app.services.history_service import (
    delete_history,
    get_history_detail,
    get_history_list,
    save_history,
)

router = APIRouter(tags=["History"])


@router.post("/save", response_model=HistorySaveResponse)
async def save_history_endpoint(request: HistorySaveRequest, db: Session = Depends(get_db)):
    try:
        history_id = save_history(db, request)
        return HistorySaveResponse(
            code=200,
            message="success",
            data={"id": history_id}
        )
    except Exception as e:
        return HistorySaveResponse(
            code=500,
            message=f"保存失败: {e!s}",
            data=None
        )


@router.get("/list", response_model=HistoryListResponse)
async def get_history_list_endpoint(db: Session = Depends(get_db), limit: int = 20):
    try:
        records = get_history_list(db, limit)
        return HistoryListResponse(
            code=200,
            message="success",
            data=records
        )
    except Exception as e:
        return HistoryListResponse(
            code=500,
            message=f"查询失败: {e!s}",
            data=None
        )


@router.get("/{history_id}", response_model=HistoryDetailResponse)
async def get_history_detail_endpoint(history_id: int, db: Session = Depends(get_db)):
    try:
        record = get_history_detail(db, history_id)
        if not record:
            return HistoryDetailResponse(
                code=404,
                message="记录不存在",
                data=None
            )
        return HistoryDetailResponse(
            code=200,
            message="success",
            data=record
        )
    except Exception as e:
        return HistoryDetailResponse(
            code=500,
            message=f"查询失败: {e!s}",
            data=None
        )


@router.delete("/{history_id}", response_model=HistoryDeleteResponse)
async def delete_history_endpoint(history_id: int, db: Session = Depends(get_db)):
    try:
        success = delete_history(db, history_id)
        if not success:
            return HistoryDeleteResponse(
                code=404,
                message="记录不存在",
                data=None
            )
        return HistoryDeleteResponse(
            code=200,
            message="success",
            data={"id": history_id}
        )
    except Exception as e:
        return HistoryDeleteResponse(
            code=500,
            message=f"删除失败: {e!s}",
            data=None
        )
