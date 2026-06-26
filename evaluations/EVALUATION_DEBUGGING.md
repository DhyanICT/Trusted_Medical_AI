# Evaluation Debugging Guide

## Common Issues and Solutions

### Issue: Low Precision/Recall Scores Despite Good System Performance

If your system works well in practice but evaluation scores are low, here are the likely causes:

#### 1. **Title Mismatch**
The ground truth expects specific titles, but your database might have slightly different naming.

**Solution**: Check the actual titles in your retrieved chunks:
- Run the evaluation and look at the debug output for the first query
- Compare the retrieved chunk titles with what's in `ground_truth.json`
- Update `ground_truth.json` to match actual data, or vice versa

#### 2. **Case Sensitivity**
Titles might have different capitalization.

**Solution**: The matching logic now handles case-insensitive matching, but verify your data.

#### 3. **Empty Title Requirements**
If `title_contains` is empty in ground truth, it should match any chunk of that kind. The improved matching logic handles this.

#### 4. **Disease Name Variations**
The system might detect "Type 2 diabetes" but the ground truth expects "Type 2 diabetes" - check for exact matches.

**Example**: 
- System detects: "Diabetic coma" 
- Ground truth expects: "Type 2 diabetes"
- These don't match, so `disease_match` will be `false`

#### 5. **Kind Mismatch**
Chunks might be labeled differently than expected.

**Check**: Look at the `kind` field in retrieved chunks vs. `expected_kinds` in ground truth.

## How to Debug

### Step 1: Run Evaluation with Debug Output

The evaluation now prints debug info for the first query:
```bash
cd evaluations
python run_comprehensive_evaluation.py
```

Look for:
- `📋 Retrieved chunks` - Shows what was actually retrieved
- `🎯 Expected` - Shows what ground truth expects
- `📊 Matching results` - Shows precision/recall

### Step 2: Check Retrieved Chunks

The debug output shows:
- The kind of each chunk (disease, drug, reddit)
- The title of each chunk
- The similarity score

Compare these with your `ground_truth.json` expectations.

### Step 3: Verify Ground Truth Matches Your Data

Check if your ground truth expectations match what's actually in your database:

1. **Disease names**: Are they exact matches?
2. **Drug names**: Do they match exactly (e.g., "Metformin" vs "metformin")?
3. **Reddit posts**: Are there actually Reddit posts in your database for the expected diseases?

### Step 4: Update Ground Truth or Data

**Option A**: Update `ground_truth.json` to match your actual data
- Change `title_contains` to match actual titles
- Adjust `min_relevant_chunks` if needed
- Update `expected_kinds` if your data structure differs

**Option B**: Update your data to match ground truth
- Ensure disease names match exactly
- Ensure drug names are consistent
- Load Reddit posts if expected but missing

## Matching Logic Details

The matching function checks:
1. **Kind match**: Chunk kind must match ground truth kind (if specified)
2. **Title match**: 
   - If `title_contains` is specified: chunk title must contain that substring
   - If `title_contains` is empty: any chunk of matching kind is considered relevant

## Example: Type 2 Diabetes Query

**Ground Truth Expects**:
- `kind: "disease"`, `title_contains: "type 2 diabetes"`
- `kind: "drug"`, `title_contains: "metformin"`
- `kind: "reddit"`, `title_contains: ""` (any Reddit post)

**System Retrieves**:
- `[disease] Type 2 diabetes` ✅ Matches
- `[drug] Metformin` ✅ Matches (case-insensitive)
- `[reddit] My experience with diabetes` ✅ Matches (any reddit post)
- `[disease] Diabetic coma` ❌ Doesn't match (wrong disease)

## Improving Evaluation Accuracy

1. **Make ground truth more flexible**: Use partial matches or multiple acceptable titles
2. **Check your data**: Ensure your database has the expected content
3. **Adjust expectations**: If your system retrieves different but still relevant chunks, update ground truth
4. **Use semantic matching**: Consider using embeddings to match semantically similar titles (future enhancement)

## Quick Fix: Relaxed Matching

If you want more lenient matching, you can modify `match_chunk_to_ground_truth` to:
- Use fuzzy string matching
- Check for partial word matches
- Consider synonyms

But for now, the substring matching should work for most cases.

