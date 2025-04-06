
# MATRIX PRODUCT TRAINING REV AD

**For Customers**  
**March 2025**  
**Cornelius Bernhardt**  
_Field Integration Engineer AVIA LX & MATRIX_

---

## Table of Contents

1. Product Overview & Specs  
2. Layout & Configuration  
3. Interfaces: Electrical & Communication  
4. Operation & Pulse Modes  
5. Maintenance & Troubleshooting  
6. Packaging & Shipment  
7. Environmental Guidelines  

---

## Product Overview & Specifications

### Coherent Nanosecond UV Portfolio Line-Up

| Model        | Power Range       | Repetition Rate     | Cooling |
|--------------|-------------------|----------------------|---------|
| Matrix 355   | 5 & 10 W          | up to 300 kHz        | Air     |
| Avia LX 355  | 10 to 30 W        | up to 300 kHz        | Water   |
| Avia LX 532  | 40 W              | up to 300 kHz        | Water   |
| Avia NX 355  | 20 to 55 W        | up to 300 kHz        | Water   |
| Avia NX 532  | 65 W              | up to 300 kHz        | Water   |

_Coherent pioneered ultraviolet laser technology with over 50 years of expertise._

---

### Specifications (Matrix 355)

| Specification                    | Matrix 355-5       | Matrix 355-10      |
|----------------------------------|--------------------|--------------------|
| Average Power (W)                | 5 at 50 kHz        | 10 at 50 kHz       |
| Pulse Repetition Rate (kHz)     | up to 300          | up to 300          |
| Pulse Duration (ns)             | < 30               | < 30               |
| Pulse-to-Pulse Stability (%)    | < 4                | < 4                |
| Beam Parameters (nominal)       | 2.5 mm and 0.25 mrad| same               |
| Circularity (%)                 | > 85               | > 85               |
| Spatial Mode                    | TEM00              | TEM00              |
| M²                              | < 1.3              | < 1.3              |
| Output Power Stability (%)      | < 2                | < 2                |
| Maximum Heat Load (W)           | <200 / 410 typical | same               |
| Warm-up Time (Cold Start)       | < 20 minutes       | < 20 minutes       |
| Warm-up Time (Warm Start)       | < 5 minutes        | < 5 minutes        |

#### Environmental Specs

- **Operating Temp:** 0°C to 40°C (45°C derated)
- **Non-Operating Temp:** -20°C to 60°C  
- **Altitude:** Operating: 0–10,000 ft / Non-Operating: 0–45,000 ft  
- **Humidity:** 0–80% (non-condensing)  
- **Input Voltage:** 48 VDC  
- **Power Supply (VA):** < 500  
- **Control:** Ethernet, RS-232, TTL/OS  

---

## Functional Design

Laser cavity includes:

- Q-switch
- Laser crystal
- Second Harmonic Generation (SHG)
- Third Harmonic Generation (THG)

Design style:
- End-pumped (efficient)
- Intra-cavity (high pulse stability)

---

## Performance Charts

### Power vs. Rep Rate (Matrix 355-10)

| Rep Rate (kHz) | Power (W) |
|----------------|-----------|
| 50             | ~10.0     |
| 75             | ~9.6      |
| 100            | ~9.0      |
| 150            | ~8.0      |
| 200            | ~7.0      |
| 250            | ~6.2      |
| 300            | ~5.5      |

### Power vs. Repetition Rate

| Repetition Rate (kHz) | Power (W) |
|-----------------------|-----------|
| 50                    | 10.0      |
| 75                    | 9.6       |
| 100                   | 9.1       |
| 125                   | 8.4       |
| 150                   | 7.8       |
| 200                   | 6.8       |
| 250                   | 6.0       |
| 300                   | 5.5       |

---

### Pulse Width vs. Repetition Rate

| Repetition Rate (kHz) | Pulse Width (ns) |
|-----------------------|------------------|
| 50                    | 21               |
| 75                    | 23               |
| 100                   | 25               |
| 125                   | 28               |
| 150                   | 31               |
| 200                   | 36               |
| 250                   | 42               |
| 300                   | 47               |

---

### Peak-to-Peak Stability (ΔP) vs. Repetition Rate

