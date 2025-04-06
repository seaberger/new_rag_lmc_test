# Matrix Laser Host Command Set (Excluding SCPI Commands)

## Spot Flags

### Spot Status Flags

| blank             | blank        | blank                            |
|:------------------|:-------------|:---------------------------------|
| Spot Status Flags | Description  | Comments                         |
| 0x00000001        | Spot new     | Limits: 0 - <10% of Spotlifetime |
| 0x00000002        | Spot used    | Limits: >10% of Spotlifetime     |
| 0x00000004        | Spot bad     | Limits: >200% of Spotlifetime    |
|                   |              | TBD: >133,33%                    |
| 0x00000008        | Spot locked  | Set by Factory                   |
| …..               | blank        | blank                            |
| 0x10000000        | blank        | blank                            |
| 0x20000000        | blank        | blank                            |
| 0x40000000        | Has Warnings | blank                            |
| 0x80000000        | Has Faults   | blank                            |

### Spot Warning Flags

| blank   | blank              | blank                  |
|:--------|:-------------------|:-----------------------|
| blank   | Spot Warning Flags | Description            |
| blank   | 0x00000001         | First Spot Warning     |
| blank   | 0x00000002         | Second Spot Warning    |
| blank   | 0x00000004         | First Crystal Warning  |
| blank   | 0x00000008         | Second Crystal Warning |
| blank   | …..                | blank                  |
| blank   | 0x10000000         | blank                  |
| blank   | 0x20000000         | blank                  |
| blank   | 0x40000000         | blank                  |
| blank   | 0x80000000         | blank                  |

### Spot Fault Flags

| blank                                                                                            | blank   | blank            | blank                     | blank                            |
|:-------------------------------------------------------------------------------------------------|:--------|:-----------------|:--------------------------|:---------------------------------|
| Comments                                                                                         | blank   | Spot Fault Flags | Description               | Comment                          |
| Can be set by customer in                                                                        | blank   | 0x00000001       | Spot End of Life (EOL)    | Troubleshooting guide:           |
| [% of Spot lifetime (1500h)]                                                                     |         |                  |                           | Change to next available spot.   |
| Default is 150%                                                                                  |         |                  |                           |                                  |
| Factory: 100%                                                                                    |         |                  |                           |                                  |
| TBD: 90%                                                                                         |         |                  |                           |                                  |
| Default is 200%                                                                                  | blank   | 0x00000002       | Crystal End of Life (EOL) | Troubleshooting guide:           |
| Factory: 120%                                                                                    |         |                  |                           | Please contact Coherent Service. |
| TBD: 100%                                                                                        |         |                  |                           |                                  |
| Number of Good Spots = 1                                                                         | blank   | 0x00000004       | blank                     | blank                            |
| Number of Good Spots = 1 and Hourcounter of this Spot reached 200% of Lifetime (Can be adjusted) | blank   | 0x00000008       | blank                     | blank                            |
| Factory: 100%                                                                                    |         |                  |                           |                                  |
| blank                                                                                            | blank   | …..              | blank                     | blank                            |
| blank                                                                                            | blank   | 0x10000000       | blank                     | blank                            |
| blank                                                                                            | blank   | 0x20000000       | blank                     | blank                            |
| blank                                                                                            | blank   | 0x40000000       | blank                     | blank                            |
| blank                                                                                            | blank   | 0x80000000       | blank                     | blank                            |

## Status Codes

