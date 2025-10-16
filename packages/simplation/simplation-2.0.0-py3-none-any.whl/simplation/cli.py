
#?--------------------------------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os,re
from difflib import get_close_matches
import pyfiglet
from colorama import Fore, Style, init
from rich.console import Console
from rich.table import Table
from rich import box
#?--------------------------------------------------------------------------------------------------------------
class SimulationDataAnalyzer:

    def __init__(self):
        self.data           = None
        self.headers        = []
        self.time_column    = "Time"
        self.units          = {}
        self.console        = Console()
        
    init(autoreset=True)

    def display_banner(self):
        """Display the application banner with pyfiglet and colors"""
        os.system('cls' if os.name == 'nt' else 'clear')

        print(Fore.MAGENTA + "=" * 70)
        # Create the main title with pyfiglet
        try:
            title = pyfiglet.figlet_format("SIMPLATION", font="doom" )
            print(Fore.CYAN + title)
            
        except:
            # Fallback if pyfiglet fails
            print(Fore.CYAN + "SIMPLATION")

        # Tool description
        print(Fore.MAGENTA + "─" * 70)
        print(Fore.WHITE +  "Simulation Data Analysis Tool Load, Analyze, and Visualize ")
        print(Fore.WHITE +  "CSV Simulation Data Statistical Analysis, Signal Processing, Plotting")
        print(Fore.MAGENTA + "─" * 70)
        print(Fore.LIGHTBLACK_EX +  " © M.GUENI - 10-05-2025 - v0.0.1")
        # Bottom border
        print(Fore.MAGENTA + "=" * 70)
        print(Style.RESET_ALL)  # Reset colors
        
    def load_csv(self, file_path, has_headers=True, header_file=None):
        """Load CSV file with or without headers"""
        try:
            if has_headers:
                self.data           = pd.read_csv(file_path)
                self.headers        = self.data.columns.tolist()
            else:
                if header_file:
                    with open(header_file, 'r') as f:
                        headers     = json.load(f)
                    self.data       = pd.read_csv(file_path, header=None, names=headers)
                    self.headers    = headers
                else:
                    # Generate default headers
                    self.data       = pd.read_csv(file_path, header=None)
                    num_columns     = len(self.data.columns)
                    self.headers    = [f"Column_{i}" for i in range(num_columns)]
                    self.headers[0] = "Time"  # Assume first column is time
            
            print(Fore.MAGENTA + "─" * 70)
            print(Fore.GREEN + f"✓ Successfully loaded data with {len(self.data)} rows and {len(self.headers)} columns")
            print(Fore.MAGENTA + "─" * 70)
            
            # Auto-detect units from header names
            self._detect_units()
            
        except Exception as e:
            print(Fore.RED + f"✗ Error loading file: {e}")
            return False
        return True
    
    def _detect_units(self):
        """Auto-detect units from signal names - checks only last 2 words"""
        unit_patterns = {
            # Electrical quantities
            'current': 'A',
            'voltage': 'V', 
            'power': 'W',
            'dissipation': 'W',
            'loss': 'W',
            'losses': 'W',
            'energy': 'J',
            'frequency': 'Hz',
            'resistance': 'Ω',
            'impedance': 'Ω',
            'inductance': 'H',
            'capacitance': 'F',
            'charge': 'C',
            'flux': 'Wb',
            'field': 'T',
            
            # Thermal quantities
            'temperature': '°C',
            'temp': '°C',
            'heat': 'J',
            
            # Mechanical quantities
            'speed': 'rpm',
            'velocity': 'm/s',
            'torque': 'Nm',
            'force': 'N',
            'position': 'm',
            'displacement': 'm',
            'angle': '°',
            'rotation': 'rad',
            'acceleration': 'm/s²',
            
            # Time and ratios
            'time': 's',
            'period': 's',
            'duration': 's',
            'duty': '%',
            'cycle': '%',
            'efficiency': '%',
            'eff': '%',
            'ratio': '',
            'factor': '',
            
            # Signal characteristics
            'ripple': 'V',
            'drop': 'V',
            'noise': 'V',
            'offset': 'V',
            'gain': '',
            'amplitude': 'V',
            'magnitude': 'V',
            
            # Power quality
            'power factor': '',
            'pf': '',
            'harmonics': '',
            'thd': '%',
            'distortion': '%',
            
            # Control systems
            'error': 'V',
            'reference': 'V',
            'setpoint': 'V',
            'feedback': 'V',
            'control': 'V',
            'command': 'V',
            
            # Protection
            'threshold': 'V',
            'limit': 'V',
            'protection': 'V',
            'fault': '',
            'trip': '',
            
            # Measurements
            'measured': '',
            'sensed': '',
            'sampled': '',
            'digital': '',
            'analog': '',
            'adc': '',
            'dac': '',
            
            # Waveforms and signals
            'waveform': 'V',
            'signal': 'V',
            'pulse': 'V',
            'wave': 'V',
            'carrier': 'V',
            'modulator': 'V'
        }
        
        for header in self.headers:
            header_lower = header.lower()
            words = header_lower.split()
            
            # Check last 2 words (or just last word if only 1 word)
            if len(words) >= 2:
                last_two_words = ' '.join(words[-2:])
                last_word = words[-1]
            else:
                last_two_words = header_lower
                last_word = header_lower
            
            unit_found = False
            
            # First check the last two words as a phrase
            for pattern, unit in unit_patterns.items():
                if ' ' in pattern:  # Multi-word patterns
                    if pattern in last_two_words:
                        self.units[header] = unit
                        unit_found = True
                        break
                else:  # Single word patterns
                    if pattern == last_word:
                        self.units[header] = unit
                        unit_found = True
                        break
            
            # If no unit found in last words, check the entire header for key patterns
            if not unit_found:
                # Special cases that should override last-word detection
                special_patterns = {
                    'current': 'A',
                    'voltage': 'V',
                    'power': 'W',
                    'temperature': '°C'
                }
                
                for pattern, unit in special_patterns.items():
                    if pattern in header_lower:
                        self.units[header] = unit
                        unit_found = True
                        break
            
            # Default to no unit if nothing matched
            if not unit_found:
                self.units[header] = ''
                
    def _find_best_match(self, signal_name):
        """Find the best matching header for a given signal name"""
        if signal_name in self.headers:
            return signal_name
        
        # Try exact match first
        matches = get_close_matches(signal_name, self.headers, n=1, cutoff=0.6)
        if matches:
            return matches[0]
        
        # Try partial matching
        for header in self.headers:
            if signal_name.lower() in header.lower() or header.lower() in signal_name.lower():
                return header
        
        return None
    
    def get_signal_data(self, signal_name):
        """Get data for a signal with fuzzy matching"""
        matched_header = self._find_best_match(signal_name)
        if matched_header:
            return self.data[matched_header], matched_header, self.units.get(matched_header, '')
        else:
            # Show suggestions
            suggestions = get_close_matches(signal_name, self.headers, n=3, cutoff=0.3)
            if suggestions:
                print(Fore.YELLOW + f"Did you mean: {', '.join(suggestions)}?")
            return None, None, None
    
    def calculate_mean(self, signal_name):
        """Calculate mean of a signal"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            mean_val = np.mean(data)
            return mean_val, actual_name, unit
        return None, None, None
    
    def calculate_rms(self, signal_name):
        """Calculate RMS of a signal"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            rms_val = np.sqrt(np.mean(data**2))
            return rms_val, actual_name, unit
        return None, None, None
    
    def calculate_std(self, signal_name):
        """Calculate standard deviation of a signal"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            std_val = np.std(data)
            return std_val, actual_name, unit
        return None, None, None
    
    def calculate_max(self, signal_name):
        """Calculate maximum of a signal"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            max_val = np.max(data)
            return max_val, actual_name, unit
        return None, None, None
    
    def calculate_min(self, signal_name):
        """Calculate minimum of a signal"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            min_val = np.min(data)
            return min_val, actual_name, unit
        return None, None, None
    
    def calculate_ptp(self, signal_name):
        """Calculate peak-to-peak value of a signal"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            ptp_val = np.ptp(data)
            return ptp_val, actual_name, unit
        return None, None, None
    
    def calculate_median(self, signal_name):
        """Calculate median of a signal"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            median_val = np.median(data)
            return median_val, actual_name, unit
        return None, None, None
    
    def calculate_variance(self, signal_name):
        """Calculate variance of a signal"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            var_val = np.var(data)
            return var_val, actual_name, unit
        return None, None, None
    
    def calculate_crest_factor(self, signal_name):
        """Calculate crest factor (peak-to-RMS ratio)"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            rms_val = np.sqrt(np.mean(data**2))
            peak_val = np.max(np.abs(data))
            crest_factor = peak_val / rms_val if rms_val != 0 else float('inf')
            return crest_factor, actual_name, ''
        return None, None, None
    
    def calculate_form_factor(self, signal_name):
        """Calculate form factor (RMS-to-mean ratio)"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            rms_val = np.sqrt(np.mean(data**2))
            mean_val = np.mean(np.abs(data))
            form_factor = rms_val / mean_val if mean_val != 0 else float('inf')
            return form_factor, actual_name, ''
        return None, None, None
    
    def calculate_ripple_factor(self, signal_name):
        """Calculate ripple factor (AC-to-DC ratio)"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            dc_component = np.mean(data)
            ac_component = np.sqrt(np.mean((data - dc_component)**2))
            ripple_factor = ac_component / dc_component if dc_component != 0 else float('inf')
            return ripple_factor, actual_name, ''
        return None, None, None
    
    def calculate_efficiency(self, output_signal, input_signal):
        """Calculate efficiency (output power / input power)"""
        output_data, output_name, output_unit = self.get_signal_data(output_signal)
        input_data, input_name, input_unit = self.get_signal_data(input_signal)
        
        if output_data is not None and input_data is not None:
            # Assuming signals are power values
            output_power = np.mean(output_data)
            input_power = np.mean(input_data)
            efficiency = (output_power / input_power) * 100 if input_power != 0 else float('inf')
            return efficiency, f"{output_name} vs {input_name}", '%'
        return None, None, None
    
    def calculate_power_factor(self, voltage_signal, current_signal):
        """Calculate power factor (real power / apparent power)"""
        voltage_data, voltage_name, voltage_unit = self.get_signal_data(voltage_signal)
        current_data, current_name, current_unit = self.get_signal_data(current_signal)
        
        if voltage_data is not None and current_data is not None:
            # Calculate real power and apparent power
            real_power = np.mean(voltage_data * current_data)
            apparent_power = np.sqrt(np.mean(voltage_data**2)) * np.sqrt(np.mean(current_data**2))
            power_factor = real_power / apparent_power if apparent_power != 0 else 0
            return power_factor, f"{voltage_name} & {current_name}", ''
        return None, None, None
    
    def calculate_thd(self, signal_name, fundamental_freq=50):
        """Calculate Total Harmonic Distortion (simplified version)"""
        data, actual_name, unit = self.get_signal_data(signal_name)
        if data is not None:
            # Simplified THD calculation using FFT
            fft_result = np.fft.fft(data)
            frequencies = np.fft.fftfreq(len(data))
            
            # Find fundamental and harmonics
            fundamental_idx = np.argmax(np.abs(fft_result[1:len(fft_result)//2])) + 1
            fundamental_power = np.abs(fft_result[fundamental_idx])**2
            
            # Sum of harmonics power (excluding fundamental)
            total_harmonic_power = np.sum(np.abs(fft_result)**2) - fundamental_power
            
            thd = np.sqrt(total_harmonic_power / fundamental_power) * 100
            return thd, actual_name, '%'
        return None, None, None
    
    def calculate_energy(self, power_signal, time_signal="Time"):
        """Calculate energy consumption (integral of power over time)"""
        power_data, power_name, power_unit = self.get_signal_data(power_signal)
        time_data, time_name, time_unit = self.get_signal_data(time_signal)
        
        if power_data is not None and time_data is not None:
            # Integrate power over time using trapezoidal rule
            energy = np.trapz(power_data, time_data)
            return energy, power_name, 'J'
        return None, None, None
    
    def plot_signals(self, signal_y, signal_x=None):
        """Plot signals against time or against each other"""
        try:
            plt.figure(figsize=(12, 6))
            
            if signal_x is None or signal_x.lower() == 'time':
                # Plot against time
                time_data, time_name, time_unit = self.get_signal_data("Time")
                y_data, y_name, y_unit = self.get_signal_data(signal_y)
                
                if time_data is not None and y_data is not None:
                    plt.plot(time_data, y_data)
                    plt.xlabel(f"{time_name} [{time_unit}]")
                    plt.ylabel(f"{y_name} [{y_unit}]")
                    plt.title(f"{y_name} vs {time_name}")
                    plt.grid(True)
                else:
                    print(Fore.RED + "✗ Could not find required signals for plotting")
                    return
            else:
                # Plot signal_y vs signal_x
                x_data, x_name, x_unit = self.get_signal_data(signal_x)
                y_data, y_name, y_unit = self.get_signal_data(signal_y)
                
                if x_data is not None and y_data is not None:
                    plt.plot(x_data, y_data)
                    plt.xlabel(f"{x_name} [{x_unit}]")
                    plt.ylabel(f"{y_name} [{y_unit}]")
                    plt.title(f"{y_name} vs {x_name}")
                    plt.grid(True)
                else:
                    print(Fore.RED + "✗ Could not find required signals for plotting")
                    return
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            print(Fore.RED + f"✗ Error plotting: {e}")
    
    def _evaluate_simple_operation(self, command):
        """Evaluate a simple operation like 'mean of signal'"""
        operations = {
            'mean of': self.calculate_mean,
            'rms of': self.calculate_rms,
            'std of': self.calculate_std,
            'max of': self.calculate_max,
            'min of': self.calculate_min,
            'ptp of': self.calculate_ptp,
            'median of': self.calculate_median,
            'variance of': self.calculate_variance,
            'crest factor of': self.calculate_crest_factor,
            'form factor of': self.calculate_form_factor,
            'ripple factor of': self.calculate_ripple_factor,
            'thd of': self.calculate_thd,
        }
        
        # Special two-signal operations
        special_operations = {
            'efficiency of': self.calculate_efficiency,
            'power factor of': self.calculate_power_factor,
        }
        
        # Check for special two-signal operations first
        for op_prefix, op_func in special_operations.items():
            if command.startswith(op_prefix):
                # Extract signals after "efficiency of signal1 vs signal2"
                remaining = command[len(op_prefix):].strip()
                if ' vs ' in remaining:
                    signal1, signal2 = remaining.split(' vs ', 1)
                    value, actual_name, unit = op_func(signal1.strip(), signal2.strip())
                    if value is not None:
                        return "{}{} {} = {}{:.6f} {}[{}]{}".format(Fore.CYAN, op_prefix.capitalize(), actual_name,Fore.GREEN, value, Fore.YELLOW, unit, Style.RESET_ALL)                

                    else:
                        return Fore.RED + f"✗ Could not calculate {op_prefix}"
                else:
                    return Fore.RED + f"✗ Usage: {op_prefix}<signal1> vs <signal2>"
        
        # Check for regular single-signal operations
        for op_prefix, op_func in operations.items():
            if command.startswith(op_prefix):
                signal_name = command[len(op_prefix):].strip()
                value, actual_name, unit = op_func(signal_name)
                if value is not None:
                    return "{}{} {} = {}{:.6f} {}[{}]{}".format(Fore.CYAN, op_prefix.capitalize(), actual_name,Fore.GREEN, value, Fore.YELLOW, unit, Style.RESET_ALL)                
                else:
                    return Fore.RED + f"✗ Signal '{signal_name}' not found"
        return None
    
    def evaluate_complex_expression(self, expression):
        """Evaluate complex mathematical expressions"""
        try:
            print(Fore.CYAN + "Evaluating expression...")
            
            # Create a copy of the expression to work with
            working_expr = expression
            
            # Find all operations in the expression
            operations = []
            op_patterns = [
                (r'mean\s+of\s+[^()/*+\-^]+', 'mean'),
                (r'rms\s+of\s+[^()/*+\-^]+', 'rms'),
                (r'std\s+of\s+[^()/*+\-^]+', 'std'),
                (r'max\s+of\s+[^()/*+\-^]+', 'max'),
                (r'min\s+of\s+[^()/*+\-^]+', 'min'),
                (r'ptp\s+of\s+[^()/*+\-^]+', 'ptp'),
                (r'median\s+of\s+[^()/*+\-^]+', 'median'),
                (r'variance\s+of\s+[^()/*+\-^]+', 'variance'),
                (r'crest factor\s+of\s+[^()/*+\-^]+', 'crest_factor'),
                (r'form factor\s+of\s+[^()/*+\-^]+', 'form_factor'),
                (r'ripple factor\s+of\s+[^()/*+\-^]+', 'ripple_factor'),
                (r'thd\s+of\s+[^()/*+\-^]+', 'thd'),
            ]
            
            # Extract all operations and replace with placeholders
            placeholders = {}
            placeholder_count = 0
            
            for pattern, op_type in op_patterns:
                matches = re.finditer(pattern, working_expr, re.IGNORECASE)
                for match in matches:
                    full_match = match.group(0)
                    signal_name = full_match.split(' of ')[1].strip()
                    
                    # Calculate the value based on operation type
                    if op_type == 'mean':
                        value, actual_name, unit = self.calculate_mean(signal_name)
                    elif op_type == 'rms':
                        value, actual_name, unit = self.calculate_rms(signal_name)
                    elif op_type == 'std':
                        value, actual_name, unit = self.calculate_std(signal_name)
                    elif op_type == 'max':
                        value, actual_name, unit = self.calculate_max(signal_name)
                    elif op_type == 'min':
                        value, actual_name, unit = self.calculate_min(signal_name)
                    elif op_type == 'ptp':
                        value, actual_name, unit = self.calculate_ptp(signal_name)
                    elif op_type == 'median':
                        value, actual_name, unit = self.calculate_median(signal_name)
                    elif op_type == 'variance':
                        value, actual_name, unit = self.calculate_variance(signal_name)
                    elif op_type == 'crest_factor':
                        value, actual_name, unit = self.calculate_crest_factor(signal_name)
                    elif op_type == 'form_factor':
                        value, actual_name, unit = self.calculate_form_factor(signal_name)
                    elif op_type == 'ripple_factor':
                        value, actual_name, unit = self.calculate_ripple_factor(signal_name)
                    elif op_type == 'thd':
                        value, actual_name, unit = self.calculate_thd(signal_name)
                    
                    if value is not None:
                        placeholder = f"__VAL{placeholder_count}__"
                        placeholders[placeholder] = value
                        working_expr = working_expr.replace(full_match, placeholder, 1)
                        placeholder_count += 1
                        # Color the intermediate calculations
                        print(Fore.WHITE + f"  {full_match} = {Fore.GREEN}{value:.6f}{Style.RESET_ALL}")
                    else:
                        return Fore.RED + f"✗ Could not evaluate: {full_match}"
            
            # Now evaluate the mathematical expression with placeholders
            for placeholder, value in placeholders.items():
                working_expr = working_expr.replace(placeholder, str(value))
            
            # Safe evaluation with allowed functions
            allowed_names = {
                'np': np,
                'max': max,
                'min': min, 
                'mean': np.mean,
                'std': np.std,
                'sqrt': np.sqrt,
                'sin': np.sin,
                'cos': np.cos,
                'tan': np.tan,
                'exp': np.exp,
                'log': np.log,
                'log10': np.log10,
                'pi': np.pi,
                'e': np.e,
                'abs': abs,
                'sum': sum,
                'len': len,
            }
            
            # Evaluate the expression
            result = eval(working_expr, {'__builtins__': {}}, allowed_names)
            
            # Color the final result: dark green for the numeric value
            return f"{Fore.CYAN}Result: {Fore.WHITE}{expression} = {Fore.GREEN}{result:.6f}{Style.RESET_ALL}"
            
        except Exception as e:
            return Fore.RED + f"✗ Error evaluating expression: {e}"
    
    def list_signals(self):
        """List all available signals using Rich table"""
        table = Table(title="📊 Available Signals", show_header=True, header_style="bold magenta", box=box.ROUNDED)
        
        table.add_column("#", style="cyan", width=4)
        table.add_column("Signal Name", style="white", min_width=30)
        table.add_column("Unit", style="yellow", width=8)
        
        for i, header in enumerate(self.headers):
            unit = self.units.get(header, '')
            table.add_row(str(i), header, unit)
        
        self.console.print(table)
    
    def show_stats(self, signal_name=None):
        """Show statistics for a signal or all signals using Rich tables"""
        if signal_name:
            data, actual_name, unit = self.get_signal_data(signal_name)
            if data is not None:
                stats = {
                    'Mean': np.mean(data),
                    'RMS': np.sqrt(np.mean(data**2)),
                    'Std': np.std(data),
                    'Min': np.min(data),
                    'Max': np.max(data),
                    'Peak-to-Peak': np.ptp(data),
                    'Median': np.median(data),
                    'Variance': np.var(data),
                    'Crest Factor': np.max(np.abs(data)) / np.sqrt(np.mean(data**2)) if np.sqrt(np.mean(data**2)) != 0 else float('inf'),
                    'Form Factor': np.sqrt(np.mean(data**2)) / np.mean(np.abs(data)) if np.mean(np.abs(data)) != 0 else float('inf'),
                }
                
                table = Table(title=f"📈 Statistics for {actual_name} [{unit}]", show_header=True, header_style="bold cyan", box=box.ROUNDED)
                table.add_column("Statistic", style="white", width=15)
                table.add_column("Value", style="green", width=15)
                
                for stat_name, value in stats.items():
                    table.add_row(stat_name, f"{value:.6f}")
                
                self.console.print(table)
            else:
                print(Fore.RED + f"✗ Signal '{signal_name}' not found")
        else:
            # Show brief stats for all signals
            table = Table(title="📊 Brief Statistics for All Signals", show_header=True, header_style="bold cyan", box=box.ROUNDED)
            
            table.add_column("Signal", style="white", width=38)
            table.add_column("Mean", style="green", width=12)
            table.add_column("RMS", style="green", width=12)
            table.add_column("Min", style="green", width=12)
            table.add_column("Max", style="green", width=12)
            table.add_column("Unit", style="yellow", width=8)
            
            for header in self.headers[1:]:  # Skip time
                data = self.data[header]
                unit = self.units.get(header, '')
                table.add_row(
                    header[:38],
                    f"{np.mean(data):.4f}",
                    f"{np.sqrt(np.mean(data**2)):.4f}",
                    f"{np.min(data):.4f}",
                    f"{np.max(data):.4f}",
                    unit
                )
            
            self.console.print(table)
#?--------------------------------------------------------------------------------------------------------------
def is_simple_operation(command):
    """Check if the command is a simple operation like 'mean of signal'"""
    simple_ops = [
        'mean of', 'rms of', 'std of', 'max of', 'min of', 
        'ptp of', 'median of', 'variance of', 'crest factor of', 
        'form factor of', 'ripple factor of', 'thd of',
        'efficiency of', 'power factor of'
    ]
    
    for op in simple_ops:
        if command.strip().startswith(op):
            return True
    return False

def main():
    analyzer = SimulationDataAnalyzer()
    analyzer.display_banner()
    
    # Get CSV file path
    while True:
        csv_path = input("\nEnter path to CSV file: ").strip()
        if os.path.exists(csv_path):
            break
        else:
            print(Fore.RED + "✗ File not found. Please enter a valid path.")
    
    # Check if file has headers
    while True:
        has_headers = input("Does the CSV file have headers? (y/n): ").strip().lower()
        if has_headers in ['y', 'yes','Y','YES','Yes']:
            header_file = None
            break
        elif has_headers in ['n', 'no','N','NO','No']:
            header_file = input("Enter path to header JSON file: ").strip()
            if not os.path.exists(header_file):
                print(Fore.RED + "✗ Header file not found.")
                continue
            break
        else:
            print("Please answer 'y' or 'n'")
    
    # Load the data
    if not analyzer.load_csv(csv_path, has_headers in ['y', 'yes'], header_file):
        return
    
    print(Fore.MAGENTA + "─" * 70)
    print(Fore.GREEN + "Data loaded successfully! You can now run commands.")
    print(Fore.YELLOW + "Type 'help' for available commands, 'exit' to quit.")
    print(Fore.YELLOW + "Type 'examples' to see usage examples.")
    print(Fore.MAGENTA + "─" * 70)
    
    # Command loop
    while True:
        try:
            command = input(Fore.CYAN + "\n>>> " + Style.RESET_ALL).strip()
            
            if command.lower() in ['exit', 'quit', 'q']:
                print(Fore.GREEN + "Goodbye!")
                break
            elif command.lower() in ['help', '?']:
                print(Fore.CYAN + """