| Repetition Rate (kHz) | Peak-to-Peak Stability (%) |
|-----------------------|----------------------------|
| 50                    | 1.2                        |
| 75                    | 1.5                        |
| 100                   | 1.8                        |
| 125                   | 2.0                        |
| 150                   | 2.3                        |
| 200                   | 2.6                        |
| 250                   | 3.2                        |
| 300                   | 4.0                        |

---

### Power vs. Spot Number

| Spot Number | Power (W) |
|-------------|-----------|
| 1           | 10.0      |
| 2           | 10.0      |
| 3           | 10.0      |
| 4           | 10.0      |
| 5           | 10.0      |
| 6           | 10.0      |
| 7           | 10.0      |
| 8           | 10.0      |
| 9           | 10.0      |
| 10          | 10.0      |


---

## Dimensions & Configuration

### Laser Head

**Dimensions** (approx):

- Width: 238 mm
- Depth: 360 mm
- Height: 165 mm

### Air-Cooling Option

- Width: 358.5 mm
- Height (fan): ~65 mm
- Air intake clearance: 15 cm recommended

### Mounting Plate

Key dimensions:

- Overall length: ~310 mm
- Width: ~125 mm
- Multiple M5 holes spaced 19–29 mm apart for mounting

### Full System

Enclosure with stacked fan, laser head, and baseplate.

**Approx Dimensions**:

- Width: ~240 mm
- Height: ~230 mm (with fans)
- Depth: ~370 mm

---

### Cooling Options

Coherent offers **three different cooling choices**:

1. **Air cooling using a factory fan assembly**
   - PWM signal profile matched to fan model and tested with the laser.
   - High cooling efficiency by impingement cooling.
   - Checked for vibration and resonance behavior.

2. **Custom air cooling**
   - Requires close consultation with Coherent.

3. **Water cooling (customer-supplied)**

**Note:**  
- Ensure **~15 cm** of free space above the air intake for the Coherent air cooling assembly.

**Diagram (Side View)**  
- Air flows vertically through a dual-fan assembly mounted on the housing.  
- Dimensions (approx.):  
  - Fan Height: 40.55 mm  
  - Air Intake Clearance Required: 150 mm  

---

### Cooling Requirements

- **Interface**: ALL? query allows customer cooling control status check.
- **Elevated housing temperature** ensures safe operation in wide temperature and humidity ranges.

**Temperature Operating Windows:**

| Parameter                      | Value                          |
|-------------------------------|--------------------------------|
| Housing Temperature Set Point | 50°C                           |
| Normal Operating Range        | 48–52°C                        |
| Time Outside Normal Range     | 50 minutes max before shutdown |
| Hard Shutdown Limits          | Below 45°C or above 55°C       |

- If the laser exceeds the hard temperature limits, it will shut down and raise a fault.

**Air-Cooling Tip:**  
Maintain **15 cm of free space above the fan inlet** for full cooling capacity.

---

### Interfaces

The MATRIX laser system includes standard communication and control interfaces:

- **SCPI commands**
- **Ethernet** with integrated WebUI
- **RS-232**
- **TTL/OS control**

---

### Backpanel Connectors

**Connector List (left to right, as seen from the rear):**

- **2× Interlock**  
  - Performance Level d (safety interlocks)

- **Control I/O** – D-SUB 25 connector  
  - For external control and monitoring

- **Ethernet (RJ-45)**  
  - For SCPI and WebUI interface

- **Fan Connector**  
  - Powers external fan module

- **Power Supply** – 3-pin XLR  
  - Provides 48 VDC input

- **Protective Earth (PE)**  
  - Grounding pin for safety

---

### Electrical Requirements & Interlock

**Power Supply via 3-pin XLR connector**  
- Separate connections for Laser Diode (LD) and Controller

**DC Output Requirements**

| Parameter                   | Requirement                   |
|----------------------------|-------------------------------|
| Electrical Power           | 48 VDC ± 5%                   |
| Power Consumption          | <400 W typical / <500 W max   |
| Noise                      | <50 mV                        |
| Current                    | <12 A                         |
| Electrical Safety          | SELV (Safety Extra Low Voltage) |

