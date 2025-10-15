"""Intent service for detecting user intents and matching synonyms."""

import re
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass
from ..types.agent import IntentDetectionResult


@dataclass
class IntentMatch:
    """Base class for intent matches."""
    value: str
    score: float


@dataclass
class VendorMatch(IntentMatch):
    """Vendor match result."""
    type: str = "vendor"


@dataclass
class AttributeMatch(IntentMatch):
    """Attribute match result."""
    type: str = "attribute"
    key: str = ""


@dataclass
class CategoryMatch(IntentMatch):
    """Category match result."""
    type: str = "category"
    level: str = ""


@dataclass
class IntentAnalysis:
    """Intent analysis result."""
    normalized_query: str
    vendor_matches: List[VendorMatch]
    attribute_matches: List[AttributeMatch]
    category_matches: List[CategoryMatch]
    high_confidence_areas: int
    high_confidence: bool
    filter_attributes: Dict[str, Union[str, List[str]]]
    filter_vendors: List[str]
    filter_categories: List[str]
    query_for_search: str
    suggested_facets: List[str]


@dataclass
class IntentStatsSnapshot:
    """Intent statistics snapshot."""
    total_products: Optional[int] = None
    total_attributes: Optional[int] = None
    total_vendors: Optional[int] = None
    total_categories: Optional[int] = None
    top_vendors: List[str] = None
    top_categories: List[str] = None
    top_attributes: List[str] = None


