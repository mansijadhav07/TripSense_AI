# Quick Test Guide - Bug Fixes Verification

## 🎯 Quick Start

### 1. Start Backend API
```bash
cd apps/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend (in new terminal)
```bash
cd apps/web
npm run dev
```

### 3. Open Browser
Navigate to: http://localhost:3000/discover

---

## ✅ Test Checklist

### Test 1: Initial Load
- [ ] Page loads without errors
- [ ] Recommendations appear (12 hotels)
- [ ] No console errors
- [ ] Loading spinner shows briefly

### Test 2: Destination Filter
- [ ] Type "Paris" in destination field
- [ ] Click "Apply & Recalculate"
- [ ] Results update to show Paris hotels
- [ ] Hotel locations show Paris-related names

### Test 3: Rating Filter
- [ ] Move "Min Overall Rating" slider to 4.5
- [ ] Click "Apply & Recalculate"
- [ ] All shown hotels have rating ≥ 4.5 stars
- [ ] Results change from previous

### Test 4: Model Selection
- [ ] Click "Popularity" model tab
- [ ] Results update immediately (no Apply needed)
- [ ] Click "Content-Based" model tab
- [ ] Results update again with different ranking
- [ ] Click "Hybrid Ensemble" model tab
- [ ] Results update to hybrid recommendations

### Test 5: Aspect Weights
- [ ] Move "Cleanliness" slider to 3.0x
- [ ] Move "Service" slider to 2.5x
- [ ] Click "Apply & Recalculate"
- [ ] Results update with new scoring
- [ ] Hotels with high cleanliness scores rank higher

### Test 6: Combined Filters
- [ ] Set destination to "London"
- [ ] Set min rating to 4.0
- [ ] Move "Location" slider to 3.0x
- [ ] Select "Content-Based" model
- [ ] Click "Apply & Recalculate"
- [ ] Results show London hotels with high ratings and good locations

### Test 7: Reset Filters
- [ ] Click "Reset Filters" button (if visible after filtering)
- [ ] All filters reset to defaults
- [ ] Results show broad recommendations

### Test 8: Browser Console
- [ ] Open browser DevTools (F12)
- [ ] Check Console tab
- [ ] Should see NO errors
- [ ] Should NOT see MetaMask errors
- [ ] May see informational logs only

### Test 9: Network Requests
- [ ] Open DevTools Network tab
- [ ] Change a filter and apply
- [ ] See POST request to `/api/v1/recommendations/generate`
- [ ] Click on request, check:
  - [ ] Request payload has correct filters
  - [ ] Response status is 200
  - [ ] Response has recommendations array

### Test 10: Rapid Changes
- [ ] Quickly change model 3-4 times
- [ ] Results update each time
- [ ] No race condition errors
- [ ] UI stays responsive

---

## 🔍 Backend Verification

### Run Test Suite
```bash
python3 test_fixes.py
```

Expected output:
```
============================================================
Testing Backend Recommendation Service
============================================================

1. Initializing RecommendationService...
   ✅ Service initialized with 50780 hotels

2. Generating basic recommendations (hybrid model)...
   ✅ Generated 5 recommendations

[... all tests pass ...]

============================================================
All Backend Tests Passed! ✅
============================================================
```

### Manual API Test
```bash
# Test with curl
curl -X POST http://localhost:8000/api/v1/recommendations/generate \
  -H "Content-Type: application/json" \
  -d '{
    "top_n": 5,
    "model_type": "hybrid",
    "filters": {
      "destination": "Paris",
      "min_rating": 4.0
    },
    "aspect_weights": {
      "cleanliness": 2.0,
      "service": 1.5,
      "location": 1.0,
      "rooms": 1.0,
      "value": 1.0
    }
  }'
```

Expected: JSON response with 5 recommendations

---

## 🐛 What Was Fixed

1. **Static Results** - Filters now properly update recommendations
2. **MetaMask Errors** - Console errors suppressed
3. **API Parsing** - Robust response handling
4. **Race Conditions** - Proper state management
5. **Logging** - Better debugging information

---

## ❌ If You See Issues

### Frontend won't start
```bash
cd apps/web
rm -rf .next node_modules
npm install
npm run dev
```

### Backend won't start
```bash
cd apps/api
pip3 install -r requirements.txt
python3 -m uvicorn main:app --reload
```

### Port already in use
```bash
# Kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9

# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9
```

### API not responding
Check logs in the API terminal for errors

### Recommendations not updating
1. Open browser console (F12)
2. Check Network tab for failed requests
3. Verify API is running on port 8000
4. Check request payload has correct filters

---

## 📸 Expected Screenshots

### Before Fix
- Same hotels appear regardless of filters
- Console shows MetaMask errors
- Changing model doesn't update results

### After Fix
- Different hotels for different destinations
- Clean console (no errors)
- Model changes immediately update results
- Aspect weights affect ranking
- Everything responsive and working

---

## ✨ Success Indicators

✅ All 10 test cases pass
✅ No console errors
✅ Recommendations update in real-time
✅ All filters work correctly
✅ Backend test suite passes
✅ API responds correctly to manual curl tests

---

## 🎉 You're Done!

If all tests pass, the bug fixes are working correctly and the application is fully functional!