**Interlock Solutions (2 options):**

1. **Use interlock connectors** (recommended)
2. **Cut Laser Diode (LD) supply voltage** for hard safety shutoff

> **Note:** Communication to the laser remains enabled even if the interlock is open.

**XLR Pinout:**

- **Pin 1 (GND)**  
- **Pin 2 (+48V Housekeeping)**  
- **Pin 3 (+48V LD Supply)**

---

### External Interface Connector – DSUB25

This 25-pin D-SUB connector is used for external control, monitoring, and triggering of the laser system.

#### DSUB25 Pinout Table

| Pin | Signal Name       | Description                                                                 |
|-----|-------------------|-----------------------------------------------------------------------------|
| 1   | –                 | Not connected                                                               |
| 2   | –                 | Not connected                                                               |
| 3   | –                 | Not connected                                                               |
| 4   | GND               | Ground                                                                      |
| 5   | Status 2          | Laser Warm-Up Status Indicator (3.3V TTL, active high)                      |
| 6   | RS232 RXD         | RS232 Receive – Connect to PC RS232 Transmit                                |
| 7   | Status 4          | Laser Emission Status Indicator (3.3V TTL, active high)                     |
| 8   | –                 | Not connected                                                               |
| 9   | Sync-OUT          | Output signal synchronization (3.3V TTL) – falling edge of signal indicates pulse fired |
| 10  | GND               | Ground                                                                      |
| 11  | GND               | Ground                                                                      |
| 12  | GND               | Ground                                                                      |
| 13  | Relay Contact A   | Relay contact A (Relay closed between Pin 13 and 15 when laser is ON)       |
| 14  | +48V Output       | Output 48V (100 mA current max)                                             |
| 15  | Relay Contact B   | Relay contact B (Relay closed between Pin 13 and 15 when laser is ON)       |
| 16  | GND               | Ground                                                                      |
| 17  | Status 1          | Laser Ready Status Indicator (3.3V TTL, active high)                        |
| 18  | Status 3          | Laser Warm-Up Status Indicator (3.3V TTL, active high)                      |
| 19  | RS232 TXD         | RS232 Transmit – Connect to PC RS232 Receive                                |
| 20  | +5V Output        | Output 5V (100 mA current max)                                              |
| 21  | Trigger Input     | Trigger Input (3.3V TTL, 100 ohm input series resistor)                     |
| 22  | GND               | Ground                                                                      |
| 23  | +5V Output        | Output 5V (100 mA current max)                                              |
| 24  | –                 | Not connected                                                               |
| 25  | Relay Contact B   | Relay contact B (duplicate of Pin 15, closes with Pin 13 when laser is ON)  |

> **Note:** Relay Contact A & B form a dry contact when the laser is emitting, useful for safety interlock chains or remote status monitoring.

---

### Command Set

The MATRIX laser uses an **SCPI-based command syntax** for remote communication.

#### Example Command Format

```
SOURce:AM:STATe ON
```

Structure:
- `Rootword : Keyword : Keyword Setting`

---

### Access Levels

- **USER** – Standard access for basic operation and monitoring
- **ENHANCED USER** – Extended control and configuration options

---

### Registers

- **Warnings**
- **Faults**

---

### `ALL?` Query

This single query returns a summary of key parameters in sequence:

| Sequence | Parameter Name             |
|----------|----------------------------|
| 1        | Status                     |
| 2        | Warnings                   |
| 3        | Faults                     |
| 4        | Actual Housing Temperature |
| 5        | Actual Laserdiode Temperature |
| 6        | Actual SHG Temperature     |
| 7        | Actual THG Temperature     |
| 8        | Operation Hours            |
| 9        | Laserdiode Hours           |
| 10       | THG Crystal Hours          |
| 11       | Actual THG Spot Hours      |
| 12       | Actual THG Spot Number     |
| 13       | Actual THG Spot Status     |
| 14       | Scaled UV-Power            |

> Use `ALL?` for efficient monitoring or polling.

---

### WebUI – Graphical User Interface

The MATRIX laser system includes a built-in **WebUI**, accessible via Ethernet and a standard web browser.