| Controller Status Register   | Unnamed: 1   | Unnamed: 2       | Unnamed: 3                                      | Unnamed: 4                                      |
|:-----------------------------|:-------------|:-----------------|:------------------------------------------------|:------------------------------------------------|
| Bit                          | Mask         | Label            | Description                                     | Comment                                         |
| 0                            | 0x00000001   | Laser Fault      | Laser is in Fault State                         | Troubleshooting guide:                          |
|                              |              |                  |                                                 | Please reset the laser using the "*RST" command |
| 1                            | 0x00000002   | Laser Startup    | Laser is in Startup State                       | blank                                           |
| 2                            | 0x00000004   | Laser Warmup     | Laser is in Warmup State                        | blank                                           |
| 3                            | 0x00000008   | Laser Standby    | Laser is in Standy State                        | blank                                           |
| 4                            | 0x00000010   | Laser Emission   | Laser is in Emission State                      | blank                                           |
| 5                            | 0x00000020   | -                | -                                               | -                                               |
| 6                            | 0x00000040   | -                | -                                               | -                                               |
| 7                            | 0x00000080   | -                | -                                               | -                                               |
| 8                            | 0x00000100   | Warnings present | There are Warning present, see Warning Register | Check Details                                   |
| 9                            | 0x00000200   | Faults present   | There are Faults present, see Fault Register    | Check Details                                   |
| 10                           | 0x00000400   | -                | -                                               | -                                               |
| 11                           | 0x00000800   | -                | -                                               | -                                               |
| 12                           | 0x00001000   | -                | -                                               | -                                               |
| 13                           | 0x00002000   | -                | -                                               | -                                               |
| 14                           | 0x00004000   | -                | -                                               | -                                               |
| 15                           | 0x00008000   | -                | -                                               | -                                               |
| 16                           | 0x00010000   | -                | -                                               | -                                               |
| 17                           | 0x00020000   | -                | -                                               | -                                               |
| 18                           | 0x00040000   | -                | -                                               | -                                               |
| 19                           | 0x00080000   | -                | -                                               | -                                               |
| 20                           | 0x00100000   | -                | -                                               | -                                               |
| 21                           | 0x00200000   | -                | -                                               | -                                               |
| 22                           | 0x00400000   | -                | -                                               | -                                               |
| 23                           | 0x00800000   | -                | -                                               | -                                               |
| 24                           | 0x01000000   | -                | -                                               | -                                               |
| 25                           | 0x02000000   | -                | -                                               | -                                               |
| 26                           | 0x04000000   | -                | -                                               | -                                               |
| 27                           | 0x08000000   | -                | -                                               | -                                               |
| 28                           | 0x10000000   | -                | -                                               | -                                               |
| 29                           | 0x20000000   | -                | -                                               | -                                               |
| 30                           | 0x40000000   | -                | -                                               | -                                               |
| 31                           | 0x80000000   | -                | -                                               | -                                               |

## Warning Codes

