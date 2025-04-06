
# Matrix NX Laser System – Electronics & Connector Interface

## Customer Interface Overview

The Matrix NX laser includes a **25-pin D-Sub connector (X100)** and **two Phoenix 2-pin connectors (X101 and X102)** for interfacing with external systems:

### 25-Pin D-Sub Connector (X100)

| Pin  | Function                          |
|------|-----------------------------------|
| 1    | Reserved                          |
| 2    | Reserved                          |
| 3    | Status_1                          |
| 4    | Status_2                          |
| 5    | Status_3                          |
| 6    | Status_4                          |
| 7    | HF-SyncOut                        |
| 8    | RS232_RxD                         |
| 9    | RS232_TxD                         |
| 10   | HF-Level Control                  |
| 11   | HF-Trigger                        |
| 12   | GND                               |
| 13   | GND                               |
| 14   | GND                               |
| 15   | GND                               |
| 16   | F101 – Fuse 300 mA                |
| 17   | F100 – Fuse 500 mA                |
| 18   | +48V Power Input                  |
| 19   | +48V Power Input                  |
| 20   | Relay Contact A (Normally Open)   |
| 21   | Relay Contact B (Normally Open)   |
| 22–25| Not assigned in diagram           |

> Connector X100 is a 25-pin D-Sub female connector.

### Interlock Contacts (Phoenix 2-pin)

**X101: Interlock 1**
- Pin 1: Interlock_1+
- Pin 2: Interlock_1–

**X102: Interlock 2**
- Pin 1: Interlock_2+
- Pin 2: Interlock_2–

> These interlocks must be closed for laser operation.

---

## Safety and Performance Level

The Matrix NX interlock and control system is evaluated according to **DIN EN ISO 13849-1:2016**.

- **Category**: 2  
  - Two independent interlocks  
  - Monitored logic (m)  
  - Two output stages: "LD Supply" and "Enable LD DC/DC"

- **Diagnostic Coverage (DCavg)**:  
  - Calculated as 99.03%  
  - Considered **high**

- **Mean Time to Dangerous Failure (MTTFd)**:
  - Channel 1: 35.46 years  
  - Channel 2: 45.02 years  
  - Both rated **high**

- **Performance Level Achieved**: **PL d**

> Based on Telcordia standards and simplified evaluation methods from ISO 13849-1:2016.

