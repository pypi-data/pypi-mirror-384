# POLICY: Free AI Models Only for Sampling Operations

**Date**: 2025-01-14  
**Status**: MANDATORY  
**Type**: Policy / Configuration

## Overview

This MCP server MUST ONLY use free AI models for all sampling and query generation operations. Paid models should never be used to avoid incurring costs for users.

## Policy Statement

⚠️ **CRITICAL REQUIREMENT**: All AI-powered sampling, query generation, and query refinement operations MUST use only FREE models (marked as 0x in GitHub Copilot).

## Approved Free Models

As of January 2025, the following models are FREE and approved for use:

- ✅ **Copilot SWE (Preview)** - 0x (Free)
- ✅ **GPT-4.1** - 0x (Free) 
- ✅ **GPT-4o** - 0x (Free)

## Prohibited Paid Models

The following models are PAID and must NOT be used:

- ❌ **Claude Sonnet 3.5** - 1x (Paid)
- ❌ **Claude Sonnet 3.7** - 1x (Paid)
- ❌ **Claude Sonnet 4** - 1x (Paid)
- ❌ **GPT-5 mini** - 0x (may change to paid)
- ❌ **GPT-4o** - 0x (any paid variants)

## Implementation Details

### Configuration

The policy is enforced through `src/core/config.json`:

```json
{
  "ai_models": {
    "preferred_models": [
      "Copilot SWE (Preview)",
      "GPT-4.1",
      "GPT-4o"
    ],
    "use_free_models_only": true,
    "fallback_to_rule_based": true,
    "model_selection_note": "Always prefer free models (0x in GitHub Copilot). Paid models should never be used for sampling operations."
  }
}
```

### Code Safeguards

1. **Module Documentation** (`src/tools/ai_query_builder.py`)
   - Warning in module docstring about free models only
   - Explicit list of approved free models
   - Clear prohibition against paid models

2. **Method Documentation**
   - `_generate_query()`: Documents free model requirement
   - `_refine_query()`: References approved model list
   - Instructions to check config before any AI API calls

3. **Current Implementation**
   - Currently uses **rule-based generation** (100% FREE, no API costs)
   - Future AI integration must respect the free-models-only policy

## Affected Components

### Current Status (Rule-Based)
- ✅ `src/tools/ai_query_builder.py` - Uses rule-based generation (FREE)
- ✅ `src/tools/query_sampler.py` - No AI model usage
- ✅ `src/tools/query_sampler_simple.py` - No AI model usage

### Future AI Integration Points
When AI models are integrated in the future, these operations must use free models only:

1. **Query Generation** (`AIQueryBuilder._generate_query()`)
   - Generate KQL queries from natural language intent
   - Must check `config.ai_models.use_free_models_only` before API calls
   - Must select from `config.ai_models.preferred_models` list

2. **Query Refinement** (`AIQueryBuilder._refine_query()`)
   - Refine queries based on error feedback
   - Same model selection rules apply

3. **Query Suggestions** (`AIQueryBuilder.suggest_query_improvements()`)
   - Suggest improvements to existing queries
   - Same model selection rules apply

## Model Selection Logic (Future)

When implementing AI model integration, use this logic:

```python
# Pseudocode for future AI integration
def select_model(config):
    if not config['ai_models']['use_free_models_only']:
        raise ConfigError("Free models only policy is disabled!")
    
    # Try free models in preference order
    for model in config['ai_models']['preferred_models']:
        if is_model_free(model):
            return model
    
    # Fallback to rule-based if no free models available
    if config['ai_models']['fallback_to_rule_based']:
        logger.warning("No free AI models available, using rule-based generation")
        return None  # Use rule-based
    
    raise NoFreeModelsError("No free models available and fallback disabled")
```

## Monitoring Model Status

Free/paid status of models can change over time. To stay updated:

1. **Check GitHub Copilot UI** - Models marked "0x" are currently free
2. **Review Azure OpenAI Pricing** - For API-based access
3. **Monitor Announcements** - GitHub and Microsoft AI service updates

## Updating This Policy

If model pricing changes:

1. Update the approved/prohibited model lists in this document
2. Update `config.json` preferred models list
3. Update code comments in `ai_query_builder.py`
4. Test that free models are still being selected
5. Notify users of any changes

## Rationale

### Why Free Models Only?

1. **Cost Control**: Prevents unexpected charges for users
2. **Accessibility**: Ensures all users can use sampling features
3. **Transparency**: Clear about resource usage
4. **Sustainability**: Rule-based fallback ensures functionality even without free models

### Alternative Approaches Considered

- ❌ **Allow paid models with usage caps**: Too complex, risk of overages
- ❌ **Require API keys**: Barrier to entry, user friction
- ✅ **Rule-based fallback**: Best alternative, zero cost, deterministic

## Testing Requirements

When implementing AI model integration:

1. **Test Model Selection**
   - Verify only free models are selected
   - Verify paid models are rejected
   - Test fallback to rule-based when no free models available

2. **Test Configuration Validation**
   - Verify `use_free_models_only` flag is respected
   - Test behavior when config is misconfigured

3. **Test Cost Monitoring**
   - Ensure no paid API calls are made
   - Log all model selection decisions

## Compliance

All contributors and future developers MUST:

- ✅ Read and understand this policy
- ✅ Review code changes for AI model usage
- ✅ Verify free-model-only requirement in PRs
- ✅ Update policy when model pricing changes

## Questions & Support

If you need to use paid models for a specific use case:

1. Document the business justification
2. Propose user-opt-in mechanism with cost warnings
3. Discuss with project maintainers
4. Update this policy with approved exceptions

**Default answer**: Use rule-based generation instead of paid models.

---

**Last Updated**: 2025-01-14  
**Next Review**: Check model pricing quarterly or when new models released
