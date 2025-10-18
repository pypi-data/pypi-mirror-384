from typing import List, Dict
import re
from Levenshtein import ratio

from nomenklatura.matching.types import Feature, HeuristicAlgorithm, FtResult, ScoringConfig
from nomenklatura.matching.util import props_pair, FNUL
from followthemoney.proxy import E


class CustomV1Config:
    """Static configuration for CustomV1 matching algorithm"""
    # Main feature weights
    SURNAME_WEIGHT = 0.50
    FIRSTNAME_WEIGHT = 0.35
    MIDDLENAME_WEIGHT = 0.15
    FULLNAME_WEIGHT = 0.30
    
    # DOB component weights
    DOB_YEAR_WEIGHT = 0.09
    DOB_MONTH_WEIGHT = 0.0375
    DOB_DAY_WEIGHT = 0.0225
    
    # Title weight
    TITLE_WEIGHT = 0.05
    
    # Qualifier weights (penalties)
    SURNAME_MISMATCH_PENALTY = -1.0
    FIRSTNAME_MISMATCH_PENALTY = -1.0
    DOB_YEAR_MISMATCH_PENALTY = -0.15
    GENDER_MISMATCH_PENALTY = -0.05
    COUNTRY_MISMATCH_PENALTY = -0.10
    
    # Thresholds
    SURNAME_MIN_THRESHOLD = 0.90
    FIRSTNAME_MIN_THRESHOLD = 0.90
    MIDDLENAME_MIN_THRESHOLD = 0.90


class NameParser:
    """Parse and clean names"""
    
    TITLES = {
        'hon': 'hon', 'hon.': 'hon', 'honorable': 'hon',
        'engr': 'engr', 'engr.': 'engr', 'engineer': 'engr',
        'revrd': 'rev', 'revrd.': 'rev', 'rev': 'rev', 'rev.': 'rev', 'reverend': 'rev',
        'mr': 'mr', 'mr.': 'mr',
        'mrs': 'mrs', 'mrs.': 'mrs',
        'ms': 'ms', 'ms.': 'ms',
        'miss': 'miss',
        'dr': 'dr', 'dr.': 'dr', 'doctor': 'dr',
        'prof': 'prof', 'prof.': 'prof', 'professor': 'prof',
        'sir': 'sir', 'dame': 'dame', 'lord': 'lord', 'lady': 'lady',
        'chief': 'chief', 'alhaji': 'alhaji', 'alhaja': 'alhaja',
        'esq': 'esq', 'esq.': 'esq', 'esquire': 'esq'
    }
    
    @classmethod
    def extract_title(cls, name: str) -> tuple:
        """Extract title from name"""
        parts = name.strip().split()
        if not parts:
            return None, name
        
        first_part = parts[0].lower()
        if first_part in cls.TITLES:
            normalized_title = cls.TITLES[first_part]
            remaining_name = ' '.join(parts[1:])
            return normalized_title, remaining_name
        
        return None, name
    
    @classmethod
    def remove_title(cls, name: str) -> str:
        """Remove title from name"""
        _, name_without_title = cls.extract_title(name)
        return name_without_title
    
    @classmethod
    def normalize_name(cls, name: str) -> str:
        """Normalize name for comparison"""
        name = ' '.join(name.split()).lower()
        name = re.sub(r'[.,\-_]', ' ', name)
        name = ' '.join(name.split())
        return name
    
    @classmethod
    def parse_compound_name(cls, name: str) -> List[str]:
        """Parse compound names"""
        parts = re.split(r'[-\s]+', name.lower())
        return [p for p in parts if p]


