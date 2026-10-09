# Simple research workflow

```mermaid
flowchart TB
    CORPUS[22-source documentary corpus<br/>60 chunks]

    CORPUS -->|Train / development split| DEV[8 development sources<br/>30 chunks]
    CORPUS -->|Test / held-out split| TEST[14 held-out sources<br/>30 chunks]

    DEV --> S1DEV[Stage 1 prompt iterations<br/>model, temperature, framework<br/>and segmentation fixed]
    S1DEV --> S1FREEZE[Frozen Stage 1 prompt<br/>V6]

    DEV --> BANK[Fixed development evidence bank<br/>390 records]
    BANK --> S2DEV[Stage 2 prompt development<br/>P0 to P1 to P2 to P3 to P4 to P5<br/>plus synthetic boundary cases]
    S2DEV --> S2FREEZE[Frozen Stage 2 prompt<br/>P5]

    TEST --> APPLY1[Apply frozen Stage 1]
    S1FREEZE --> APPLY1
    APPLY1 --> HELD[Held-out Stage 1 evaluation<br/>238 candidates / 232 accepted]

    BANK --> MERGE[Combined final evidence bank<br/>390 + 232 = 622 records]
    HELD --> MERGE
    MERGE --> APPLY2[Apply frozen Stage 2]
    S2FREEZE --> APPLY2
    APPLY2 --> FINAL[Provisional assessment<br/>31 DEMA indicators]

    FINAL --> REVIEW[Existing Togo assessment<br/>and expert evaluation<br/>comparison only]

    classDef corpus fill:#f5f5f5,stroke:#666,color:#222;
    classDef development fill:#fff3d6,stroke:#c58a16,color:#3d2b00;
    classDef heldout fill:#e8f2ff,stroke:#3973ac,color:#102a43;
    classDef frozen fill:#eee8ff,stroke:#6f52a2,color:#2c1f4a;
    classDef final fill:#e5f6ec,stroke:#3b8f5a,color:#163d25;
    classDef review fill:#f1f1f1,stroke:#888,color:#333,stroke-dasharray: 5 5;

    class CORPUS corpus;
    class DEV,S1DEV,BANK,S2DEV development;
    class TEST,APPLY1,HELD heldout;
    class S1FREEZE,S2FREEZE,APPLY2 frozen;
    class MERGE,FINAL final;
    class REVIEW review;
```

- Prompt development used only the eight-source development set.
- The 14-source set was held out until Stage 1 had been frozen.
- The existing Togo assessment and expert evaluations were introduced only after prompt development; they did not refine either prompt.
