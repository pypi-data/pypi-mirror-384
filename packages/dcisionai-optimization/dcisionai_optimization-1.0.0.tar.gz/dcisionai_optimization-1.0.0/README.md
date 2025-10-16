# DcisionAI MCP Server

> **Optimization Intelligence for AI Workflows**

The DcisionAI MCP Server provides optimization capabilities through the Model Context Protocol (MCP), enabling AI agents to solve complex optimization problems across multiple industries.

## 🚀 **Features**

- **7 Industry Workflows**: Manufacturing, Healthcare, Retail, Marketing, Financial, Logistics, Energy
- **Qwen 30B Integration**: Advanced mathematical optimization
- **Real-Time Results**: Actual optimization solutions with mathematical proofs
- **MCP Protocol**: Seamless integration with AI development environments

## 📦 **Installation**

### **From PyPI (Coming Soon)**
```bash
pip install dcisionai-optimization
```

### **From Source**
```bash
cd mcp-server
pip install -e .
```

## 🔧 **Quick Start**

### **1. Start the MCP Server**
```bash
cd mcp-server/src
python mcp_server.py
```

### **2. Configure Your IDE**
Add to your MCP configuration:
```json
{
  "mcpServers": {
    "dcisionai-optimization": {
      "command": "python",
      "args": ["-m", "dcisionai_mcp_server.robust_mcp"]
    }
  }
}
```

### **3. Use in Your AI Agent**
```python
# Example: Optimize manufacturing production
result = mcp.execute_workflow(
    industry="manufacturing",
    workflow_id="production_planning"
)
```

## 🛠 **Available Tools**

- `classify_intent` - Identify optimization problem type
- `analyze_data` - Assess data readiness for optimization
- `build_model` - Create mathematical optimization model
- `solve_optimization` - Find optimal solution
- `get_workflow_templates` - Get available industry workflows
- `execute_workflow` - Run complete optimization workflow

## 📚 **Documentation**

- [API Reference](docs/api-reference.md)
- [Workflow Guide](docs/workflows.md)
- [Integration Examples](docs/examples.md)

## 🎯 **Supported Industries**

| Industry | Workflows | Use Cases |
|----------|-----------|-----------|
| **Manufacturing** | Production Planning, Resource Allocation, Quality Optimization | Production scheduling, capacity planning, quality control |
| **Healthcare** | Staff Scheduling, Resource Allocation, Patient Flow | Hospital operations, staff optimization, patient care |
| **Retail** | Pricing Optimization, Inventory Management, Demand Forecasting | Dynamic pricing, stock optimization, demand prediction |
| **Marketing** | Campaign Optimization, Budget Allocation, Channel Selection | Ad spend optimization, campaign performance, ROI maximization |
| **Financial** | Portfolio Optimization, Risk Management, Budget Allocation | Investment strategies, risk assessment, capital allocation |
| **Logistics** | Route Optimization, Supply Chain, Inventory Management | Delivery optimization, supply chain efficiency, warehouse management |
| **Energy** | Energy Mix Optimization, Grid Management, Demand Response | Renewable energy planning, grid optimization, demand management |

## 🔬 **Technical Details**

- **Model**: Qwen 30B for mathematical optimization
- **Protocol**: Model Context Protocol (MCP)
- **Languages**: Python, JavaScript
- **Dependencies**: See [requirements.txt](requirements.txt)

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 **License**

MIT License - see [LICENSE](LICENSE) for details.

---

**Ready to add optimization intelligence to your AI workflows?** 🚀
