"""
ivolatility_backtesting.py - UNIVERSAL BACKTEST FRAMEWORK
Version 4.1 - Dual RAM Display (Process + Container)

Key Features:
- ResourceMonitor: CPU/RAM tracking (cgroups v2 + psutil fallback)
- Enhanced progress bar with ETA, CPU%, RAM
- Shows BOTH Python process RAM AND container total RAM
- api_call(): Auto-normalization for dict/DataFrame responses
- 30+ metrics, charts, exports
- One-command: run_backtest()

Usage:
    from ivolatility_backtesting import *
    
    init_api(os.getenv("API_KEY"))
    
    data = api_call('/equities/eod/stock-prices', 
                   symbol='AAPL', 
                   from_='2024-01-01',
                   to='2024-12-31',
                   debug=True)
    
    analyzer = run_backtest(my_strategy, CONFIG)

Resource Monitoring:
    - CPU: Process CPU % (smoothed over 5 readings)
    - RAM: Shows BOTH metrics when in container:
      * Green: Python process memory (your strategy)
      * Blue: Total container memory (includes Jupyter, cache, etc.)
    
Progress Display Example:
    Processing 2024-07-30 (144/252)
    ETA: 5m 23s | CPU: 46.8% | RAM: 856MB (42%) Python | 1280MB (64%) Container
    Container: 1.0 cores, 2.0GB limit
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import ivolatility as ivol
import os
import time
import psutil

sns.set_style('darkgrid')
plt.rcParams['figure.figsize'] = (15, 8)


# ============================================================
# RESOURCE MONITOR
# ============================================================
class ResourceMonitor:
    """Monitor CPU and RAM - shows PROCESS resources (Python), not full container"""
    
    def __init__(self, show_container_total=False):
        self.process = psutil.Process()
        self.cpu_count = psutil.cpu_count()
        self.last_cpu_time = None
        self.last_check_time = None
        self.use_cgroups = self._check_cgroups_v2()
        self.show_container_total = show_container_total  # False = process RAM, True = container RAM
        
        # CPU smoothing for more stable readings
        self.cpu_history = []
        self.cpu_history_max = 5  # Average over last 5 readings
        
        # Determine actual CPU quota for containers
        if self.use_cgroups:
            quota = self._read_cpu_quota()
            if quota and quota > 0:
                self.cpu_count = quota  # Override with container quota
        
        self.context = "Container" if self.use_cgroups else "Host"
        
    def _read_cpu_quota(self):
        """Read CPU quota from cgroups v2 (returns cores, e.g., 1.5)"""
        try:
            with open('/sys/fs/cgroup/cpu.max', 'r') as f:
                line = f.read().strip()
                if line == 'max':
                    return None  # No limit
                parts = line.split()
                if len(parts) == 2:
                    quota = int(parts[0])  # microseconds
                    period = int(parts[1])  # microseconds
                    return quota / period  # cores (e.g., 100000/100000 = 1.0)
        except:
            pass
        return None
        
    def get_context_info(self):
        """Returns monitoring context and resource limits"""
        if self.use_cgroups:
            current, max_mem = self._read_cgroup_memory()
            ram_info = ""
            if max_mem:
                max_mem_gb = max_mem / (1024**3)
                ram_info = f", {max_mem_gb:.1f}GB limit"
            
            mem_type = "container total" if self.show_container_total else "process only"
            return f"Container (CPU: {self.cpu_count:.1f} cores{ram_info}) - RAM: {mem_type}"
        else:
            total_ram_gb = psutil.virtual_memory().total / (1024**3)
            return f"Host ({self.cpu_count} cores, {total_ram_gb:.0f}GB RAM) - RAM: process"
        
    def _check_cgroups_v2(self):
        try:
            return os.path.exists('/sys/fs/cgroup/cpu.stat') and \
                   os.path.exists('/sys/fs/cgroup/memory.current')
        except:
            return False
    
    def _read_cgroup_cpu(self):
        try:
            with open('/sys/fs/cgroup/cpu.stat', 'r') as f:
                for line in f:
                    if line.startswith('usage_usec'):
                        return int(line.split()[1])
        except:
            pass
        return None
    
    def _read_cgroup_memory(self):
        try:
            with open('/sys/fs/cgroup/memory.current', 'r') as f:
                current = int(f.read().strip())
            with open('/sys/fs/cgroup/memory.max', 'r') as f:
                max_mem = f.read().strip()
                if max_mem == 'max':
                    max_mem = psutil.virtual_memory().total
                else:
                    max_mem = int(max_mem)
            return current, max_mem
        except:
            pass
        return None, None
    
    def get_cpu_percent(self):
        """Get CPU% with smoothing - shows container limits if in container, host if not"""
        if self.use_cgroups:
            current_time = time.time()
            current_cpu = self._read_cgroup_cpu()
            
            if current_cpu and self.last_cpu_time and self.last_check_time:
                time_delta = current_time - self.last_check_time
                cpu_delta = current_cpu - self.last_cpu_time
                
                if time_delta > 0:
                    # Calculate based on container CPU quota
                    cpu_percent = (cpu_delta / (time_delta * 1_000_000)) * 100
                    
                    # Clamp to container limits
                    cpu_percent = min(cpu_percent, 100 * self.cpu_count)
                    
                    # Add to history for smoothing
                    self.cpu_history.append(cpu_percent)
                    if len(self.cpu_history) > self.cpu_history_max:
                        self.cpu_history.pop(0)
                    
                    self.last_cpu_time = current_cpu
                    self.last_check_time = current_time
                    
                    # Return smoothed average
                    return round(sum(self.cpu_history) / len(self.cpu_history), 1)
            
            self.last_cpu_time = current_cpu
            self.last_check_time = current_time
        
        # Fallback: host resources with smoothing
        try:
            cpu = self.process.cpu_percent(interval=0.1)
            if cpu == 0:
                cpu = psutil.cpu_percent(interval=0.1)
            
            self.cpu_history.append(cpu)
            if len(self.cpu_history) > self.cpu_history_max:
                self.cpu_history.pop(0)
            
            return round(sum(self.cpu_history) / len(self.cpu_history), 1)
        except:
            return 0.0
    
    def get_memory_info(self):
        """
        Get memory usage - returns BOTH process and container/host
        
        Returns:
            tuple: (process_mb, process_pct, container_mb, container_pct)
                   If no container, container values = process values
        """
        try:
            # Get process memory (Python only)
            mem = self.process.memory_info()
            process_mb = mem.rss / (1024 * 1024)
            
            if self.use_cgroups:
                # Get container total and limit
                current, max_mem = self._read_cgroup_memory()
                if max_mem:
                    process_percent = (mem.rss / max_mem) * 100
                    
                    if current:
                        container_mb = current / (1024 * 1024)
                        container_percent = (current / max_mem) * 100
                        return (
                            round(process_mb, 1), 
                            round(process_percent, 1),
                            round(container_mb, 1),
                            round(container_percent, 1)
                        )
                    
                    # No container data, return process only
                    return (
                        round(process_mb, 1), 
                        round(process_percent, 1),
                        round(process_mb, 1),
                        round(process_percent, 1)
                    )
            
            # Host: calculate % of total RAM
            total = psutil.virtual_memory().total
            percent = (mem.rss / total) * 100
            
            # On host, process = "container" (no container isolation)
            return (
                round(process_mb, 1), 
                round(percent, 1),
                round(process_mb, 1),
                round(percent, 1)
            )
            
        except:
            return 0.0, 0.0, 0.0, 0.0


def create_progress_bar():
    """Create enhanced progress bar with ETA, CPU%, RAM"""
    from IPython.display import display
    import ipywidgets as widgets
    
    progress_bar = widgets.FloatProgress(
        value=0, min=0, max=100,
        description='Progress:',
        bar_style='info',
        style={'bar_color': '#00ff00'},
        layout=widgets.Layout(width='100%', height='30px')
    )
    
    status_label = widgets.HTML(
        value="<b style='color:#0066cc'>Starting...</b>"
    )
    
    display(widgets.VBox([progress_bar, status_label]))
    
    monitor = ResourceMonitor()
    start_time = time.time()
    
    return progress_bar, status_label, monitor, start_time


def update_progress(progress_bar, status_label, monitor, current, total, start_time, message="Processing"):
    """
    Update progress bar with ETA, CPU%, RAM (shows BOTH process and container)
    """
    progress = (current / total) * 100
    progress_bar.value = progress
    
    elapsed = time.time() - start_time
    if current > 0:
        eta_seconds = (elapsed / current) * (total - current)
        eta_str = format_time(eta_seconds)
    else:
        eta_str = "calculating..."
    
    cpu = monitor.get_cpu_percent()
    process_mb, process_pct, container_mb, container_pct = monitor.get_memory_info()
    
    # Build RAM display - show both if different, otherwise just one
    if abs(container_mb - process_mb) > 10:  # Significant difference (>10MB)
        ram_display = (
            f"RAM: <span style='color:#4CAF50'>{process_mb}MB ({process_pct}%)</span> Python | "
            f"<span style='color:#2196F3'>{container_mb}MB ({container_pct}%)</span> Container"
        )
    else:
        # Same values (on host or small difference)
        ram_display = f"RAM: {process_mb}MB ({process_pct}%)"
    
    # Context info
    if monitor.use_cgroups:
        context_info = f"Container: {monitor.cpu_count:.1f} cores"
        current, max_mem = monitor._read_cgroup_memory()
        if max_mem:
            context_info += f", {max_mem / (1024**3):.1f}GB limit"
    else:
        context_info = f"Host: {monitor.cpu_count} cores"
    
    status_label.value = (
        f"<b style='color:#0066cc'>{message} ({current}/{total})</b><br>"
        f"<span style='color:#666'>ETA: {eta_str} | CPU: {cpu}% | {ram_display}</span><br>"
        f"<span style='color:#999;font-size:10px'>{context_info}</span>"
    )


def format_time(seconds):
    """Format seconds to human readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# ============================================================
