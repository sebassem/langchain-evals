# Threshold Configuration Quick Reference

## Default Thresholds
```
CONCISENESS_THRESHOLD=0.7   # 70% minimum
CORRECTNESS_THRESHOLD=0.8   # 80% minimum  
HALLUCINATION_THRESHOLD=0.9 # 90% minimum
```

## Recommended Threshold Ranges

### Conciseness (0.0 - 1.0)
- **0.5-0.6**: Lenient - allows verbose responses
- **0.7-0.8**: Balanced - good middle ground
- **0.9+**: Strict - requires very concise responses

### Correctness (0.0 - 1.0)
- **0.6-0.7**: Lenient - allows some inaccuracies
- **0.8-0.9**: Standard - good accuracy required
- **0.95+**: Strict - near-perfect accuracy needed

### Hallucination (0.0 - 1.0)
- **0.7-0.8**: Lenient - some minor hallucinations allowed
- **0.9-0.95**: Standard - minimal hallucinations
- **0.98+**: Strict - virtually no hallucinations

## Setting Up in GitHub

### Repository Variables (Recommended)
Go to: `Settings > Secrets and Variables > Actions > Variables`

Add these variables:
```
Name: CONCISENESS_THRESHOLD
Value: 0.7

Name: CORRECTNESS_THRESHOLD  
Value: 0.8

Name: HALLUCINATION_THRESHOLD
Value: 0.9
```

### Testing Different Thresholds
You can test different threshold values by:
1. Updating the repository variables
2. Running the workflow manually
3. Observing the results before applying to PRs

## Tips for Setting Thresholds

1. **Start Conservative**: Begin with lower thresholds and increase gradually
2. **Monitor Results**: Track how often evaluations pass/fail over time
3. **Consider Context**: Different types of content may need different thresholds
4. **Team Consensus**: Align threshold values with team quality expectations
5. **Iterative Adjustment**: Fine-tune based on real-world performance
