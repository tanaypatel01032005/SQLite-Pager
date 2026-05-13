import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESULT_PATH = os.path.join(DATA_DIR, "masters_results.json")
OUTPUT_DIR = os.path.join(DATA_DIR, "plots")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Set style
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({'font.size': 12, 'figure.autolayout': True})

def load_data():
    with open(RESULT_PATH, "r") as f:
        return json.load(f)

def plot_exp1(data):
    print("Plotting EXP 1...")
    modes = list(data.keys())
    means = [data[m]["mean"] for m in modes]
    stds = [data[m]["std"] for m in modes]
    
    plt.figure(figsize=(8, 6))
    bars = plt.bar(modes, means, yerr=stds, capsize=10, color=['#4C72B0', '#55A868'])
    plt.ylabel("Execution Time (s)")
    plt.title("Journaling Mode Performance (1000 Indiv. Commits)\nMean $\pm$ Std Dev")
    
    # Add labels
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{height:.2f}s', ha='center', va='bottom', fontweight='bold')
    
    plt.savefig(os.path.join(OUTPUT_DIR, "journal_throughput.png"), dpi=300)
    plt.close()

def plot_exp2(data):
    print("Plotting EXP 2...")
    sizes = [int(s) for s in data.keys()]
    latencies = [data[s]["mean"] * 1000 for s in data.keys()] # ms
    
    plt.figure(figsize=(10, 6))
    plt.plot(sizes, latencies, marker='o', linewidth=2, color='#C44E52')
    plt.xscale('log')
    plt.xlabel("Cache Size (Pages)")
    plt.ylabel("Read Latency (ms)")
    plt.title("The Cache Inflection Point\nLatency vs. Available PCache Size")
    
    # Identify knee (simplified)
    plt.annotate('Knee of the Curve', xy=(100, latencies[5]), xytext=(200, max(latencies)*0.8),
                 arrowprops=dict(facecolor='black', shrink=0.05))
    
    plt.grid(True, which="both", ls="-", alpha=0.5)
    plt.savefig(os.path.join(OUTPUT_DIR, "cache_inflection.png"), dpi=300)
    plt.close()

def plot_exp3(data):
    print("Plotting EXP 3...")
    threads = [int(t) for t in data.keys()]
    throughput = [data[t] for t in data.keys()]
    
    plt.figure(figsize=(10, 6))
    plt.plot(threads, throughput, marker='s', linewidth=2, color='#8172B2')
    plt.xlabel("Concurrent Threads")
    plt.ylabel("Throughput (Ops/sec)")
    plt.title("Concurrency Scaling (80% Read / 20% Write)\nWAL Mode with Shared Memory Index")
    plt.xticks(threads)
    
    plt.savefig(os.path.join(OUTPUT_DIR, "concurrency_scaling.png"), dpi=300)
    plt.close()

def plot_exp5(data):
    print("Plotting EXP 5...")
    modes = list(data.keys())
    waf = [data[m]["waf"] for m in modes]
    
    plt.figure(figsize=(8, 6))
    colors = ['#CCB974', '#64B5CD']
    bars = plt.bar(modes, waf, color=colors)
    plt.ylabel("Write Amplification Factor (WAF)")
    plt.title("Write Amplification: Physical vs. Logical I/O")
    
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                 f'{height:.2f}x', ha='center', va='bottom', fontweight='bold')
    
    plt.savefig(os.path.join(OUTPUT_DIR, "write_amplification.png"), dpi=300)
    plt.close()

def main():
    try:
        data = load_data()
        plot_exp1(data["exp1"])
        plot_exp2(data["exp2"])
        plot_exp3(data["exp3"])
        plot_exp5(data["exp5"])
        print(f"All plots generated in {OUTPUT_DIR}")
    except Exception as e:
        print(f"Error generating plots: {e}")

if __name__ == "__main__":
    main()
