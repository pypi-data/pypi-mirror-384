# Simplation

A powerful command-line tool for analyzing and visualizing simulation data from CSV files.

## Features

- 📊 **Statistical Analysis**: Mean, RMS, standard deviation, min, max, peak-to-peak
- 📈 **Signal Quality Metrics**: Crest factor, form factor, ripple factor, THD
- ⚡ **Power System Analysis**: Efficiency, power factor calculations
- 🎨 **Rich Visualization**: Beautiful tables and colored output
- 🔍 **Fuzzy Matching**: Intelligent signal name matching
- 📋 **Complex Expressions**: Mathematical operations combining multiple signals
- 🎯 **Auto Unit Detection**: Automatic unit recognition from signal names

## Installation

```bash
pip install simplation

https://pypi.org/project/simplation/2.0.0/
```
```bash
Quick Start
bash
# Launch the interactive tool
simplation

# Or run directly on a CSV file
simplation --file data.csv
```
```bash
Available Commands
Type help in the interactive tool to see all available commands, or examples for detailed usage examples.

```
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