| Controller Warning Register   | Unnamed: 1   | Unnamed: 2                    | Unnamed: 3                                                                      | Unnamed: 4                                                                                                         |
|:------------------------------|:-------------|:------------------------------|:--------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------|
| Bit                           | Mask         | Label                         | Description                                                                     | Comments                                                                                                           |
| 0                             | 0x00000001   | Interlocks Open               | Interlocks are open                                                             | Troubleshooting guide:                                                                                             |
|                               |              |                               |                                                                                 | Check for open Interlock circuits and loose connections, close Interlock loops.                                    |
|                               |              |                               |                                                                                 | Check SysLog for intermitent interlock contact.                                                                    |
| 1                             | 0x00000002   | Current Spot EOL              | Current Spot is End of Life                                                     | Troubleshooting guide:                                                                                             |
|                               |              |                               |                                                                                 | Change to next available spot.                                                                                     |
| 2                             | 0x00000004   | LD Supply Voltage not present | LD Supply Voltage is not present (Voltage below 48V(+-10%))                     | Troubleshooting guide:                                                                                             |
|                               |              |                               |                                                                                 | Check if LD-Supply Voltage is present (Pin 1 of Neutrik Connector) (Customer). Otherwise check F600 Fuse (Service) |
| 3                             | 0x00000008   | No MAC-Address assigned       | There is no MAC-Address assigned to Laser                                       | Call Coherent Service. There are No-Web Services available when no MAC Address is assigned                         |
| 4                             | 0x00000010   | Housing Temperature Deviating | Housing Temperature is outside the Ready- but still inside the Deviation Window | Troubleshooting guide:                                                                                             |
|                               |              |                               |                                                                                 | Check, if ambient temperature is in valid range                                                                    |
| 5                             | 0x00000020   | -                             | -                                                                               | -                                                                                                                  |
| 6                             | 0x00000040   | -                             | -                                                                               | -                                                                                                                  |
| 7                             | 0x00000080   | -                             | -                                                                               | -                                                                                                                  |
| 8                             | 0x00000100   | -                             | -                                                                               | -                                                                                                                  |
| 9                             | 0x00000200   | -                             | -                                                                               | -                                                                                                                  |
| 10                            | 0x00000400   | -                             | -                                                                               | -                                                                                                                  |
| 11                            | 0x00000800   | -                             | -                                                                               | -                                                                                                                  |
| 12                            | 0x00001000   | -                             | -                                                                               | -                                                                                                                  |
| 13                            | 0x00002000   | -                             | -                                                                               | -                                                                                                                  |
| 14                            | 0x00004000   | -                             | -                                                                               | -                                                                                                                  |
| 15                            | 0x00008000   | -                             | -                                                                               | -                                                                                                                  |
| 16                            | 0x00010000   | -                             | -                                                                               | -                                                                                                                  |
| 17                            | 0x00020000   | -                             | -                                                                               | -                                                                                                                  |
| 18                            | 0x00040000   | -                             | -                                                                               | -                                                                                                                  |
| 19                            | 0x00080000   | -                             | -                                                                               | -                                                                                                                  |
| 20                            | 0x00100000   | -                             | -                                                                               | -                                                                                                                  |
| 21                            | 0x00200000   | -                             | -                                                                               | -                                                                                                                  |
| 22                            | 0x00400000   | -                             | -                                                                               | -                                                                                                                  |
| 23                            | 0x00800000   | -                             | -                                                                               | -                                                                                                                  |
| 24                            | 0x01000000   | -                             | -                                                                               | -                                                                                                                  |
| 25                            | 0x02000000   | -                             | -                                                                               | -                                                                                                                  |
| 26                            | 0x04000000   | -                             | -                                                                               | -                                                                                                                  |
| 27                            | 0x08000000   | -                             | -                                                                               | -                                                                                                                  |
| 28                            | 0x10000000   | -                             | -                                                                               | -                                                                                                                  |
| 29                            | 0x20000000   | -                             | -                                                                               | -                                                                                                                  |
| 30                            | 0x40000000   | -                             | -                                                                               | -                                                                                                                  |
| 31                            | 0x80000000   | -                             | -                                                                               | -                                                                                                                  |

## Fault Codes

