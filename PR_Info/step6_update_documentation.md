# Step 6: Clean Up Documentation

## Objective
Update all documentation to reflect the simplified command structure.

## Tasks

1. **Update USER_GUIDE.md**
   - Remove `init` command section
   - Remove `list-server-types` command section  
   - Update `validate` command section with new functionality
   - Simplify examples

2. **Update README.md**
   - Remove references to removed commands
   - Update command list
   - Simplify quick start guide

3. **Update help texts in code**
   - Check all help strings in `cli_utils.py`
   - Update command descriptions
   - Ensure consistency

4. **Remove unnecessary documentation**
   - Check for any other docs that reference removed commands
   - Remove overly detailed documentation that adds complexity

## Documentation Principles
- **Shorter is better** - remove verbose explanations
- **Show, don't tell** - use examples instead of long descriptions
- **Focus on common use cases** - remove edge case documentation

## Files to Update
- `docs/config/USER_GUIDE.md`
- `docs/config/README.md` (if exists)
- `README.md`
- Help strings in `src/config/cli_utils.py`
- Any example scripts or test files

## Expected Outcome
- Shorter, clearer documentation
- No references to removed commands
- Easier onboarding for new users