#### Key Features

- Integrated into the laser system — no external software required.
- Accessed via browser using the laser's IP address.
- **Single-page design** for easy operation and monitoring.
- Real-time control and feedback of laser parameters.

---

### WebUI Overview Sections

- **Top Bar**
  - **Pulse Mode** selector (e.g., CW, Gated, etc.)
  - **Repetition Rate (Rep. Rate)** display and control
  - **Power Output (W)** readout

- **Control Buttons**
  - Buttons for toggling:
    - Laser On/Off
    - Interlock status
    - Emission status
    - Power setting
    - Trigger settings
    - WebUI reset

- **Status & Diagnostics Tabs**
  - **Status & State**
  - **Warnings** – Shows active warnings (if any)
  - **Faults** – Shows current system faults
  - **No Faults / No Warnings** indicators

- **Command Input Console**
  - Custom SCPI command line input
  - Command history and output feedback shown below

- **Information Panel**
  - Shows live readings:
    - **Operation hours**
    - **Laserdiode hours**
    - **Housing temperature**
    - **THG/SHG temperature**
    - **THG Spot Status**
    - **Scaled UV Power**

---

> **Note:** WebUI access requires network connectivity. Default Ethernet configuration may need to be adjusted based on your network.

---

### Pulse Modes & Power Control

The MATRIX laser supports four primary pulse control modes:

| Pulse Control      | External Trigger | Pulsing Parameters                               |
|--------------------|------------------|--------------------------------------------------|
| Internal Continuous| Not Required     | Internal Repetition Rate                         |
| Gated              | Required         | Internal Repetition Rate triggered by Gate Signal|
| PulseTrack         | Required         | External Trigger with Adjustable Pulse Width     |
| CW                 | Not Required     | Not Applicable                                   |

---

#### Notes

- **Next Feature**: PulseEQ (upcoming enhancement)
- **Diode Current Control**:
  - 5W Laser: Full range adjustable
  - 10W Laser: Limited to 80%–100% of nominal power output

---

### Pulse Mode Decision Flow

Use this flowchart to determine the best pulse mode based on application needs:

```
Your Application/Process needs...
        |
        |-- Up charge (First Burst) slower than 20 ms?
        |       |
        |       |-- No --> PulseTrack – External
        |       |
        |       |-- Yes
        |            |
        |            |-- Exact amount of pulses per trigger?
        |                   |
        |                   |-- Yes --> PulseTrack – Burst
        |                   |
        |                   |-- No  --> PulseTrack – Gated
        |
        |-- Up charge (First Burst) faster than 20 ms?
                |
                |-- Yes --> PulseTrack – External
```

> The decision depends on how quickly the energy buildup (first burst) is needed and whether a specific number of pulses is required.

---

### Pulse Mode – Continuous Internal

- **No external signal or hardware** required.
- Pulses generated continuously at the **internally set repetition rate**.
- Useful for initial laser setup and determining correct diode current for power output.

#### Signal Timing Diagram

| Signal | Behavior                        |
|--------|---------------------------------|
| Gate   | Not used                        |
| RF     | Uniform pulse signal            |
| Output | Matches RF (steady pulse train) |

> Commonly used in **first-time startup** procedures.

---

### Pulse Mode – Gated

- **External gate signal is required**.
- Pulses fire at internal rep rate **only while gate is high**.
- Gate signal can be inverted if needed.

#### Benefits
- Reduces thermal transients — improves performance consistency.
- Ideal for applications like **scribing** or **cutting lines**.

#### Signal Timing Diagram

| Signal | Behavior                        |
|--------|---------------------------------|
| Gate   | High during active pulsing      |
| RF     | Internal pulse stream while Gate is high |
| Output | Matches RF when Gate is active  |

---

### Pulse Mode – PulseTrack

- **Requires external trigger** signal.
- A **single pulse** is generated on each **falling edge** of the trigger.
- Output energy is **proportional to trigger pulse width (Tw)**.

#### Benefits

- Ideal for fast pulse energy modulation
- Independent of pulse repetition rate
- Commonly used for:
  - **Drilling**
  - **Ablation**
  - Complex processing where fast pulse energy control is needed