| Controller Fault Register   | Unnamed: 1   | Unnamed: 2                          | Unnamed: 3                                                 | Unnamed: 4                                                                                                 |
|:----------------------------|:-------------|:------------------------------------|:-----------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------|
| Bit                         | Mask         | Label                               | Description                                                | Comments                                                                                                   |
| 0                           | 0x00000001   | Housing Temperature Protection      | Housing Temperature out of Protection Range                | Troubleshooting guide: Make sure the laser housing is in the range: Default Value FW -> 10°C to 90°C       |
|                             |              |                                     |                                                            | Factory: 3°C -60°C                                                                                         |
| 1                           | 0x00000002   | Vanadate Temperature Protection     | Vanadate Temperature out of Protection Range               | Call Coherent Service ( Check Protection range. Default Value FW: 10°C to 90°C ) Factory: 0°C -70°C        |
| 2                           | 0x00000004   | Reso Temperature Protection         | Reso Temperature out of Protection Range                   | Call Coherent Service ( Check Protection range. Default Value FW: 10°C to 90°C ) Factory: 0°C -70°C        |
| 3                           | 0x00000008   | Laserdiode Temperature Protection   | Laserdiode Temperature out of Protection Range             | Call Coherent Service ( Check Protection range. Default Value FW: 10°C to 90°C ) Factory: 0°C -95°C        |
| 4                           | 0x00000010   | SHG Temperature Protection          | SHG Temperature out of Protection Range                    | Call Coherent Service ( Check Protection range. Default Value FW: 10°C to 90°C ) Factory: 0°C -100°C       |
| 5                           | 0x00000020   | THG Temperature Protection          | THG Temperature out of Protection Range                    | Call Coherent Service ( Check Protection range. Default Value FW: 10°C to 90°C ) Factory: 0°C -100°C       |
|                             |              |                                     |                                                            | Move to next spot suggestion?                                                                              |
| 6                           | 0x00000040   | SHG Temperature Control Failure     | SHG Actual-Temperature could not reach Set-Temperature     | Call Coherent Service ( Check PID Parameters, Check Ready Window/Time Parameters, Check Voltage/Current )  |
| 7                           | 0x00000080   | THG Temperature Control Failure     | THG Actual-Temperature could not reach Set-Temperature     | Call Coherent Service ( Check PID Parameters, Check Ready Window/Time Parameters, Check Voltage/Current )  |
| 8                           | 0x00000100   | Housing Temperature Sensor Fault    | Broken or Shorted Housing Temperature Sensor               | Call Coherent Service                                                                                      |
| 9                           | 0x00000200   | Vandate Temperature Sensor Fault    | Broken or Shorted Vanadate Temperature Sensor              | Call Coherent Service                                                                                      |
| 10                          | 0x00000400   | Reso Temperature Sensor Fault       | Broken or Shorted Reso Temperature Sensor                  | Call Coherent Service                                                                                      |
| 11                          | 0x00000800   | Laserdiode Temperature Sensor Fault | Broken or Shorted Laserdiode Temperature Sensor            | Call Coherent Service                                                                                      |
| 12                          | 0x00001000   | SHG Temperature Sensor Fault        | Broken or Shorted SHG Temperature Sensor                   | Call Coherent Service                                                                                      |
| 13                          | 0x00002000   | THG Temperature Sensor Fault        | Broken or Shorted THG Temperature Sensor                   | Call Coherent Service                                                                                      |
| 14                          | 0x00004000   | -                                   | -                                                          | blank                                                                                                      |
| 15                          | 0x00008000   | -                                   | -                                                          | blank                                                                                                      |
| 16                          | 0x00010000   | Laserdiode Current Protection       | Laserdiode Current above Protection Limit                  | Call Coherent Service (Check Protection Limit. Default Value FW: 20A)                                      |
|                             |              |                                     |                                                            | Factory: 10A                                                                                               |
| 17                          | 0x00020000   | Laserdiode Current Control Failure  | Laserdiode Actual-Current does not match Set-Current       | Call Coherent Service                                                                                      |
| 18                          | 0x00040000   | Laserdiode Current Sensor Fault     | Laserdiode Current could not be measured                   | Call Coherent Service                                                                                      |
| 19                          | 0x00080000   | -                                   | -                                                          | blank                                                                                                      |
| 20                          | 0x00100000   | Laserdiode Over Voltage Protection  | Laserdiode Voltage above Protection Limit                  | Call Coherent Service (Check Protection Limit. Default Value FW: 25V)                                      |
| 21                          | 0x00200000   | Laserdiode Under Voltage Protection | Laserdiode Voltage below Protection Limit                  | Call Coherent Service                                                                                      |
| 22                          | 0x00400000   | Laserdiode Voltage Sensor Fault     | Laserdiode Voltage could not be measured                   | Call Coherent Service                                                                                      |
| 23                          | 0x00800000   | -                                   | -                                                          | blank                                                                                                      |
| 24                          | 0x01000000   | General Temperature Fault           | Failure in Temperature Module                              | Call Coherent Service (Check Error Flags of specific Instance)                                             |
| 25                          | 0x02000000   | General Laserdiode Fault            | Failure in Laserdiode Module                               | Call Coherent Service (Check Error Flags of specific Instance)                                             |
| 26                          | 0x04000000   | -                                   | -                                                          | blank                                                                                                      |
| 27                          | 0x08000000   | -                                   | -                                                          | blank                                                                                                      |
| 28                          | 0x10000000   | Internal Hardware Fault             | Internal Hardware Failure                                  | Call Coherent Service                                                                                      |
| 29                          | 0x20000000   | Deviation 2f/3f                     | 2f/3f Temperature Deviation Fault during Operation State   | Call Coherent Service (Check Deviation Time/Window) FW:  +/-0,5°C permanently +/-1°C for 10s? (not tested) |
| 30                          | 0x40000000   | Deviation Housing                   | Housing Temperature Deviation Fault during Operation State | Call Coherent Service (Check Deviation Time/Window) Factory: +/-2°C permanently +/-5°C for 50min           |
| 31                          | 0x80000000   | -                                   | -                                                          | blank                                                                                                      |

