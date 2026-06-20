from datetime import datetime

import sqlalchemy as sa

from app.core.base_schema import AuthSchema
from app.core.dependencies import require_superadmin
from app.core.exceptions import CustomException
from app.core.logger import logger

from .crud import PluginCRUD
from .model import PluginModel, TenantPluginModel
from .schema import PluginCreateSchema, PluginOutSchema, PluginQueryParam, PluginUpdateSchema


class PluginService:
    """
    插件管理服务（仅超级管理员可操作 CRUD，租户通过 marketplace/install/uninstall/toggle/my 操作）
    """

    @classmethod
    @require_superadmin
    async def page_service(
        cls,
        auth: AuthSchema,
        page_no: int,
        page_size: int,
        search: PluginQueryParam | None = None,
        order_by: list | None = None,
    ) -> dict:
        """
        分页查询插件

        参数:
        - auth (AuthSchema): 认证信息模型
        - page_no (int): 页码
        - page_size (int): 每页数量
        - search (PluginQueryParam | None): 查询参数
        - order_by (list | None): 排序参数

        返回:
        - dict: 分页数据
        """
        return await PluginCRUD(auth).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=order_by or [{"sort": "asc"}],
            search=vars(search) if search else None,
            out_schema=PluginOutSchema,
        )

    @classmethod
    @require_superadmin
    async def detail_service(cls, auth: AuthSchema, id: int) -> PluginOutSchema:
        """
        插件详情

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 插件ID

        返回:
        - PluginOutSchema: 插件详情
        """
        return await PluginCRUD(auth).get_or_404(id=id, out_schema=PluginOutSchema)

    @classmethod
    @require_superadmin
    async def create_service(cls, auth: AuthSchema, data: PluginCreateSchema) -> PluginOutSchema:
        """
        创建插件

        参数:
        - auth (AuthSchema): 认证信息模型
        - data (PluginCreateSchema): 插件创建模型

        返回:
        - PluginOutSchema: 插件详情
        """
        if await PluginCRUD(auth).get(code=data.code):
            raise CustomException(msg="创建失败，插件编码已存在")
        obj = await PluginCRUD(auth).create(data=data)
        return PluginOutSchema.model_validate(obj)

    @classmethod
    @require_superadmin
    async def update_service(cls, auth: AuthSchema, id: int, data: PluginUpdateSchema) -> PluginOutSchema:
        """
        更新插件

        参数:
        - auth (AuthSchema): 认证信息模型
        - id (int): 插件ID
        - data (PluginUpdateSchema): 插件更新模型

        返回:
        - PluginOutSchema: 插件详情
        """
        _ = await PluginCRUD(auth).get_or_404(id=id)
        updated = await PluginCRUD(auth).update(id=id, data=data)
        return PluginOutSchema.model_validate(updated)

    @classmethod
    @require_superadmin
    async def delete_service(cls, auth: AuthSchema, ids: list[int]) -> None:
        """
        删除插件

        参数:
        - auth (AuthSchema): 认证信息模型
        - ids (list[int]): 插件ID列表

        返回:
        - None
        """
        await PluginCRUD(auth).delete(ids=ids)

    # ───── 插件市场 API ─────

    @classmethod
    async def marketplace_service(cls, auth: AuthSchema, page_no: int, page_size: int, category: str | None = None) -> dict:
        """
        插件市场列表（租户端）

        参数:
        - auth (AuthSchema): 认证信息模型
        - page_no (int): 页码
        - page_size (int): 每页数量
        - category (str | None): 分类筛选

        返回:
        - dict: 分页数据（含租户的 installed/purchased 标记）
        """
        search = {}
        if category:
            search["category"] = ("eq", category)
        search["status"] = ("eq", "0")
        result = await PluginCRUD(auth).page(
            offset=(page_no - 1) * page_size,
            limit=page_size,
            order_by=[{"sort": "asc"}],
            search=search,
            out_schema=PluginOutSchema,
        )
        tenant_id = getattr(auth, "tenant_id", None) or auth.user.tenant_id
        if tenant_id and result.items:
            records = await auth.db.execute(
                sa.select(TenantPluginModel.plugin_id, TenantPluginModel.purchased).where(
                    TenantPluginModel.tenant_id == tenant_id,
                )
            )
            record_map = {r[0]: r[1] for r in records.all()}
            for item in result.items:
                pid = item["id"]
                item["installed"] = pid in record_map
                item["purchased"] = record_map.get(pid, False)
        return result

    @classmethod
    async def install_service(cls, auth: AuthSchema, plugin_id: int) -> None:
        """
        安装插件

        参数:
        - auth (AuthSchema): 认证信息模型
        - plugin_id (int): 插件ID

        返回:
        - None
        """
        tenant_id = getattr(auth, "tenant_id", None) or auth.user.tenant_id
        if not tenant_id:
            raise CustomException(msg="无法获取租户信息")

        # 平台租户不限制插件安装
        if tenant_id != 1:
            from app.api.v1.module_platform.package.service import PackageService

            allowed_plugin_ids = await PackageService.get_tenant_available_plugin_ids(auth, tenant_id)
            # 套餐有插件配置时，仅允许安装套餐内的插件
            if allowed_plugin_ids and plugin_id not in allowed_plugin_ids:
                raise CustomException(msg="当前套餐不支持安装此插件")

        plugin = await PluginCRUD(auth).get(id=plugin_id)
        if not plugin or plugin.status == 1:
            raise CustomException(msg="该数据不存在")

        # 付费插件需要先购买
        if tenant_id != 1 and getattr(plugin, "price", 0) > 0:
            exist = await auth.db.execute(
                sa.select(TenantPluginModel)
                .where(
                    TenantPluginModel.tenant_id == tenant_id,
                    TenantPluginModel.plugin_id == plugin_id,
                )
                .limit(1)
            )
            tp_record = exist.scalar_one_or_none()
            if not tp_record or not tp_record.purchased:
                raise CustomException(msg="此插件为付费插件，请先购买后再安装")

        exist = await auth.db.execute(
            sa.select(TenantPluginModel)
            .where(
                TenantPluginModel.tenant_id == tenant_id,
                TenantPluginModel.plugin_id == plugin_id,
            )
            .limit(1)
        )
        if exist.scalar_one_or_none():
            await auth.db.execute(
                sa.update(TenantPluginModel)
                .where(
                    TenantPluginModel.tenant_id == tenant_id,
                    TenantPluginModel.plugin_id == plugin_id,
                )
                .values(enabled=False)
            )
        else:
            tp = TenantPluginModel(
                tenant_id=tenant_id,
                plugin_id=plugin_id,
                enabled=False,
                purchased=True if getattr(plugin, "price", 0) == 0 else False,
                installed_time=datetime.now(),
            )
            auth.db.add(tp)
        await auth.db.flush()
        logger.info(f"租户[{tenant_id}]安装插件[{plugin.name}]")

    @classmethod
    async def uninstall_service(cls, auth: AuthSchema, plugin_id: int) -> None:
        """
        卸载插件

        参数:
        - auth (AuthSchema): 认证信息模型
        - plugin_id (int): 插件ID

        返回:
        - None
        """
        tenant_id = getattr(auth, "tenant_id", None) or auth.user.tenant_id
        if not tenant_id:
            raise CustomException(msg="无法获取租户信息")
        await auth.db.execute(
            sa.delete(TenantPluginModel).where(
                TenantPluginModel.tenant_id == tenant_id,
                TenantPluginModel.plugin_id == plugin_id,
            )
        )
        await auth.db.flush()
        logger.info(f"租户[{tenant_id}]卸载插件[{plugin_id}]")

    @classmethod
    async def toggle_service(cls, auth: AuthSchema, plugin_id: int) -> None:
        """
        启用/禁用插件

        参数:
        - auth (AuthSchema): 认证信息模型
        - plugin_id (int): 插件ID

        返回:
        - None
        """
        tenant_id = getattr(auth, "tenant_id", None) or auth.user.tenant_id
        tp = await auth.db.execute(
            sa.select(TenantPluginModel)
            .where(
                TenantPluginModel.tenant_id == tenant_id,
                TenantPluginModel.plugin_id == plugin_id,
            )
            .limit(1)
        )
        tp = tp.scalar_one_or_none()
        if not tp:
            raise CustomException(msg="未安装该插件")
        tp.enabled = not tp.enabled
        await auth.db.flush()
        logger.info(f"租户[{tenant_id}]插件[{plugin_id}]状态→{tp.enabled}")

    @classmethod
    async def my_plugins_service(cls, auth: AuthSchema) -> list[dict]:
        """
        查询我的插件列表（租户端）

        参数:
        - auth (AuthSchema): 认证信息模型

        返回:
        - list[dict]: 已安装插件列表
        """
        tenant_id = getattr(auth, "tenant_id", None) or auth.user.tenant_id
        if not tenant_id:
            return []
        result = await auth.db.execute(
            sa.select(PluginModel, TenantPluginModel).join(TenantPluginModel, TenantPluginModel.plugin_id == PluginModel.id).where(TenantPluginModel.tenant_id == tenant_id).order_by(PluginModel.sort)
        )
        plugins = []
        for p, tp in result.all():
            d = PluginOutSchema.model_validate(p)
            d["enabled"] = tp.enabled
            d["installed"] = True
            d["installed_time"] = tp.installed_time.strftime("%Y-%m-%d %H:%M") if tp.installed_time else ""
            plugins.append(d)
        return plugins

    # ───── 插件热重载 ─────

    @classmethod
    def reload_service(cls) -> str:
        """
        热重载插件路由（同步函数，直接操作模块缓存与 app.routes）。

        要求 init_app.py 已在启动时调用 discover.set_app_ref(app)，
        否则仅重建 Router 对象，不会更新运行中的 app 路由。

        返回:
        - str: 重载结果描述
        """
        from app.core.discover import reload_dynamic_router

        router = reload_dynamic_router()
        route_count = len(router.routes) if router and hasattr(router, "routes") else 0
        logger.info(f"插件热重载完成，动态路由共 {route_count} 条")
        return f"插件路由热重载完成，共注册 {route_count} 条路由"