# Feature functions
def custom_surname_match(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Match surnames with compound name support"""
    query_surnames, result_surnames = props_pair(query, result, ["lastName"])
    
    if not query_surnames or not result_surnames:
        return FtResult(score=FNUL, detail=None)
    
    best_score = FNUL
    best_match = None
    
    for q_surname, r_surname in zip(query_surnames, result_surnames):
        if not q_surname or not r_surname:
            continue
        
        q_parts = NameParser.parse_compound_name(q_surname)
        r_parts = NameParser.parse_compound_name(r_surname)
        
        if NameParser.normalize_name(q_surname) == NameParser.normalize_name(r_surname):
            return FtResult(score=1.0, detail=f"Exact surname match: {q_surname}")
        
        if len(q_parts) > 1 or len(r_parts) > 1:
            if q_parts and r_parts:
                last_q = q_parts[-1]
                max_score = max(ratio(last_q, rp) for rp in r_parts)
                if max_score > best_score:
                    best_score = max_score
                    best_match = f"Compound surname: {q_surname} ~ {r_surname}"
        else:
            score = ratio(
                NameParser.normalize_name(q_surname),
                NameParser.normalize_name(r_surname)
            )
            if score > best_score:
                best_score = score
                best_match = f"Surname: {q_surname} ~ {r_surname}"
    
    return FtResult(score=best_score, detail=best_match)


def custom_firstname_match(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Match first names with title removal"""
    query_firsts, result_firsts = props_pair(query, result, ["firstName"])
    
    if not query_firsts or not result_firsts:
        return FtResult(score=FNUL, detail=None)
    
    best_score = FNUL
    best_match = None
    
    for q_first, r_first in zip(query_firsts, result_firsts):
        if not q_first or not r_first:
            continue
        
        q_clean = NameParser.remove_title(q_first)
        r_clean = NameParser.remove_title(r_first)
        
        if NameParser.normalize_name(q_clean) == NameParser.normalize_name(r_clean):
            return FtResult(score=1.0, detail=f"Exact firstname match: {q_first}")
        
        score = ratio(
            NameParser.normalize_name(q_clean),
            NameParser.normalize_name(r_clean)
        )
        if score > best_score:
            best_score = score
            best_match = f"Firstname: {q_first} ~ {r_first}"
    
    return FtResult(score=best_score, detail=best_match)


def custom_middlename_match(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Match middle names if present"""
    query_middles, result_middles = props_pair(query, result, ["middleName"])
    
    if not query_middles or not result_middles:
        return FtResult(score=1.0, detail="No middle name to compare")
    
    best_score = FNUL
    best_match = None
    
    for q_middle, r_middle in zip(query_middles, result_middles):
        if not q_middle or not r_middle:
            return FtResult(score=1.0, detail="Middle name optional")
        
        if NameParser.normalize_name(q_middle) == NameParser.normalize_name(r_middle):
            return FtResult(score=1.0, detail=f"Exact middlename match: {q_middle}")
        
        score = ratio(
            NameParser.normalize_name(q_middle),
            NameParser.normalize_name(r_middle)
        )
        if score > best_score:
            best_score = score
            best_match = f"Middlename: {q_middle} ~ {r_middle}"
    
    return FtResult(score=best_score, detail=best_match)


def custom_fullname_match(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Match combined full names"""
    q_firsts = query.get("firstName", [])
    r_firsts = result.get("firstName", [])
    q_middles = query.get("middleName", [])
    r_middles = result.get("middleName", [])
    q_lasts = query.get("lastName", [])
    r_lasts = result.get("lastName", [])
    
    q_parts = []
    r_parts = []
    
    if q_firsts:
        q_parts.append(NameParser.remove_title(q_firsts[0]))
    if r_firsts:
        r_parts.append(NameParser.remove_title(r_firsts[0]))
    
    if q_middles:
        q_parts.append(q_middles[0])
    if r_middles:
        r_parts.append(r_middles[0])
    
    if q_lasts:
        q_parts.append(q_lasts[0])
    if r_lasts:
        r_parts.append(r_lasts[0])
    
    if not q_parts or not r_parts:
        return FtResult(score=FNUL, detail=None)
    
    q_full = NameParser.normalize_name(' '.join(q_parts))
    r_full = NameParser.normalize_name(' '.join(r_parts))
    
    if q_full == r_full:
        return FtResult(score=1.0, detail=f"Exact full name match: {q_full}")
    
    score = ratio(q_full, r_full)
    return FtResult(score=score, detail=f"Full name: {q_full} ~ {r_full}")


def custom_dob_year_match(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Match DOB years"""
    query_dobs, result_dobs = props_pair(query, result, ["birthDate"])
    
    if not query_dobs or not result_dobs:
        return FtResult(score=1.0, detail="No DOB to compare")
    
    for q_dob, r_dob in zip(query_dobs, result_dobs):
        if not q_dob or not r_dob:
            continue
        
        q_year = q_dob.split('-')[0] if '-' in q_dob else q_dob[:4]
        r_year = r_dob.split('-')[0] if '-' in r_dob else r_dob[:4]
        
        if q_year == r_year:
            return FtResult(score=1.0, detail=f"DOB year match: {q_year}")
    
    return FtResult(score=FNUL, detail="DOB year mismatch")


def custom_dob_month_match(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Match DOB months"""
    query_dobs, result_dobs = props_pair(query, result, ["birthDate"])
    
    if not query_dobs or not result_dobs:
        return FtResult(score=1.0, detail="No DOB to compare")
    
    for q_dob, r_dob in zip(query_dobs, result_dobs):
        if not q_dob or not r_dob:
            continue
        
        q_parts = q_dob.split('-')
        r_parts = r_dob.split('-')
        
        if len(q_parts) >= 1 and len(r_parts) >= 1:
            if q_parts[0] != r_parts[0]:
                return FtResult(score=FNUL, detail="Year mismatch")
        
        if len(q_parts) >= 2 and len(r_parts) >= 2:
            if q_parts[1] == r_parts[1]:
                return FtResult(score=1.0, detail=f"DOB month match: {q_parts[0]}-{q_parts[1]}")
    
    return FtResult(score=FNUL, detail="DOB month mismatch")


def custom_dob_day_match(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Match DOB days"""
    query_dobs, result_dobs = props_pair(query, result, ["birthDate"])
    
    if not query_dobs or not result_dobs:
        return FtResult(score=1.0, detail="No DOB to compare")
    
    for q_dob, r_dob in zip(query_dobs, result_dobs):
        if not q_dob or not r_dob:
            continue
        
        q_parts = q_dob.split('-')
        r_parts = r_dob.split('-')
        
        if len(q_parts) >= 2 and len(r_parts) >= 2:
            if q_parts[0] != r_parts[0] or q_parts[1] != r_parts[1]:
                return FtResult(score=FNUL, detail="Year/month mismatch")
        
        if len(q_parts) >= 3 and len(r_parts) >= 3:
            if q_parts[2] == r_parts[2]:
                return FtResult(score=1.0, detail=f"Full DOB match: {q_dob}")
    
    return FtResult(score=FNUL, detail="DOB day mismatch")


def custom_title_match(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Match titles"""
    q_firsts = query.get("firstName", [])
    r_firsts = result.get("firstName", [])
    
    if not q_firsts or not r_firsts:
        return FtResult(score=FNUL, detail=None)
    
    q_title, _ = NameParser.extract_title(q_firsts[0])
    r_title, _ = NameParser.extract_title(r_firsts[0])
    
    if not q_title or not r_title:
        return FtResult(score=FNUL, detail=None)
    
    if q_title == r_title:
        return FtResult(score=1.0, detail=f"Title match: {q_title}")
    
    return FtResult(score=FNUL, detail=f"Title mismatch: {q_title} vs {r_title}")


def custom_gender_mismatch(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Penalty for gender mismatch"""
    query_genders, result_genders = props_pair(query, result, ["gender"])
    
    if not query_genders or not result_genders:
        return FtResult(score=FNUL, detail=None)
    
    for q_gender, r_gender in zip(query_genders, result_genders):
        if not q_gender or not r_gender:
            continue
        
        if q_gender.lower() != r_gender.lower():
            return FtResult(score=1.0, detail=f"Gender mismatch: {q_gender} vs {r_gender}")
    
    return FtResult(score=FNUL, detail=None)


def custom_country_mismatch(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Penalty for country mismatch"""
    query_countries, result_countries = props_pair(query, result, ["country"])
    
    if not query_countries or not result_countries:
        return FtResult(score=FNUL, detail=None)
    
    for q_country, r_country in zip(query_countries, result_countries):
        if not q_country or not r_country:
            continue
        
        if q_country.lower() != r_country.lower():
            return FtResult(score=1.0, detail=f"Country mismatch: {q_country} vs {r_country}")
    
    return FtResult(score=FNUL, detail=None)


def custom_dob_year_mismatch(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Penalty for DOB year mismatch"""
    query_dobs, result_dobs = props_pair(query, result, ["birthDate"])
    
    if not query_dobs or not result_dobs:
        return FtResult(score=FNUL, detail=None)
    
    for q_dob, r_dob in zip(query_dobs, result_dobs):
        if not q_dob or not r_dob:
            continue
        
        q_year = q_dob.split('-')[0] if '-' in q_dob else q_dob[:4]
        r_year = r_dob.split('-')[0] if '-' in r_dob else r_dob[:4]
        
        if q_year != r_year:
            return FtResult(score=1.0, detail=f"DOB year mismatch: {q_year} vs {r_year}")
    
    return FtResult(score=FNUL, detail=None)


def custom_surname_mismatch(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Penalty for low surname match"""
    surname_result = custom_surname_match(query, result, config)
    
    if surname_result.score < CustomV1Config.SURNAME_MIN_THRESHOLD:
        return FtResult(score=1.0, detail=f"Surname below threshold: {surname_result.score:.2f}")
    
    return FtResult(score=FNUL, detail=None)


def custom_firstname_mismatch(query: E, result: E, config: ScoringConfig) -> FtResult:
    """Penalty for low firstname match"""
    firstname_result = custom_firstname_match(query, result, config)
    
    if firstname_result.score < CustomV1Config.FIRSTNAME_MIN_THRESHOLD:
        return FtResult(score=1.0, detail=f"Firstname below threshold: {firstname_result.score:.2f}")
    
    return FtResult(score=FNUL, detail=None)


class CustomV1(HeuristicAlgorithm):
    """
    Custom matching algorithm optimized for person matching
    """
    
    NAME = "custom-v1"
    
    features = [
        # Main name matching features
        Feature(func=custom_surname_match, weight=CustomV1Config.SURNAME_WEIGHT),
        Feature(func=custom_firstname_match, weight=CustomV1Config.FIRSTNAME_WEIGHT),
        Feature(func=custom_middlename_match, weight=CustomV1Config.MIDDLENAME_WEIGHT),
        Feature(func=custom_fullname_match, weight=CustomV1Config.FULLNAME_WEIGHT),
        
        # DOB matching features
        Feature(func=custom_dob_year_match, weight=CustomV1Config.DOB_YEAR_WEIGHT),
        Feature(func=custom_dob_month_match, weight=CustomV1Config.DOB_MONTH_WEIGHT),
        Feature(func=custom_dob_day_match, weight=CustomV1Config.DOB_DAY_WEIGHT),
        
        # Title matching
        Feature(func=custom_title_match, weight=CustomV1Config.TITLE_WEIGHT),
        
        # Qualifiers (penalties)
        Feature(func=custom_surname_mismatch, weight=CustomV1Config.SURNAME_MISMATCH_PENALTY, qualifier=True),
        Feature(func=custom_firstname_mismatch, weight=CustomV1Config.FIRSTNAME_MISMATCH_PENALTY, qualifier=True),
        Feature(func=custom_dob_year_mismatch, weight=CustomV1Config.DOB_YEAR_MISMATCH_PENALTY, qualifier=True),
        Feature(func=custom_gender_mismatch, weight=CustomV1Config.GENDER_MISMATCH_PENALTY, qualifier=True),
        Feature(func=custom_country_mismatch, weight=CustomV1Config.COUNTRY_MISMATCH_PENALTY, qualifier=True),
    ]
    
    @classmethod
    def compute_score(
        cls, scores: Dict[str, float], weights: Dict[str, float]
    ) -> float:
        """Compute final score following nomenklatura pattern"""
        mains: List[float] = []
        for feat in cls.features:
            if feat.qualifier:
                continue
            weight = scores.get(feat.name, FNUL) * weights.get(feat.name, FNUL)
            mains.append(weight)
        score = max(mains) if mains else FNUL
        for feat in cls.features:
            if not feat.qualifier:
                continue
            weight = scores.get(feat.name, FNUL) * weights.get(feat.name, FNUL)
            score += weight
        return max(0.0, min(1.0, score))