class IntentService:
    """Service for detecting user intents and matching synonyms."""
    
    def __init__(
        self,
        catalog_data: Dict[str, Any],
        synonyms: Optional[Dict[str, Dict[str, List[str]]]] = None,
        top_n: int = 10
    ):
        """Initialize the intent service.
        
        Args:
            catalog_data: Catalog metadata
            synonyms: Synonym mappings
            top_n: Number of top entries to track
        """
        self.catalog_data = catalog_data
        self.top_n = top_n
        self.synonyms = self._normalize_synonym_map(synonyms or {})
        
        # Prepare candidates
        self.vendors: List[Dict[str, Any]] = []
        self.attributes: List[Dict[str, Any]] = []
        self.categories: List[Dict[str, Any]] = []
        self.stats_snapshot: IntentStatsSnapshot
        
        self._prepare_candidates()
        self.stats_snapshot = self._build_stats_snapshot()
    
    def analyze(self, query: str) -> IntentAnalysis:
        """Analyze a query for intent detection.
        
        Args:
            query: User query to analyze
            
        Returns:
            Intent analysis result
        """
        normalized_query = self._normalize_phrase(query)
        tokens = self._tokenize(query)
        token_set = set(tokens)
        self._expand_token_set_with_synonyms(token_set, normalized_query)
        
        vendor_matches = self._match_vendors(token_set, normalized_query)
        attribute_matches = self._match_attributes(token_set, normalized_query)
        category_matches = self._match_categories(token_set, normalized_query)
        
        high_confidence_scores = [
            vendor_matches[0].score if vendor_matches else 0,
            attribute_matches[0].score if attribute_matches else 0,
            category_matches[0].score if category_matches else 0
        ]
        high_confidence_areas = sum(1 for score in high_confidence_scores if score >= 0.9)
        high_confidence = high_confidence_areas >= 2
        
        filter_vendors = [match.value for match in vendor_matches if match.score >= 0.9]
        filter_attributes = self._collect_attribute_filters(attribute_matches)
        filter_categories = [match.value for match in category_matches if match.score >= 0.9]
        
        query_facets = []
        query_facets.extend(filter_categories)
        query_facets.extend(filter_vendors)
        
        for key, value in filter_attributes.items():
            if isinstance(value, list):
                query_facets.extend([f"{key}: {v}" for v in value])
            else:
                query_facets.append(f"{key}: {value}")
        
        query_for_search = (
            f"{query.strip()} | {' | '.join(query_facets)}" if query_facets else query.strip()
        )
        
        suggested_facets = self._build_suggested_facets(
            vendor_matches, attribute_matches, category_matches
        )
        
        return IntentAnalysis(
            normalized_query=normalized_query,
            vendor_matches=vendor_matches,
            attribute_matches=attribute_matches,
            category_matches=category_matches,
            high_confidence_areas=high_confidence_areas,
            high_confidence=high_confidence,
            filter_attributes=filter_attributes,
            filter_vendors=filter_vendors,
            filter_categories=filter_categories,
            query_for_search=query_for_search,
            suggested_facets=suggested_facets
        )
    
    def detect_intent(self, query: str) -> IntentDetectionResult:
        """Detect intent from a query.
        
        Args:
            query: User query
            
        Returns:
            Intent detection result
        """
        analysis = self.analyze(query)
        
        # Determine primary intent
        if analysis.vendor_matches and analysis.vendor_matches[0].score >= 0.8:
            intent = "vendor_search"
            confidence = analysis.vendor_matches[0].score
        elif analysis.category_matches and analysis.category_matches[0].score >= 0.8:
            intent = "category_search"
            confidence = analysis.category_matches[0].score
        elif analysis.attribute_matches and analysis.attribute_matches[0].score >= 0.8:
            intent = "attribute_search"
            confidence = analysis.attribute_matches[0].score
        else:
            intent = "general_search"
            confidence = 0.5
        
        return IntentDetectionResult(
            intent=intent,
            confidence=confidence,
            entities={
                "vendors": analysis.filter_vendors,
                "categories": analysis.filter_categories,
                "attributes": analysis.filter_attributes
            },
            synonyms_matched=analysis.suggested_facets
        )
    
    def detect_info_request(self, query: str) -> Optional[str]:
        """Detect if query is requesting information.
        
        Args:
            query: User query
            
        Returns:
            Type of info request or None
        """
        lowered = query.lower()
        
        # More specific patterns to avoid false positives
        if re.search(r'(what|show|list|tell me about).*(vendor|brand|label)s?', lowered):
            return 'vendors'
        
        if re.search(r'(what|show|list|tell me about).*(category|categories|department|section)s?', lowered):
            return 'categories'
        
        if re.search(r'(what|show|list|tell me about).*(attribute|filter|option|detail)s?', lowered):
            return 'attributes'
        
        return None
    
    def get_top_entries(self, entry_type: str) -> List[str]:
        """Get top entries for a given type.
        
        Args:
            entry_type: Type of entries to get
            
        Returns:
            List of top entries
        """
        if entry_type == 'vendors':
            return self.stats_snapshot.top_vendors or []
        elif entry_type == 'categories':
            return self.stats_snapshot.top_categories or []
        else:
            return self.stats_snapshot.top_attributes or []
    
    def get_stats_snapshot(self) -> IntentStatsSnapshot:
        """Get current statistics snapshot.
        
        Returns:
            Statistics snapshot
        """
        return self.stats_snapshot
    
    def _prepare_candidates(self) -> None:
        """Prepare candidate lists for matching."""
        self._prepare_vendors()
        self._prepare_attributes()
        self._prepare_categories()
    
    def _prepare_vendors(self) -> None:
        """Prepare vendor candidates."""
        vendors = self.catalog_data.get('data', {}).get('vendors', [])
        self.vendors = [
            {
                'kind': 'vendor',
                'value': vendor,
                'normalized': self._normalize_phrase(vendor),
                'tokens': self._tokenize(vendor)
            }
            for vendor in vendors
        ]
    
    def _prepare_attributes(self) -> None:
        """Prepare attribute candidates."""
        names = self.catalog_data.get('data', {}).get('attributes', {}).get('names', [])
        values_by_key = self.catalog_data.get('data', {}).get('attributes', {}).get('values', {})
        
        self.attributes = []
        
        for key in names:
            values = values_by_key.get(key, [])
            for value in values:
                normalized = self._normalize_phrase(value)
                tokens = self._tokenize(value)
                
                if not tokens:
                    continue
                
                synonyms = self._get_attribute_synonyms(key, value)
                
                self.attributes.append({
                    'kind': 'attribute',
                    'key': key,
                    'value': value,
                    'normalized': normalized,
                    'tokens': tokens,
                    'synonyms': synonyms
                })
    
    def _prepare_categories(self) -> None:
        """Prepare category candidates."""
        unique_levels = self.catalog_data.get('data', {}).get('categories', {}).get('unique_levels', {})
        
        levels_in_priority_order = ['level_3', 'level_2', 'level_4', 'level_1']
        added_values = set()
        
        for level in levels_in_priority_order:
            values = unique_levels.get(level, [])
            for value in values:
                normalized = self._normalize_phrase(value)
                if normalized in added_values:
                    continue
                added_values.add(normalized)
                
                tokens = self._tokenize(value)
                if not tokens:
                    continue
                
                self.categories.append({
                    'kind': 'category',
                    'level': level,
                    'value': value,
                    'normalized': normalized,
                    'tokens': tokens
                })
    
    def _build_stats_snapshot(self) -> IntentStatsSnapshot:
        """Build statistics snapshot."""
        stats = self.catalog_data.get('data', {}).get('stats', {})
        vendors = self.catalog_data.get('data', {}).get('vendors', [])
        attribute_names = self.catalog_data.get('data', {}).get('attributes', {}).get('names', [])
        unique_levels = self.catalog_data.get('data', {}).get('categories', {}).get('unique_levels', {})
        
        categories = (
            unique_levels.get('level_3', []) or
            unique_levels.get('level_2', []) or
            unique_levels.get('level_1', [])
        )
        
        return IntentStatsSnapshot(
            total_products=stats.get('total_products'),
            total_attributes=stats.get('total_attributes'),
            total_vendors=len(vendors),
            total_categories=len(categories),
            top_vendors=vendors[:self.top_n],
            top_categories=categories[:self.top_n],
            top_attributes=attribute_names[:self.top_n]
        )
    
    def _match_vendors(self, token_set: Set[str], normalized_query: str) -> List[VendorMatch]:
        """Match vendors against tokens."""
        matches = []
        for candidate in self.vendors:
            score = self._compute_score(token_set, normalized_query, candidate)
            if score > 0:
                matches.append(VendorMatch(value=candidate['value'], score=score))
        
        return sorted(matches, key=lambda x: x.score, reverse=True)[:5]
    
    def _match_attributes(self, token_set: Set[str], normalized_query: str) -> List[AttributeMatch]:
        """Match attributes against tokens."""
        matches = []
        for candidate in self.attributes:
            score = self._compute_attribute_score(token_set, normalized_query, candidate)
            if score > 0:
                matches.append(AttributeMatch(
                    value=candidate['value'],
                    score=score,
                    key=candidate['key']
                ))
        
        return sorted(matches, key=lambda x: x.score, reverse=True)[:5]
    
    def _match_categories(self, token_set: Set[str], normalized_query: str) -> List[CategoryMatch]:
        """Match categories against tokens."""
        matches = []
        for candidate in self.categories:
            score = self._compute_score(token_set, normalized_query, candidate)
            if score > 0:
                matches.append(CategoryMatch(
                    value=candidate['value'],
                    score=score,
                    level=candidate['level']
                ))
        
        return sorted(matches, key=lambda x: x.score, reverse=True)[:5]
    
    def _compute_score(self, token_set: Set[str], normalized_query: str, candidate: Dict[str, Any]) -> float:
        """Compute match score for a candidate."""
        tokens = candidate.get('tokens', [])
        if not tokens:
            return 0
        
        if self._contains_whole_phrase(normalized_query, candidate['normalized']):
            return 1
        
        matches = sum(1 for token in tokens if token in token_set)
        if matches == 0:
            return 0
        
        return matches / len(tokens)
    
    def _compute_attribute_score(self, token_set: Set[str], normalized_query: str, candidate: Dict[str, Any]) -> float:
        """Compute match score for an attribute candidate."""
        score = self._compute_score(token_set, normalized_query, candidate)
        
        if score >= 1:
            return score
        
        synonyms = candidate.get('synonyms', [])
        if synonyms:
            for synonym in synonyms:
                if self._contains_whole_phrase(normalized_query, synonym):
                    return 1
                
                synonym_tokens = synonym.split()
                if synonym_tokens and all(token in token_set for token in synonym_tokens):
                    return 1
        
        return score
    
    def _collect_attribute_filters(self, matches: List[AttributeMatch]) -> Dict[str, Union[str, List[str]]]:
        """Collect attribute filters from matches."""
        threshold = 0.9
        filter_map: Dict[str, Set[str]] = {}
        
        for match in matches:
            if match.score < threshold:
                continue
            
            if match.key not in filter_map:
                filter_map[match.key] = set()
            filter_map[match.key].add(match.value)
        
        filters = {}
        for key, values in filter_map.items():
            unique_values = list(values)
            filters[key] = unique_values[0] if len(unique_values) == 1 else unique_values
        
        return filters
    
    def _build_suggested_facets(
        self,
        vendor_matches: List[VendorMatch],
        attribute_matches: List[AttributeMatch],
        category_matches: List[CategoryMatch]
    ) -> List[str]:
        """Build suggested facets from matches."""
        suggestions = []
        seen = set()
        
        def add_suggestion(value: str) -> None:
            normalized = value.lower()
            if normalized not in seen:
                seen.add(normalized)
                suggestions.append(value)
        
        for match in vendor_matches[:3]:
            add_suggestion(match.value)
        
        for match in category_matches[:3]:
            add_suggestion(match.value)
        
        for match in attribute_matches[:3]:
            add_suggestion(f"{match.key}: {match.value}")
        
        return suggestions[:6]
    
    def _normalize_phrase(self, text: str) -> str:
        """Normalize a phrase for matching."""
        return re.sub(
            r'\s+', ' ',
            re.sub(r'[^a-z0-9\s]', ' ', text.lower().replace('&', ' and '))
        ).strip()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for matching."""
        normalized = self._normalize_phrase(text)
        raw_tokens = normalized.split()
        return [self._stem(token) for token in raw_tokens if token]
    
    def _stem(self, token: str) -> str:
        """Simple stemming for tokens."""
        if len(token) <= 3:
            return token
        
        if token.endswith('ies'):
            return token[:-3] + 'y'
        elif token.endswith('es'):
            return token[:-2]
        elif token.endswith('s'):
            return token[:-1]
        
        return token
    
    def _contains_whole_phrase(self, text: str, phrase: str) -> bool:
        """Check if text contains a whole phrase."""
        if not phrase or not phrase.strip():
            return False
        
        escaped = re.escape(phrase)
        pattern = r'\b' + escaped.replace(r'\ ', r'\s+') + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))
    
    def _get_attribute_synonyms(self, attribute_key: str, attribute_value: str) -> List[str]:
        """Get synonyms for an attribute value."""
        normalized_key = self._normalize_phrase(attribute_key)
        synonyms_by_value = self.synonyms.get(normalized_key, {})
        
        normalized_value = self._normalize_phrase(attribute_value)
        return synonyms_by_value.get(normalized_value, [])
    
    def _expand_token_set_with_synonyms(self, token_set: Set[str], normalized_query: str) -> None:
        """Expand token set with synonyms."""
        for value_map in self.synonyms.values():
            for canonical_value, synonyms in value_map.items():
                if self._contains_whole_phrase(normalized_query, canonical_value):
                    canonical_tokens = canonical_value.split()
                    token_set.update(canonical_tokens)
                
                for synonym in synonyms:
                    if self._contains_whole_phrase(normalized_query, synonym):
                        canonical_tokens = canonical_value.split()
                        token_set.update(canonical_tokens)
    
    def _normalize_synonym_map(
        self, synonym_map: Dict[str, Dict[str, List[str]]]
    ) -> Dict[str, Dict[str, List[str]]]:
        """Normalize synonym map."""
        normalized = {}
        
        for attribute_key, value_map in synonym_map.items():
            normalized_key = self._normalize_phrase(attribute_key)
            if normalized_key not in normalized:
                normalized[normalized_key] = {}
            
            for value_key, synonyms in value_map.items():
                normalized_value = self._normalize_phrase(value_key)
                normalized_synonyms = [
                    self._normalize_phrase(synonym) for synonym in synonyms
                ]
                
                enriched = (
                    normalized_synonyms if normalized_value in normalized_synonyms
                    else [normalized_value] + normalized_synonyms
                )
                
                normalized[normalized_key][normalized_value] = list(set(enriched))
        
        return normalized