## SCPI Response Codes

| SCPI Errors   | Unnamed: 1                               | Unnamed: 2                                                                                                                                                    |
|:--------------|:-----------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Error Code    | Error Text                               | Comments                                                                                                                                                      |
| -610          | SCPI_ERROR_EXECUTION_TIMEOUT             | Troubleshooting guide: Reduce the amount of queries/commands sent to the laser. Wait for the proper handshake (/r/nOK/n/r), before sending new command/query. |
| -600          | SCPI_ERROR_TIMEOUT                       | Check, if End of Command Indicator was sent (\r\n)                                                                                                            |
| -550          | SCPI_ERROR_PRIORITY_PROBLEM              | blank                                                                                                                                                         |
| -500          | SCPI_ERROR_NO_ANSWER_WANTED              | blank                                                                                                                                                         |
| -400          | SCPI_ERROR_QUERY_UNAVAILABLE             | blank                                                                                                                                                         |
| -350          | SCPI_ERROR_QUEUE_OVERFLOW                | blank                                                                                                                                                         |
| -321          | SCPI_ERROR_OUT_OF_MEMORY                 | blank                                                                                                                                                         |
| -310          | SCPI_ERROR_SYSTEM_ERROR                  | blank                                                                                                                                                         |
| -257          | SCPI_ERROR_FILE_NOT_NAMED                | blank                                                                                                                                                         |
| -256          | SCPI_ERROR_FILE_DOES_NOT_EXIST           | blank                                                                                                                                                         |
| -250          | SCPI_ERROR_BYTE_ORDER_ERROR              | blank                                                                                                                                                         |
| -242          | SCPI_ERROR_VALUE_TEMPORARILY_UNAVAILABLE | blank                                                                                                                                                         |
| -241          | SCPI_ERROR_DEVICE_UNAVAILABLE            | blank                                                                                                                                                         |
| -222          | SCPI_ERROR_EXTRA_PARAMETER               | blank                                                                                                                                                         |
| -221          | SCPI_ERROR_SETTINGS_CONFLICT             | blank                                                                                                                                                         |
| -220          | SCPI_ERROR_INVALID_PARAMETER             | blank                                                                                                                                                         |
| -203          | SCPI_ERROR_COMMAND_PROTECTED             | Ensure correct Access Level                                                                                                                                   |
| -200          | SCPI_ERROR_EXECUTION_ERROR               | blank                                                                                                                                                         |
| -109          | SCPI_ERROR_PARAMETER_MISSING             | Check for correct Command Structure                                                                                                                           |
| -102          | SCPI_ERROR_SYNTAX_ERROR                  | blank                                                                                                                                                         |
| -100          | SCPI_ERROR_COMMAND_ERROR                 | blank                                                                                                                                                         |
| 0             | SCPI_ERROR_NONE                          | blank                                                                                                                                                         |

