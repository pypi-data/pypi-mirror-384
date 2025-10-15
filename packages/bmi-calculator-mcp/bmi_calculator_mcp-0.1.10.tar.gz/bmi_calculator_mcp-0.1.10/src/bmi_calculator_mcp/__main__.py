from mcp.server.fastmcp import FastMCP

# 创建MCP服务器实例
mcp = FastMCP("bmi-calculator-mcp")

@mcp.tool()
def calculate_bmi(height: float, weight: float) -> str:
    """计算BMI值并返回健康状况评估
    
    参数:
        height: 身高（米）
        weight: 体重（千克）
    
    返回:
        BMI计算结果和健康状况评估
    """
    try:
        # 验证输入
        if height <= 0 or weight <= 0:
            return "错误：身高和体重必须为正数"
            
        # 计算BMI
        bmi = weight / (height * height)
        
        # 评估健康状况
        if bmi < 18.5:
            status = "体重过轻"
        elif bmi < 24:
            status = "体重正常"
        elif bmi < 28:
            status = "超重"
        else:
            status = "肥胖"
            
        return f"BMI值：{bmi:.1f}\n健康状况：{status}"
        
    except Exception as e:
        return f"计算出错：{str(e)}"

def main():
    """MCP 服务器入口点"""
    import sys
    
    # 处理命令行参数
    # 注意：输出到stderr以避免污染stdout的JSON-RPC通信
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ['--help', '-h']:
            sys.stderr.write("BMI Calculator MCP Server\n")
            sys.stderr.write("Version: 0.1.10\n")
            sys.stderr.write("\nUsage: bmi-calculator-mcp\n")
            sys.stderr.write("\nThis server uses stdio transport to communicate via MCP protocol.\n")
            sys.stderr.write("It provides a tool to calculate BMI based on height and weight.\n")
            sys.exit(0)
        elif arg in ['--version', '-v']:
            sys.stderr.write("bmi-calculator-mcp version 0.1.10\n")
            sys.exit(0)
    
    # 启动MCP服务器 (stdio transport)
    # stdout只能用于JSON-RPC消息，其他日志都输出到stderr
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