# API HELPER - AUTOMATIC NORMALIZATION
# ============================================================
class APIHelper:
    """Normalizes API responses to consistent format"""
    
    @staticmethod
    def normalize_response(response, debug=False):
        if response is None:
            if debug:
                print("[APIHelper] Response is None")
            return None
        
        if isinstance(response, dict):
            if 'data' in response:
                if debug:
                    print(f"[APIHelper] Dict response: {len(response['data'])} records")
                return response
            else:
                if debug:
                    print("[APIHelper] Dict without 'data' key")
                return None
        
        if isinstance(response, pd.DataFrame):
            if response.empty:
                if debug:
                    print("[APIHelper] Empty DataFrame")
                return None
            
            records = response.to_dict('records')
            if debug:
                print(f"[APIHelper] DataFrame converted: {len(records)} records")
            return {'data': records, 'status': 'success'}
        
        if debug:
            print(f"[APIHelper] Unexpected type: {type(response)}")
        return None


class APIManager:
    """Centralized API key management"""
    _api_key = None
    _methods = {}
    
    @classmethod
    def initialize(cls, api_key):
        if not api_key:
            raise ValueError("API key cannot be empty")
        cls._api_key = api_key
        ivol.setLoginParams(apiKey=api_key)
        print(f"[API] Initialized: {api_key[:10]}...{api_key[-5:]}")
    
    @classmethod
    def get_method(cls, endpoint):
        if cls._api_key is None:
            api_key = os.getenv("API_KEY")
            if not api_key:
                raise ValueError("API key not set. Call init_api(key) first")
            cls.initialize(api_key)
        
        if endpoint not in cls._methods:
            ivol.setLoginParams(apiKey=cls._api_key)
            cls._methods[endpoint] = ivol.setMethod(endpoint)
        
        return cls._methods[endpoint]


