'''mermaid

graph TD
    %% --- STYLING DEFINITIONS ---
    classDef layer1 fill:#DAE8FC,stroke:#6c8ebf,stroke-width:2px,color:#000000,font-size:14pt,font-family:Arial;
    classDef layer2 fill:#F5F5F5,stroke:#b8b8b8,stroke-width:2px,color:#000000,font-size:14pt,font-family:Arial;
    classDef layer3 fill:#FFF2CC,stroke:#d6b656,stroke-width:2px,color:#000000,font-size:14pt,font-family:Arial;
    
    classDef nodeStyle fill:#ffffff,stroke:#000000,stroke-width:2px,rx:5,ry:5,font-family:Arial,font-size:12pt;
    classDef starNode fill:#ffffff,stroke:#b20000,stroke-width:4px,rx:5,ry:5,font-family:Arial,font-size:12pt;
    classDef dbStyle fill:#ffffff,stroke:#000000,stroke-width:2px,shape:cylinder,font-family:Arial,font-size:12pt;
    classDef decisionStyle fill:#ffffff,stroke:#000000,stroke-width:2px,shape:diamond,font-family:Arial,font-size:12pt;
    classDef subText font-size:10pt,color:#555555,font-style:italic;

    %% --- LAYER 1: PRESENTATION ---
    subgraph TopLayer [PRESENTATION LAYER GUI & VISUALIZER]
        direction LR
        U[👤 User]:::nodeStyle --> B1(Click 'Load SP3'):::nodeStyle
        
        D1[🖥️ Render 2D Ground Track Map<br/><span class=subText>Matplotlib Interactive Backend</span>]:::nodeStyle
        
        D1 -- User Clicks on Map? --> DEC{Decision}:::decisionStyle
        DEC -- No --> IDLE(Idle State):::nodeStyle
        
        W1(Generate Skyplot Window<br/><span class=subText>Visibility Analysis Polar Plot</span>):::nodeStyle
    end

    %% --- LAYER 2: CONTROLLER ---
    subgraph MidLayer [CONTROLLER LAYER MAIN LOGIC]
        direction LR
        C1(Route File Path):::nodeStyle
        C2(Prepare Visualization Data):::nodeStyle
    end

    %% --- LAYER 3: COMPUTATIONAL CORE ---
    subgraph BotLayer [COMPUTATIONAL CORE & DATA BACKEND]
        direction LR
        DB1[(Raw SP3/RINEX Files<br/><span class=subText>data/*.sp3</span>)]:::dbStyle
        P1(Data Parsing & Ingestion<br/><span class=subText>Extract Epochs - read_sp3.py</span>):::nodeStyle
        P2(Preprocessing & Structure<br/><span class=subText>Convert to NumPy Arrays</span>):::nodeStyle
        P3(⭐ Lagrange Interpolation Engine ⭐<br/><span class=subText>10th Order Polynomial Densification</span>):::starNode
        P4(Coordinate Transformation<br/><span class=subText>ECEF X,Y,Z -> WGS84 Lat,Lon,Alt</span>):::nodeStyle
        
        CALC(Calculate Azimuth & Elevation<br/><span class=subText>Station-to-Satellite Vector Math</span>):::nodeStyle
    end

    %% --- CONNECTIONS BETWEEN LAYERS & FLOW ---
    %% ADIM 2: Akışı Başlatma
    B1 ==> C1
    C1 ==> DB1

    %% ADIM 3: Veri İşleme Boru Hattı (Alt Katman)
    DB1 ==> P1 ==> P2 ==> P3 ==> P4

    %% ADIM 4: Sonuçları Gösterme (Yukarı Çıkış)
    P4 ==> C2
    C2 ==> D1

    %% ADIM 5: Etkileşim ve Analiz (Sağ Taraf)
    DEC -- Yes: Get Coordinates ==> CALC
    CALC ==> W1

    %% Link Styling to be orthogonal and thicker
    linkStyle default stroke-width:2px,fill:none,stroke:black,straight;

    %% Apply Layer Styles to Subgraphs
    class TopLayer layer1;
    class MidLayer layer2;
    class BotLayer layer3;
'''