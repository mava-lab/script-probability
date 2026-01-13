import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os

class ZumaModernSampler:
    def __init__(self, root):
        self.root = root
        self.root.title("Zuma 概率分布分析工具 v2.1")
        
        # 针对 11 寸 Mac 优化初始大小
        self.root.geometry("1000x850")
        self.root.minsize(800, 600)
        
        # 配置文件名
        self.file_name = 'Zuma_20260113.xlsx'
        self.sheet_name = '工作表2'
        
        self.sub_tables = {}
        self.t1_data = {}
        
        self.style = ttk.Style()
        self.setup_ui()
        self.load_excel_data()

    def load_excel_data(self):
        if not os.path.exists(self.file_name):
            self.status_label.config(text=f"❌ 找不到文件: {self.file_name}", foreground="#e74c3c")
            return

        try:
            # 读取 Excel
            df = pd.read_excel(self.file_name, sheet_name=self.sheet_name, header=None, engine='openpyxl')
            
            # 定位 Table 1
            t1_idx = None
            for idx, val in df.iloc[:, 1].items():
                if "Table 1" in str(val):
                    t1_idx = idx
                    break
            
            if t1_idx is None:
                messagebox.showerror("格式错误", "未找到 'Table 1' 标识")
                return

            # 解析 Table 1
            labels = df.iloc[t1_idx + 1, 2:].dropna().tolist()
            weights = df.iloc[t1_idx + 2, 2:2+len(labels)].astype(float).tolist()
            mapping = df.iloc[t1_idx + 3, 2:2+len(labels)].tolist()
            self.t1_data = {'labels': labels, 'weights': weights, 'mapping': mapping}

            # 解析子表
            self.sub_tables = {}
            for idx, val in df.iloc[:, 2].items():
                val_str = str(val).strip()
                if "Table" in val_str and "Table 1" not in val_str:
                    table_id = val_str.replace(" ", "")
                    vals = df.iloc[idx + 1, 2:].dropna().astype(float).tolist()
                    weights_sub = df.iloc[idx + 2, 2:2+len(vals)].astype(float).tolist()
                    self.sub_tables[table_id] = (vals, weights_sub)
            
            self.status_label.config(text=f"✅ 数据加载成功: 已识别 {len(self.sub_tables)} 个权重表", foreground="#27ae60")
            
        except Exception as e:
            messagebox.showerror("读取失败", f"Excel 处理出错: {e}")

    def setup_ui(self):
        self.style.configure("TButton", font=("Heiti SC", 12), padding=6)
        self.style.configure("Header.TLabel", font=("Heiti SC", 18, "bold"))

        main_container = ttk.Frame(self.root, padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)

        header_label = ttk.Label(main_container, text="ZUMA 权重随机模拟分析", style="Header.TLabel")
        header_label.pack(pady=(0, 20))

        ctrl_frame = ttk.LabelFrame(main_container, text=" 参数配置 ", padding="15")
        ctrl_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(ctrl_frame, text="模拟抽样次数:", font=("Heiti SC", 11)).pack(side=tk.LEFT, padx=10)
        self.times_entry = ttk.Entry(ctrl_frame, width=15, font=("Arial", 12))
        self.times_entry.insert(0, "1000")
        self.times_entry.pack(side=tk.LEFT, padx=10)

        self.run_btn = ttk.Button(ctrl_frame, text="▶ 执行模拟", command=self.run_sampling)
        self.run_btn.pack(side=tk.LEFT, padx=20)

        self.status_label = ttk.Label(ctrl_frame, text="就绪", font=("Heiti SC", 10))
        self.status_label.pack(side=tk.RIGHT, padx=10)

        result_frame = ttk.Frame(main_container)
        result_frame.pack(fill=tk.BOTH, expand=True)

        self.result_area = scrolledtext.ScrolledText(
            result_frame, 
            width=100, 
            height=35, 
            font=("Menlo", 11),
            padx=15,
            pady=15,
            background="#f8f9fa",
            foreground="#2c3e50",
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#dee2e6"
        )
        self.result_area.pack(fill=tk.BOTH, expand=True)
        
        # 配置颜色标签
        self.result_area.tag_configure("win_red", foreground="#e74c3c", font=("Menlo", 11, "bold"))
        self.result_area.tag_configure("summary_title", font=("Heiti SC", 12, "bold"), spacing1=10)
        self.result_area.tag_configure("total_blue", foreground="#3498db", font=("Menlo", 12, "bold"))

    def sample_one(self):
        t1_w = self.t1_data['weights']
        idx = np.random.choice(len(t1_w), p=np.array(t1_w)/sum(t1_w))
        label = self.t1_data['labels'][idx]
        if label == '0.0-0.0': return 0.0
        
        target_table = str(self.t1_data['mapping'][idx]).replace(" ", "")
        if target_table in self.sub_tables:
            v, w = self.sub_tables[target_table]
            return v[np.random.choice(len(w), p=np.array(w)/sum(w))]
        return 0.0

    def run_sampling(self):
        if not self.t1_data: return
        try:
            times = int(self.times_entry.get())
        except: return

        self.result_area.delete(1.0, tk.END)
        self.result_area.insert(tk.END, f"📋 正在生成 {times} 次随机样本...\n\n")
        
        results = []
        player_win_count = 0
        
        for i in range(1, times + 1):
            res = self.sample_one()
            results.append(res)
            
            res_str = f"{res:>8.2f} " 
            
            if res > 1:
                player_win_count += 1
                self.result_area.insert(tk.END, res_str, "win_red")
            else:
                self.result_area.insert(tk.END, res_str)
            
            if i % 10 == 0:
                self.result_area.insert(tk.END, "\n")
        
        # 基础统计
        total_gains = sum(results) # 计算玩家总获得
        avg_gain = total_gains / times if times > 0 else 0
        zero_count = results.count(0.0)
        any_win_count = times - zero_count
        
        # 统计面板展示
        self.result_area.insert(tk.END, f"\n\n{'━'*60}\n", "summary_title")
        self.result_area.insert(tk.END, "📊 模拟统计报告\n", "summary_title")
        self.result_area.insert(tk.END, f"  • 总样本量: {times}\n")
        self.result_area.insert(tk.END, f"  • 零收益(0.0): {zero_count} 次\n")
        self.result_area.insert(tk.END, f"  • 命中奖池(>0): {any_win_count} 次 (命中率: {(any_win_count/times)*100:.2f}%)\n")
        
        win_rate = (player_win_count / times) * 100
        self.result_area.insert(tk.END, f"  • 玩家获胜(>1): {player_win_count} 次 (获胜率: {win_rate:.2f}%)\n", "win_red")
        
        # 新增统计项：玩家总获得
        self.result_area.insert(tk.END, f"  • 玩家总获得: {total_gains:.2f}", "total_blue")
        self.result_area.insert(tk.END, f" (单局平均: {avg_gain:.4f})\n")
        
        self.result_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ZumaModernSampler(root)
    root.mainloop()