#### Signal Timing Diagram

| Signal | Behavior                           |
|--------|------------------------------------|
| Gate   | Pulse width varies                 |
| RF     | Pulse follows falling edge of Gate |
| Output | Energy scales with width of Gate   |

> Linear relationship between energy and `Tw` (pulse width) up to the nominal rep rate.

---

### PulseTrack – Energy Proportional to Pulse Width

- The energy of each output pulse is directly **proportional to the external trigger pulse width** (`Tw`).
- Shorter `Tw` → lower energy  
- Longer `Tw` → higher energy  
- Maximum energy occurs when `Tw` reaches the internal rep rate interval.

#### Practical Use

- Enables rapid modulation of pulse energy
- Maintains precise energy control without needing to alter the laser’s repetition rate

#### Visualization Summary

```
Pulse Energy ∝ Tw
```

> Ideal for applications where pulse energy must be dynamically adjusted during the process.

---

### PulseTrack – Frequency Independence

- If the **external trigger pulse width** is **shorter than the trigger period**, then:
  - Changing the **trigger frequency** has **no effect** on pulse energy.
  - Pulse energy remains governed by `Tw`, not frequency.

#### Implication

- Allows decoupling of pulse energy and repetition rate
- Flexibility to optimize processes without modifying energy control settings

#### Notes

- For best linearity, keep repetition rates **below or near nominal frequency**
- Higher frequencies may introduce “steps” or energy inconsistencies

> This enables high-speed material processing without sacrificing precision.

---

### PulseTrack Mode – Linearity Performance

**Chart Summary (Visual Reference Only):**

- X-Axis: **Pulse Width (Tw)**
- Y-Axis: **Pulse Energy**

**Key Observation:**

- The relationship between `Tw` and Pulse Energy is **strongly linear** up to a certain threshold (~Nominal rep rate)
- Above that threshold, non-linearity and energy “steps” may occur

---

#### Recommended Range:

- Use **up to nominal frequency** for best linear energy control
- Carefully evaluate performance above this range

> This performance is especially valuable for precise ablation, drilling, or micromachining where energy control is critical.

---

### PulseTrack – Duty Cycle Limitations

To ensure reliable pulse separation and prevent overlapping pulses, **maximum duty cycle limits** must be observed.

#### Key Limitation

- If **trigger pulses are too close together**:
  - The laser may **combine** two signals.
  - Result: A **single pulse** with approximately **2× energy** at **½ the expected repetition rate**.

#### Best Practices

- Ensure sufficient time between external trigger pulses.
- Avoid excessive duty cycles or narrow separation margins.

#### Consequences of Overlap

| Condition                       | Result                                |
|--------------------------------|---------------------------------------|
| Inadequate spacing             | Two pulses merge into one             |
| Excess duty cycle              | Causes energy instability             |
| System response                | Unreliable output / Overdriven pulse  |

> Always test your trigger scheme to confirm pulse integrity.

---

### Pulse Mode – PulseEQ (Upcoming Feature)

- **Requires external hardware and trigger signal**
- A **single pulse is generated** on each **rising edge** of the trigger

#### Key Benefits

- **Pulse energy is consistent**, regardless of trigger spacing
- **Repetition rate is fully flexible**
- Energy is **not tied to the external trigger duty cycle**

---

#### Mode Characteristics

| Feature                      | Description                                 |
|-----------------------------|---------------------------------------------|
| Trigger Type                | Rising edge                                 |
| Energy Consistency          | All pulses have equal energy                |
| Repetition Rate             | Freely selectable                           |
| Power Modulation            | Via WebUI or SCPI (internal control)        |
| Transient Performance       | Excellent – reduced thermal variation       |

> Ideal for **scribing** or **cutting** applications where repetition rate varies but uniform energy is required.

---

### PulseEQ – Example Behavior

This page shows example traces comparing **external trigger frequency** to **internal energy handling**.

#### Example 1: 40 kHz External, 50 kHz Internal

- Laser ignores excess internal capacity
- Fires one pulse per external trigger

#### Example 2: 20 kHz External, 50 kHz Internal

- Same internal reservoir
- Still maintains **equal energy pulses** spaced by 50 μs (20 kHz)

