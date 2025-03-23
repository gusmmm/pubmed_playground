# PubMed and PMC Query Building Instructions

## Overview
This document provides guidelines for AI systems to transform natural language queries into effective PubMed and PubMed Central (PMC) search strings. The instructions focus on creating syntactically correct and effective searches.

## Database Selection

### PubMed vs PMC
- PubMed: For searching all biomedical literature metadata
- PubMed Central (PMC): For searching full-text open access articles
  
### When to Use Each
- Use PubMed for: comprehensive literature searches, finding latest publications
- Use PMC for: accessing full text, open access content, text mining

## Query Structure Fundamentals

### Base Components
- Terms: Individual search words or phrases
- Fields: Specific areas to search within
- Operators: AND, OR, NOT (must be uppercase)
- Filters: Database-specific restrictions

### Field Tags by Database

#### PubMed Tags
- [Title] - Title only search
- [Title/Abstract] - Title and abstract search
- [Author] - Author name search
- [Journal] - Journal name search
- [MeSH Terms] - Medical Subject Headings
- [Date - Publication] - Publication date

#### PMC Tags
- [tiab] - Title and abstract
- [sb] - Subset/filter
- [edat] - Entrez date
- [filter] - PMC-specific filters

## Query Construction Rules

### Basic Syntax Rules
1. Enclose multi-word terms in quotes:
   ```
   "stem cells"[Title]      # Correct
   stem cells[Title]        # Incorrect
   ```

2. Field tags must be attached to terms:
   ```
   "heart attack"[Title]    # Correct
   [Title]"heart attack"    # Incorrect
   ```

3. Use parentheses for complex expressions:
   ```
   (fMRI[Title] OR "functional MRI"[Title]) AND "open access"[sb]
   ```

### Filter Syntax by Database

#### PubMed Filters
```
Open Access: "open access"[Filter]
Date Range: "YYYY/MM/DD"[Date - Publication]
Language: "english"[Language]
Article Type: "journal article"[Publication Type]
```

#### PMC Filters
```
Open Access: "open access"[sb]
Date Range: "YYYY/MM/DD"[edat]
Recent Content: "recent"[filter]
Full Text: "free full text"[sb]
```

## Query Validation Rules

### 1. Field Tag Validation
```
Valid tags:
- [Title]
- [Abstract]
- [Title/Abstract] or [tiab]
- [Author]
- [Journal]
- [MeSH Terms]
- [All Fields]
```

### 2. Date Format Validation
```
Valid: "2024/01/01"[Date - Publication]
Valid: "last 5 years"[PDat]
Invalid: "2024"[Date - Publication]
Invalid: "2024:2025"[Date]
```

### 3. Filter Combinations
```
Maximum filters per query: 3
Order: content -> type -> date

Correct:
(fMRI[Title] OR "functional MRI"[Title]) AND "open access"[sb] AND "2024/01/01"[edat]

Incorrect:
fMRI[Title] AND "open access"[Filter] AND "free fulltext"[filter] AND "english"[Language]
```

## Common Error Patterns and Solutions

### 1. Invalid Filter Combinations
```
WRONG: fMRI[Title] AND "open access"[Filter] AND "free fulltext"[filter]
RIGHT: fMRI[Title] AND "open access"[sb]
```

### 2. Date Range Syntax
```
WRONG: 2024:2025[Date]
RIGHT: "2024/01/01":"2025/12/31"[Date - Publication]
```

### 3. Field Specifier Errors
```
WRONG: "functional MRI"[Title Abstract]
RIGHT: "functional MRI"[Title/Abstract]
```

## Query Testing Protocol

### 1. Component Testing
Test each part of the query separately:
```
Step 1: Test main term
fMRI[Title]

Step 2: Add primary filter
fMRI[Title] AND "open access"[sb]

Step 3: Add date filter
fMRI[Title] AND "open access"[sb] AND "2024/01/01"[edat]
```

### 2. Response Validation
Check these elements in the API response:
```
1. Count > 0
2. Query translation matches intent
3. No warning messages
4. Retrieved PMIDs/PMCIDs are valid
```

### 3. Result Quality Check
Verify that:
```
1. Titles contain search terms
2. Dates match restrictions
3. Access type matches filters
4. Content type is appropriate
```

## Natural Language Query Transformation

### Step 1: Extract Key Components
```
Natural: "Find recent open access fMRI studies"

Components:
- Main concept: fMRI
- Time: recent
- Access: open access
```

### Step 2: Build Query
```
1. Start with main concept:
   (fMRI[Title] OR "functional magnetic resonance imaging"[Title])

2. Add filters:
   AND "open access"[sb]

3. Add time constraint:
   AND "recent"[filter]
```

## Best Practices

1. Always validate field tags before use
2. Use explicit date formats
3. Test queries incrementally
4. Check warning messages
5. Verify result relevance
6. Document query construction steps

## Error Handling

### Common API Errors
1. Invalid filter: Check filter syntax and database compatibility
2. No results: Broaden search terms or remove restrictive filters
3. Query translation error: Verify field tag syntax
4. Too many filters: Simplify query structure

### Recovery Steps
1. Remove problematic components
2. Test simplified query
3. Add components back one at a time
4. Document successful patterns