Available commands:
  Basic Statistics:
    mean of <signal>              - Calculate mean value
    rms of <signal>               - Calculate RMS value  
    std of <signal>               - Calculate standard deviation
    max of <signal>               - Find maximum value
    min of <signal>               - Find minimum value
    ptp of <signal>               - Calculate peak-to-peak value
    median of <signal>            - Calculate median value
    variance of <signal>          - Calculate variance

  Signal Quality Metrics:
    crest factor of <signal>      - Calculate crest factor (peak/RMS)
    form factor of <signal>       - Calculate form factor (RMS/mean)
    ripple factor of <signal>     - Calculate ripple factor (AC/DC)
    thd of <signal>               - Calculate Total Harmonic Distortion

  Power System Analysis:
    efficiency of <out> vs <in>   - Calculate efficiency (%)
    power factor of <V> vs <I>    - Calculate power factor

  Visualization & Analysis:
    plot <signal>                 - Plot signal vs time
    plot <y_signal> vs <x_signal> - Plot two signals against each other
    stats [signal]                - Show statistics for signal or all signals
    list                          - List all available signals

  Complex Expressions:
    <math expression>             - Evaluate complex mathematical expressions
                                    using operations above with + - * / ( )

  System Commands:
    help                          - Show this help message
    examples                      - Show usage examples
    exit                          - Exit the program
                """)
                
            elif command.lower() == 'examples':
                print(Fore.CYAN + """
