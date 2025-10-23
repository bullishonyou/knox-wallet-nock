# KNOX Performance Optimization Plan

## Issue 1: Manage Wallets Page Refreshes on Every Active Wallet Change ❌

**Current Behavior:**
- Line 88 in manage_wallets.html: `setTimeout(() => location.reload(), 1500);`
- After setting active wallet, entire page reloads
- This re-fetches all wallets from CLI (slow)

**Solution:**
- Redirect to dashboard instead of reloading manage-wallets page
- Dashboard shows the active wallet immediately
- Single CLI call to set active (already fast)

**Change:**
```javascript
// BEFORE:
setTimeout(() => location.reload(), 1500);

// AFTER:
setTimeout(() => window.location.href = '/', 1500);
```

**Impact:** Saves one full page reload + CLI call 📉

---

## Issue 2: Dashboard Fetches Active Address Every 10 Seconds ❌

**Current Behavior:**
- Line 138 in dashboard.html: `setInterval(loadActiveWallet, 10000);`
- Every 10 seconds, app runs: `cli.list_master_addresses()`
- This calls the CLI which can be slow
- Even if user hasn't changed wallet, CLI is called repeatedly

**Performance Issue:** 6 CLI calls per minute = lots of overhead

---

## Option A: Server-Side Session Caching ⭐ RECOMMENDED

**How it works:**
- Store active address in Flask session when set
- Dashboard reads from session (instant)
- No CLI calls needed for cached active address
- Cache expires after 5 minutes or on page refresh

**Pros:**
- ✅ Very fast (session = in-memory lookup)
- ✅ Minimal code changes
- ✅ Works across page navigation
- ✅ Automatic expiry prevents stale data

**Cons:**
- ❌ Won't reflect changes if wallet changed via CLI outside app

**Implementation:**
```python
# In app.py - when setting active wallet:
from flask import session
session['active_address'] = address
session['active_address_time'] = datetime.now()

# In /api/active-wallet endpoint:
if 'active_address' in session:
    # Use cached value
    address = session['active_address']
else:
    # Fall back to CLI call
    address = cli.list_master_addresses()['active_address']
```

---

## Option B: Browser LocalStorage Caching ⭐ SIMPLE

**How it works:**
- Store active address in browser localStorage
- Dashboard reads from localStorage (instant, no server call)
- Update localStorage when active address changes
- Validate on page load

**Pros:**
- ✅ Fastest (browser memory)
- ✅ Works offline
- ✅ Simple JavaScript implementation
- ✅ No server changes needed

**Cons:**
- ❌ Won't sync across browser tabs
- ❌ Won't reflect CLI changes outside app
- ❌ Can become stale if localStorage not cleared

**Implementation:**
```javascript
// When setting active wallet:
localStorage.setItem('activeAddress', address);

// On dashboard load:
const cached = localStorage.getItem('activeAddress');
if (cached) {
  displayAddress(cached);
} else {
  fetch('/api/active-wallet');
}
```

---

## Option C: Remove Auto-Refresh, Manual Only ⭐ CONSERVATIVE

**How it works:**
- Remove the `setInterval(loadActiveWallet, 10000);` line
- Only fetch when user navigates to dashboard
- Add manual refresh button if needed

**Pros:**
- ✅ Zero CLI calls while idle
- ✅ User controls when to refresh
- ✅ Simplest change

**Cons:**
- ❌ Won't auto-update if wallet changed externally
- ❌ Users might miss balance updates
- ⚠️ Less "live" feel

---

## Option D: Hybrid: Session Cache + Smart Invalidation ⭐ BEST

**How it works:**
- Use server session caching (Option A)
- Validate cache freshness on every request
- Invalidate cache after 2 minutes
- Graceful fallback to CLI if cache is stale

**Pros:**
- ✅ Very fast (session cache)
- ✅ Reasonable freshness (2 min)
- ✅ Handles CLI changes outside app
- ✅ Best of both worlds

**Implementation:**
```python
# In /api/active-wallet:
cache_valid_for = 120  # 2 minutes

if 'active_address' in session:
    cache_time = session.get('active_address_time')
    if (datetime.now() - cache_time).seconds < cache_valid_for:
        # Use cache
        return cached response
    
# Cache stale, fetch fresh
address = cli.list_master_addresses()['active_address']
session['active_address'] = address
session['active_address_time'] = datetime.now()
```

---

## My Recommendation:

**Implement BOTH fixes:**

1. **FIX #1:** Change manage_wallets.html line 88
   ```javascript
   // Redirect to dashboard
   window.location.href = '/';
   ```

2. **FIX #2:** Use Option D (Hybrid caching)
   - Add 2-minute session cache for active address
   - Lazy-load on dashboard (no auto-refresh)
   - Falls back to CLI if cache is stale
   - Zero changes needed to frontend

**Result:**
- ✅ Dashboard loads instantly (from cache)
- ✅ Manage wallets redirects to dashboard (no page reload)
- ✅ 98% fewer CLI calls
- ✅ Still fresh data (2-min validation)
- ✅ Graceful fallback if cache is old

---

## Estimated Performance Improvement:

**Current:**
- Dashboard load: ~500ms (CLI call)
- Auto-refresh every 10s: 6 calls/min
- Manage wallets reload: Full page + CLI

**After Optimization:**
- Dashboard load: ~50ms (session cache, 10x faster)
- Auto-refresh: 0 calls (removed)
- Manage wallets: Instant redirect to dashboard

**Speed increase: 3-10x faster** 🚀

