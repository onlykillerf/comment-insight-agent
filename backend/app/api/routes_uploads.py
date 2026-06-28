from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UploadedDataset
from app.schemas import FieldMappingUpdate, UploadOut
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("", response_model=UploadOut, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    source_kind: str = Form(...),
    db: Session = Depends(get_db),
) -> UploadedDataset:
    """Save and preview a browser-uploaded comment dataset."""

    return await UploadService().create(db, file, source_kind)


@router.get("/{upload_id}", response_model=UploadOut)
def get_upload(upload_id: str, db: Session = Depends(get_db)) -> UploadedDataset:
    return _get_upload(db, upload_id)


@router.patch("/{upload_id}/mapping", response_model=UploadOut)
def update_mapping(
    upload_id: str,
    payload: FieldMappingUpdate,
    db: Session = Depends(get_db),
) -> UploadedDataset:
    dataset = _get_upload(db, upload_id)
    return UploadService().update_mapping(db, dataset, payload.field_mapping)


@router.delete("/{upload_id}", status_code=204)
def delete_upload(upload_id: str, db: Session = Depends(get_db)) -> Response:
    dataset = _get_upload(db, upload_id)
    if dataset.tasks:
        raise HTTPException(status_code=409, detail="该文件已绑定任务，不能删除")
    Path(dataset.stored_path).unlink(missing_ok=True)
    db.delete(dataset)
    db.commit()
    return Response(status_code=204)


def _get_upload(db: Session, upload_id: str) -> UploadedDataset:
    dataset = db.get(UploadedDataset, upload_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="上传文件不存在")
    return dataset
