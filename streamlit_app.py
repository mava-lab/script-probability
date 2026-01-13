import streamlit as st
import pandas as pd
import numpy as np

# 设置网页配置
st.set_page_config(page_title="Zuma 权重概率模拟器", layout="wide")

st.title("📊 Zuma 权重随机模拟分析工具")
st.markdown("---")

# 侧边栏：文件上传
st.sidebar.header("配置区域")
uploaded_file = st.sidebar.file_uploader("请上传 Zuma_20260113.xlsx 文件", type=["xlsx"])
times = st.sidebar.number_input("模拟抽样次数", min_value=1, max_value=100000, value=1000)
run_button = st.sidebar.button("▶ 开始模拟")

def load_data(file):
    try:
        # 读取 Excel 的 工作表2
        df = pd.read_excel(file, sheet_name='工作表2', header=None, engine='openpyxl')
        
        # 定位 Table 1
        t1_idx = None
        for idx, val in df.iloc[:, 1].items():
            if "Table 1" in str(val):
                t1_idx = idx
                break
        
        if t1_idx is None:
            return None, None, "未找到 Table 1 标识"

        # 解析 Table 1
        labels = df.iloc[t1_idx + 1, 2:].dropna().tolist()
        weights = df.iloc[t1_idx + 2, 2:2+len(labels)].astype(float).tolist()
        mapping = df.iloc[t1_idx + 3, 2:2+len(labels)].tolist()
        t1_data = {'labels': labels, 'weights': weights, 'mapping': mapping}

        # 解析子表
        sub_tables = {}
        for idx, val in df.iloc[:, 2].items():
            val_str = str(val).strip()
            if "Table" in val_str and "Table 1" not in val_str:
                table_id = val_str.replace(" ", "")
                vals = df.iloc[idx + 1, 2:].dropna().astype(float).tolist()
                weights_sub = df.iloc[idx + 2, 2:2+len(vals)].astype(float).tolist()
                sub_tables[table_id] = (vals, weights_sub)
        
        return t1_data, sub_tables, "Success"
    except Exception as e:
        return None, None, str(e)

def sample_one(t1_data, sub_tables):
    t1_w = t1_data['weights']
    idx = np.random.choice(len(t1_w), p=np.array(t1_w)/sum(t1_w))
    label = t1_data['labels'][idx]
    if label == '0.0-0.0': return 0.0
    
    target_table = str(t1_data['mapping'][idx]).replace(" ", "")
    if target_table in sub_tables:
        v, w = sub_tables[target_table]
        return v[np.random.choice(len(w), p=np.array(w)/sum(w))]
    return 0.0

if uploaded_file:
    t1_data, sub_tables, msg = load_data(uploaded_file)
    
    if t1_data:
        st.success(f"✅ 成功加载文件！检测到 {len(sub_tables)} 个细分权重表。")
        
        if run_button:
            # 执行模拟
            results = [sample_one(t1_data, sub_tables) for _ in range(times)]
            
            # --- 展示统计结果 ---
            total_gains = sum(results)
            zero_count = results.count(0.0)
            player_win_count = sum(1 for r in results if r > 1)
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("总获得", f"{total_gains:.2f}")
            col2.metric("平均回报 (RTP)", f"{(total_gains/times):.4f}")
            col3.metric("未中奖 (0.0)", f"{zero_count}次")
            col4.metric("玩家获胜 (>1)", f"{player_win_count}次")

            st.markdown("### 抽样明细 (大于 1 的结果已标红)")
            
            # --- 结果展示 (使用颜色显示) ---
            # 网页版使用 Markdown 展示更美观
            display_html = '<div style="font-family: monospace; line-height: 2.0; font-size: 14px;">'
            for i, res in enumerate(results, 1):
                color = "#ff4b4b" if res > 1 else "#31333F"
                font_weight = "bold" if res > 1 else "normal"
                display_html += f'<span style="color: {color}; font-weight: {font_weight}; margin-right: 15px;">[{i:03d}]: {res:>6.2f}</span>'
                if i % 8 == 0: display_html += "<br>"
            display_html += '</div>'
            
            st.write(display_html, unsafe_allow_html=True)
    else:
        st.error(f"数据解析失败: {msg}")
else:
    st.info("💡 请在左侧侧边栏上传 Excel 文件以开始。")
    