---

#### Key Point

- PulseEQ uses an **internal rep rate** to maintain energy stability, even when external trigger rate is lower.
- No need to modulate pulse width or energy externally.

> This enables **predictable, stable output** across a range of dynamic triggering conditions.

---

## Maintenance & Troubleshooting

This section covers routine service topics and diagnostic tools for the MATRIX laser system.

---

### Topics Covered

- Output Window Care
- THG Spot Usage and Lifetime
- Spot Management
- Hourmeters and Wear Indicators
- Fault & Warning Diagnosis
- Current Control Limits
- Firmware Updates

> Proper preventive maintenance and monitoring can significantly extend laser system life.

---

### Lifetime & Performance – THG Spot Management

The system includes an **integrated THG shifter** with **10 pre-qualified THG spots**, each with defined lifetime expectations:

#### Spot Lifetime Estimates

| Spot Usage Mode | Continuous Operation Lifetime |
|-----------------|-------------------------------|
| 10W Operation    | > 1500 hours per spot         |
| 5W Operation     | > 2000 hours per spot         |

---

### THG Crystal Design

- Enhanced crystal tested thoroughly for long lifetime
- Maintains beam quality over extended use
- Design includes **power overhead** to ensure stability across total system life

> Automatic spot shifting ensures consistent performance without manual realignment.

---

### THG Spot Warnings and End-of-Life Logic

The system actively tracks usage and provides early warnings as each THG spot nears its lifetime limit.

#### Warning Thresholds

| Warning Stage        | Time Threshold (10W) | Time Threshold (5W) | System Behavior             |
|----------------------|----------------------|----------------------|-----------------------------|
| 1st Warning          | 90% of rated life    | 90% of rated life    | Warning message appears     |
| 2nd Warning          | 100% of rated life   | 100% of rated life   | Urgent warning, suggest shift |
| Spot End-of-Life (EoL)| >2000h               | >2500h               | Fault triggered, hard stop  |

---

- Once a spot reaches its **EoL threshold**, the laser will enter a **hard shutdown state** to protect the optics.
- Operator must **manually shift to the next spot** or initiate service action.

> THG spot management is a key part of the preventive maintenance system.

---

### Fault Register

Faults are part of the system’s self-protection mechanisms. When a fault is detected:

- The **laser enters fault state**
- All current- and temperature-carrying components are **shut off**
- Requires **manual intervention** to reset

---

#### Fault Reset Procedure

1. Address the root cause of the fault
2. Send command: `*RST`
3. Wait < 1 minute for system to restart
4. Perform warm-up if required

---

### Faults Returned via `ALL?` Query – Position 3

| Mask          | Label                               | Description                                              |
|---------------|--------------------------------------|----------------------------------------------------------|
| 0x00000001    | Housing Temp Protection              | Out of protection range                                  |
| 0x00000002    | Vanadate Temp Protection             | Out of protection range                                  |
| 0x00000004    | Reso Temp Protection                 | Out of protection range                                  |
| 0x00000008    | LD Temp Protection                   | Out of protection range                                  |
| 0x00000010    | SHG Temp Protection                  | Out of protection range                                  |
| 0x00000020    | THG Temp Protection                  | Out of protection range                                  |
| 0x00000040    | SHG Temp Control Failure             | Could not reach set temperature                          |
| 0x00000080    | THG Temp Control Failure             | Could not reach set temperature                          |
| 0x00000100    | Housing Temp Sensor Fault            | Sensor broken/shorted                                    |
| 0x00000200    | Vanadate Temp Sensor Fault           | Sensor broken/shorted                                    |
| 0x00000400    | Reso Temp Sensor Fault               | Sensor broken/shorted                                    |
| 0x00000800    | LD Temp Sensor Fault                 | Sensor broken/shorted                                    |
| 0x00001000    | SHG Temp Sensor Fault                | Sensor broken/shorted                                    |
| 0x00002000    | THG Temp Sensor Fault                | Sensor broken/shorted                                    |
| 0x00010000    | LD Current Protection                | Above protection limit                                   |
| 0x00020000    | LD Current Control Failure           | Set and actual current mismatch                          |
| 0x00040000    | LD Current Sensor Fault              | Could not measure current                                |
| 0x00100000    | LD Over Voltage Protection           | Voltage too high                                         |
| 0x00200000    | LD Under Voltage Protection          | Voltage too low                                          |
| 0x00400000    | LD Voltage Sensor Fault              | Could not measure voltage                                |
| 0x01000000    | General Temperature Fault            | Temperature module error                                 |
| 0x02000000    | General Laserdiode Fault             | Laserdiode module error                                  |
| 0x10000000    | Internal Hardware Fault              | Hardware failure                                         |
| 0x20000000    | Deviation 2f/3f                      | 2f/3f temp deviation fault during operation              |
| 0x40000000    | Deviation Housing                    | Housing temp deviation fault during operation            |

