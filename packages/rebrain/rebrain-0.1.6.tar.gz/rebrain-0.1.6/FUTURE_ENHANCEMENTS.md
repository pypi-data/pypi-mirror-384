# Future Enhancements

This document tracks opportunities for improving rebrain's user experience and functionality. These are not urgent bugs, but quality-of-life improvements worth considering for future releases.

---

## UX Improvements

### Simpler Input File Structure
**Current:** Users must create `data/raw/conversations.json` directory structure manually  
**Proposed:** Allow `data/conversations.json` at root level, auto-create internal structure  
**Benefit:** Reduces friction for first-time users - just drop the file and run  
**Implementation:** Add path detection in `rebrain/cli.py:run_pipeline()` to check both locations

**Priority:** Medium  
**Effort:** Low (~30 min)  
**Version Target:** 0.1.4

---

## MCP Enhancements

### stdio Mode Stability
**Current:** stdio mode has known stability issues with Cursor/Claude Desktop  
**Status:** HTTP mode works reliably, documented as recommended approach  
**Future:** Investigate FastMCP stdio transport stability, consider alternative transports  
**Priority:** Low (workaround exists)

---

## Documentation

### Video Walkthrough
**Target:** 5-minute YouTube demo showing end-to-end usage with UV  
**Covers:** Export → Process → MCP setup → Query in Claude  
**Priority:** Low  
**Effort:** Medium

---

## Notes

- Keep Quick Start minimal - complexity goes in advanced sections
- Prioritize zero-setup experience (UV/UVX over pip)
- Test with fresh users before 1.0 release

