
# Fix Retrieval Failure in Long Context Demo

The system fails to retrieve relevant memories in the 5000-turn demo because the memory decay parameters are too aggressive for this duration. Memories from Turn 4500 (Age 500) are decayed to near-zero scores, and older ones are pruned completely.

## User Review Required
> [!IMPORTANT]
> This change adjusts the memory system's internal parameters (`decay_lambda` and `max_memory_age_turns`) to be less aggressive. This allows the system to retain and retrieve memories over longer interaction horizons (5000+ turns).

## Proposed Changes

### Configuration
#### [MODIFY] [config.yaml](file:///C:/Users/shyam.BATCONSOLE/Desktop/neurohack-memory/config.yaml)
- **Increase** `max_memory_age_turns` from `1400` to `6000` to prevent hard-pruning of memories in 5000-turn tests.
- **Decrease** `decay_lambda` from `0.008` to `0.001` to ensure 500-turn-old memories remain relevant (approx 0.6 decay factor instead of 0.018).

## Verification Plan

### Automated Tests
- Run `reproduce_issue.py` (simulating Turn 4500 injection -> Turn 5000 retrieval).
- **Expectation**: The "When can I call?" query should return the "Preference: ... 4 PM and 6 PM" memory with a score > 0.3.

### Manual Verification
- (Optional) Run `demo.py --turns 5000` (Takes ~15 mins).
- User can verify the `RETRIEVAL TEST` section at the end of the demo output.
