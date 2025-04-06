# Customer Change Log  
**Revision**: AB  
**Author**: Coherent Lübeck (Cornelius Bernhardt)  
**Date**: 01Oct2024  
**Last Change**: 06Dec2024  
**For Customer Use**  

**Page**: 1 / 2

---

## Change Status

| Rev | Changes                     | Date      | Remarks         |
|:---:|:----------------------------|:----------|:----------------|
| AA  | Initial Release            | 01Oct2024 |                 |
| AB  | Added FW 0.17.0 & FW 0.18.0  | 06Dec2024 |                 |

---

## FW 0.18.0

- Moved command `SOURce:TEMPerature:LEVel:SET TEMP_STAGE_THG` and  
  `SOURce:TEMPerature:LEVel:SET TEMP_STAGE_SHG` to **ENHANCED USER** access level.  
- Bug fixes.

---

## FW 0.17.0

- Added possibility for customers to change LD-Current in percent of nominal LD-Set Current.  
  - Commands:  
    - `CONFiguration:DIODe:CURRent:SET LD_DRIVER <float>` (USER)  
    - `CONFiguration:DIODe:CURRent:SET? LD_DRIVER` (USER)  
  - Default is 100%.
- Added functionality to invert input trigger signal polarity in GATED and APEC Mode:  
  - `SOURce:PULSe:CONFiguration:TRIGger:POLarity <HIGH|LOW>` (USER)  
  - `SOURce:PULSe:CONFiguration:TRIGger:POLarity?` (USER)  
  - Can only be changed when the laser is not in Emission State. Default is **HIGH**.
- Added functionality to enable pulsing only when the Gate signal is not applied (GATED/APEC).
- Added pull-up/pull-down resistors at the trigger input pin to ensure a defined Gate Input State  
  even if the Trigger Signal Cable is removed.
- Added possibility to switch IP assigning methods. Enable/disable DHCP:  
  - `CONFiguration:IP:DHCP <ON|OFF>` (USER)  
  - Query with `CONFiguration:IP:DHCP?` (USER)  
  - If DHCP is disabled, a predefined static IP address is used.
- Added functionality to define a static IP address (when DHCP is disabled):  
  - `CONFiguration:IP:STATic:ADDRess <aaa.bbb.ccc.ddd>` (USER)  
  - `CONFiguration:IP:STATic:ADDRess?` (USER)

---

**Page**: 2 / 2

## FW 0.14.0

- Added Ethernet and Web-Server functionality. The Web-Server uses HTTP and JSON for responses.
- Added functionality to query IP address and netmask using:  
  - `SYSTem:IP:ADDRess?`  
  - `SYSTem:IP:MASK?` (USER access level)  
  - IP is assigned by an external DHCP server.
- Added SCPI Command `ALL?` to query a set of parameters in **USER** Access Level:

### Parameter Sequence of "ALL?" Command

| SCPI Command                                   | Seq | Parameter Name               | Equivalent SCPI Command                               |
|------------------------------------------------|----:|------------------------------|--------------------------------------------------------|
| ALL? (1)  Status                               |  1 | Status                       | `SYSTem:FLAGs:STATus?`                                |
| ALL? (2)  Warnings                             |  2 | Warnings                     | `SYSTem:FLAGs:WARNings?`                              |
| ALL? (3)  Faults                               |  3 | Faults                       | `SYSTem:FLAGs:FAULts?`                                |
| ALL? (4)  Actual Housing Temperature           |  4 | Actual Housing Temperature   | `SOURce:TEMPerature:ACTual? TEMP_MONITOR_HOUSING`     |
| ALL? (5)  Actual Laserdiode Temperature        |  5 | Actual Laserdiode Temperature| `SOURce:TEMPerature:ACTual? TEMP_MONITOR_LD`          |
| ALL? (6)  Actual SHG Temperature               |  6 | Actual SHG Temperature       | `SOURce:TEMPerature:ACTual? TEMP_STAGE_SHG`           |
| ALL? (7)  Actual THG Temperature               |  7 | Actual THG Temperature       | `SOURce:TEMPerature:ACTual? TEMP_STAGE_THG`           |
| ALL? (8)  Operation Hours                      |  8 | Operation Hours              | `SYSTem:HOURmeter:GET? OPERATION`                     |
| ALL? (9)  Laserdiode Hours                     |  9 | Laserdiode Hours             | `SYSTem:HOURmeter:GET? LASERDIODE`                    |
| ALL? (10) THG Crystal Hours                    | 10 | THG Crystal Hours            | `SOURce:STEPper:SPOT:HOURmeter:CRYStal?`              |
| ALL? (11) Actual THG Spot Hours                | 11 | Actual THG Spot Hours        | `SOURce:STEPper:SPOT:HOURmeter:ACTual?`               |
| ALL? (12) Actual THG Spot Number               | 12 | Actual THG Spot Number       | `SOURce:STEPper:SPOT:GET?`                            |
| ALL? (13) Actual THG Spot Status               | 13 | Actual THG Spot Status       | `SOURce:STEPper:SPOT:FLAGs:STATus?`                   |
| ALL? (14) Scaled UV-Power                      | 14 | Scaled UV-Power              | `SERVice:DETector:POWer:SCALed?`                      |

- Added an additional warning flag **No MAC-Address assigned** (Bit 3, `0x00000008`).  
- Bug fixes.
