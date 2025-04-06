# Setting Up a Serial Connection and Operating via SCPI Commands for the Matrix NX  
**Revision**: AA  
**Created By**: Alexander Goldt  
**Last Change**: For Internal Use  
**Date**: 2023-02-24  
**Page**: 1 of 1  

---

## Terminal Program Used

- HTerm

---

## Configuration / Procedure

1. Select the COM Port  
2. Set the Baud Rate to **115200**  
3. Set Data Bits to **8**  
4. Set Stop Bits to **1**  
5. Set Parity to **None**  
6. Set New Line to **CR+LF**  
7. Set "Send on enter" to **CR-LF**  
8. Click the **Connect** button

---

## SCPI Command Syntax

The syntax of an SCPI command is based on a **root word**, which is separated from the first **key word** by a colon (`:`). After the key word, additional key words can follow, each separated by a colon.

Any parameters follow the final key word, separated by a space.  
Queries (i.e., read operations) end with a question mark (`?`) after the final key word.

---

### Figure 1

*Example illustrating the syntax of an SCPI command.*
