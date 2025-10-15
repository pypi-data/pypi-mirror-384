# BMI Calculator MCP Server

**bmi-calculator-mcp**

A Model Context Protocol server for calculating BMI (Body Mass Index).

## Server Config

```json
{
  "mcpServers": {
    "bmi-calculator-mcp": {
      "command": "uvx",
      "args": ["bmi-calculator-mcp"],
      "env": {}
    }
  }
}
```

## Description

This is a simple MCP server that provides a tool to calculate Body Mass Index (BMI) based on height (in meters) and weight (in kilograms). It returns the BMI value and a health status assessment.
