"""OB Oracle SQL 查询 Controller"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import JSONResponse

from app.common.response import ErrorResponse, ResponseSchema, SuccessResponse
from app.core.base_schema import AuthSchema, PaginationQueryParam
from app.core.dependencies import AuthPermission, db_getter
from app.core.logger import logger
from sqlalchemy.ext.asyncio import AsyncSession

from .history_service import QueryHistoryService
from .schema import ObOracleQueryRequest, ObOracleQueryResponse
from .service import ObOracleQueryService

ObOracleQueryRouter = APIRouter(tags=["OceanBase 管理", "SQL查询"])


@ObOracleQueryRouter.post(
    "/execute",
    summary="执行 SQL 查询",
    response_model=ResponseSchema[ObOracleQueryResponse],
)
async def execute_sql(
    data: ObOracleQueryRequest,
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_ob_oracle_query:query:execute"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    # 校验数据源是否对该模块和当前用户可见
    if data.module_name:
        from app.api.v1.module_system.ob_oracle_config.service import ObOracleConfigService

        service = ObOracleConfigService(auth, db)
        user_id = auth.user.id if auth.user else None
        visible = await service.list_for_module(
            module_name=data.module_name, user_id=user_id
        )
        visible_ids = {c.id for c in visible}
        if data.config_id not in visible_ids:
            return ErrorResponse(msg="该数据源对当前模块或用户不可见")

    history_service = QueryHistoryService(auth, db)
    try:
        result = await ObOracleQueryService.execute(
            config_id=data.config_id,
            sql=data.sql,
            max_rows=data.max_rows,
        )

        # 脱敏后处理（独立 try/except，脱敏失败不影响查询结果）
        result["is_masked"] = False
        result["masked_columns"] = []
        if result.get("rows") and result.get("columns"):
            try:
                from ..masking.engine import apply_masking

                masked_rows, masked_info = await apply_masking(
                    config_id=data.config_id,
                    columns=result["columns"],
                    rows=result["rows"],
                    db=db,
                    sql=data.sql,
                )
                if masked_info:
                    result["rows"] = masked_rows
                    result["is_masked"] = True
                    result["masked_columns"] = [m["column_name"] for m in masked_info]
            except Exception as mask_err:
                logger.warning("脱敏处理失败，返回原始数据: {}", mask_err)

        # 保存成功历史
        await history_service.save_history(
            config_id=data.config_id,
            config_name=None,
            sql=data.sql,
            status=0,
            elapsed_ms=result.get("elapsed_ms"),
            row_count=result.get("total"),
        )
        return SuccessResponse(data=result, msg="查询成功")
    except ValueError as e:
        # 保存失败历史
        await history_service.save_history(
            config_id=data.config_id,
            config_name=None,
            sql=data.sql,
            status=1,
            error_msg=str(e),
        )
        return ErrorResponse(msg=str(e))
    except Exception as e:
        logger.error("SQL 查询执行异常: {}", e, exc_info=True)
        await history_service.save_history(
            config_id=data.config_id,
            config_name=None,
            sql=data.sql,
            status=1,
            error_msg=str(e),
        )
        return ErrorResponse(msg="SQL 查询执行失败，请检查 SQL 语句")


@ObOracleQueryRouter.get(
    "/history/list",
    summary="查询 SQL 执行历史",
    response_model=ResponseSchema[dict],
)
async def list_history(
    page: Annotated[PaginationQueryParam, Depends()],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_ob_oracle_query:query:execute"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
    config_id: int | None = Query(None, description="数据源ID"),
    status: int | None = Query(None, description="状态(0:成功 1:失败)"),
) -> JSONResponse:
    result = await QueryHistoryService(auth, db).page(
        page_no=page.page_no,
        page_size=page.page_size,
        config_id=config_id,
        status=status,
    )
    return SuccessResponse(data=result, msg="查询历史成功")


@ObOracleQueryRouter.delete(
    "/history/delete",
    summary="删除历史记录",
    response_model=ResponseSchema[None],
)
async def delete_history(
    ids: Annotated[list[int], Body(description="ID列表")],
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_ob_oracle_query:query:execute"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await QueryHistoryService(auth, db).delete(ids=ids)
    return SuccessResponse(msg="删除成功")


@ObOracleQueryRouter.delete(
    "/history/clear",
    summary="清空历史记录",
    response_model=ResponseSchema[None],
)
async def clear_history(
    auth: Annotated[AuthSchema, Depends(AuthPermission(["module_ob_oracle_query:query:execute"]))],
    db: Annotated[AsyncSession, Depends(db_getter)],
) -> JSONResponse:
    await QueryHistoryService(auth, db).clear()
    return SuccessResponse(msg="清空成功")