📚 SIMPLATION USAGE EXAMPLES
──────────────────────────────────────────────────────────────────────

1. BASIC STATISTICS:
   mean of Output Voltage           - Average output voltage
   rms of Input Current             - RMS value of input current
   max of Transformer Temperature   - Maximum temperature reached
   min of Output Power              - Minimum power output
   ptp of Ripple Voltage            - Peak-to-peak ripple voltage
   std of Noise Signal              - Standard deviation of noise

2. SIGNAL QUALITY ANALYSIS:
   crest factor of Motor Current    - Ratio of peak to RMS current
   form factor of AC Voltage        - Waveform shape quality factor
   ripple factor of DC Output       - AC component relative to DC
   thd of Mains Voltage             - Total Harmonic Distortion

3. POWER SYSTEM ANALYSIS:
   efficiency of Output Power vs Input Power    - System efficiency
   power factor of Mains Voltage vs Line Current - Power factor

4. VISUALIZATION:
   plot Output Voltage              - Plot voltage vs time
   plot Output Current vs Time      - Plot current vs time  
   plot Efficiency vs Load          - Plot efficiency vs load parameter
   plot Temperature vs Output Power - Correlation analysis

5. COMPLEX EXPRESSIONS:
   (mean of Vout * max of Iout) / 1000                    - Power calculation
   (rms of Voltage * rms of Current)                      - Apparent power
   std of Noise / mean of Signal                          - Signal-to-noise ratio
   (max of Temperature - min of Temperature) / 2          - Temperature swing
   (ptp of Ripple / mean of DC) * 100                     - Ripple percentage
   efficiency of Output Power vs Input Power * 100        - Efficiency in %

