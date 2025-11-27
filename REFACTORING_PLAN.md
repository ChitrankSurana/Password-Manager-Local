# Main Window Refactoring Plan

## Problem

`main_window.py` is 3,761 lines - too large for easy maintenance.

## Solution: Split into Logical Modules

### Proposed Structure:

```

src/gui/
├── main_window.py              (Core window - ~800 lines)
├── password_list_manager.py    (List operations - ~1000 lines)
├── password_operations.py      (Add/Edit/Delete - ~800 lines)
├── search_filter_manager.py    (Search/Filter - ~400 lines)
├── toolbar_manager.py          (Toolbar/Menu - ~300 lines)
└── statistics_dashboard.py     (Stats/Analytics - ~400 lines)
```

## Phase 1: Preparation ✅ (Do Now)

- [x] Analyze main_window.py structure
- [x] Identify logical boundaries
- [x] Create refactoring plan
- [ ] Create backup of original file

## Phase 2: Extract Password List Manager (Week 1)

- [ ] Create `password_list_manager.py`
- [ ] Move password list display logic
- [ ] Move list event handlers
- [ ] Test functionality
- [ ] Update imports in main_window.py

## Phase 3: Extract Password Operations (Week 1-2)

- [ ] Create `password_operations.py`
- [ ] Move add password dialog
- [ ] Move edit password dialog
- [ ] Move delete password logic
- [ ] Test all CRUD operations

## Phase 4: Extract Search/Filter (Week 2)

- [ ] Create `search_filter_manager.py`
- [ ] Move search functionality
- [ ] Move filter logic
- [ ] Test search accuracy

## Phase 5: Extract Toolbar/Menu (Week 2)

- [ ] Create `toolbar_manager.py`
- [ ] Move toolbar creation
- [ ] Move menu handlers
- [ ] Test all menu items

## Phase 6: Extract Statistics (Week 3)

- [ ] Create `statistics_dashboard.py`
- [ ] Move statistics display
- [ ] Move analytics logic
- [ ] Test dashboard

## Phase 7: Testing & Cleanup (Week 3)

- [ ] Comprehensive integration testing
- [ ] Update all documentation
- [ ] Remove commented code
- [ ] Final code review

## Estimated Effort: 2-3 weeks

## Risk Level: Medium (extensive testing required)

## Priority: Medium (improves maintainability, not critical for beta)

## Decision: DEFER TO POST-BETA

**Recommendation:** Since your project is production-ready and you want to start beta testing, defer this refactoring until after initial beta feedback. Focus on:

1. Beta testing
2. Gathering user feedback
3. Fixing critical bugs
4. Then tackle this refactoring with clear priorities

The current code works well - refactoring can wait until you have real-world usage data to inform the best way to split the modules.
