  CREATE TABLE oracle_demo (
      id          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      name        VARCHAR2(100)  NOT NULL,
      description VARCHAR2(500),
      status      NUMBER         DEFAULT 0 NOT NULL
  );
  
  -- 添加字段注释
  COMMENT ON TABLE  oracle_demo              IS 'Oracle 示例表';
  COMMENT ON COLUMN oracle_demo.id          IS '主键ID';
  COMMENT ON COLUMN oracle_demo.name        IS '名称';
  COMMENT ON COLUMN oracle_demo.description IS '描述';
  COMMENT ON COLUMN oracle_demo.status      IS '状态(0:启用 1:禁用)';