6. MULTI-SIGNAL ANALYSIS:
   stats                           - Show all signals statistics
   stats Output Voltage            - Detailed stats for specific signal
   list                            - Browse all available signals

7. REAL-WORLD SCENARIOS:
   Power Supply Analysis:
     mean of Output Voltage
     ptp of Output Ripple
     efficiency of Output Power vs Input Power
     crest factor of Input Current

   Motor Drive Analysis:
     max of Motor Current
     rms of Phase Voltage
     power factor of Input Voltage vs Input Current
     plot Motor Speed vs Torque

   Thermal Analysis:
     max of Junction Temperature
     mean of Heat Sink Temperature  
     stats Temperature Signals
     plot Temperature vs Time

   Power Quality:
     thd of Input Voltage
     thd of Input Current
     power factor of Grid Voltage vs Grid Current

──────────────────────────────────────────────────────────────────────
💡 TIPS:
• Use fuzzy matching: 'mean of vout' will match 'Output Voltage'
• Complex expressions support: +, -, *, /, (), **
• Units are auto-detected: [V], [A], [W], [°C], etc.
• Rich tables for better data visualization
• Colors for easy result interpretation
                """)
                
            elif command.lower() == 'list':
                analyzer.list_signals()
            elif command.startswith('stats'):
                parts = command.split()
                if len(parts) > 1:
                    analyzer.show_stats(' '.join(parts[1:]))
                else:
                    analyzer.show_stats()
            elif command.startswith('plot'):
                parts = command.split()
                if len(parts) >= 2:
                    if 'vs' in parts:
                        vs_index = parts.index('vs')
                        if vs_index + 1 < len(parts):
                            y_signal = ' '.join(parts[1:vs_index])
                            x_signal = ' '.join(parts[vs_index+1:])
                            analyzer.plot_signals(y_signal, x_signal)
                        else:
                            print(Fore.RED + "✗ Usage: plot <y_signal> vs <x_signal>")
                    else:
                        analyzer.plot_signals(' '.join(parts[1:]))
                else:
                    print(Fore.RED + "✗ Usage: plot <signal> OR plot <y_signal> vs <x_signal>")
            else:
                # Check if it's a simple operation
                if is_simple_operation(command):
                    result = analyzer._evaluate_simple_operation(command)
                    if result:
                        print(result)
                    else:
                        print(Fore.RED + "✗ Invalid command")
                else:
                    # Complex expression
                    result = analyzer.evaluate_complex_expression(command)
                    print(result)
                
        except KeyboardInterrupt:
            print(Fore.GREEN + "\n\nGoodbye!")
            break
        except Exception as e:
            print(Fore.RED + f"✗ Error: {e}")
#?--------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
#?--------------------------------------------------------------------------------------------------------------