> All faults must be cleared before laser can resume operation.

---

### Warning Register

Warnings indicate **non-critical conditions** that may affect performance or require attention. They **do not shut down** the laser.

- Automatically cleared once the condition is resolved.
- Returned via `ALL?` Query – Position 2.

---

#### Common Warnings

| Mask        | Label                          | Description                                             |
|-------------|---------------------------------|---------------------------------------------------------|
| 0x00000001  | Interlocks Open                | Interlock circuit is open                               |
| 0x00000002  | Current Spot EOL               | THG spot has reached end-of-life                        |
| 0x00000004  | LD Supply Voltage Missing      | Voltage below 48V (±10%)                                |
| 0x00000008  | No MAC Address                 | Laser has no MAC address assigned                       |
| 0x00000010  | Housing Temp Deviating         | Outside ready range but within deviation tolerance      |

> Other bits reserved for future use or currently unused are listed but not active in this revision.

---

### SCPI Error Messages

The MATRIX laser communicates errors using SCPI-standard error codes and messages.

---

#### Common SCPI Error Handling Tips

- Invalid syntax or unsupported commands return a **SCPI Error**.
- Check command spelling, structure, and required access level (USER vs. ENHANCED USER).
- Use the `SYSTem:ERRor?` command to retrieve the most recent error message.
- Clear error queue with `*CLS`.

---

#### Example SCPI Error Queries

```scpi
SYSTem:ERRor?
*CLS
```

> When automating control, always check the error queue to catch silent failures.

---

### UV Power Monitor Calibration

The MATRIX laser includes an internal power detector, which can be calibrated against an external power meter.

---

#### Calibration Commands

| Command                                     | Unit  | Access Level | Description                                              |
|--------------------------------------------|-------|---------------|----------------------------------------------------------|
| `SERV:DET:POW:RAW?`                         | V     | USER          | Query actual measured detector voltage                   |
| `SERV:DET:POW:SCALed?`                      | W     | USER          | Query scaled optical power (Voltage × Scale + Offset)    |
| `CONF:DET:SCALe?` / `CONF:DET:SCALe <val>`  | W/V   | USER          | Get/Set power scaling factor                             |
| `CONF:DET:OFFSet?` / `CONF:DET:OFFSet <val>`| W     | USER          | Get/Set power offset                                     |

---

#### Recommended Calibration Procedure

1. Set laser to **Internal Continuous Mode**
2. Set laser to **10 W output**
3. Adjust **scaling factor** to match external powermeter
4. Turn off laser
5. Apply **offset correction**

> This ensures internal power readings accurately reflect real output.

---

### Output Window Maintenance

The output window must be kept clean to maintain beam quality and prevent damage.

---

#### Inspection Procedure

- Use a **torch (flashlight)** at a **high angle of incidence** to inspect for:
  - Dust
  - Smudges
  - Coating degradation

---

#### Cleaning Procedure

| Tool/Material            | Use Recommendation                    |
|--------------------------|----------------------------------------|
| Gloves                   | Always wear to prevent contamination   |
| Lens Cleaning Paper      | Use a new sheet for each wipe          |
| Pure Ethanol or IPA      | Wet wipe gently; **one-pass only**     |

---

**Warning:**  
A **degraded output window cannot be field-replaced.** Contact Coherent service for replacement.

> Regular inspection reduces risk of beam instability or optical damage.

---


