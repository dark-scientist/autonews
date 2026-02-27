import logging

logger = logging.getLogger(__name__)

# TIER 1 keywords (score 0.25 each) — unambiguous auto signals
TIER1_KEYWORDS = [
    # Auto OEMs - Stock market names
    'ola electric', 'olaelectric', 'ola ev',
    'sml mahindra', 'sml isuzu',
    'tata motors', 'tatamotors',
    'maruti suzuki', 'marutisuzuki', 'msil',
    'hero motocorp', 'heromotocorp',
    'bajaj auto', 'bajajauto',
    'tvs motor', 'tvsmotor', 'tvs supply chain', 'tvs-sc',
    'eicher motors', 'eichers',
    'ashok leyland', 'ashokleyland',
    'force motors', 'forcemotors',
    'mahindra & mahindra', 'mahindra and mahindra', 'm&m',
    'hyundai motor india', 'hyundai india ipo',
    # Tyre companies
    'mrf limited', 'mrf tyre',
    'ceat tyre', 'ceat ltd',
    'apollo tyres', 'apollo tyre',
    'balkrishna industries', 'bkt tyre',
    # Auto ancillary
    'motherson sumi', 'motherson', 'samvardhana motherson',
    'bosch india', 'bosch ltd',
    'minda industries', 'minda corp', 'uno minda',
    'varroc engineering', 'varroc',
    'endurance technologies', 'endurance tech',
    'suprajit engineering',
    'fiem industries',
    'lumax industries', 'lumax auto',
    'sona blw', 'sona comstar',
    'rane holdings', 'rane brake',
    'gabriel india',
    'sundram fasteners',
    'exide industries', 'exide battery',
    'amara raja', 'amara raja batteries',
    # Stock market auto terms
    'nifty auto', 'nifty auto index',
    'bse auto', 'auto index',
    'auto sector rally', 'auto sector stocks',
    # Industry bodies
    'siam', 'fada', 'acma',
    # Auto events
    'auto expo', 'bharat mobility', 'motoverse',
    'india auto show', 'motor show india',
    # Unambiguous terms
    'automobile', 'automotive industry',
    'vehicle recall', 'car recall',
    'electric vehicle', 'ev charging', 'gigafactory',
    'auto ancillary', 'auto component', 'auto parts maker',
]

# TIER 2 keywords (score 0.15 each) — strong signals
TIER2_KEYWORDS = [
    # Brands
    'tesla', 'toyota', 'honda', 'ford', 'bmw', 'mercedes', 'audi',
    'volkswagen', 'vw', 'hyundai', 'kia', 'nissan', 'chevrolet',
    'general motors', 'gm', 'stellantis', 'chrysler', 'jeep',
    'volvo', 'jaguar', 'land rover', 'porsche', 'ferrari',
    'lamborghini', 'tata motors', 'mahindra', 'maruti', 'suzuki',
    'bajaj', 'hero motocorp', 'tvs motor', 'ola electric', 'ather',
    'rivian', 'lucid motors', 'nio', 'byd', 'xpeng', 'geely',
    'renault', 'peugeot', 'fiat', 'subaru', 'mazda', 'mitsubishi',
    'lexus', 'acura', 'infiniti', 'cadillac', 'buick', 'lincoln',
    'genesis', 'skoda', 'seat', 'cupra', 'alfa romeo',
    # Vehicle types
    'suv', 'sedan', 'hatchback', 'coupe', 'pickup truck', 'pickup',
    'minivan', 'crossover', 'mpv', 'two-wheeler', 'motorcycle',
    'scooter', 'electric bike',
    # EV terms
    'ev ', 'evs', 'bev', 'phev', 'hybrid vehicle',
    'plug-in hybrid', 'battery electric',
    'charging station', 'range anxiety',
    'solid state battery', 'battery pack', 'lithium ion',
    'regenerative braking',
    # Industry terms
    'auto industry', 'car market', 'auto market', 'vehicle sales',
    'car sales', 'dealership', 'dealer network', 'oem',
    'car plant', 'auto plant', 'vehicle production', 'assembly line',
    # Tech
    'adas', 'autonomous driving', 'self-driving', 'autopilot',
    'connected car', 'ota update', 'infotainment', 'powertrain',
    'drivetrain', 'transmission', 'turbocharger', 'internal combustion',
    # Racing
    'formula 1', 'formula one', 'f1', 'nascar', 'motogp', 'indycar',
    'rally racing', 'le mans', 'motorsport',
    # Supply chain
    'tier 1 supplier', 'tier-1 supplier',
    'semiconductor shortage', 'auto supply chain',
    # Auto-adjacent tech
    'xiaomi car', 'xiaomi ev', 'xiaomi auto',
    'apple car', 'apple carplay',
    'google waymo', 'waymo',
    'baidu apollo', 'baidu ev',
    # Charging ecosystem
    'charge zone', 'chargezone',
    'tata power ev', 'tata power charging',
    'statiq', 'kazam ev',
    # Emission/regulations
    'emission norms', 'emission', 'fuel efficiency',
]

# TIER 3 keywords (score 0.08 each) — weak signals
TIER3_KEYWORDS = [
    'automotive', 'vehicle', 'vehicles', 'car', 'cars',
    'fuel', 'fuel price',
    'auto parts', 'auto stock', 'auto shares',
    'two-wheeler stock', 'passenger vehicle stock',
]


def score_article(article: dict) -> tuple[float, list]:
    """Score article based on tiered automobile keyword matching."""
    title = (article.get('title', '') + ' ' + article.get('title', '')).lower()  # title weighted 2x
    body = article.get('content', '')[:1500].lower()
    text = title + ' ' + body
    
    score = 0.0
    matched = []
    
    # Tier 1: Unambiguous auto signals (0.25 each)
    for kw in TIER1_KEYWORDS:
        if kw.lower() in text:
            score += 0.25
            matched.append(f'T1:{kw}')
    
    # Tier 2: Strong signals (0.15 each)
    for kw in TIER2_KEYWORDS:
        if kw.lower() in text:
            score += 0.15
            matched.append(f'T2:{kw}')
    
    # Tier 3: Weak signals (0.08 each)
    for kw in TIER3_KEYWORDS:
        if kw.lower() in text:
            score += 0.08
            matched.append(f'T3:{kw}')
    
    return min(score, 1.0), matched[:5]


def filter_automobile_articles(articles: list, threshold: float = 0.25) -> tuple:
    """Filter articles to automobile-related only using tiered keyword scoring."""
    auto = []
    rejected = []
    
    for a in articles:
        score, keywords = score_article(a)
        if score >= threshold:
            a['auto_score'] = score
            a['auto_keywords'] = keywords
            auto.append(a)
            # Log sample of newly-caught articles
            if score >= 0.25 and any('T1:' in k for k in keywords):
                logger.info(f"[FILTER IN] {a['title'][:50]}... (score={score:.2f}, keywords={keywords[:3]})")
        else:
            rejected.append(a)
    
    logger.info(f"[FILTER] {len(auto)} automobile / {len(rejected)} non-automobile articles")
    return auto, rejected
