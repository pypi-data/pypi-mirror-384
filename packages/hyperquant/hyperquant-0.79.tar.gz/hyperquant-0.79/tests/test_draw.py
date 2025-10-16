from hyperquant.draw import draw
import pandas as pd

# 假设 df 里有两列: "time" 和 "pnl"
df = pd.DataFrame({
    "time": pd.date_range("2025-01-01", periods=100, freq="D"),
    "pnl": (1 + 0.01 * pd.Series(range(100))).cumprod()  # 模拟净值曲线
})

# 配置图表
data_dict = [{
    "col": "pnl",          # 要画的列
    "series_name": "盈利曲线",  # 曲线名称
    "draw_type": "Line",   # 类型：曲线
    "color": "red",        # 可选，指定颜色
    "height": 500,         # 子图高度（像素）
    "is_smooth": True,     # 曲线是否平滑
    "dec_length": 2        # 小数显示位数
}]

# 绘制
draw(
    df=df,
    data_dict=data_dict,
    date_col="time",
    title="策略盈利曲线",
    path="pnl_chart.html",
    show=True
)