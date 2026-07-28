-- ============================================================
-- OceanBase Oracle 租户 - ob_oracle_demo 表初始化脚本
-- 用途：在 OceanBase Oracle 租户中创建序列和示例表
-- 执行环境：OceanBase Oracle 模式（非 MySQL）
-- ============================================================

-- 1. 创建序列（供 CURRVAL 取回插入的 ID，会话级，无并发竞争）
CREATE SEQUENCE ob_oracle_demo_seq START WITH 1 INCREMENT BY 1 NOCACHE;

-- 2. 创建表（使用显式序列 DEFAULT，而非 GENERATED ALWAYS AS IDENTITY）
CREATE TABLE ob_oracle_demo (
    id          NUMBER DEFAULT ob_oracle_demo_seq.NEXTVAL PRIMARY KEY,
    name        VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    status      NUMBER DEFAULT 0
);

-- 3. 验证
SELECT sequence_name FROM user_sequences WHERE sequence_name = 'OB_ORACLE_DEMO_SEQ';
SELECT table_name FROM user_tables WHERE table_name = 'OB_ORACLE_DEMO';