def init_api(api_key=None):
    """Initialize IVolatility API"""
    if api_key is None:
        api_key = os.getenv("API_KEY")
    APIManager.initialize(api_key)


def api_call(endpoint, debug=False, **kwargs):
    """Make API call with automatic response normalization"""
    try:
        if debug and APIManager._api_key:
            base_url = "https://restapi.ivolatility.com"
            url_params = {}
            for key, value in kwargs.items():
                clean_key = key.rstrip('_') if key.endswith('_') else key
                url_params[clean_key] = value
            
            params_str = "&".join([f"{k}={v}" for k, v in url_params.items()])
            full_url = f"{base_url}{endpoint}?apiKey={APIManager._api_key}&{params_str}"
            print(f"\n[API] Full URL:")
            print(f"[API] {full_url}\n")
        
        method = APIManager.get_method(endpoint)
        response = method(**kwargs)
        
        normalized = APIHelper.normalize_response(response, debug=debug)
        
        if normalized is None and debug:
            print(f"[api_call] Failed to get data")
            print(f"[api_call] Endpoint: {endpoint}")
            print(f"[api_call] Params: {kwargs}")
        
        return normalized
    
    except Exception as e:
        if debug:
            print(f"[api_call] Exception: {e}")
            print(f"[api_call] Endpoint: {endpoint}")
            print(f"[api_call] Params: {kwargs}")
        return None


