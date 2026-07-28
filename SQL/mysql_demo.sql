-- ============================================================
-- MySQL 多数据源 - mysql_demo 表初始化脚本
-- 用途：在外部 MySQL 数据库中创建 mysql_demo 示例表
-- 执行环境：外部 MySQL 数据库（非主库）
-- ============================================================

CREATE TABLE IF NOT EXISTS mysql_demo (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL COMMENT '名称',
    description VARCHAR(500) COMMENT '描述',
    status      INT DEFAULT 0 COMMENT '状态(0:启用 1:禁用)'
) COMMENT='MySQL 多数据源示例表';

-- 验证
SHOW CREATE TABLE mysql_demo;