## Counter Descriptions

| SCPI Command                       | blank        | blank                                                                         |
|:-----------------------------------|:-------------|:------------------------------------------------------------------------------|
| SCPI Command                       | Counter Name | Description                                                                   |
| SYSTem:HOURmeter:GET?              | blank        | blank                                                                         |
| SYSTem:HOURmeter:GET?              | OPERATION    | Starts Counting, whenever System is powered on                                |
| SYSTem:HOURmeter:GET?              | 2F_3F        | Starts Counting, whenever 2f/3f Temperture Module is enabled                  |
| SYSTem:HOURmeter:GET?              | HOUSING      | Starts Counting, whenever Housing Heaters are active                          |
| SYSTem:HOURmeter:GET?              | LASERDIODE   | Starts Counting, whenever Laserdiode Module is enabled                        |
| SYSTem:HOURmeter:GET?              | blank        | blank                                                                         |
| SOURce:STEPper:SPOT:HOURmeter:GET? | blank        | blank                                                                         |
| SOURce:STEPper:SPOT:HOURmeter:GET? | SPOTx        | Starts Counting, depending on actual Pulsemode                                |
| SOURce:STEPper:SPOT:HOURmeter:GET? | blank        | CONTINUOUS: Counter Active, when Laserdiode and Pulsing is enabled            |
| SOURce:STEPper:SPOT:HOURmeter:GET? | blank        | GATED: Counter Active, when Laseriode is enabled and Gating Signal is applied |
| SOURce:STEPper:SPOT:HOURmeter:GET? | blank        | APEC: Counter Active, when Laserdiode is enabled and Gating Signal is applied |
| SOURce:STEPper:SPOT:HOURmeter:GET? | blank        | PULSETRACK: Counter Active, when Laserdiode and Pulsing is enabled            |
| SOURce:STEPper:SPOT:HOURmeter:GET? | blank        | SUPPRESSION: Counter Active, when Laserdiode and Pulsing is enabled           |
| SOURce:STEPper:SPOT:HOURmeter:GET? | blank        | CW: Counter never Active                                                      |

## XALL

