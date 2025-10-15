# Design of LIGO data cache

## Timestamps

A suggestion: timestamps should be in units of `1/R` where `R` is the data rate of the channel.  
These should be stored in 64 bit ints, which will be enough bits for any channel 1 GHz or less in rate.

The units of these timestamps will be "gps_counts" rather than "gps_seconds".  
The meaning will be counts at rate `R` since 00:00:00 January 6, 1980. 

This has some great benefits:
- Rounding error is restricted to conversion from GPS seconds.  All in-cache calculations are exact.
- Correspondence to data array index is 1:1, reducing multiplications and reducing the risk of a math 
error in the code.

## Segment Definition

For a single channel of type `T`,

```
SEGMENT contains START, DATA
    START is a GPS_COUNT
    DATA is an array of T     
```

### Segment evaluations

```
SEGMENT.END := SEGMENT.START + len(SEGMENT.DATA)
```

following the convention that `SEGMENT.END` is the timestamp of the last element of `SEGMENT.DATA` + 1

### Segment Operations

These are all the basic operations on segments.  Every other operation is composed of these.

#### Join

A pure function that only joins exactly adjacent segments, otherwise fails.

```
JOIN(A,B)  
where A,B are SEGEMENTS
returns SEGMENT or FAIL
    
    if A.START > B.START
        return JOIN(B,A)
    else
        if A.END  == B.START
            return SEGMENT (
                START := A.START
                DATA := concatenate(A.DATA, B.DATA)
            )
        else
            return FAIL
```


#### Split

A pure function that splits a single segment into two, with the later half starting at a given time.

```angular2html
SPLIT(A,T)
where 
    A is SEGMENT
    T is TIMESTAMP
returns (SEGMENT_0, SEGMENT_1) or FAIL
where
    JOIN(SEGMENT_0, SEGMENT_1) == A
    SEGMENT_0.START < SEGMENT_1.START
    SEGMENT_1.START == T
    
    if T >= A.START and T < A.END
        I := T - A.START
        return (
            SEGMENT(
                START := A.START
                DATA := A.DATA[:I]
            ),
            SEGMENT(
                START := T,
                DATA := A.DATA[I:]
            )
        )
    else
        return FAIL
```

### Compound operations

These operations are derived from the fundamental operations

#### Overlap Join

Join two segments that partially overlap.

There's a case where `A.END > B.END`, but we don't need to handle it, since it won't
come up during cache operation.

```angular2html
OVERLAP_JOIN(A,B)
where A,B are segments
returns SEGMENT or FAIl

    if A.START > B.START
        return OVERLAP_JOIN(B,A)
    if A.END  >= B.START and A.END <= B.END
        (L, _) := SPLIT(A, B.START)
        return JOIN(L, B)
    else
        return FAIL
```

## Cache

The cache is an array of non-contiguous segments sorted by `SEGMENT.START`.

```angular2html
CACHE is array of SEGMENTS
GUARANTEES
    for any SEGMENT C[N] in a CACHE, C[N].START > C[N-1].END and
    C[N].END  < C[N+1].START
```

```angular2html
INDEX is an integer or BEFORE, or AFTER
```
An index value is either an integer index into the cache or is `BEFORE` or `AFTER`.

`BEFORE` and `AFTER`  are symbolic values meaning respectively before any element 
of the cache or after any element.

Some conventions for this document: 
 - `BEFORE + 1 == 0`
 - `AFTER == len(C)` 
 - `C[BEFORE] == NONE`
 - `C[AFTER} == NONE`

### Cache evaluations

#### Bounds

Efficient evaluation would use a binary search.

```
LATEST_PREDECESSOR(C, T)
where
    C is a CACHE  
    T is a TIMESTAMP
returns INDEX

    return max(each I where C[I].START <= T, BEFORE) 
```

```
EARLIEST_SUCCESSOR(C,T)
where
    C is a CACHE
    T is a TIMESTAMP
return INDEX
    
    return min(each I where C[I].END >= T, AFTER)
```

### Cache operations

Basic cache operations

#### Drop

Not a pure function.  Mutates `C`.

```angular2html
DROP(C, A)
where 
    C is a CACHE
    A is a SEGMENT
```

Drop a segment from the cache.  The operation succeeds if the segment is not in the cache.

In particular, if we call drop on a segment before it has been inserted into the cache,
the drop succeeds without having to do anything.

#### Insert

Not a pure function.  Mutates `C`.

```angular2html
INSERT(C,A)
where
    C is a CACHE
    A is a SEGMENT
```

Insert a segment into the cache.  The insertion should fail if the guarantees in the `CACHE`
definition aren't met.  This is how the guarantees are maintained.

### Compound operations

#### Add

Add a data segment to the cache

Modifies cache in place.  Not a pure function.

```
ADD(C, A)
where
    C is a CACHE
    A is a SEGMENT
    
    FIRST_INDEX := LATEST_PREDECESSOR(C, A.START)
    LAST_INDEX := EARLIEST_SUCCESSOR(C, A.END)
    
    if LAST_INDEX == FIRST_INDEX
        `# we already contain the new segment, don't do anything
        return
    
    FIRST = C[FIRST_INDEX]
    LAST = C[LAST_INDEX]
        
    # get rid of any totally overlapped segments from the cache    
    for each I where FIRST_INDEX  < I < LAST_INDEX
        DROP(C, C[I])    
        
    NEW_SEGMENT := A
        
    if FIRST != NONE and FIRST.END >= NEW_SEGMENT.START:        
        NEW_SEGMENT := OVERLAP_JOIN(FIRST, NEW_SEGMENT)
        DROP(C, FIRST)            
        
    if LAST != NONE and NEW_SEGMENT.END >= LAST.START
        NEW_SEGMENT := OVERLAP_JOIN(NEW_SEGMENT, LAST)
        DROP(C, LAST)
    
    INSERT(C, NEW_SEGMNENT) 
```