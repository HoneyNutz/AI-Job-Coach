# Refactoring Plan for AI Job Coach

## Current Status
The original `app.py` file is ~1889 lines and becoming difficult to maintain.

## New Structure

### Completed Files:
✅ `ui/__init__.py` - UI package initialization
✅ `ui/styles.py` - All CSS styling (~400 lines)
✅ `ui/navigation.py` - Top navigation bar component (~40 lines)
✅ `ui/components.py` - Reusable components (progress tracker, page headers) (~100 lines)
✅ `utils/__init__.py` - Utils package initialization
✅ `utils/session_state.py` - Session state management (~100 lines)
✅ `utils/file_helpers.py` - File operations for job tracking (~20 lines)
✅ `pages/__init__.py` - Pages package initialization

### Remaining Work:

#### 1. Create `pages/settings.py`
Extract all settings-related functions:
- `render_settings()`
- `render_model_settings()`
- `render_api_key_settings()`
- `render_resume_settings()`
- `render_signature_settings()`

#### 2. Create `pages/job_tracker.py`
Extract job tracker functionality:
- `render_job_tracker()`
- Job listing and management
- Notes editing functionality

#### 3. Create `pages/job_coach.py`
Extract main job coach workflow:
- `render_enter_jd()`
- `render_jd_processed()`
- `render_skill_gap()`
- `render_cover_letter()`
- `render_update_resume()`

#### 4. Update `app.py` to Main Entry Point
Reduce to ~150 lines:
- Page config
- Agent initialization
- Simple routing logic
- Import and call page render functions

## Benefits:
- **Maintainability**: Each file focuses on one feature
- **Readability**: Easier to understand and navigate
- **Collaboration**: Multiple developers can work simultaneously
- **Testing**: Individual modules can be tested in isolation
- **Performance**: Faster load times with lazy imports

## File Size Estimates:
- `app.py`: 1889 → ~150 lines (92% reduction)
- `ui/styles.py`: ~400 lines
- `ui/navigation.py`: ~40 lines
- `ui/components.py`: ~100 lines
- `pages/settings.py`: ~150 lines
- `pages/job_tracker.py`: ~200 lines
- `pages/job_coach.py`: ~800 lines
- `utils/session_state.py`: ~100 lines
- `utils/file_helpers.py`: ~20 lines

Total: ~1960 lines across 9 focused files vs 1889 lines in one monolithic file
