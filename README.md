# OA3CapacityManagement

Repo for OA3 hackathon creatign residential EV capacity management implementation. 

- Program representing a feeder
- 10 customers on a given feeder
- Each customer has an EV and a VEN (abbreviated as VEN)
- Each VEN has a load shape and will request more capacity 

- VENs have a normal subscription load level they will not exceed (e.g. 5kW)
- If a VEN needs more load (to charge an EV faster) they will send a reservation above their subscription level
  - reservations can have different values at multiple intervals
  - VTN has 3 options
    - Reservation acceepted with no fee, and will say which reservations are given at which interval
    - Reservation rejected, with announcement of cost of capacity at each interval
      - VEN can make another offer with a new request at the fee described, which should be accepted
     
# AI swimlane diagram
  ---
title: OA3CapacityManagement Process
---

%% Swimlane Diagram for OA3CapacityManagement
%% Copy and paste this into your GitHub README.md with Mermaid rendering enabled
sequenceDiagram
    participant Feeder as Program (Feeder)
    participant Customer as Customers (10 with EVs and VENs)
    participant VEN as VEN (Virtual End Node)
    participant VTN as VTN (Virtual Top Node)
    
    Feeder->>Customer: Feeder supplies capacity to 10 customers
    Customer->>VEN: Each customer operates through its VEN
    
    Note over VEN: Each VEN has a load shape and normal subscription level (e.g., 5kW)
    
    VEN->>VEN: Normal operations within subscription level
    VEN->>VTN: Request reservation for additional capacity
    
    alt VTN accepts reservation
        VTN->>VEN: Reservation accepted without fee
        Note over VEN, VTN: Specify intervals for reservation
    else VTN rejects reservation
        VTN->>VEN: Reservation rejected with capacity cost announcement
        VEN->>VTN: Sends new request with adjusted fee
        VTN->>VEN: Accepts new request
    end
