# 🎉 Complete W&B Monitoring Setup: Cost, Performance, and System Health

**Last Updated**: November 5, 2025 | **Version**: 2.0

This document provides a complete guide to the Weights & Biases (W&B) monitoring system integrated into the Multimodal Medical Diagnosis application. It covers initial setup, cost tracking, performance analysis, system health monitoring, and how to interpret the data on your W&B dashboard.

---

## 📚 1. Quick Start & Overview

### 🚀 How to Use

1.  **Start Your App**: Run the startup script to ensure W&B is enabled.
    ```bash
    python start_fresh_app.py
    ```
    This automatically:
    - Enables W&B monitoring.
    - Creates a fresh, timestamped session run.
    - Begins tracking all metrics.

2.  **Make API Calls**: Use the application as you normally would. Every analysis request automatically logs:
    - API Costs (OpenAI, Gemini)
    - Execution Times
    - Token Usage
    - System Health (CPU, Memory, GPU)

3.  **Check Your Dashboard**: All data is streamed in real-time to your personal dashboard.
    - **URL**: [https://wandb.ai/arunchukkala-lamar-university/multimodal-medical-diagnosis](https://wandb.ai/arunchukkala-lamar-university/multimodal-medical-diagnosis)

### ✨ Key Features

-   ✅ **Automatic Cost Calculation**: No manual math needed.
-   ✅ **Per-Provider Tracking**: Instantly see which API is cheaper and faster.
-   ✅ **System Health Monitoring**: Keep an eye on CPU, GPU, and Memory usage.
-   ✅ **Easy-to-Read Charts**: Simple X-axis (time) and Y-axis (metric value).
-   ✅ **Per-Session Tracking**: Each server start creates a new, clean run.
-   ✅ **Real-time Updates**: Metrics appear on your dashboard instantly.
-   ✅ **Mobile Friendly**: Check your dashboard from anywhere with the W&B app.

---

## 📊 2. Understanding the Dashboard & Charts

### 🎯 The Two Axes Explained Simply

-   **X-Axis (Horizontal)**: Represents **TIME**. The further right you go, the more recent the data.
-   **Y-Axis (Vertical)**: Represents the **METRIC VALUE**. The higher up the chart, the larger the value (e.g., higher cost, slower time, more memory used).

### 📈 How to Read a Line Chart

Line charts are the most common type you'll see. They show how a metric changes over time.

```
Value
  |     ↗ Going up = Increasing (e.g., costs are rising)
  |    /
  |___/  ↘ Going down = Decreasing (e.g., performance is improving)
  |_____ Time →
```

-   **Spiky Line (↗↘)**: Inconsistent or volatile metric (e.g., unstable network).
-   **Flat Line (→)**: Stable and consistent metric (e.g., steady costs).

###  visual-guide-to-charts

For more visual examples, see the **Visual Guide to Understanding W&B Charts** section below.

---

## 💰 3. Key Metrics to Watch

This is a quick reference for the most important metrics available on your dashboard.

### 💰 Cost Metrics

| Metric | What It Means | Good Value |
| --- | --- | --- |
| `costs/total_cost_usd` | Total money spent across all APIs. | Lower is better |
| `costs/openai/total_cost_usd` | Total spending on OpenAI. | Compare with Gemini |
| `costs/gemini/total_cost_usd` | Total spending on Gemini. | Compare with OpenAI |
| `costs/openai/api_calls` | Number of times OpenAI was called. | Track usage |
| `costs/gemini/api_calls` | Number of times Gemini was called. | Track usage |

### ⏱️ Performance Metrics

| Metric | What It Means | Good Value |
| --- | --- | --- |
| `performance/openai/avg_execution_time_seconds` | Average OpenAI response time. | < 3 seconds |
| `performance/gemini/avg_execution_time_seconds` | Average Gemini response time. | < 2 seconds |
| `performance/openai/min_execution_time_seconds` | Fastest OpenAI response (best case). | Shows potential |
| `performance/openai/max_execution_time_seconds` | Slowest OpenAI response (worst case). | Shows bottlenecks |

### 🖥️ System Health Metrics

| Metric | What It Means | Good Value |
| --- | --- | --- |
| `system/cpu_usage_percent` | CPU load on the server. | 30-70% |
| `system/memory_percent_used` | RAM percentage currently in use. | < 80% |
| `system/gpu_0/memory_percent_used` | GPU memory usage (if available). | 50-95% |

---

## 🛠️ 4. Setup & Technical Details

### 📦 Files Created

-   **`app/core/cost_tracker.py`**: The engine that calculates costs and system metrics.
-   **`app/core/fresh_wandb_monitor.py`**: The enhanced W&B wrapper that logs all data.
-   **`start_fresh_app.py`**: The recommended script to start the server with monitoring enabled.
-   **`test_cost_tracking.py`**: A script to test and verify all new tracking features.

### 💰 API Pricing Used

-   **OpenAI (gpt-4o-mini)**: $0.00015 / 1K input tokens, $0.0006 / 1K output tokens.
-   **Gemini (gemini-2.5-flash)**: $0.000075 / 1K input tokens, $0.0003 / 1K output tokens.

### ⚙️ Initial Setup

1.  **Install Dependencies**: `pip install wandb==0.17.0 psutil`
2.  **Get API Key**: Get your key from [https://wandb.ai/authorize](https://wandb.ai/authorize).
3.  **Configure Environment**: Create a `.env` file in the project root with the following:
    ```
    # Enable W&B monitoring
    WANDB_ENABLED=true

    # Your API key from wandb.ai/authorize
    WANDB_API_KEY=your_actual_api_key_here
    ```

---

## 🎨 5. Customizing Your Dashboard

You can create your own reports and charts in W&B.

1.  **Go to Your Project**: [https://wandb.ai/arunchukkala-lamar-university/multimodal-medical-diagnosis](https://wandb.ai/arunchukkala-lamar-university/multimodal-medical-diagnosis)
2.  **Click "Create Report"**.
3.  **Add Panels** to visualize the metrics you care about.

#### Example: Add a Cost Chart

1.  Add a new panel.
2.  Select metrics: `costs/total_cost_usd`, `costs/openai/total_cost_usd`, `costs/gemini/total_cost_usd`.
3.  Choose chart type: "Line Chart".
4.  Title the panel: "API Costs Over Time".

#### Example: Add a Performance Chart

1.  Add a new panel.
2.  Select metrics: `performance/openai/avg_execution_time_seconds`, `performance/gemini/avg_execution_time_seconds`.
3.  Choose chart type: "Line Chart".
4.  Title the panel: "API Response Times".

---

## 💡 6. Analysis & Decision Making

### ❓ Answering Key Questions

-   **Which API is cheaper?**
    -   Compare `costs/openai/total_cost_usd` vs. `costs/gemini/total_cost_usd`.
    -   Divide each by their respective `api_calls` to get cost-per-call.

-   **Which API is faster?**
    -   Compare `performance/openai/avg_execution_time_seconds` vs. `performance/gemini/avg_execution_time_seconds`.

-   **Is my system healthy?**
    -   `system/cpu_usage_percent` should ideally be between 30-70%.
    -   `system/memory_percent_used` should be below 80% to avoid slowdowns.

### 🌍 Real-World Example

**Scenario**: You run 100 medical diagnoses.

**Your Dashboard Might Show**:

| Provider | Calls | Total Cost | Avg. Time | Success Rate |
| --- | --- | --- | --- | --- |
| OpenAI | 60 | $0.024 | 2.5s | 98% |
| Gemini | 40 | $0.003 | 1.8s | 100% |

**Decision**: Gemini is significantly cheaper and faster for this workload. It would be wise to prioritize it in the VLM router.

---

## 🆘 7. Troubleshooting & Support

| Problem | Solution |
| --- | --- |
| No data showing on dashboard | Ensure the app is running and `WANDB_ENABLED=true` is set in your `.env` file. |
| Metrics are all zero | Make sure API calls are actually being made in the application. |
| Charts look strange or broken | Try refreshing the W&B page. |
| Missing GPU metrics | GPU metrics will only appear if a CUDA-enabled GPU is detected and used. |

-   **W&B Docs**: [https://docs.wandb.ai](https://docs.wandb.ai)
-   **Check Logs**: `.\wandb\run-*\logs`

---

## 🖼️ Appendix: Visual Guide to Understanding W&B Charts

### Line Chart Examples

-   **Increasing Costs**: The line goes up and to the right. You're spending more over time.
    !increasing_costs_chart
-   **Improving Performance**: The line goes down and to the right. Your API is getting faster.
    !improving_performance_chart
-   **Inconsistent Performance**: The line is spiky. Your API response times are unpredictable.
    !inconsistent_performance_chart

### Bar Chart Example

-   **API Cost Comparison**: Taller bar means higher cost. Easy to see which provider is more expensive.
    !cost_comparison_bar_chart

### System Health Examples

-   **Healthy CPU Usage (30-70%)**: The line stays in the middle of the chart.
    !healthy_cpu_chart
-   **High Memory Usage (>80%)**: The line is near the top of the chart, indicating a risk of slowdowns.
    !high_memory_chart
