import streamlit as st
import pandas as pd
import numpy as np
import time
from bisect import bisect_right

# 网页配置
st.set_page_config(page_title="Zuma 权重 & 映射专业模拟器", layout="wide")

st.title("📊 Zuma 权重随机模拟分析工具 (网页版 v3.4)")
st.markdown("""
通过上传 Excel 文件，模拟 Zuma 概率分布并映射 NewTimes 离散值。
- **红色**: 获胜 ($x > 1$)
- **绿色**: 中奖但未过倍 ($0 < x \le 1$)
- **灰色**: 未中奖 ($x = 0$)
""")

# 侧边栏配置
st.sidebar.header("📁 文件上传")
file_zuma = st.sidebar.file_uploader("1. 上传 Zuma_20260113.xlsx", type=["xlsx"])
file_times = st.sidebar.file_uploader("2. 上传 NewTimes.xlsx", type=["xlsx"])

st.sidebar.markdown("---")
st.sidebar.header("⚙️ 模拟设置")
num_samples = st.sidebar.number_input("模拟次数", min_value=1, max_value=50000, value=1000)
run_btn = st.sidebar.button("▶ 开始模拟", use_container_width=True)

# 数据加载函数
@st.cache_data
def load_and_parse_files(fz, ft):
    try:
        # 解析 Zuma 权重
        df_z = pd.read_excel(fz, sheet_name='工作表2', header=None, engine='openpyxl')
        t1_idx = next(i for i, v in df_z.iloc[:, 1].items() if "Table 1" in str(v))
        t1 = {
            'labels': df_z.iloc[t1_idx + 1, 2:].dropna().tolist(),
            'weights': df_z.iloc[t1_idx + 2, 2:].dropna().astype(float).tolist(),
            'mapping': df_z.iloc[t1_idx + 3, 2:].tolist()
        }
        
        subs = {}
        for idx, val in df_z.iloc[:, 2].items():
            if "Table" in str(val) and "Table 1" not in str(val):
                table_id = str(val).replace(" ", "")
                subs[table_id] = (
                    df_z.iloc[idx + 1, 2:].dropna().astype(float).tolist(),
                    df_z.iloc[idx + 2, 2:].dropna().astype(float).tolist()
                )
        
        # 解析 NewTimes 映射列表
        df_t = pd.read_excel(ft, engine='openpyxl')
        mapping_list = sorted([round(float(x), 2) for x in df_t.iloc[:, 0].dropna().unique()])
        
        return t1, subs, mapping_list, None
    except Exception as e:
        return None, None, None, str(e)

if file_zuma and file_times:
    t1_data, sub_tables, mapping_list, err = load_and_parse_files(file_zuma, file_times)
    
    if err:
        st.error(f"文件解析出错: {err}")
    else:
        st.sidebar.success("✅ 文件已加载")
        
        if run_btn:
            # --- 执行模拟 ---
            start_time = time.perf_counter()
            
            res_x = [] # 原始值
            res_y = [] # 映射值
            diff_records = [] # 差异记录 [(序号, x, y)]
            
            # 随机权重准备
            t1_weights = np.array(t1_data['weights'])
            t1_p = t1_weights / t1_weights.sum()
            
            for i in range(1, num_samples + 1):
                # 1. 第一层随机
                idx = np.random.choice(len(t1_data['labels']), p=t1_p)
                label = t1_data['labels'][idx]
                
                x = 0.0
                if label != '0.0-0.0':
                    t_id = str(t1_data['mapping'][idx]).replace(" ", "")
                    v_s, w_s = sub_tables[t_id]
                    # 2. 第二层随机
                    x = v_s[np.random.choice(len(w_s), p=np.array(w_s)/sum(w_s))]
                
                # 3. NewTimes 映射
                y = 0.0
                if x > 0:
                    midx = bisect_right(mapping_list, round(x, 2))
                    y = mapping_list[max(0, midx-1)] if midx > 0 else mapping_list[0]
                
                res_x.append(x)
                res_y.append(y)
                
                if round(x, 2) != round(y, 2):
                    diff_records.append((i, x, y))

            duration_ms = (time.perf_counter() - start_time) * 1000

            # --- 统计面板 ---
            st.markdown("### 📈 模拟统计报告")
            st_col1, st_col2, st_col3, st_col4 = st.columns(4)
            
            total_gains = sum(res_x)
            rtp = total_gains / num_samples
            win_over_1 = sum(1 for x in res_x if x > 1)
            
            st_col1.metric("玩家总获得 (X)", f"{total_gains:.2f}")
            st_col2.metric("理论 RTP", f"{rtp:.4f}")
            st_col3.metric("获胜次数 (>1)", f"{win_over_1}次")
            st_col4.metric("计算耗时", f"{duration_ms:.2f} ms")

            # --- 抽样明细展示 ---
            st.markdown("### 📋 抽样明细")
            
            # 使用 HTML 构建网格视图，适配颜色
            html_content = '<div style="font-family: monospace; font-size: 13px; line-height: 1.8;">'
            for i, (x, y) in enumerate(zip(res_x, res_y), 1):
                rx, ry = round(x, 2), round(y, 2)
                
                # 颜色判断逻辑
                if rx == 0:
                    color = "#7f8c8d" # 灰色
                    display_text = "0.00"
                elif rx > 1:
                    color = "#e74c3c" # 红色
                    display_text = f"{rx:.2f}({ry:.2f})" if rx != ry else f"{rx:.2f}"
                else:
                    color = "#27ae60" # 绿色 (0 < x <= 1)
                    display_text = f"{rx:.2f}({ry:.2f})" if rx != ry else f"{rx:.2f}"
                
                # 拼接 HTML
                html_content += f'<span style="color: {color}; margin-right: 15px;">[{i:03d}]: {display_text}</span>'
                if i % 8 == 0:
                    html_content += "<br>"
            
            html_content += '</div>'
            st.write(html_content, unsafe_allow_html=True)

            # --- 差异明细 ---
            with st.expander(f"📌 查看映射差异项清单 ({len(diff_records)}次)"):
                if diff_records:
                    diff_df = pd.DataFrame(diff_records, columns=["序号", "原始随机值(x)", "映射值(y)"])
                    st.dataframe(diff_df, use_container_width=True)
                else:
                    st.write("本次模拟中，所有随机值均在映射表中精确匹配。")
else:
    st.info("👋 请在侧边栏上传所需的两个 Excel 文件以开始模拟。")