| SCPI Command   | Parameter    | Returning Parameter Sequence   | Returning Parameter Name   | Equivalent SCPI Command                         |
|:---------------|:-------------|:-------------------------------|:---------------------------|:------------------------------------------------|
| SCPI Command   | Parameter    | Returning Parameter Sequence   | Returning Parameter Name   | Equivalent SCPI Command                         |
| SERVice:XALL?  | TEMPeratures | 1                              | Reso Temperature           | SOURce:TEMPerature:ACTual? TEMP_MONITOR_RESO    |
| blank          | blank        | 2                              | Vanadat Temperature        | SOURce:TEMPerature:ACTual? TEMP_MONITOR_VANADAT |
| blank          | blank        | 3                              | Laserdiode Temperature     | SOURce:TEMPerature:ACTual? TEMP_MONITOR_LD      |
| blank          | blank        | 4                              | Housing Temperature        | SOURce:TEMPerature:ACTual? TEMP_MONITOR_HOUSING |
| blank          | blank        | 5                              | SHG Temperature            | SOURce:TEMPerature:ACTual? TEMP_STAGE_SHG       |
| blank          | blank        | 6                              | THG Temperature            | SOURce:TEMPerature:ACTual? TEMP_STAGE_THG       |
| blank          | blank        | 7                              | Actual SHG Voltage         | SERVice:MODule:VOLTage:LEVel? SHG_VOLT_ACT      |
| blank          | blank        | 8                              | Actual THG Voltage         | SERVice:MODule:VOLTage:LEVel? THG_VOLT_ACT      |
| blank          | blank        | 9                              | Actual SHG Current         | SERVice:MODule:CURRent:LEVel? SHG_CURR_ACT      |
| blank          | blank        | 10                             | Actual THG Current         | SERVice:MODule:CURRent:LEVel? THG_CURR_ACT      |
| blank          | STEPper      | 1                              | Actual Stepper Position    | CALibration:STEPper:SPOT:COORdinate:ACTual?     |
| blank          | blank        | 2                              | Actual Spot Number         | SOURce:STEPper:SPOT:GET?                        |
| blank          | blank        | 3                              | Spot Hours                 | SOURce:STEPper:SPOT:HOURmeter:ACTual?           |
| blank          | blank        | 4                              | Spot Hours Remain          | SOURce:STEPper:SPOT:HOURmeter:REMain? SPOT      |
| blank          | blank        | 5                              | Crystal Hours              | SOURce:STEPper:SPOT:HOURmeter:CRYStal?          |
| blank          | blank        | 6                              | Spot Status                | SOURce:STEPper:SPOT:FLAGs:STATus?               |
| blank          | blank        | 7                              | Spot Warnings              | SOURce:STEPper:SPOT:FLAGs:WARNings?             |
| blank          | blank        | 8                              | Spot Faults                | SOURce:STEPper:SPOT:FLAGs:FAULTs?               |
| blank          | OTHers       | 1                              | Fan Output Drive           | SERVice:FAN:CONTroller:OUTput?                  |
| blank          | blank        | 2                              | Laserdiode Current         | SOURce:CURRent:LEVel? LD_DRIVER                 |
| blank          | blank        | 3                              | System Status Flags        | SYSTem:FLAGs:STATus?                            |
| blank          | blank        | 4                              | Scaled UV-Power            | SERVice:DETector:POWer:SCALed?                  |
| blank          | blank        | 5                              | Raw UV-Power               | SERVice:DETector:POWer:RAW?                     |
| blank          | blank        | 6                              | Operation Hours            | SYSTem:HOURmeter:GET? OPERATION                 |
| blank          | blank        | 7                              | LD Hours                   | SYSTem:HOURmeter:GET? LASERDIODE                |

## ALL

| SCPI Command   | Returning Parameter Sequence   | Returning Parameter Name      | Equivalent SCPI Command                         |
|:---------------|:-------------------------------|:------------------------------|:------------------------------------------------|
| SCPI Command   | Returning Parameter Sequence   | Returning Parameter Name      | Equivalent SCPI Command                         |
| ALL?           | 1                              | Status                        | SYSTem:FLAGs:STATus?                            |
| blank          | 2                              | Warnings                      | SYSTem:FLAGs:WARNings?                          |
| blank          | 3                              | Faults                        | SYSTem:FLAGs:FAULts?                            |
| blank          | 4                              | Actual Housing Temperature    | SOURce:TEMPerature:ACTual? TEMP_MONITOR_HOUSING |
| blank          | 5                              | Actual Laserdiode Temperature | SOURce:TEMPerature:ACTual? TEMP_MONITOR_LD      |
| blank          | 6                              | Actual SHG Temperature        | SOURce:TEMPerature:ACTual? TEMP_STAGE_SHG       |
| blank          | 7                              | Actual THG Temperature        | SOURce:TEMPerature:ACTual? TEMP_STAGE_THG       |
| blank          | 8                              | Operation Hours               | SYSTem:HOURmeter:GET? OPERATION                 |
| blank          | 9                              | Laserdiode Hours              | SYSTem:HOURmeter:GET? LASERDIODE                |
| blank          | 10                             | THG Crystal Hours             | SOURce:STEPper:SPOT:HOURmeter:CRYStal?          |
| blank          | 11                             | Actual THG Spot Hours         | SOURce:STEPper:SPOT:HOURmeter:ACTual?           |
| blank          | 12                             | Actual THG Spot Number        | SOURce:STEPper:SPOT:GET?                        |
| blank          | 13                             | Actual THG Spot Status        | SOURce:STEPper:SPOT:FLAGs:STATus?               |
| blank          | 14                             | Scaled UV-Power               | SERVice:DETector:POWer:SCALed?                  |

