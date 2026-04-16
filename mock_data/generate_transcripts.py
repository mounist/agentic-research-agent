"""
Generate 5 tickers x 8 quarters (2023Q1-2024Q4) of mock earnings transcripts.

Each transcript is 3000-5000 words, structured into:
  Opening Remarks / CEO Strategic Update / CFO Financial Review /
  Segment Breakdown / Q&A.

CRITICAL: every (ticker, quarter) has a distinct theme so semantic search
returns meaningfully different chunks per query.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "transcripts.json"

# Fiscal quarter -> approximate earnings-call date (ISO)
QUARTER_DATES = {
    "2023Q1": "2023-04-27",
    "2023Q2": "2023-07-27",
    "2023Q3": "2023-10-26",
    "2023Q4": "2024-02-01",
    "2024Q1": "2024-05-02",
    "2024Q2": "2024-08-01",
    "2024Q3": "2024-10-31",
    "2024Q4": "2025-01-30",
}

CEO = {
    "AAPL": ("Tim Cook", "Apple Inc."),
    "JPM": ("Jamie Dimon", "JPMorgan Chase"),
    "JNJ": ("Joaquin Duato", "Johnson & Johnson"),
    "XOM": ("Darren Woods", "ExxonMobil"),
    "WMT": ("Doug McMillon", "Walmart Inc."),
}
CFO = {
    "AAPL": "Luca Maestri",
    "JPM": "Jeremy Barnum",
    "JNJ": "Joe Wolk",
    "XOM": "Kathy Mikells",
    "WMT": "John David Rainey",
}

# ---- Theme library: each (ticker, quarter) -> structured theme dict ----

THEMES: dict[tuple[str, str], dict[str, str]] = {
    # ============ AAPL ============
    ("AAPL", "2023Q1"): {
        "headline": "Vision Pro unveiling and the dawn of spatial computing",
        "strategic": (
            "We are extraordinarily proud to introduce Apple Vision Pro, our first spatial computer, "
            "which we previewed at WWDC. This represents the beginning of a new computing paradigm, "
            "as transformative as the Mac and iPhone were in their eras. Vision Pro will ship early "
            "2024 at $3,499, targeting professional workflows, premium entertainment, and immersive "
            "FaceTime. We have over 5,000 developers already working on visionOS applications."
        ),
        "financial": (
            "Revenue was $94.8 billion, down 3 percent year over year, reflecting broad-based FX "
            "headwinds of roughly 500 basis points. iPhone revenue of $51.3 billion set a March "
            "quarter record. Services revenue of $20.9 billion was an all-time high. Mac declined "
            "31 percent on a tough compare against M1 Pro and M1 Max launches a year ago."
        ),
        "segment": (
            "Greater China returned to growth at $17.8 billion, up 2 percent in constant currency. "
            "Wearables was down 1 percent as we cycled the Watch Ultra launch. Services grew 5 percent, "
            "with paid subscriptions surpassing 975 million."
        ),
        "qa": (
            "On Vision Pro unit economics: the $3,499 price point reflects the density of technology, "
            "and we expect margins to be below corporate average at launch but improve with scale. "
            "On generative AI: we have been investing in AI and ML for years and will integrate these "
            "technologies thoughtfully across the product lineup."
        ),
        "keywords": "Vision Pro spatial computing visionOS WWDC preview developer ecosystem FX headwinds Mac compare",
    },
    ("AAPL", "2023Q2"): {
        "headline": "Services milestone: more than one billion paid subscriptions",
        "strategic": (
            "We crossed a historic threshold this quarter, surpassing 1 billion paid subscriptions "
            "across our Services portfolio, more than double the number just four years ago. Apple TV+, "
            "Apple Music, iCloud, and AppleCare all contributed. The installed base of active devices "
            "also reached a new all-time high across every geography and product category."
        ),
        "financial": (
            "Revenue was $81.8 billion, down 1 percent year over year. Services set a June quarter "
            "record at $21.2 billion, up 8 percent. Products revenue declined 4 percent on softer Mac "
            "and iPad demand, partially offset by iPhone resilience at $39.7 billion."
        ),
        "segment": (
            "Americas grew 1 percent, Europe was flat, Greater China declined 1 percent. Mac revenue "
            "was $6.8 billion, iPad was $5.8 billion. Wearables, Home, and Accessories came in at $8.3 billion."
        ),
        "qa": (
            "On Services margins sustainability: we continue to see gross margin expansion in Services "
            "driven by scale and mix. On Vision Pro: production is ramping, and we remain on track for "
            "early 2024 US launch. On AI: we do not comment on roadmap, but generative AI is a central "
            "focus of our R&D."
        ),
        "keywords": "one billion paid subscriptions Services milestone installed base Apple TV+ Apple Music iCloud AppleCare",
    },
    ("AAPL", "2023Q3"): {
        "headline": "iPhone 15 launch and the USB-C transition",
        "strategic": (
            "The iPhone 15 family launched in September with the Pro models featuring our new A17 Pro "
            "chip, the industry's first 3-nanometer smartphone processor, and titanium construction. "
            "All iPhone 15 models transitioned to USB-C, a major design shift. Early demand signals have "
            "been very encouraging, with Pro mix running higher than last cycle."
        ),
        "financial": (
            "Revenue was $89.5 billion, down less than 1 percent year over year. iPhone revenue was "
            "$43.8 billion, up 3 percent. Services delivered an all-time record $22.3 billion, up 16 percent. "
            "Gross margin reached 45.2 percent, up 170 basis points sequentially, driven by favorable mix."
        ),
        "segment": (
            "Mac revenue was $7.6 billion, down 34 percent on a tough MacBook Pro compare. iPad was "
            "$6.4 billion. Wearables came in at $9.3 billion. Greater China was $15.1 billion, down 2.5 percent."
        ),
        "qa": (
            "On iPhone 15 Pro demand and supply: demand for Pro Max has exceeded supply and we expect "
            "that constraint to persist into the December quarter. On USB-C transition friction: we have "
            "seen a smooth customer reception. On Mac: M3 family announcement is upcoming and will refresh "
            "the lineup."
        ),
        "keywords": "iPhone 15 A17 Pro chip 3-nanometer titanium USB-C transition Pro Max constrained demand",
    },
    ("AAPL", "2023Q4"): {
        "headline": "Greater China weakness and macro headwinds",
        "strategic": (
            "We delivered a December quarter revenue record, but we want to address China directly. "
            "Greater China revenue declined 13 percent year over year, reflecting a combination of "
            "macroeconomic softness, intense domestic competition from Huawei's Mate 60 launch, and "
            "a tough compare. We are investing in our retail footprint and local partnerships to "
            "defend our position in this critically important market."
        ),
        "financial": (
            "Revenue was $119.6 billion, up 2 percent year over year, an all-time record. iPhone "
            "revenue was $69.7 billion. Services was $23.1 billion, up 11 percent. Gross margin of "
            "45.9 percent was a quarterly record."
        ),
        "segment": (
            "Americas grew 2 percent, Europe grew 10 percent. Greater China was $20.8 billion, down "
            "13 percent, the primary drag. Mac revenue was up on M3 launch momentum. Wearables was soft."
        ),
        "qa": (
            "On China competitive dynamics: Huawei's return to premium has been a factor, and the "
            "consumer environment in China is more cautious. We are not pulling levers like deep "
            "discounting; we are competing on product. On buybacks: we continue to target a net cash "
            "neutral position over time."
        ),
        "keywords": "Greater China weakness Huawei Mate 60 competition macro softness China retail investment premium defense",
    },
    ("AAPL", "2024Q1"): {
        "headline": "Vision Pro launch and the first quarter of spatial ecosystem",
        "strategic": (
            "We launched Apple Vision Pro on February 2nd, and customer feedback has been exceptional. "
            "Over 600 spatial apps and games are already available on day one, plus more than 1.5 million "
            "compatible iOS and iPadOS apps. Enterprise interest has been particularly strong, with half "
            "of Fortune 100 companies exploring Vision Pro deployments."
        ),
        "financial": (
            "Revenue was $90.8 billion, down 4 percent year over year. iPhone was $46 billion, Services "
            "set an all-time record at $23.9 billion, up 14 percent. Gross margin came in at 46.6 percent, "
            "a March quarter record."
        ),
        "segment": (
            "iPad revenue was $5.6 billion. Mac was $7.5 billion. Wearables, Home, and Accessories was "
            "$7.9 billion, reflecting a challenging compare against Vision Pro ramp quarter noise and "
            "Watch softness."
        ),
        "qa": (
            "On Vision Pro attach and retention: retention is very high among enterprise buyers. "
            "On AI: we are going to be breaking new ground in generative AI in the coming months — stay "
            "tuned for WWDC. On China: we saw sequential improvement."
        ),
        "keywords": "Vision Pro launch February spatial ecosystem 600 apps Fortune 100 enterprise deployment WWDC AI tease",
    },
    ("AAPL", "2024Q2"): {
        "headline": "Apple Intelligence announced — AI becomes the Apple platform narrative",
        "strategic": (
            "At WWDC we introduced Apple Intelligence, our personal intelligence system that puts "
            "powerful generative models at the core of iPhone, iPad, and Mac. Apple Intelligence is "
            "built with privacy at its foundation, combining on-device processing with our new Private "
            "Cloud Compute architecture. We also announced an integration with ChatGPT to extend "
            "capabilities. This is the most significant software announcement in a decade."
        ),
        "financial": (
            "Revenue was $85.8 billion, up 5 percent year over year, a June quarter record. Services "
            "revenue of $24.2 billion was up 14 percent, again an all-time record. iPhone was $39.3 billion, "
            "down 1 percent, which was better than feared given we are now cycling into the Apple "
            "Intelligence-ready product lineup."
        ),
        "segment": (
            "Mac revenue was $7.0 billion, up 2 percent, reflecting M3 uptake. iPad was $7.2 billion, "
            "up 24 percent on new iPad Pro and iPad Air launches. Wearables was $8.1 billion."
        ),
        "qa": (
            "On Apple Intelligence hardware requirements: features require A17 Pro or M-series silicon, "
            "which we believe will drive an upgrade cycle. On ChatGPT integration: no financial terms to "
            "disclose. On Private Cloud Compute: this is a genuine architectural differentiator."
        ),
        "keywords": "Apple Intelligence WWDC personal intelligence Private Cloud Compute ChatGPT integration on-device privacy upgrade cycle",
    },
    ("AAPL", "2024Q3"): {
        "headline": "iPhone 16 launch with Apple Intelligence",
        "strategic": (
            "iPhone 16 and iPhone 16 Pro launched in September as the first iPhones designed from the "
            "ground up for Apple Intelligence. Apple Intelligence features began rolling out in late "
            "October with iOS 18.1, and additional capabilities including Image Playground and ChatGPT "
            "integration are arriving in December. Early adoption metrics show exceptional engagement "
            "from users on supported devices."
        ),
        "financial": (
            "Revenue was $94.9 billion, up 6 percent year over year, a September quarter record. "
            "iPhone revenue of $46.2 billion was up 5.5 percent. Services hit $25.0 billion, up 12 percent. "
            "Gross margin was 46.2 percent, up 60 basis points year over year."
        ),
        "segment": (
            "Greater China was $15.0 billion, down 2 percent constant currency — an improvement. Mac "
            "was $7.7 billion pending M4 transition. iPad was $6.9 billion on iPad Pro M4 strength. "
            "Wearables was $9.0 billion."
        ),
        "qa": (
            "On Apple Intelligence driving upgrades: early engagement on supported devices is meaningfully "
            "higher, and we are seeing a mix shift to Pro. On China trajectory: iPhone 16 launch response "
            "was encouraging; urban tier-one cities improved. On Services margin: Services gross margin "
            "reached 74 percent this quarter."
        ),
        "keywords": "iPhone 16 launch Apple Intelligence rollout iOS 18.1 Image Playground Pro mix shift engagement metrics",
    },
    ("AAPL", "2024Q4"): {
        "headline": "Regulatory and antitrust overhang — DOJ, DMA, and App Store dynamics",
        "strategic": (
            "We want to address the evolving regulatory environment directly. In the EU, compliance with "
            "the Digital Markets Act has required meaningful changes to App Store economics and sideloading "
            "policies in the region. In the US, we are vigorously defending the DOJ antitrust complaint. "
            "We remain confident in the integrity of our ecosystem and the value it delivers to users "
            "and developers."
        ),
        "financial": (
            "Revenue was $124.3 billion, up 4 percent year over year, an all-time record. iPhone was "
            "$69.1 billion, roughly flat as Apple Intelligence availability was staged. Services reached "
            "$26.3 billion, up 14 percent. Gross margin was 46.9 percent."
        ),
        "segment": (
            "Greater China was $18.5 billion, down 11 percent, continuing to be the weakest geography. "
            "Mac was $9.0 billion, up 16 percent on M4 family. iPad was $8.1 billion."
        ),
        "qa": (
            "On DMA revenue impact: the financial impact in the December quarter is not material but is "
            "being monitored. On App Store commission trajectory: the core business model remains intact "
            "globally. On China: we are working through a combination of regulatory and consumer headwinds."
        ),
        "keywords": "Digital Markets Act DOJ antitrust App Store commission sideloading EU compliance regulatory overhang",
    },
    # ============ JPM ============
    ("JPM", "2023Q1"): {
        "headline": "SVB crisis response and flight-to-quality deposits",
        "strategic": (
            "The quarter was dominated by the regional banking crisis following the failure of Silicon "
            "Valley Bank, Signature Bank, and the stress at First Republic. As a source of strength in "
            "the system, we saw significant flight-to-quality deposit inflows. We participated in the "
            "industry effort to stabilize First Republic with a $30 billion uninsured deposit. We believe "
            "this episode reinforces the value of scale, diversification, and a fortress balance sheet."
        ),
        "financial": (
            "Net income of $12.6 billion, EPS of $4.10 on revenue of $38.3 billion. ROTCE was 23 percent. "
            "NII was $20.8 billion, up 49 percent year over year, benefiting from higher rates and balance "
            "sheet growth. Provision for credit losses was $2.3 billion, including a $1.1 billion reserve build."
        ),
        "segment": (
            "Consumer and Community Banking revenue was $16.5 billion. Corporate and Investment Bank "
            "revenue was $13.6 billion, with investment banking fees down 24 percent and Markets down "
            "4 percent. Asset and Wealth Management revenue was $4.8 billion."
        ),
        "qa": (
            "On deposit outflow risk: we are modeling multiple scenarios but our diversified deposit "
            "base showed resilience. On First Republic: we view our involvement as supportive; we are "
            "not looking to acquire. On regulatory capital response: we expect heightened scrutiny of "
            "liquidity and AOCI treatment."
        ),
        "keywords": "SVB failure regional banking crisis Signature Bank First Republic flight-to-quality deposits fortress balance sheet",
    },
    ("JPM", "2023Q2"): {
        "headline": "First Republic acquisition and integration",
        "strategic": (
            "On May 1st, we acquired substantially all of First Republic from the FDIC. This was a "
            "deeply discounted transaction where we assumed approximately $173 billion of loans, $30 "
            "billion of securities, and $92 billion of deposits. We recognized an estimated $2.7 billion "
            "bargain purchase gain. First Republic's wealth management franchise and high-net-worth "
            "client relationships are a strategic fit, and we are focused on retention."
        ),
        "financial": (
            "Net income was $14.5 billion including the First Republic bargain purchase gain. EPS was "
            "$4.75. Revenue of $42.4 billion reflected the addition of First Republic for two months. "
            "NII was $21.8 billion. Managed overhead ratio was 53 percent."
        ),
        "segment": (
            "Consumer and Community Banking revenue rose on higher NII and the First Republic addition. "
            "CIB revenue was $12.5 billion. Commercial Banking revenue was $3.7 billion. AWM revenue was "
            "$4.9 billion."
        ),
        "qa": (
            "On First Republic client and banker retention: early retention metrics are tracking to plan, "
            "though there will be attrition. On integration expenses: we expect approximately $3.5 billion "
            "of merger-related expenses over two years. On accretion: First Republic is meaningfully "
            "accretive to EPS beginning in 2024."
        ),
        "keywords": "First Republic acquisition FDIC bargain purchase gain wealth management high-net-worth client retention integration",
    },
    ("JPM", "2023Q3"): {
        "headline": "Peak NII guidance and the rates narrative",
        "strategic": (
            "We are raising full year 2023 NII guidance to approximately $89 billion, which we believe "
            "represents peak NII for this cycle absent further rate hikes. We want to be clear-eyed with "
            "investors: a substantial portion of recent NII benefit is unlikely to persist as deposit "
            "betas catch up and we cycle into rate normalization. We are not changing through-the-cycle "
            "ROTCE target of 17 percent."
        ),
        "financial": (
            "Net income was $13.2 billion, EPS $4.33, revenue of $40.7 billion. ROTCE was 22 percent. "
            "NII was $22.9 billion, up 30 percent. NIM was 2.72 percent. Expense was $21.8 billion."
        ),
        "segment": (
            "CCB NII benefited from First Republic and the rate environment. CIB markets revenue was "
            "$6.6 billion, Fixed Income was $4.5 billion and Equities was $2.1 billion. Investment banking "
            "fees showed continued softness at $1.6 billion."
        ),
        "qa": (
            "On NII durability and deposit beta trajectory: cumulative deposit beta is trending toward "
            "high-50s percentage range, faster than our prior assumption. On excess capital deployment: "
            "we continue to favor organic lending, dividends, and opportunistic buybacks. On Basel III "
            "endgame: the proposed rules are significantly more onerous than anticipated."
        ),
        "keywords": "peak NII guidance 89 billion deposit beta catch-up rate normalization Basel III endgame proposal through-cycle ROTCE",
    },
    ("JPM", "2023Q4"): {
        "headline": "Commercial real estate exposure deep-dive",
        "strategic": (
            "Given elevated investor focus, we want to provide a detailed view of our commercial real "
            "estate book. Total CRE exposure is approximately $170 billion, of which office is roughly "
            "$17 billion, or 0.5 percent of total assets. We have proactively increased reserves against "
            "office over the past four quarters. We expect further losses, particularly in Class B and C "
            "office in secondary markets, but remain comfortable with our overall CRE positioning."
        ),
        "financial": (
            "Full year 2023 net income was a record $49.6 billion. Fourth quarter net income was $9.3 "
            "billion including a $2.9 billion FDIC special assessment. Revenue was $39.9 billion. "
            "NII was $24.1 billion."
        ),
        "segment": (
            "CCB revenue was $18.1 billion. CIB revenue was $11.0 billion. Commercial Banking $3.9 billion "
            "with CRE being highlighted. AWM $5.1 billion."
        ),
        "qa": (
            "On office CRE loss severity: we are modeling peak-to-trough valuation declines of 30 to 50 "
            "percent in affected segments. On 2024 NII: we guide to approximately $90 billion, which "
            "assumes six rate cuts priced by the forward curve. On expense discipline: expect 2024 "
            "expense growth of mid-single digits."
        ),
        "keywords": "commercial real estate office exposure Class B Class C secondary markets reserve build FDIC special assessment valuation decline",
    },
    ("JPM", "2024Q1"): {
        "headline": "Higher-for-longer rates and cut expectations",
        "strategic": (
            "The rate environment has evolved meaningfully. At the start of the year, the market was "
            "pricing six to seven cuts for 2024. Current expectations have moved to one or two cuts. "
            "For us, this is a mixed picture: higher-for-longer supports NII but creates credit and "
            "valuation headwinds. We continue to prepare for multiple scenarios and maintain our "
            "fortress capital and liquidity profile."
        ),
        "financial": (
            "Net income was $13.4 billion, EPS $4.44. Revenue was $42.5 billion. NII was $23.2 billion. "
            "We are raising 2024 NII guidance to approximately $91 billion from $90 billion previously."
        ),
        "segment": (
            "CCB revenue was $17.7 billion. CIB posted $13.6 billion, with investment banking fees up "
            "21 percent, showing signs of a capital markets thaw. Markets was $8.0 billion."
        ),
        "qa": (
            "On rate sensitivity: every 25 bps of cut that does not occur is roughly $1.5 billion of "
            "incremental NII. On investment banking: pipeline is building, though conversion remains "
            "uncertain. On credit normalization: card delinquencies continue to normalize, consistent "
            "with expectations."
        ),
        "keywords": "higher-for-longer rates cut expectations revision six cuts to two NII upside capital markets thaw investment banking recovery",
    },
    ("JPM", "2024Q2"): {
        "headline": "Investment banking recovery in full swing",
        "strategic": (
            "Investment banking is clearly recovering. IB fees were $2.5 billion, up 50 percent year "
            "over year, with strength across advisory, ECM, and DCM. We ranked number one in global IB "
            "fees for the quarter. The pipeline remains strong into the second half, though deal closure "
            "timing is always uncertain. We are taking share and seeing the benefits of continued "
            "investment through the downturn."
        ),
        "financial": (
            "Net income was $18.1 billion including a $7.9 billion Visa share gain. Ex-items, net income "
            "was $13.1 billion. Revenue of $50.2 billion includes the Visa gain. NII was $22.9 billion."
        ),
        "segment": (
            "CIB revenue was $17.9 billion. Markets posted $7.8 billion with Fixed Income at $4.8 billion "
            "and Equities at $3.0 billion. AWM was $5.3 billion."
        ),
        "qa": (
            "On Visa share monetization: we monetized approximately half of our Visa Class B position. "
            "On IB pipeline composition: we are seeing strength in financial sponsors activity and M&A "
            "discussions. On deposit competition: intensity has stabilized."
        ),
        "keywords": "investment banking recovery IB fees 50 percent growth ECM DCM advisory league tables Visa share monetization financial sponsors",
    },
    ("JPM", "2024Q3"): {
        "headline": "Credit card delinquency normalization — not deterioration",
        "strategic": (
            "Card credit performance is normalizing toward pre-pandemic levels. Net charge-off rate in "
            "card was 3.5 percent, up from 2.6 percent a year ago. We want to emphasize: this is "
            "normalization, not deterioration. Our through-the-cycle loss models anticipated this "
            "trajectory, and underwriting remains disciplined. The consumer is broadly healthy, but "
            "lower-income segments are stretched."
        ),
        "financial": (
            "Net income was $12.9 billion, EPS $4.37, revenue $42.6 billion. ROTCE was 19 percent. "
            "NII ex-Markets was $91.5 billion full-year 2024 run rate. 2025 NII ex-Markets guidance "
            "is $87 to $88 billion, reflecting the full impact of rate cuts."
        ),
        "segment": (
            "CCB revenue was $17.8 billion, card loans up 11 percent. CIB $17.0 billion with IB fees up "
            "31 percent. Markets $7.2 billion."
        ),
        "qa": (
            "On card loss curve: we expect charge-off rates to stabilize around 3.6 percent range in 2025, "
            "consistent with a soft landing base case. On CRE office: we are past peak concern. On 2025 "
            "NII: assumes 150 basis points cumulative cuts."
        ),
        "keywords": "credit card delinquency normalization pre-pandemic levels through-cycle loss models lower-income stretched soft landing",
    },
    ("JPM", "2024Q4"): {
        "headline": "2025 NII outlook and Basel III endgame reproposal",
        "strategic": (
            "Looking into 2025, the two key themes are the NII trajectory and the Basel III endgame. "
            "On NII: we expect NII ex-Markets of approximately $90 billion for 2025, a modest upward "
            "revision driven by slower anticipated rate cuts. On Basel III endgame: the reproposal from "
            "the Federal Reserve reduces the capital impact meaningfully versus the original proposal. "
            "We welcome the more risk-sensitive approach."
        ),
        "financial": (
            "Full year 2024 net income was $58.5 billion, a record. Fourth quarter net income was $14.0 "
            "billion, EPS $4.81, revenue of $43.7 billion. CET1 ratio was 15.7 percent."
        ),
        "segment": (
            "CCB revenue was $18.4 billion. CIB revenue was $17.6 billion. Commercial Banking "
            "$3.6 billion. AWM $5.8 billion."
        ),
        "qa": (
            "On 2025 NII trajectory: the quarterly glide path is roughly $22 to $23 billion through the "
            "year. On excess capital deployment: buyback pace will remain elevated until clarity on "
            "endgame finalization. On credit: broadly stable, with continued card normalization."
        ),
        "keywords": "2025 NII outlook 90 billion Basel III endgame reproposal capital impact reduction record full year earnings excess capital",
    },
    # ============ JNJ ============
    ("JNJ", "2023Q1"): {
        "headline": "Pharmaceutical pipeline momentum and DARZALEX growth",
        "strategic": (
            "Our Innovative Medicine business is performing well, led by DARZALEX, which grew 18 percent "
            "globally in multiple myeloma. We filed for six major regulatory approvals this quarter, "
            "including TALVEY and TECVAYLI in multiple myeloma expansion indications. Our pipeline "
            "continues to produce, and we remain confident in our 2025 target of $57 billion in Innovative "
            "Medicine sales."
        ),
        "financial": (
            "Reported sales were $24.7 billion, up 5.6 percent operationally. Adjusted EPS was $2.68. "
            "Pharmaceutical sales of $13.4 billion grew 7.2 percent operationally. MedTech sales of "
            "$7.5 billion grew 6.4 percent."
        ),
        "segment": (
            "DARZALEX $2.4 billion, STELARA $2.4 billion, TREMFYA $782 million. MedTech Orthopedics "
            "and Cardiovascular grew mid-single digits. Consumer Health pending separation."
        ),
        "qa": (
            "On DARZALEX duration ahead of biosimilars: we have patent protection and lifecycle management "
            "well into the late decade. On TREMFYA IBD readouts: Phase 3 data in Crohn's is a major near-"
            "term catalyst. On STELARA biosimilar timing: first biosimilar entry expected in early 2025 US."
        ),
        "keywords": "DARZALEX multiple myeloma pipeline TALVEY TECVAYLI regulatory filings Innovative Medicine 57 billion target",
    },
    ("JNJ", "2023Q2"): {
        "headline": "Kenvue separation completed — J&J becomes a two-segment company",
        "strategic": (
            "We completed the separation of Kenvue, our consumer health business, through an exchange "
            "offer. This is a transformational milestone, creating a more focused Johnson & Johnson "
            "centered on Innovative Medicine and MedTech. We retained approximately 9.5 percent of "
            "Kenvue shares post-exchange. The separation unlocks focused capital allocation and "
            "management attention for our healthcare innovation platforms."
        ),
        "financial": (
            "Reported sales were $25.5 billion. Adjusted EPS was $2.80. Pharmaceutical growth was 6.0 "
            "percent operationally. MedTech grew 14.7 percent reported, including Abiomed acquisition."
        ),
        "segment": (
            "DARZALEX $2.5 billion, STELARA $2.7 billion. MedTech Cardiovascular accelerated with "
            "Abiomed contributing. Vision and Orthopedics solid."
        ),
        "qa": (
            "On post-separation capital allocation framework: a strong commitment to the dividend, M&A "
            "that reinforces our therapy platforms, and share repurchases. On Kenvue retained stake: we "
            "will dispose in a disciplined manner. On MedTech margin path: Abiomed is accretive over time."
        ),
        "keywords": "Kenvue separation exchange offer two-segment focused company 9.5 percent retained stake Abiomed integration",
    },
    ("JNJ", "2023Q3"): {
        "headline": "Abiomed pulsed field ablation and electrophysiology momentum",
        "strategic": (
            "Our MedTech Cardiovascular business is a standout performer this year, driven by our "
            "electrophysiology franchise. Abiomed's Impella platform continues to grow globally, and we "
            "are very encouraged by early readouts from the admIRE study of our VARIPULSE pulsed field "
            "ablation system. PFA is a transformational technology for atrial fibrillation, and we expect "
            "to be a leader in this emerging modality."
        ),
        "financial": (
            "Reported sales were $21.4 billion post-Kenvue exit. Adjusted EPS was $2.66. Innovative "
            "Medicine $13.9 billion, MedTech $7.5 billion."
        ),
        "segment": (
            "DARZALEX $2.5 billion. MedTech EP grew double digits. Orthopedics posted mid-single digits. "
            "Vision soft on competitive dynamics in contact lenses."
        ),
        "qa": (
            "On PFA competitive dynamics: the market is moving fast with multiple entrants but clinical "
            "differentiation will matter. On STELARA exclusivity: litigation settlements gave us visibility "
            "into 2025 biosimilar launches. On talc litigation: we continue to pursue resolution."
        ),
        "keywords": "Abiomed Impella electrophysiology pulsed field ablation VARIPULSE admIRE study atrial fibrillation",
    },
    ("JNJ", "2023Q4"): {
        "headline": "Talc litigation strategy reset and reserve posture",
        "strategic": (
            "We want to address talc litigation directly. After two prior attempts at a prepackaged "
            "bankruptcy solution for LTL Management, we are now pursuing resolution through traditional "
            "litigation channels. We have increased our reserves by $7 billion this year, bringing total "
            "reserves to approximately $10 billion. We continue to maintain the scientific position that "
            "our talc products are safe."
        ),
        "financial": (
            "Full year 2023 reported sales $85.2 billion. Q4 sales $21.4 billion. Adjusted EPS $2.29 "
            "for the quarter. Full year adjusted EPS $10.07."
        ),
        "segment": (
            "Innovative Medicine $14.0 billion. MedTech $7.7 billion, closing a strong year. Key drug "
            "contributions similar to prior quarter."
        ),
        "qa": (
            "On talc reserve adequacy: the $10 billion reserve is our best estimate of reasonably estimable "
            "resolution. On 2024 guidance: we expect operational sales growth of 5 to 6 percent. On "
            "STELARA biosimilar: formal US entry expected Q1 2025 with Humira-like erosion curve."
        ),
        "keywords": "talc litigation LTL Management bankruptcy rejection 10 billion reserve traditional litigation Humira-like erosion",
    },
    ("JNJ", "2024Q1"): {
        "headline": "Shockwave Medical acquisition announced",
        "strategic": (
            "We announced an agreement to acquire Shockwave Medical for approximately $13.1 billion, "
            "adding intravascular lithotripsy to our cardiovascular platform. Shockwave's IVL technology "
            "addresses calcified coronary and peripheral artery disease, a large and growing clinical "
            "need. Combined with our existing EP and Abiomed platforms, this creates the most "
            "comprehensive interventional cardiovascular portfolio in the industry."
        ),
        "financial": (
            "Reported sales $21.4 billion, up 3.9 percent operationally ex-COVID. Adjusted EPS $2.71. "
            "Innovative Medicine $13.6 billion, MedTech $7.8 billion."
        ),
        "segment": (
            "DARZALEX $2.7 billion. MedTech Cardiovascular up 7 percent pre-Shockwave. Vision improving."
        ),
        "qa": (
            "On Shockwave strategic rationale: IVL has a long runway for growth and our global channel "
            "accelerates penetration. On financing: a combination of debt and cash; accretive to EPS "
            "in year two. On STELARA biosimilar: Q1 2025 launches confirmed."
        ),
        "keywords": "Shockwave Medical acquisition 13.1 billion intravascular lithotripsy IVL calcified arteries interventional cardiology",
    },
    ("JNJ", "2024Q2"): {
        "headline": "Pipeline in focus — TREMFYA IBD and next-wave bispecifics",
        "strategic": (
            "Our pipeline is entering a particularly productive phase. TREMFYA received FDA approval "
            "in ulcerative colitis and filed in Crohn's, opening a multi-billion dollar expansion. "
            "Our bispecific antibody franchise — TECVAYLI, TALVEY, and RYBREVANT in lung cancer — "
            "continues to ramp. We are also advancing early pipeline in neuroscience and immunology, "
            "with several compounds moving into pivotal trials."
        ),
        "financial": (
            "Reported sales $22.4 billion, up 4.3 percent operationally ex-COVID. Adjusted EPS $2.82. "
            "Innovative Medicine $14.5 billion, MedTech $8.0 billion."
        ),
        "segment": (
            "DARZALEX $2.9 billion. TREMFYA $1.0 billion. STELARA $2.7 billion pre-biosimilar. RYBREVANT "
            "growth accelerating."
        ),
        "qa": (
            "On TREMFYA IBD ramp: we see TREMFYA exceeding $5 billion at peak. On bispecifics durability: "
            "TECVAYLI and TALVEY show deep responses, and combinations are a key focus. On Shockwave: "
            "closing expected in second half."
        ),
        "keywords": "TREMFYA IBD approval ulcerative colitis Crohn's bispecific antibodies RYBREVANT lung cancer pipeline expansion",
    },
    ("JNJ", "2024Q3"): {
        "headline": "STELARA biosimilar erosion begins",
        "strategic": (
            "STELARA biosimilar competition commenced in the US this quarter. We expect modest price "
            "impact in Q4, accelerating to 40 to 50 percent volume erosion through 2025. We estimate "
            "$4 to $5 billion of STELARA US revenue at risk in 2025. Our growth portfolio — TREMFYA, "
            "DARZALEX, CARVYKTI, bispecifics, and new launches — is designed to more than offset this "
            "over time, but 2025 will be a transition year."
        ),
        "financial": (
            "Reported sales $22.5 billion, up 5.2 percent operationally. Adjusted EPS $2.42. Innovative "
            "Medicine $14.6 billion. MedTech $7.9 billion including partial-quarter Shockwave."
        ),
        "segment": (
            "DARZALEX $3.0 billion. TREMFYA $1.1 billion. STELARA $2.5 billion facing imminent erosion."
        ),
        "qa": (
            "On STELARA erosion pacing: 40 to 50 percent US volume erosion by 2H 2025. On TREMFYA IBD "
            "absorption: IL-23 mechanism advantages support strong share capture. On talc: pursuing "
            "third bankruptcy attempt while litigating."
        ),
        "keywords": "STELARA biosimilar launch erosion curve 4 to 5 billion at risk transition year TREMFYA IL-23 offset",
    },
    ("JNJ", "2024Q4"): {
        "headline": "2025 guidance reset and multi-year growth bridge",
        "strategic": (
            "Looking to 2025, we are providing a transparent bridge across the STELARA headwind. "
            "Operational sales growth is expected to be 0.5 to 2.0 percent, with growth ex-STELARA of "
            "5.0 percent or better. Adjusted operational EPS growth is expected to be approximately flat. "
            "We remain confident in accelerating growth in 2026 and beyond as our pipeline launches ramp."
        ),
        "financial": (
            "Full year 2024 sales $88.8 billion. Q4 reported sales $22.5 billion. Adjusted EPS $2.04. "
            "Shockwave now fully integrated into MedTech results."
        ),
        "segment": (
            "Innovative Medicine full year $57.1 billion. MedTech $31.9 billion. Key drugs and devices "
            "all tracking to plan."
        ),
        "qa": (
            "On 2026 reacceleration bridge: pipeline launches plus STELARA lap drive growth back to 5+ "
            "percent. On M&A appetite post-Shockwave: still open to bolt-on, balance sheet supports. "
            "On talc: legal process continues, no new material developments."
        ),
        "keywords": "2025 guidance reset STELARA bridge flat EPS growth 2026 reacceleration pipeline launches multi-year outlook",
    },
    # ============ XOM ============
    ("XOM", "2023Q1"): {
        "headline": "Permian production growth and Guyana ramp",
        "strategic": (
            "We delivered strong first quarter results, driven by continued advantaged growth in our "
            "Permian Basin and Guyana operations. Permian production reached 580,000 barrels per day, "
            "up 40 percent year over year. In Guyana, the Payara development is on schedule for "
            "startup later this year, which will bring Guyana capacity to approximately 620,000 barrels "
            "per day across three FPSOs."
        ),
        "financial": (
            "Earnings were $11.4 billion on revenue of $86.6 billion. Cash flow from operations was "
            "$16.3 billion. Capital expenditures of $6.4 billion were consistent with full-year guidance. "
            "Shareholder returns totaled $8.1 billion including $4.3 billion of buybacks."
        ),
        "segment": (
            "Upstream $6.5 billion. Energy Products $4.2 billion. Chemical Products $371 million. "
            "Specialty Products solid at $774 million."
        ),
        "qa": (
            "On Permian cost trajectory: unit costs continue to decline as we apply cube development. "
            "On Guyana reserves: ongoing appraisal continues to expand the resource base. On capital "
            "allocation: buybacks continue at a $17.5 billion annual pace."
        ),
        "keywords": "Permian Basin 580 thousand barrels Guyana Payara FPSO cube development advantaged growth",
    },
    ("XOM", "2023Q2"): {
        "headline": "Downstream margin normalization and chemical softness",
        "strategic": (
            "Industry refining margins have normalized from the extraordinary levels of 2022. This is "
            "consistent with our expectations and with the historical pattern of margin mean reversion. "
            "Our integrated downstream business remains well-positioned given the complexity of our "
            "refining footprint. Chemical margins are at cyclical lows as supply additions continue to "
            "weigh on polyethylene."
        ),
        "financial": (
            "Earnings were $7.9 billion, down from $17.9 billion in the prior-year quarter. Revenue was "
            "$82.9 billion. Cash flow from operations was $9.4 billion. Capital spending tracked to plan."
        ),
        "segment": (
            "Upstream $4.6 billion. Energy Products $2.4 billion. Chemical Products $828 million with "
            "margin pressure. Specialty Products $657 million."
        ),
        "qa": (
            "On chemical margin recovery timing: trough conditions likely through 2023, with recovery "
            "into 2024 as demand stabilizes. On M&A environment: we continue to screen opportunities "
            "that meet our return hurdles. On Low Carbon Solutions: progressing on CCS commercial contracts."
        ),
        "keywords": "downstream margin normalization refining mean reversion chemical cyclical lows polyethylene oversupply Low Carbon Solutions",
    },
    ("XOM", "2023Q3"): {
        "headline": "Pioneer Natural Resources merger announced",
        "strategic": (
            "We announced an all-stock agreement to acquire Pioneer Natural Resources for approximately "
            "$60 billion in equity value. This transaction transforms our Permian position, adding more "
            "than 850,000 net acres with high-quality inventory. Combined with our existing Permian, we "
            "will have the most extensive and contiguous acreage position in the basin with approximately "
            "1.3 million net acres. We expect to close in the first half of 2024."
        ),
        "financial": (
            "Earnings were $9.1 billion on revenue of $90.8 billion. Cash flow from operations was "
            "$16.0 billion. Free cash flow was $11.7 billion. Shareholder distributions $8.1 billion."
        ),
        "segment": (
            "Upstream $5.7 billion. Energy Products $2.4 billion. Chemical Products $249 million. "
            "Guyana production ramping with Payara."
        ),
        "qa": (
            "On Pioneer synergies: we expect $2 billion annualized by 2026. On regulatory approval: we "
            "are confident in the path, given competitive Permian landscape. On cultural integration: "
            "common operating philosophy on capital discipline."
        ),
        "keywords": "Pioneer Natural Resources acquisition 60 billion all-stock Permian 1.3 million acres synergies 2 billion",
    },
    ("XOM", "2023Q4"): {
        "headline": "Denbury and carbon capture platform",
        "strategic": (
            "We closed the acquisition of Denbury in November, adding the largest owned and operated "
            "CO2 pipeline network in the US. This is foundational for our Low Carbon Solutions business, "
            "enabling carbon capture, transportation, and storage offerings to hard-to-abate industrial "
            "emitters. We have signed long-term CCS agreements with CF Industries, Linde, and Nucor. "
            "Low Carbon Solutions is building a real commercial business."
        ),
        "financial": (
            "Full year 2023 earnings $36.0 billion. Q4 earnings $7.6 billion. Full year CFO $55.4 "
            "billion. Shareholder returns $32.4 billion. Debt-to-capital ratio 17 percent."
        ),
        "segment": (
            "Upstream $4.1 billion. Energy Products $3.2 billion. Chemical Products $781 million. "
            "Specialty Products $623 million."
        ),
        "qa": (
            "On CCS commercialization timeline: meaningful revenue contribution from 2025 as contracts "
            "come online. On 2024 production: expect modest growth ex-Pioneer. On Pioneer close timing: "
            "targeting Q2 2024 pending FTC."
        ),
        "keywords": "Denbury acquisition CO2 pipeline carbon capture storage CCS CF Industries Linde Nucor Low Carbon Solutions commercialization",
    },
    ("XOM", "2024Q1"): {
        "headline": "Guyana development acceleration",
        "strategic": (
            "Guyana continues to be one of the greatest deepwater developments in history. We sanctioned "
            "the Whiptail project, which will be the sixth FPSO development in the Stabroek block, "
            "bringing gross production capacity to over 1.3 million barrels per day by 2027. Exploration "
            "success continues, with the resource base now exceeding 11 billion barrels of oil equivalent. "
            "Per-barrel development cost in Guyana is among the lowest in our portfolio."
        ),
        "financial": (
            "Earnings were $8.2 billion on revenue of $83.1 billion. Cash flow from operations was "
            "$14.7 billion. Capital spending was $5.8 billion."
        ),
        "segment": (
            "Upstream $5.7 billion. Energy Products $1.4 billion reflecting narrower crack spreads. "
            "Chemical Products $785 million."
        ),
        "qa": (
            "On Pioneer close timing: FTC review ongoing, tracking to second quarter. On Guyana tax "
            "and royalty regime: stable under the production sharing contract. On Whiptail startup: "
            "targeting 2027."
        ),
        "keywords": "Guyana Whiptail FPSO sixth development 1.3 million barrels Stabroek 11 billion resource exploration success",
    },
    ("XOM", "2024Q2"): {
        "headline": "Pioneer close and integration execution",
        "strategic": (
            "We closed the Pioneer acquisition on May 3rd. Combined Permian production is now approximately "
            "1.3 million barrels of oil equivalent per day, making us the largest producer in the basin. "
            "Integration is tracking ahead of plan — we have begun applying our cube development approach "
            "to Pioneer acreage and are seeing early productivity improvements. Synergies are tracking "
            "to the $2 billion run rate by 2026 with potential upside."
        ),
        "financial": (
            "Earnings were $9.2 billion. Revenue of $93.1 billion. CFO $15.2 billion. Free cash flow "
            "$10.6 billion. Shareholder distributions $9.5 billion including buybacks."
        ),
        "segment": (
            "Upstream $7.1 billion including Pioneer. Energy Products $1.3 billion. Chemical Products "
            "$779 million."
        ),
        "qa": (
            "On Pioneer synergy composition: roughly 50 percent operating efficiency, 25 percent capital "
            "efficiency, 25 percent logistics. On Permian well productivity: 10 to 15 percent uplift on "
            "Pioneer acreage where we have applied technology. On Guyana Yellowtail: on schedule."
        ),
        "keywords": "Pioneer close May 3 Permian 1.3 million barrels largest producer synergies ahead of plan integration execution",
    },
    ("XOM", "2024Q3"): {
        "headline": "Refining capacity additions weighing on downstream",
        "strategic": (
            "Global refining capacity additions, primarily in the Middle East and Asia, are weighing on "
            "crack spreads. Our integrated Gulf Coast operations have maintained capture rates that "
            "outperform the broader industry given complexity and heavy sour crude flexibility. Our "
            "Beaumont expansion continues to run at record throughput. We expect downstream margins to "
            "remain pressured through 2025."
        ),
        "financial": (
            "Earnings were $8.6 billion, EPS $2.01, revenue $90.0 billion. CFO $17.6 billion. Free "
            "cash flow $11.3 billion."
        ),
        "segment": (
            "Upstream $6.2 billion on 4.6 million boe/d record production. Energy Products $1.3 billion. "
            "Chemical Products $893 million up 35 percent."
        ),
        "qa": (
            "On new refining capacity scale: 2 to 3 million bpd adds over two years, material pressure. "
            "On 2025 buyback pace: $20 billion per year trajectory sustainable. On chemical recovery: "
            "seeing signs of margin improvement."
        ),
        "keywords": "refining capacity additions Middle East Asia crack spreads compression Gulf Coast complexity advantage capture rates",
    },
    ("XOM", "2024Q4"): {
        "headline": "2030 plan reiteration and $165B investment envelope",
        "strategic": (
            "We are reaffirming our 2030 corporate plan. Capital spending of $27 to $33 billion through "
            "2030, totaling approximately $165 billion. We expect to grow earnings by $20 billion and "
            "cash flow by $30 billion by 2030 versus 2024 at constant prices. Low Carbon Solutions is "
            "expected to contribute meaningfully by decade-end. We remain committed to returning cash "
            "to shareholders via dividend growth and buybacks at $20 billion annually through 2026."
        ),
        "financial": (
            "Full year 2024 earnings $33.7 billion. Q4 earnings $7.4 billion on revenue $83.4 billion. "
            "CFO $55 billion for the year."
        ),
        "segment": (
            "Upstream full year $25 billion. Energy Products $4.2 billion. Chemical Products $3.3 "
            "billion. Production exited at 4.7 million boe/d."
        ),
        "qa": (
            "On 2030 plan resiliency: designed to compete at low commodity prices. On dividend growth: "
            "42 years of consecutive increases. On Lithium business: pilot progressing on Arkansas."
        ),
        "keywords": "2030 corporate plan 165 billion capital envelope 20 billion earnings growth Low Carbon Solutions dividend aristocrat lithium Arkansas",
    },
    # ============ WMT ============
    ("WMT", "2023Q1"): {
        "headline": "E-commerce growth acceleration and omni integration",
        "strategic": (
            "Our strategy of leveraging our store network for omni fulfillment continues to drive results. "
            "US e-commerce grew 27 percent, with pickup and delivery contributing the majority. We now "
            "reach more than 80 percent of US households with same-day delivery. The convergence of "
            "physical and digital is our core competitive advantage. We are investing in automation to "
            "further improve the unit economics of online orders."
        ),
        "financial": (
            "Consolidated revenue was $152.3 billion, up 7.6 percent constant currency. Walmart US "
            "comps up 7.4 percent. Adjusted EPS was $1.47."
        ),
        "segment": (
            "Walmart US revenue $104.0 billion. Sam's Club $21.5 billion comp growth 7.0 percent "
            "ex-fuel. International $26.8 billion including Walmex strength."
        ),
        "qa": (
            "On operating margin trajectory: still expect modest expansion long term, but near-term mix "
            "pressure from e-commerce and health. On grocery inflation: food inflation is moderating "
            "from peaks. On general merchandise demand: discretionary categories remain soft."
        ),
        "keywords": "e-commerce 27 percent same-day delivery 80 percent households omni fulfillment automation convergence",
    },
    ("WMT", "2023Q2"): {
        "headline": "Flipkart scale and international growth engine",
        "strategic": (
            "Flipkart continues to be a major strategic asset in India, one of the largest and fastest-"
            "growing consumer markets in the world. GMV growth remains strong, with the Big Billion Days "
            "event approaching. PhonePe, which we spun out earlier, continues to scale in digital payments. "
            "Walmex in Mexico also delivered strong results with comps in the high single digits."
        ),
        "financial": (
            "Revenue $161.6 billion, up 5.7 percent CC. Walmart US comps 6.4 percent. Adjusted EPS "
            "$1.84. We raised full-year guidance for the second time."
        ),
        "segment": (
            "Walmart US $110.9 billion. Sam's Club $22.6 billion. International $27.6 billion with "
            "Flipkart and Walmex leading."
        ),
        "qa": (
            "On Flipkart profitability path: focused on unit economics improvement, with BBD festival "
            "key seasonal driver. On advertising growth: Walmart Connect up 35 percent, $2.1 billion "
            "LTM pace. On higher-income customer gains: accelerating and sticky."
        ),
        "keywords": "Flipkart India GMV Big Billion Days PhonePe Walmex Mexico international growth engine",
    },
    ("WMT", "2023Q3"): {
        "headline": "Warehouse automation and supply chain transformation",
        "strategic": (
            "We are in the middle of a multi-year supply chain transformation. We have deployed "
            "automation in our next-generation distribution centers with Symbotic, and we are now "
            "rolling out our Alphabot micro-fulfillment systems to local stores. By 2026, we expect "
            "65 percent of our stores to be serviced by automation, and 55 percent of our fulfillment "
            "center volume will be automated. This is a critical investment in unit economics and speed."
        ),
        "financial": (
            "Revenue $160.8 billion, up 5.2 percent CC. Walmart US comps 4.9 percent. Adjusted EPS "
            "$1.53."
        ),
        "segment": (
            "Walmart US $110.0 billion with general merchandise still soft. Sam's Club $21.9 billion. "
            "International $28.9 billion."
        ),
        "qa": (
            "On automation capex trajectory: peaking in 2024-2025. On general merchandise inflection: "
            "Q3 holiday signal will be key. On Walmart+ membership traction: accelerating subscriber "
            "growth."
        ),
        "keywords": "automation Symbotic Alphabot micro-fulfillment 65 percent stores automated supply chain transformation",
    },
    ("WMT", "2023Q4"): {
        "headline": "Membership and Walmart+ momentum",
        "strategic": (
            "Walmart+ membership continues to grow at a strong double-digit clip. Members spend "
            "approximately 2x to 3x more than non-members, so growing membership is a powerful flywheel. "
            "We added Paramount+ streaming as a benefit, followed by deeper fuel discounts and delivery "
            "upgrades. Sam's Club membership count also reached an all-time high, with Plus tier "
            "outperforming."
        ),
        "financial": (
            "Revenue $173.4 billion, up 5.7 percent CC. Full year FY24 revenue $648.1 billion. "
            "Walmart US comps 4.0 percent. Adjusted EPS $1.80 for the quarter."
        ),
        "segment": (
            "Walmart US $120.9 billion Q4. Sam's Club $23.0 billion. International $29.6 billion."
        ),
        "qa": (
            "On Walmart+ disclosure: we still do not share member count but trends are positive. On "
            "FY25 guidance: sales growth 3-4 percent, operating income 4-6 percent. On Vizio "
            "acquisition: announced to accelerate advertising."
        ),
        "keywords": "Walmart+ membership growth flywheel Paramount streaming fuel discounts Sam's Club Plus tier Vizio acquisition",
    },
    ("WMT", "2024Q1"): {
        "headline": "Higher-income customer gains and grocery share",
        "strategic": (
            "The demographic composition of our customer base continues to evolve. Higher-income "
            "households — those earning over $100,000 — represented the majority of our share gains "
            "in grocery. This is structural and reflects the strength of our value proposition, "
            "convenience of pickup and delivery, and improvements in fresh. This trend is remarkably "
            "resilient across macroeconomic scenarios."
        ),
        "financial": (
            "Revenue $161.5 billion, up 6.0 percent CC. Walmart US comps 3.8 percent. Adjusted EPS "
            "$0.60."
        ),
        "segment": (
            "Walmart US $108.7 billion. Sam's Club $22.1 billion comp 4.6 percent ex-fuel. "
            "International $30.3 billion."
        ),
        "qa": (
            "On higher-income stickiness: strong retention even if inflation moderates; customers "
            "value the experience. On general merchandise: positive unit trends, turning point. On "
            "advertising: Walmart Connect growth 24 percent."
        ),
        "keywords": "higher-income households 100K plus grocery share gains structural shift retention stickiness fresh improvement",
    },
    ("WMT", "2024Q2"): {
        "headline": "Walmart Connect advertising scale",
        "strategic": (
            "Walmart Connect, our advertising business, is reaching meaningful scale. Advertising is "
            "becoming a structural margin tailwind for the company. Walmart Connect US grew 26 percent "
            "in the quarter. We completed the acquisition of Vizio, which accelerates connected TV "
            "advertising capabilities. Combined with our first-party data and in-store digital signage, "
            "we believe Walmart Connect can reach $5 billion+ within 3-4 years."
        ),
        "financial": (
            "Revenue $169.3 billion, up 4.8 percent CC. Walmart US comps 4.2 percent. Adjusted EPS "
            "$0.67. Operating income growth of 8.5 percent."
        ),
        "segment": (
            "Walmart US $115.3 billion. Sam's Club $22.9 billion. International $31.0 billion."
        ),
        "qa": (
            "On advertising margin contribution: incremental margins over 50 percent. On Vizio "
            "integration: early days, TV OS monetization opportunity. On general merchandise: positive "
            "comps and unit inflection confirmed."
        ),
        "keywords": "Walmart Connect 26 percent Vizio acquisition connected TV first-party data 5 billion target advertising margin",
    },
    ("WMT", "2024Q3"): {
        "headline": "General merchandise inflection and comp breadth",
        "strategic": (
            "After multiple quarters of pressure, general merchandise comps turned positive at 0.8 "
            "percent. We are seeing improvement across home, toys, and hardlines. This reflects our "
            "redesigned store layouts, the expansion of our third-party marketplace, and better "
            "execution. Combined with grocery strength, we now have broad-based momentum across "
            "categories — the healthiest composition of comp growth we have seen in several years."
        ),
        "financial": (
            "Revenue $169.6 billion, up 5.5 percent CC. Walmart US comps 5.3 percent. Adjusted EPS "
            "$0.58."
        ),
        "segment": (
            "Walmart US $114.9 billion. Sam's Club $22.7 billion. International $30.3 billion."
        ),
        "qa": (
            "On general merchandise durability: expect continued positive trajectory into Q4. On "
            "holiday outlook: Q4 comps 3-4 percent, we are ready. On higher-income stickiness: "
            "remains resilient."
        ),
        "keywords": "general merchandise inflection positive comps home toys hardlines marketplace expansion broad-based momentum",
    },
    ("WMT", "2024Q4"): {
        "headline": "FY26 guidance and the algorithm of growth",
        "strategic": (
            "Entering fiscal 2026, we are guiding to net sales growth of 3 to 4 percent and adjusted "
            "operating income growth of 3.5 to 5.5 percent. Our model is working: modest comp growth, "
            "margin expansion from alternative revenue streams — advertising, membership, marketplace — "
            "and disciplined capex. We expect the mix of higher-margin businesses to continue to "
            "expand, supporting long-term operating income growth faster than sales."
        ),
        "financial": (
            "Q4 revenue $180.6 billion. Full year FY25 revenue $681.0 billion, up 5.1 percent CC. "
            "Adjusted EPS FY25 $2.51."
        ),
        "segment": (
            "Walmart US full year $462.4 billion. Sam's Club $90.7 billion. International $121.7 "
            "billion."
        ),
        "qa": (
            "On operating income algorithm: advertising, membership, and marketplace collectively "
            "growing 20+ percent. On tariff exposure: diversified sourcing and ability to manage. "
            "On Walmart+: continues strong growth."
        ),
        "keywords": "FY26 guidance operating income algorithm alternative revenue streams advertising membership marketplace tariff diversification",
    },
}

# ---- Q&A bank: generic analyst questions to round out Q&A section ----
GENERIC_QUESTIONS = [
    ("Morgan Stanley", "Can you elaborate on the near-term margin puts and takes and how we should think about exit-rate profitability?"),
    ("Goldman Sachs", "On capital allocation, how are you balancing organic investment, M&A, and shareholder returns given the current environment?"),
    ("Bank of America", "What is your read on the underlying demand environment and how is it trending relative to your internal expectations?"),
    ("Barclays", "Can you speak to competitive dynamics and whether you are gaining or losing share in your core markets?"),
    ("Wells Fargo", "How should we think about the medium-term growth algorithm given the mix shifts you have described?"),
    ("Citi", "On guidance, what are the key assumptions that could drive upside or downside to the range you provided?"),
    ("Evercore ISI", "Can you frame the risk factors you are watching most closely over the next two to three quarters?"),
    ("Jefferies", "How do you think about returning capital versus reinvesting given the opportunity set in front of you?"),
]


def _filler_paragraph(keywords: str, seed_phrase: str) -> str:
    """Produce a distinctive ~250-word paragraph using theme keywords for search diversity."""
    kw = keywords
    return (
        f"{seed_phrase} The themes we have highlighted — {kw} — are central to how we are running the "
        f"business this quarter and how we want investors to evaluate our execution. We continue to stress "
        f"test our assumptions against a range of macroeconomic scenarios, and we maintain a disciplined "
        f"capital allocation framework that prioritizes high-return organic investment, a secure and "
        f"growing dividend, and opportunistic return of excess capital. We are mindful of the competitive "
        f"environment, but we believe our differentiated capabilities position us well. Our leadership team "
        f"and our operators are aligned on priorities, and execution discipline remains the watchword. The "
        f"granular operating metrics behind these results reinforce our confidence in the trajectory we "
        f"have described, and we look forward to demonstrating continued progress in coming quarters.\n\n"
        f"Let me add further context. When we think about {kw}, we view these not as isolated drivers but "
        f"as interlocking parts of a coherent strategic framework. Each reinforces the others, and together "
        f"they define our go-forward priorities. We have quantified management KPIs and incentive "
        f"compensation against progress on these dimensions, and we have aligned board-level reviews to "
        f"the same scorecard. That alignment matters because it ensures that quarter-to-quarter operating "
        f"decisions are made in service of long-term value creation rather than short-term optics. We "
        f"also take seriously our obligation to communicate transparently about both our achievements and "
        f"our setbacks, and we will continue to report metrics that allow investors to hold us accountable. "
        f"The operating cadence, the deployment of technology, the talent development, and the external "
        f"engagement with customers, regulators, and partners are all calibrated against this framework."
    )


def build_transcript(ticker: str, quarter: str, theme: dict[str, str]) -> str:
    ceo_name, company = CEO[ticker]
    cfo_name = CFO[ticker]
    year = quarter[:4]
    q_label = quarter[-2:]

    # ---- 1. Opening Remarks ----
    opening = (
        f"Operator: Good morning, and welcome to the {company} {q_label} {year} Earnings Conference Call. "
        f"All participants are in a listen-only mode. After the prepared remarks there will be a "
        f"question-and-answer session. Today's call is being recorded. I would now like to turn the "
        f"call over to our Head of Investor Relations.\n\n"
        f"Investor Relations: Thank you, operator, and good morning, everyone. Joining me on the call "
        f"today are {ceo_name}, our Chief Executive Officer, and {cfo_name}, our Chief Financial "
        f"Officer. Before we begin, I would like to remind you that today's call will include "
        f"forward-looking statements that are subject to risks and uncertainties. Please refer to our "
        f"most recent filings with the SEC for a discussion of those risks. We will also reference "
        f"non-GAAP financial measures, and reconciliations are available in today's earnings release "
        f"posted on our investor relations website. The theme we want investors to take away from this "
        f"quarter is: {theme['headline']}. With that, I will turn it over to {ceo_name}.\n\n"
    )

    # ---- 2. CEO Strategic Update ----
    ceo_section = (
        f"{ceo_name}, CEO: Thank you, and good morning, everyone. {theme['strategic']}\n\n"
        f"{_filler_paragraph(theme['keywords'], f'Stepping back to put this quarter in context:')}\n\n"
        f"I also want to emphasize our continued focus on talent, culture, and long-term value creation. "
        f"Our global teams have demonstrated resilience and adaptability through a period of elevated "
        f"uncertainty. We are investing in people, technology, and platforms that we believe will compound "
        f"value for our shareholders across multiple cycles. With that, let me hand it to {cfo_name} to "
        f"walk through the financial details.\n\n"
    )

    # ---- 3. CFO Financial Review ----
    cfo_section = (
        f"{cfo_name}, CFO: Thank you, {ceo_name.split()[0]}, and good morning. {theme['financial']}\n\n"
        f"Turning to the balance sheet and cash flow: we continue to operate from a position of financial "
        f"strength. Liquidity remains ample, leverage is well within our stated targets, and we have "
        f"flexibility to deploy capital across the priorities we have outlined. Working capital was "
        f"managed carefully during the quarter, and we saw favorable trends in receivables and inventory "
        f"turns relative to the prior year. Foreign exchange movements were a modest headwind on reported "
        f"revenue but had a limited effect on operating income given our natural hedging and our global "
        f"cost base.\n\n"
        f"On capital returns: we remain committed to the framework we have articulated previously. The "
        f"dividend continues to grow, and opportunistic buybacks have been executed within the authorized "
        f"program. Our longer-term capital deployment priorities remain unchanged: invest in high-return "
        f"organic growth, pursue selective M&A that strengthens our platforms, and return excess capital "
        f"to shareholders. Effective tax rate was within our guided range, and we continue to monitor the "
        f"evolving global tax landscape including Pillar Two implementation.\n\n"
        f"{_filler_paragraph(theme['keywords'], 'From a financial planning perspective, I want to underscore a few points:')}\n\n"
    )

    # ---- 4. Segment Breakdown ----
    segment_section = (
        f"{ceo_name}, CEO: Before we take questions, let me provide additional segment color. "
        f"{theme['segment']}\n\n"
        f"Across the portfolio, we are seeing the benefits of disciplined execution and targeted "
        f"investment. Each segment has its own dynamics, but the common thread is our focus on durable "
        f"competitive advantage and improving unit economics. We continue to drive efficiency initiatives "
        f"across the enterprise, leveraging scale where it matters and maintaining local agility where "
        f"it differentiates. Our segment leaders are aligned on priorities and resourced to execute.\n\n"
        f"{_filler_paragraph(theme['keywords'], 'Looking at segment-level dynamics more closely:')}\n\n"
    )

    # ---- 5. Q&A ----
    qa_intro = "Operator: We will now begin the question-and-answer session. Our first question comes from the line of an analyst.\n\n"
    qa_theme = (
        f"Analyst, Deutsche Bank: Thanks for taking my question. I wanted to drill into the theme you led "
        f"with this quarter. Can you provide more color?\n\n"
        f"{ceo_name}: Happy to. {theme['qa']}\n\n"
    )

    # Pick 5 rotating generic analyst Q&A (unique)
    h = abs(hash((ticker, quarter))) % len(GENERIC_QUESTIONS)
    q_picks = [GENERIC_QUESTIONS[(h + i) % len(GENERIC_QUESTIONS)] for i in range(5)]

    qa_generic_parts = []
    for firm, question in q_picks:
        answerer = cfo_name if "margin" in question.lower() or "capital" in question.lower() or "guidance" in question.lower() else ceo_name
        answer = _filler_paragraph(theme['keywords'], f"Thanks for the question. On that topic,")
        qa_generic_parts.append(
            f"Analyst, {firm}: {question}\n\n{answerer}: {answer}\n\n"
        )

    qa_closing = (
        f"Operator: That concludes today's question-and-answer session. I would like to turn the call "
        f"back over to {ceo_name} for closing remarks.\n\n"
        f"{ceo_name}: Thank you all for joining us today. To summarize: {theme['headline']} — this is the "
        f"story of the quarter, and we believe we are executing well against it. We look forward to "
        f"updating you on our progress next quarter. Have a great day.\n\n"
        f"Operator: This concludes today's conference call. You may now disconnect.\n"
    )

    full = (
        opening +
        ceo_section +
        cfo_section +
        segment_section +
        qa_intro +
        qa_theme +
        "".join(qa_generic_parts) +
        qa_closing
    )
    return full


def main() -> None:
    result: dict[str, list[dict]] = {}
    for ticker in CEO.keys():
        quarters = []
        for quarter, date in QUARTER_DATES.items():
            key = (ticker, quarter)
            theme = THEMES.get(key)
            if theme is None:
                raise RuntimeError(f"Missing theme for {key}")
            text = build_transcript(ticker, quarter, theme)
            quarters.append({
                "quarter": quarter,
                "transcriptdate": date,
                "text": text,
            })
        result[ticker] = quarters

    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # Summary
    print(f"Wrote {OUT}")
    for ticker, qs in result.items():
        wc_list = [len(q["text"].split()) for q in qs]
        print(f"  {ticker}: {len(qs)} quarters, word counts {min(wc_list)}-{max(wc_list)} (avg {sum(wc_list)//len(wc_list)})")


if __name__ == "__main__":
    main()
