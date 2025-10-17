# Guides and Instructions

## IRef Trim

We run a script to centrally update `TARGET_IREF_TRIM` for all the FE chips in
the PDB (that are not already assembled in modules). This script will be run
centrally every few days/weeks as new FE chips are uploaded in PDB and as FE
chips can’t be updated if they’re being shipped in the PDB.

### Action item for groups

- Please update your scripts that used the value from wafer probing ( IREF trim
  bit from “Electrical FE chip tests” test) to use the new property
  `TARGET_IREF_TRIM`.
  - In case `TARGET_IREF_TRIM` value is not filled, your script should default
    to wafer probing value `+1` ( IREF trim bit from “Electrical FE chip tests”
    test `+ 1` )

  !!! warning

      If this happens, report it back to us! (it should not happen)

- If you use `mqdbt` to retrieve the Iref trim, please update it to `v2.8.0`
  which will retrieve the Iref trim from the new field. In case
  `TARGET_IREF_TRIM` value is not filled, there will be a warning in your log.
  Use wafer probing value `+1` in those cases.
- In general, in case Iref trim from wafer probing was `15`, it stays `15`. If
  the `TARGET_IREF_TRIM` and `TARGET_IREF_TRIM_VERSION` are not set, but you’re
  wirebonding the wafer probing value `+1`, please update them accordingly
  (`TARGET_IREF_TRIM_VERSION` should be set to `1`).

Please see the flowchart diagram below
([adapted from Google Drive](https://drive.google.com/file/d/1aXKuzrX9OFWTlj0RLyq6FrhjVKi-I_V_/view?usp=sharing)).

```mermaid
flowchart TD

    A[Creating Wire Bonding Diagram for <strong>Production Modules</strong>] --> B{How do you get Iref trim value?}

    %% Left branch - custom script / prodDB
    B -->|From a custom script retrieving the wafer probing Iref trim value from prodDB| C[Retrieve&nbsp;<code>TARGET_IREF_TRIM</code>&nbsp;from&nbsp;prodDB]

    C --> D{Is <code>TARGET_IREF_TRIM</code> filled?}
    D -->|Yes| E[Use <code>TARGET_IREF_TRIM</code> in wire bonding diagram]
    D -->|No| F[Get wafer probing IREF trim bit]

    F --> G[Add 1 to wafer probing IREF trim value. Set the corresponding wirebonds]

    G --> H[Fill&nbsp;<code>TARGET_IREF_TRIM</code>&nbsp;in&nbsp;PDB&nbsp;accordingly]
    H --> I[Fill&nbsp;<code>TARGET_IREF_TRIM_VERSION</code>&nbsp;with&nbsp;1]
    I --> J[Email&nbsp;Electrical&nbsp;Performance&nbsp;coordinators]

    %% Right branch - chip config
    B -->|From the chip config| K[<strong>Update mqdbt to v2.8.0</strong><br>IRefTrim&nbsp;in&nbsp;chip&nbsp;config&nbsp;<code>= TARGET_IREF_TRIM</code>&nbsp;if&nbsp;exists<br>Otherwise&nbsp;defaults&nbsp;to&nbsp;wafer&nbsp;probing&nbsp;value]

    K --> L{<strong>Is there a warning in the log while creating the chip config?</strong><br><br><code>Warning:&nbsp;Chip&nbsp;property&nbsp;'TARGET_IREF_TRIM'&nbsp;not&nbsp;filled<br>Will&nbsp;resort&nbsp;to&nbsp;using&nbsp;wafer&nbsp;probing&nbsp;data</code>}

    L -->|Yes| M[Add&nbsp;1&nbsp;to&nbsp;value&nbsp;in&nbsp;chip&nbsp;config.<br>Set&nbsp;the&nbsp;corresponding&nbsp;wirebonds]

    M --> O[Update the IRefTrim parameter in the chip config to match that value]

    O --> H

    L -->|No| N[Use IRefTrim value from chip config in wire bonding diagram]

    %% Styles
    classDef prodDB stroke:#077e26,stroke-width:5px;
    classDef chipCfg stroke:#2514a0,stroke-width:5px;
    classDef redDecision stroke:#a01414,stroke-width:5px;

    %% Apply styles
    class C,D,E,F,G prodDB;
    class L,M,N,O chipCfg;
    class B,D redDecision;

    click J href "mailto:elisabetta.pianori@cern.ch,lingxin.meng@cern.ch,Marija.Marjanovic@cern.ch?subject=Updated%20TARGET_IREF_TRIM%20in%20PDB" "Click to email the electrical performance coordinators"
```

### Reference

- [https://indico.cern.ch/event/1560266/#120-electrical-failure-modes-o](https://indico.cern.ch/event/1560266/contributions/6574093/attachments/3089549/5471270/20250619_electricPerf.pdf)
- [https://indico.cern.ch/event/1567113/#1-iref-vddad-studies](https://indico.cern.ch/event/1567113/contributions/6602194/attachments/3100473/5493535/Curtin%20Seth%20ITkPix%20July%208%20Presentation.pdf)
