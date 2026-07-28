import cx_Oracle
cx_Oracle.init_oracle_client(lib_dir=r"C:\obclient\lib")

# 数据库连接信息
# username = 'XAG'
# password = 'Xag_123456'
# oracle_connection = 'obot7jbnen7v964g-mi.aliyun-cn-hangzhou-internet.oceanbase.cloud:1521/XAG'

# conn = cx_Oracle.connect('xag/123456@192.168.190.135:1521/mypdb')
# 创建数据库连接
# conn = cx_Oracle.connect(username, password, oracle_connection)
conn = cx_Oracle.connect('XAG/Xag_123456@obot7jbnen7v964g-mi.aliyun-cn-hangzhou-internet.oceanbase.cloud:1521/XAG')
# obclient -h10.0.68.103 -P2883 -uMPOP@MPPAYUAT#mp_cluster -pMPOP   --OK
# obclient -h10.0.101.133 -P2881 -uMPOP@MPPAYUAT -pMPOP

def exec_sql(sql):
    """执行 SQL 语句"""
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        print(f"SQL 执行成功: {sql}")
    except Exception as e:
        print(f"SQL 执行失败: {sql}")
        print(f"错误信息: {e}")
    finally:
        cur.close()


def print_data(sql):
    """查询并打印数据"""
    cur = conn.cursor()
    try:
        cur.execute(sql)
        data = cur.fetchall()
        print(f"查询结果: {data}")
        return data
    except Exception as e:
        print(f"查询失败: {sql}")
        print(f"错误信息: {e}")
        return None
    finally:
        cur.close()


def test_char_types():
    """测试字符类型"""
    print("\n=== 测试字符类型 ===")
    exec_sql("DROP TABLE test_char")
    exec_sql("""
             CREATE TABLE test_char
             (
                 id INT,
                 a  VARCHAR2(20),
                 b  CHAR(10),
                 c  NCHAR(10),
                 d  NVARCHAR2(10)
             )
             """)
    exec_sql("INSERT INTO test_char VALUES (1, 'hello3', 'xag', 'yyc', 'xrj')")
    print_data("SELECT * FROM test_char")


def main():
    """主函数"""
    try:
        print("开始测试 OceanBase 数据库 Oracle 模式连接...")

        test_char_types()

        print("\n所有测试完成！")

    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 关闭数据库连接
        if conn:
            conn.close()
            print("数据库连接已关闭")


if __name__ == "__main__":
    main()