# ============================================================
# BACKTEST RESULTS
# ============================================================
class BacktestResults:
    """Universal container for backtest results"""
    
    def __init__(self, equity_curve, equity_dates, trades, initial_capital, 
                 config, benchmark_prices=None, benchmark_symbol='SPY',
                 daily_returns=None, debug_info=None):
        
        self.equity_curve = equity_curve
        self.equity_dates = equity_dates
        self.trades = trades
        self.initial_capital = initial_capital
        self.final_capital = equity_curve[-1] if len(equity_curve) > 0 else initial_capital
        self.config = config
        self.benchmark_prices = benchmark_prices
        self.benchmark_symbol = benchmark_symbol
        self.debug_info = debug_info if debug_info else []
        
        if daily_returns is None and len(equity_curve) > 1:
            self.daily_returns = [
                (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
                for i in range(1, len(equity_curve))
            ]
        else:
            self.daily_returns = daily_returns if daily_returns else []
        
        self.max_drawdown = self._calculate_max_drawdown()
    
    def _calculate_max_drawdown(self):
        if len(self.equity_curve) < 2:
            return 0
        running_max = np.maximum.accumulate(self.equity_curve)
        drawdowns = (np.array(self.equity_curve) - running_max) / running_max * 100
        return abs(np.min(drawdowns))


# ============================================================
# BACKTEST ANALYZER (30+ METRICS)
# ============================================================
class BacktestAnalyzer:
    """Calculate all metrics from BacktestResults"""
    
    def __init__(self, results):
        self.results = results
        self.metrics = {}
    
    def calculate_all_metrics(self):
        r = self.results
        
        # Profitability
        self.metrics['total_pnl'] = r.final_capital - r.initial_capital
        self.metrics['total_return'] = (self.metrics['total_pnl'] / r.initial_capital) * 100
        
        # CAGR
        if len(r.equity_dates) > 0:
            start_date = min(r.equity_dates)
            end_date = max(r.equity_dates)
            days_diff = (end_date - start_date).days
            
            if days_diff <= 0:
                self.metrics['cagr'] = 0
                self.metrics['show_cagr'] = False
            else:
                years = days_diff / 365.25
                if years >= 1.0:
                    self.metrics['cagr'] = ((r.final_capital / r.initial_capital) ** (1/years) - 1) * 100
                    self.metrics['show_cagr'] = True
                else:
                    self.metrics['cagr'] = self.metrics['total_return'] * (365.25 / days_diff)
                    self.metrics['show_cagr'] = False
        else:
            self.metrics['cagr'] = 0
            self.metrics['show_cagr'] = False
        
        # Risk metrics
        self.metrics['sharpe'] = self._sharpe_ratio(r.daily_returns)
        self.metrics['sortino'] = self._sortino_ratio(r.daily_returns)
        self.metrics['max_drawdown'] = r.max_drawdown
        self.metrics['volatility'] = np.std(r.daily_returns) * np.sqrt(252) * 100 if len(r.daily_returns) > 0 else 0
        self.metrics['calmar'] = abs(self.metrics['total_return'] / r.max_drawdown) if r.max_drawdown > 0 else 0
        self.metrics['omega'] = self._omega_ratio(r.daily_returns)
        self.metrics['ulcer'] = self._ulcer_index(r.equity_curve)
        
        # VaR
        self.metrics['var_95'], self.metrics['var_95_pct'] = self._calculate_var(r.daily_returns, 0.95)
        self.metrics['var_99'], self.metrics['var_99_pct'] = self._calculate_var(r.daily_returns, 0.99)
        self.metrics['cvar_95'], self.metrics['cvar_95_pct'] = self._calculate_cvar(r.daily_returns, 0.95)
        
        avg_equity = np.mean(r.equity_curve) if len(r.equity_curve) > 0 else r.initial_capital
        self.metrics['var_95_dollar'] = self.metrics['var_95'] * avg_equity
        self.metrics['var_99_dollar'] = self.metrics['var_99'] * avg_equity
        self.metrics['cvar_95_dollar'] = self.metrics['cvar_95'] * avg_equity
        
        # Distribution
        self.metrics['tail_ratio'] = self._tail_ratio(r.daily_returns)
        self.metrics['skewness'], self.metrics['kurtosis'] = self._skewness_kurtosis(r.daily_returns)
        
        # Alpha/Beta
        self.metrics['alpha'], self.metrics['beta'], self.metrics['r_squared'] = self._alpha_beta(r)
        
        # Trading stats
        if len(r.trades) > 0:
            self._calculate_trading_stats(r.trades)
        else:
            self._set_empty_trading_stats()
        
        # Efficiency
        running_max = np.maximum.accumulate(r.equity_curve)
        max_dd_dollars = np.min(np.array(r.equity_curve) - running_max)
        self.metrics['recovery_factor'] = self.metrics['total_pnl'] / abs(max_dd_dollars) if max_dd_dollars != 0 else 0
        
        # Exposure time
        if len(r.trades) > 0 and 'start_date' in r.config and 'end_date' in r.config:
            total_days = (pd.to_datetime(r.config['end_date']) - pd.to_datetime(r.config['start_date'])).days
            self.metrics['exposure_time'] = self._exposure_time(r.trades, total_days)
        else:
            self.metrics['exposure_time'] = 0
        
        return self.metrics
    
    def _calculate_trading_stats(self, trades):
        trades_df = pd.DataFrame(trades)
        winning = trades_df[trades_df['pnl'] > 0]
        losing = trades_df[trades_df['pnl'] <= 0]
        
        self.metrics['total_trades'] = len(trades_df)
        self.metrics['winning_trades'] = len(winning)
        self.metrics['losing_trades'] = len(losing)
        self.metrics['win_rate'] = (len(winning) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
        
        wins_sum = winning['pnl'].sum() if len(winning) > 0 else 0
        losses_sum = abs(losing['pnl'].sum()) if len(losing) > 0 else 0
        self.metrics['profit_factor'] = wins_sum / losses_sum if losses_sum > 0 else float('inf')
        
        self.metrics['avg_win'] = winning['pnl'].mean() if len(winning) > 0 else 0
        self.metrics['avg_loss'] = losing['pnl'].mean() if len(losing) > 0 else 0
        self.metrics['best_trade'] = trades_df['pnl'].max()
        self.metrics['worst_trade'] = trades_df['pnl'].min()
        
        if len(winning) > 0 and len(losing) > 0:
            self.metrics['avg_win_loss_ratio'] = abs(self.metrics['avg_win'] / self.metrics['avg_loss'])
        else:
            self.metrics['avg_win_loss_ratio'] = 0
        
        self.metrics['max_win_streak'], self.metrics['max_loss_streak'] = self._win_loss_streaks(trades)
    
    def _set_empty_trading_stats(self):
        self.metrics.update({
            'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0,
            'win_rate': 0, 'profit_factor': 0, 'avg_win': 0, 'avg_loss': 0,
            'best_trade': 0, 'worst_trade': 0, 'avg_win_loss_ratio': 0,
            'max_win_streak': 0, 'max_loss_streak': 0
        })
    
    def _sharpe_ratio(self, returns):
        if len(returns) < 2:
            return 0
        return np.sqrt(252) * np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
    
    def _sortino_ratio(self, returns):
        if len(returns) < 2:
            return 0
        returns_array = np.array(returns)
        downside = returns_array[returns_array < 0]
        if len(downside) == 0 or np.std(downside) == 0:
            return 0
        return np.sqrt(252) * np.mean(returns_array) / np.std(downside)
    
    def _omega_ratio(self, returns, threshold=0):
        if len(returns) < 2:
            return 0
        returns_array = np.array(returns)
        gains = np.sum(np.maximum(returns_array - threshold, 0))
        losses = np.sum(np.maximum(threshold - returns_array, 0))
        return gains / losses if losses > 0 else float('inf')
    
    def _ulcer_index(self, equity_curve):
        if len(equity_curve) < 2:
            return 0
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        return np.sqrt(np.mean(drawdown ** 2)) * 100
    
    def _calculate_var(self, returns, confidence=0.95):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        returns_array = returns_array[~np.isnan(returns_array)]
        if len(returns_array) < 10:
            return 0, 0
        var_percentile = (1 - confidence) * 100
        var_return = np.percentile(returns_array, var_percentile)
        return var_return, var_return * 100
    
    def _calculate_cvar(self, returns, confidence=0.95):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        returns_array = returns_array[~np.isnan(returns_array)]
        if len(returns_array) < 10:
            return 0, 0
        var_percentile = (1 - confidence) * 100
        var_threshold = np.percentile(returns_array, var_percentile)
        tail_losses = returns_array[returns_array <= var_threshold]
        if len(tail_losses) == 0:
            return 0, 0
        cvar_return = np.mean(tail_losses)
        return cvar_return, cvar_return * 100
    
    def _tail_ratio(self, returns):
        if len(returns) < 20:
            return 0
        returns_array = np.array(returns)
        right = np.percentile(returns_array, 95)
        left = abs(np.percentile(returns_array, 5))
        return right / left if left > 0 else 0
    
    def _skewness_kurtosis(self, returns):
        if len(returns) < 10:
            return 0, 0
        returns_array = np.array(returns)
        mean = np.mean(returns_array)
        std = np.std(returns_array)
        if std == 0:
            return 0, 0
        skew = np.mean(((returns_array - mean) / std) ** 3)
        kurt = np.mean(((returns_array - mean) / std) ** 4) - 3
        return skew, kurt
    
    def _alpha_beta(self, results):
        if not hasattr(results, 'benchmark_prices') or not results.benchmark_prices:
            return 0, 0, 0
        if len(results.equity_dates) < 10:
            return 0, 0, 0
        
        benchmark_returns = []
        sorted_dates = sorted(results.equity_dates)
        
        for i in range(1, len(sorted_dates)):
            prev_date = sorted_dates[i-1]
            curr_date = sorted_dates[i]
            
            if prev_date in results.benchmark_prices and curr_date in results.benchmark_prices:
                prev_price = results.benchmark_prices[prev_date]
                curr_price = results.benchmark_prices[curr_date]
                bench_return = (curr_price - prev_price) / prev_price
                benchmark_returns.append(bench_return)
            else:
                benchmark_returns.append(0)
        
        if len(benchmark_returns) != len(results.daily_returns):
            return 0, 0, 0
        
        port_ret = np.array(results.daily_returns)
        bench_ret = np.array(benchmark_returns)
        
        bench_mean = np.mean(bench_ret)
        port_mean = np.mean(port_ret)
        
        covariance = np.mean((bench_ret - bench_mean) * (port_ret - port_mean))
        benchmark_variance = np.mean((bench_ret - bench_mean) ** 2)
        
        if benchmark_variance == 0:
            return 0, 0, 0
        
        beta = covariance / benchmark_variance
        alpha_daily = port_mean - beta * bench_mean
        alpha_annualized = alpha_daily * 252 * 100
        
        ss_res = np.sum((port_ret - (alpha_daily + beta * bench_ret)) ** 2)
        ss_tot = np.sum((port_ret - port_mean) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return alpha_annualized, beta, r_squared
    
    def _win_loss_streaks(self, trades):
        if len(trades) == 0:
            return 0, 0
        max_win = max_loss = current_win = current_loss = 0
        for trade in trades:
            if trade['pnl'] > 0:
                current_win += 1
                current_loss = 0
                max_win = max(max_win, current_win)
            else:
                current_loss += 1
                current_win = 0
                max_loss = max(max_loss, current_loss)
        return max_win, max_loss
    
    def _exposure_time(self, trades, total_days):
        if total_days <= 0 or len(trades) == 0:
            return 0
        days_with_positions = set()
        for trade in trades:
            entry = pd.to_datetime(trade['entry_date'])
            exit = pd.to_datetime(trade['exit_date'])
            date_range = pd.date_range(start=entry, end=exit, freq='D')
            days_with_positions.update(date_range.date)
        exposure_pct = (len(days_with_positions) / total_days) * 100
        return min(exposure_pct, 100.0)


# ============================================================
# RESULTS REPORTER
# ============================================================
class ResultsReporter:
    """Print comprehensive metrics report"""
    
    @staticmethod
    def print_full_report(analyzer):
        m = analyzer.metrics
        r = analyzer.results
        
        print("="*80)
        print(" "*25 + "BACKTEST RESULTS")
        print("="*80)
        print()
        
        if hasattr(r, 'debug_info') and len(r.debug_info) > 0:
            print("DEBUG INFORMATION")
            print("-"*80)
            for debug_msg in r.debug_info[:10]:
                print(debug_msg)
            if len(r.debug_info) > 10:
                print(f"... and {len(r.debug_info) - 10} more messages")
            print()
        
        print("PROFITABILITY METRICS")
        print("-"*80)
        print(f"Initial Capital:        ${r.initial_capital:>15,.2f}")
        print(f"Final Equity:           ${r.final_capital:>15,.2f}")
        print(f"Total P&L:              ${m['total_pnl']:>15,.2f}  (absolute profit/loss)")
        print(f"Total Return:            {m['total_return']:>15.2f}%  (% gain/loss)")
        if m['cagr'] != 0:
            if m['show_cagr']:
                print(f"CAGR:                    {m['cagr']:>15.2f}%  (annualized compound growth)")
            else:
                print(f"Annualized Return:       {m['cagr']:>15.2f}%  (extrapolated to 1 year)")
        print()
        
        print("RISK METRICS")
        print("-"*80)
        print(f"Sharpe Ratio:            {m['sharpe']:>15.2f}  (>1 good, >2 excellent)")
        print(f"Sortino Ratio:           {m['sortino']:>15.2f}  (downside risk, >2 good)")
        print(f"Calmar Ratio:            {m['calmar']:>15.2f}  (return/drawdown, >3 good)")
        if m['omega'] != 0:
            omega_display = f"{m['omega']:.2f}" if m['omega'] < 999 else "inf"
            print(f"Omega Ratio:             {omega_display:>15s}  (gains/losses, >1 good)")
        print(f"Maximum Drawdown:        {m['max_drawdown']:>15.2f}%  (peak to trough)")
        if m['ulcer'] != 0:
            print(f"Ulcer Index:             {m['ulcer']:>15.2f}%  (pain of drawdowns, lower better)")
        print(f"Volatility (ann.):       {m['volatility']:>15.2f}%  (annualized std dev)")
        
        if len(r.daily_returns) >= 10:
            print(f"VaR (95%, 1-day):        {m['var_95_pct']:>15.2f}% (${m['var_95_dollar']:>,.0f})  (max loss 95% confidence)")
            print(f"VaR (99%, 1-day):        {m['var_99_pct']:>15.2f}% (${m['var_99_dollar']:>,.0f})  (max loss 99% confidence)")
            print(f"CVaR (95%, 1-day):       {m['cvar_95_pct']:>15.2f}% (${m['cvar_95_dollar']:>,.0f})  (avg loss in worst 5%)")
        
        if m['tail_ratio'] != 0:
            print(f"Tail Ratio (95/5):       {m['tail_ratio']:>15.2f}  (big wins/losses, >1 good)")
        
        if m['skewness'] != 0 or m['kurtosis'] != 0:
            print(f"Skewness:                {m['skewness']:>15.2f}  (>0 positive tail)")
            print(f"Kurtosis (excess):       {m['kurtosis']:>15.2f}  (>0 fat tails)")
        
        if m['beta'] != 0 or m['alpha'] != 0:
            print(f"Alpha (vs {r.benchmark_symbol}):     {m['alpha']:>15.2f}%  (excess return)")
            print(f"Beta (vs {r.benchmark_symbol}):      {m['beta']:>15.2f}  (<1 defensive, >1 aggressive)")
            print(f"R^2 (vs {r.benchmark_symbol}):        {m['r_squared']:>15.2f}  (market correlation 0-1)")
        
        if abs(m['total_return']) > 200 or m['volatility'] > 150:
            print()
            print("⚠️  UNREALISTIC RESULTS DETECTED:")
            if abs(m['total_return']) > 200:
                print(f"  • Total return {m['total_return']:.1f}% is extremely high")
            if m['volatility'] > 150:
                print(f"  • Volatility {m['volatility']:.1f}% is higher than leveraged ETFs")
            print("  → Review configuration before trusting results")
        
        print()
        
        print("EFFICIENCY METRICS")
        print("-"*80)
        if m['recovery_factor'] != 0:
            print(f"Recovery Factor:         {m['recovery_factor']:>15.2f}  (profit/max DD, >3 good)")
        if m['exposure_time'] != 0:
            print(f"Exposure Time:           {m['exposure_time']:>15.1f}%  (time in market)")
        print()
        
        print("TRADING STATISTICS")
        print("-"*80)
        print(f"Total Trades:            {m['total_trades']:>15}")
        print(f"Winning Trades:          {m['winning_trades']:>15}")
        print(f"Losing Trades:           {m['losing_trades']:>15}")
        print(f"Win Rate:                {m['win_rate']:>15.2f}%  (% profitable trades)")
        print(f"Profit Factor:           {m['profit_factor']:>15.2f}  (gross profit/loss, >1.5 good)")
        if m['max_win_streak'] > 0 or m['max_loss_streak'] > 0:
            print(f"Max Win Streak:          {m['max_win_streak']:>15}  (consecutive wins)")
            print(f"Max Loss Streak:         {m['max_loss_streak']:>15}  (consecutive losses)")
        print(f"Average Win:            ${m['avg_win']:>15,.2f}")
        print(f"Average Loss:           ${m['avg_loss']:>15,.2f}")
        print(f"Best Trade:             ${m['best_trade']:>15,.2f}")
        print(f"Worst Trade:            ${m['worst_trade']:>15,.2f}")
        if m['avg_win_loss_ratio'] != 0:
            print(f"Avg Win/Loss Ratio:      {m['avg_win_loss_ratio']:>15.2f}  (avg win / avg loss)")
        print()
        print("="*80)


# ============================================================
# CHART GENERATOR
# ============================================================
class ChartGenerator:
    """Generate 6 professional charts"""
    
    @staticmethod
    def create_all_charts(analyzer, filename='backtest_results.png'):
        r = analyzer.results
        
        if len(r.trades) == 0:
            print("No trades to visualize")
            return
        
        trades_df = pd.DataFrame(r.trades)
        fig, axes = plt.subplots(3, 2, figsize=(18, 14))
        fig.suptitle('Backtest Results', fontsize=16, fontweight='bold', y=0.995)
        
        dates = pd.to_datetime(r.equity_dates)
        equity_array = np.array(r.equity_curve)
        
        # 1. Equity Curve
        ax1 = axes[0, 0]
        ax1.plot(dates, equity_array, linewidth=2.5, color='#2196F3')
        ax1.axhline(y=r.initial_capital, color='gray', linestyle='--', alpha=0.7)
        ax1.fill_between(dates, r.initial_capital, equity_array,
                         where=(equity_array >= r.initial_capital), 
                         alpha=0.3, color='green', interpolate=True)
        ax1.fill_between(dates, r.initial_capital, equity_array,
                         where=(equity_array < r.initial_capital), 
                         alpha=0.3, color='red', interpolate=True)
        ax1.set_title('Equity Curve', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Equity ($)')
        ax1.grid(True, alpha=0.3)
        
        # 2. Drawdown
        ax2 = axes[0, 1]
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max * 100
        ax2.fill_between(dates, 0, drawdown, alpha=0.6, color='#f44336')
        ax2.plot(dates, drawdown, color='#d32f2f', linewidth=2)
        ax2.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)
        
        # 3. P&L Distribution
        ax3 = axes[1, 0]
        pnl_values = trades_df['pnl'].values
        ax3.hist(pnl_values, bins=40, color='#4CAF50', alpha=0.7, edgecolor='black')
        ax3.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax3.set_title('P&L Distribution', fontsize=12, fontweight='bold')
        ax3.set_xlabel('P&L ($)')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Signal Performance
        ax4 = axes[1, 1]
        if 'signal' in trades_df.columns:
            signal_pnl = trades_df.groupby('signal')['pnl'].sum()
            colors = ['#4CAF50' if x > 0 else '#f44336' for x in signal_pnl.values]
            ax4.bar(signal_pnl.index, signal_pnl.values, color=colors, alpha=0.7, edgecolor='black')
            ax4.set_title('P&L by Signal', fontsize=12, fontweight='bold')
        else:
            ax4.text(0.5, 0.5, 'No signal data', ha='center', va='center', transform=ax4.transAxes)
        ax4.axhline(y=0, color='black', linewidth=1)
        ax4.grid(True, alpha=0.3, axis='y')
        
        # 5. Monthly Returns
        ax5 = axes[2, 0]
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
        trades_df['month'] = trades_df['exit_date'].dt.to_period('M')
        monthly_pnl = trades_df.groupby('month')['pnl'].sum()
        colors = ['#4CAF50' if x > 0 else '#f44336' for x in monthly_pnl.values]
        ax5.bar(range(len(monthly_pnl)), monthly_pnl.values, color=colors, alpha=0.7, edgecolor='black')
        ax5.set_title('Monthly P&L', fontsize=12, fontweight='bold')
        ax5.set_xticks(range(len(monthly_pnl)))
        ax5.set_xticklabels([str(m) for m in monthly_pnl.index], rotation=45, ha='right')
        ax5.axhline(y=0, color='black', linewidth=1)
        ax5.grid(True, alpha=0.3, axis='y')
        
        # 6. Top Symbols
        ax6 = axes[2, 1]
        if 'symbol' in trades_df.columns:
            symbol_pnl = trades_df.groupby('symbol')['pnl'].sum().sort_values(ascending=True).tail(10)
            colors = ['#4CAF50' if x > 0 else '#f44336' for x in symbol_pnl.values]
            ax6.barh(range(len(symbol_pnl)), symbol_pnl.values, color=colors, alpha=0.7, edgecolor='black')
            ax6.set_yticks(range(len(symbol_pnl)))
            ax6.set_yticklabels(symbol_pnl.index, fontsize=9)
            ax6.set_title('Top Symbols', fontsize=12, fontweight='bold')
        else:
            ax6.text(0.5, 0.5, 'No symbol data', ha='center', va='center', transform=ax6.transAxes)
        ax6.axvline(x=0, color='black', linewidth=1)
        ax6.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Chart saved: {filename}")


# ============================================================
# RESULTS EXPORTER
# ============================================================
class ResultsExporter:
    """Export results to CSV"""
    
    @staticmethod
    def export_all(analyzer, prefix='backtest'):
        r = analyzer.results
        m = analyzer.metrics
        
        if len(r.trades) == 0:
            print("No trades to export")
            return
        
        trades_df = pd.DataFrame(r.trades)
        trades_df['entry_date'] = pd.to_datetime(trades_df['entry_date']).dt.strftime('%Y-%m-%d')
        trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date']).dt.strftime('%Y-%m-%d')
        trades_df.to_csv(f'{prefix}_trades.csv', index=False)
        print(f"Exported: {prefix}_trades.csv")
        
        equity_df = pd.DataFrame({
            'date': pd.to_datetime(r.equity_dates).strftime('%Y-%m-%d'),
            'equity': r.equity_curve
        })
        equity_df.to_csv(f'{prefix}_equity.csv', index=False)
        print(f"Exported: {prefix}_equity.csv")
        
        with open(f'{prefix}_summary.txt', 'w') as f:
            f.write("BACKTEST SUMMARY\n")
            f.write("="*70 + "\n\n")
            f.write(f"Strategy: {r.config.get('strategy_name', 'Unknown')}\n")
            f.write(f"Period: {r.config.get('start_date')} to {r.config.get('end_date')}\n\n")
            f.write("PERFORMANCE\n")
            f.write("-"*70 + "\n")
            f.write(f"Total Return: {m['total_return']:.2f}%\n")
            f.write(f"Sharpe: {m['sharpe']:.2f}\n")
            f.write(f"Max DD: {m['max_drawdown']:.2f}%\n")
            f.write(f"Trades: {m['total_trades']}\n")
        
        print(f"Exported: {prefix}_summary.txt")


# ============================================================
# RUN BACKTEST
# ============================================================
def run_backtest(strategy_function, config, print_report=True,
                 create_charts=True, export_results=True,
                 chart_filename='backtest_results.png',
                 export_prefix='backtest'):
    """Run complete backtest with one command"""
    
    print("="*80)
    print(" "*25 + "STARTING BACKTEST")
    print("="*80)
    print(f"Strategy: {config.get('strategy_name', 'Unknown')}")
    print(f"Period: {config.get('start_date')} to {config.get('end_date')}")
    print(f"Capital: ${config.get('initial_capital', 0):,.0f}")
    print("="*80 + "\n")
    
    results = strategy_function(config)
    
    print("\n[*] Calculating metrics...")
    analyzer = BacktestAnalyzer(results)
    analyzer.calculate_all_metrics()
    
    if print_report:
        print("\n" + "="*80)
        ResultsReporter.print_full_report(analyzer)
    
    if create_charts and len(results.trades) > 0:
        print(f"\n[*] Creating charts: {chart_filename}")
        try:
            ChartGenerator.create_all_charts(analyzer, chart_filename)
        except Exception as e:
            print(f"[ERROR] Charts failed: {e}")
    
    if export_results and len(results.trades) > 0:
        print(f"\n[*] Exporting: {export_prefix}_*")
        try:
            ResultsExporter.export_all(analyzer, export_prefix)
        except Exception as e:
            print(f"[ERROR] Export failed: {e}")
    
    return analyzer


__all__ = [
    'BacktestResults', 'BacktestAnalyzer', 'ResultsReporter',
    'ChartGenerator', 'ResultsExporter', 'run_backtest',
    'init_api', 'api_call', 'APIHelper', 'APIManager',
    'ResourceMonitor', 'create_progress_bar', 'update_progress', 'format_time'
]